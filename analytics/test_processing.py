# analytics/test_processing.py
# -----------------------------------------------------------------------------
# Objetivo: validar a função detect_anomalies() com dados REAIS vindos do Ingestion.
# Fluxo:
#   - Busca leituras em GET /readings?limit=1000
#   - Monta DataFrame (pandas)
#   - Processa com detect_anomalies(df, window=20, z_threshold=3.0)
#   - Imprime até 10 anomalias por meter_code
# Observações:
#   - Processamento interno em UTC; exibição no dashboard pode usar America/Sao_Paulo.
#   - Este script é "cliente" apenas para teste. Não altera o banco.
# -----------------------------------------------------------------------------

from __future__ import annotations

import os
import sys
from typing import Dict, Any, List
import requests
import pandas as pd

# Importa a função implementada no Passo 1
from analytics.processing import detect_anomalies

# Permite configurar o backend via variável de ambiente (opcional)
API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")


def fetch_readings(limit: int = 1000) -> List[Dict[str, Any]]:
    """
    Consulta o endpoint do Ingestion e retorna uma lista de leituras.
    Cada leitura deve conter ao menos: meter_code, flow_lpm, ts
    """
    url = f"{API_BASE}/readings"
    try:
        resp = requests.get(url, params={"limit": limit}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        # Se o backend retorna dict com 'items' ou algo similar, ajuste aqui:
        if isinstance(data, dict) and "items" in data:
            return data["items"]
        # Caso já seja uma lista de leituras:
        if isinstance(data, list):
            return data
        raise ValueError(f"Formato inesperado da resposta: {type(data)}")
    except Exception as e:
        raise RuntimeError(f"Falha ao consultar {url}: {e}") from e


def build_dataframe(rows: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Constrói um DataFrame padronizado com colunas mínimas:
    meter_code, flow_lpm, ts
    """
    if not rows:
        raise ValueError("Nenhuma leitura retornada pelo endpoint /readings.")

    df = pd.DataFrame(rows)

    # Garante colunas obrigatórias; se vierem nomes diferentes, adeque aqui.
    required = ["meter_code", "flow_lpm", "ts"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Colunas ausentes na resposta do backend: {missing}. "
                         f"Colunas recebidas: {list(df.columns)}")

    # Coerção mínima; processamento profundo é feito dentro de detect_anomalies
    df["flow_lpm"] = pd.to_numeric(df["flow_lpm"], errors="coerce")
    df["ts"] = pd.to_datetime(df["ts"], utc=True, errors="coerce")

    return df


def print_anomalies_by_meter(df_out: pd.DataFrame, per_meter_limit: int = 10) -> None:
    """
    Imprime até N anomalias por meter_code, ordenadas por ts desc.
    """
    if "is_anomaly" not in df_out.columns:
        print("DataFrame não contém a coluna 'is_anomaly'. Nada a exibir.")
        return

    anomalies = df_out[df_out["is_anomaly"] == True].copy()
    if anomalies.empty:
        print("Nenhuma anomalia detectada para os parâmetros atuais.")
        return

    # Ordena por ts desc para ver as mais recentes primeiro
    anomalies.sort_values(["meter_code", "ts"], ascending=[
                          True, False], inplace=True)

    # Itera por hidrômetro e mostra cabeçalho
    for meter, chunk in anomalies.groupby("meter_code"):
        print(
            f"\n=== Anomalias para meter_code={meter} (máx {per_meter_limit}) ===")
        cols = ["meter_code", "ts", "flow_lpm", "rolling_mean",
                "rolling_std", "zscore", "is_anomaly"]
        to_show = [c for c in cols if c in chunk.columns]
        print(chunk[to_show].head(per_meter_limit).to_string(index=False))


def main() -> int:
    print(f"[INFO] Usando API_BASE={API_BASE}")
    try:
        rows = fetch_readings(limit=1000)
        print(f"[INFO] Leituras recebidas: {len(rows)}")
        df = build_dataframe(rows)

        # Executa a detecção de anomalias com a configuração padrão
        # df_out = detect_anomalies(df, window=20, z_threshold=3.0)
        df_out = detect_anomalies(df, window=20, method="iqr", iqr_k=1.5)

        # Resumo rápido por hidrômetro
        summary = (
            df_out.groupby("meter_code")["is_anomaly"]
            .agg(total="count", anomalias="sum")
            .reset_index()
        )
        print("\n[RESUMO] Linhas por hidrômetro e contagem de anomalias:")
        print(summary.to_string(index=False))

        # Imprime até 10 anomalias por hidrômetro
        print_anomalies_by_meter(df_out, per_meter_limit=10)

    except Exception as e:
        print(f"[ERRO] {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
