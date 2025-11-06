# analytics/processing.py
# -----------------------------------------------------------------------------
# Módulo: analytics
# Responsabilidade: rotinas de processamento e detecção de anomalias
#                     em séries temporais de vazão (flow_lpm) por hidrômetro.
#
# Esta implementação segue os requisitos definidos para o Projeto Integrador IV:
# - Função principal: detect_anomalies(df, window=20, z_threshold=3.0)
# - Entrada mínima: colunas ['meter_code', 'flow_lpm', 'ts']
# - Processamento por hidrômetro (groupby meter_code), ordenado por ts (UTC)
# - Cálculo de média/DP móveis, z-score e flag de anomalia
# - Robusto a janelas iniciais (NaN não devem gerar anomalia)
# - Não altera o DataFrame original in-place; retorna uma cópia
# - Sem efeitos colaterais de I/O (função pura)
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Iterable, List
import numpy as np
import pandas as pd


# Colunas mínimas exigidas pela função.
_REQUIRED_COLUMNS: List[str] = ["meter_code", "flow_lpm", "ts"]


def _validate_schema(df: pd.DataFrame, required: Iterable[str]) -> None:
    """
    Valida a presença das colunas obrigatórias no DataFrame.
    Lança ValueError com mensagem clara se algo estiver ausente.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame de entrada.
    required : Iterable[str]
        Coleção com os nomes das colunas exigidas.
    """
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            f"DataFrame de entrada não possui as colunas exigidas: {missing}. "
            f"Colunas recebidas: {list(df.columns)}"
        )


def _coerce_and_sort(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cria uma CÓPIA do DataFrame, garante tipos adequados e ordena por
    meter_code e ts. Mantém processamento em UTC.

    Regras:
    - 'meter_code': convertido para string
    - 'flow_lpm': convertido para numérico (valores inválidos viram NaN)
    - 'ts': convertido para datetime timezone-aware em UTC, se possível

    Returns
    -------
    pd.DataFrame
        Cópia ordenada e com tipos coerentes.
    """
    out = df.copy()

    # Normaliza tipos básicos esperados
    out["meter_code"] = out["meter_code"].astype("string")

    # Garante 'flow_lpm' numérico; valores não numéricos viram NaN
    out["flow_lpm"] = pd.to_numeric(out["flow_lpm"], errors="coerce")

    # Converte 'ts' para datetime. Se vier string/naive, torna timezone-aware (UTC).
    out["ts"] = pd.to_datetime(out["ts"], utc=True, errors="coerce")

    # Ordena o fluxo por hidrômetro e tempo
    out = out.sort_values(["meter_code", "ts"],
                          kind="mergesort", ignore_index=True)

    return out


def detect_anomalies(
    df: pd.DataFrame,
    window: int = 20,
    z_threshold: float = 3.0,
    method: str = "zscore",
    iqr_k: float = 1.5,
) -> pd.DataFrame:
    """
    Detecta anomalias por hidrômetro usando um de dois métodos:
      - 'zscore' (padrão): |z| > z_threshold, com média/DP móveis.
      - 'iqr': valores fora de [Q1 - k*IQR, Q3 + k*IQR] em janela móvel.

    Observações:
      - Processamento por grupo (meter_code) e ordenação por ts.
      - Janelas iniciais com NaN não marcam anomalia.
      - Retorna cópia com colunas: rolling_mean, rolling_std, zscore, is_anomaly.
      - Para 'iqr', rolling_mean/rolling_std/zscore ficam NaN; criamos limites
        rolling_low/rolling_high para debug, se desejar evoluir.
    """
    _validate_schema(df, _REQUIRED_COLUMNS)
    out = _coerce_and_sort(df)
    grp = out.groupby("meter_code", sort=False, group_keys=False)

    method = method.lower().strip()
    out["detector"] = method  # somente para inspeção interna

    if method == "zscore":
        rolling_mean = grp["flow_lpm"].rolling(
            window=window, min_periods=window).mean()
        rolling_std = grp["flow_lpm"].rolling(
            window=window, min_periods=window).std(ddof=0)

        out["rolling_mean"] = rolling_mean.to_numpy()
        out["rolling_std"] = rolling_std.to_numpy()

        std_pos = (out["rolling_std"] > 0) & (~out["rolling_std"].isna())
        out["zscore"] = np.nan
        out.loc[std_pos, "zscore"] = (
            (out.loc[std_pos, "flow_lpm"] - out.loc[std_pos, "rolling_mean"])
            / out.loc[std_pos, "rolling_std"]
        )

        z_valid = ~out["zscore"].isna()
        out["is_anomaly"] = False
        out.loc[z_valid & (out["zscore"].abs() > z_threshold),
                "is_anomaly"] = True
        return out

    elif method == "iqr":
        # Para IQR móvel, calculamos Q1 e Q3 por janela e marcamos outliers fora dos limites.
        # Nota: pandas não possui quantis móveis nativos por janela com groupby,
        # então usamos apply sobre cada grupo para simplicidade e clareza neste passo.
        def _iqr_rolling(series: pd.Series) -> pd.DataFrame:
            roll = series.rolling(window=window, min_periods=window)
            q1 = roll.quantile(0.25)
            q3 = roll.quantile(0.75)
            iqr = q3 - q1
            low = q1 - iqr_k * iqr
            high = q3 + iqr_k * iqr
            return pd.DataFrame({"rolling_low": low, "rolling_high": high})

        bounds = grp["flow_lpm"].apply(
            _iqr_rolling).reset_index(level=0, drop=True)
        out = out.join(bounds)

        # zscore/mean/std não se aplicam aqui (mantemos para compatibilidade de colunas)
        out["rolling_mean"] = np.nan
        out["rolling_std"] = np.nan
        out["zscore"] = np.nan

        out["is_anomaly"] = False
        valid = (~out["rolling_low"].isna()) & (~out["rolling_high"].isna())
        out.loc[valid & ((out["flow_lpm"] < out["rolling_low"]) | (
            out["flow_lpm"] > out["rolling_high"])), "is_anomaly"] = True

        return out

    else:
        raise ValueError(f"method inválido: {method}. Use 'zscore' ou 'iqr'.")


# -----------------------------------------------------------------------------
# Bloco de auto-teste opcional
# -----------------------------------------------------------------------------
# Este bloco NÃO será executado quando a função for importada por outros módulos.
# Ele serve apenas como um "sanity check" local e didático para a equipe.
if __name__ == "__main__":
    # Exemplo mínimo com duas séries (dois hidrômetros),
    # contendo um ponto artificialmente anômalo.
    data = {
        "meter_code": ["A"] * 25 + ["B"] * 25,
        "flow_lpm": (
            # Série A: valores estáveis ~10, com um pico anômalo em 25.0
            [10, 10.2, 9.8, 10.1, 10.3, 9.9, 10.0, 10.2, 9.7, 10.1,
             9.9, 10.0, 10.1, 9.8, 10.2, 9.9, 10.0, 10.1, 9.9, 10.2,
             10.0, 10.1, 9.8, 25.0, 10.0]  # <- anômalo
            +
            # Série B: valores estáveis ~5
            [5, 5.1, 5.0, 4.9, 5.2, 5.1, 5.0, 5.0, 4.8, 5.1,
             5.0, 5.0, 5.1, 4.9, 5.0, 4.9, 5.0, 5.2, 5.1, 5.0,
             5.0, 5.1, 5.2, 4.9, 5.0]
        ),
        # Timestamps fictícios em UTC com frequência de 1 minuto
        "ts": pd.date_range("2025-11-02T16:00:00Z", periods=25, freq="min").tolist()
        + pd.date_range("2025-11-02T16:00:00Z",
                        periods=25, freq="min").tolist(),
    }
    demo_df = pd.DataFrame(data)

    result = detect_anomalies(demo_df, window=20, z_threshold=3.0)
    print("Amostra de anomalias detectadas:")
    print(result[result["is_anomaly"]].head(10))
