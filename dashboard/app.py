# dashboard/app.py
from config import API_BASE, TIMEZONE

import time
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, Dict, Any, List

import pandas as pd
import requests
import streamlit as st


import os


@st.cache_data(ttl=10, show_spinner=False)
def fetch_anomalies(
    api_base: str,
    method: str = "zscore",
    window: int = 20,
    zthr: float = 3.0,
    iqrk: float = 2.0,
    meter_code: Optional[str] = None,
    since_iso: Optional[str] = None,
    limit: int = 200,
) -> pd.DataFrame:
    """Consulta /analytics/anomalies e retorna DataFrame SEM quebrar quando vier vazio ou sem colunas esperadas."""
    params: Dict[str, Any] = {
        "method": method,
        "window": window,
        "zthr": zthr,
        "iqrk": iqrk,
        "limit": limit,
    }
    if meter_code:
        params["meter_code"] = meter_code
    if since_iso:
        params["since"] = since_iso

    url = f"{api_base}/analytics/anomalies"
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    # Constrói DF a partir do JSON retornado
    df = pd.DataFrame(data if isinstance(data, list) else [])

    # Garante as colunas esperadas, mesmo que venham ausentes
    expected = ["meter_code", "ts", "flow_lpm", "zscore",
                "rolling_mean", "rolling_std", "is_anomaly"]
    for col in expected:
        if col not in df.columns:
            # cria coluna vazia com dtype apropriado
            if col in ("flow_lpm", "zscore", "rolling_mean", "rolling_std"):
                df[col] = pd.Series(dtype="float64")
            elif col == "is_anomaly":
                df[col] = pd.Series(dtype="bool")
            else:
                df[col] = pd.Series(dtype="object")

    # Tipagens e conversões seguras
    if "ts" in df.columns:
        df["ts"] = pd.to_datetime(df["ts"], utc=True, errors="coerce")
    for col in ["flow_lpm", "zscore", "rolling_mean", "rolling_std"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["is_anomaly"] = df["is_anomaly"].fillna(False).astype(bool)

    # Ordena apenas se houver 'ts' válido
    if "ts" in df.columns:
        try:
            df = df.sort_values("ts", ascending=False, ignore_index=True)
        except Exception:
            # Se houver tipo misto, ignora a ordenação para não quebrar a UI
            df = df.reset_index(drop=True)

    return df


# ---------- Utilidades ----------
@st.cache_data(ttl=5)
def fetch_readings(limit: int = 1000) -> pd.DataFrame:
    """Busca leituras no endpoint /readings e retorna um DataFrame.
    Espera campos: meter_code, flow_lpm, pressure_bar, temperature_c, ts.
    """
    try:
        resp = requests.get(f"{API_BASE}/readings",
                            params={"limit": limit}, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, list):
            data = []
        df = pd.DataFrame(data)
        if df.empty:
            return df
        # Normalizações
        # Garante colunas esperadas
        expected = ["meter_code", "flow_lpm",
                    "pressure_bar", "temperature_c", "ts"]
        for col in expected:
            if col not in df.columns:
                df[col] = None

        # Converte timestamp
        df["ts"] = pd.to_datetime(
            df["ts"], errors="coerce", utc=True).dt.tz_convert(TIMEZONE)

        # Ordena por tempo
        df = df.sort_values("ts")
        # Tipos numéricos
        for col in ["flow_lpm", "pressure_bar", "temperature_c"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        return df
    except Exception as e:
        st.error(f"Falha ao buscar /readings: {e}")
        return pd.DataFrame(columns=["meter_code", "flow_lpm", "pressure_bar", "temperature_c", "ts"])


@st.cache_data(ttl=5)
def fetch_count() -> Optional[int]:
    """Tenta ler o contador bruto em /readings/count, se disponível."""
    try:
        resp = requests.get(f"{API_BASE}/readings/count", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        # Aceita tanto {"count": N} quanto um inteiro simples
        if isinstance(data, dict) and "count" in data:
            return int(data["count"])
        if isinstance(data, int):
            return data
        return None
    except Exception:
        # Silencioso: este endpoint é opcional para o dashboard
        return None


def compute_active_sensors(df: pd.DataFrame, window_minutes: int) -> Tuple[int, int]:
    """Retorna (sensores_ativos_no_intervalo, sensores_unicos_total)."""
    if df.empty:
        return 0, 0
    total_unique = df["meter_code"].nunique(dropna=True)

    # Janela de atividade: últimos N minutos
    t_max = df["ts"].max()
    t_window_start = t_max - timedelta(minutes=window_minutes)
    recent = df[df["ts"] >= t_window_start]
    active_unique = recent["meter_code"].nunique(dropna=True)
    return active_unique, total_unique


def format_kpi(value, suffix: str = "") -> str:
    try:
        if isinstance(value, float):
            return f"{value:,.2f}{suffix}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{value:,}{suffix}".replace(",", ".")
    except Exception:
        return f"{value}{suffix}"


# função para checkar se o Arduino e o "relogio" estão emitindo valores
@st.cache_data(ttl=3)
def check_health() -> bool:
    try:
        r = requests.get(f"{API_BASE}/health", timeout=2)
        r.raise_for_status()
        return True
    except Exception:
        return False


# ---------- Layout ----------
st.set_page_config(
    page_title="Água Inteligente | Dashboard",
    page_icon="💧",
    layout="wide",
)

st.title("💧 Dashboard — Água Inteligente")
st.caption("Monitoramento de vazão em tempo real via FastAPI + Streamlit")

st.sidebar.markdown("### 🔍 Detecção de Anomalias")

method = st.sidebar.selectbox(
    "Método de detecção",
    options=["zscore", "iqr"],
    format_func=lambda x: "Z-score" if x == "zscore" else "IQR",
    index=0,
    help="Z-score é o padrão mais estável; IQR é mais sensível."
)

window = st.sidebar.number_input(
    "Tamanho da janela", min_value=5, max_value=240, value=20, step=1)
if method == "zscore":
    zthr = st.sidebar.slider("Limiar Z", min_value=1.0,
                             max_value=6.0, value=3.0, step=0.1)
    iqrk = 2.0
else:
    iqrk = st.sidebar.slider("Fator IQR", min_value=0.5,
                             max_value=4.0, value=2.0, step=0.1)
    zthr = 3.0

hours_back = st.sidebar.slider("Últimas horas", 1, 72, 24)
since_iso = (datetime.now(timezone.utc) -
             timedelta(hours=hours_back)).isoformat()
limit = st.sidebar.slider("Limite de registros", 50, 2000, 200, 50)
meter_filter = st.sidebar.text_input(
    "Filtrar por hidrômetro (opcional)").strip() or None


st.markdown("## 🚨 Alertas Recentes")

with st.spinner("Consultando anomalias..."):
    df_anom = fetch_anomalies(
        api_base=API_BASE,
        method=method,
        window=window,
        zthr=zthr,
        iqrk=iqrk,
        meter_code=meter_filter,
        since_iso=since_iso,
        limit=limit,
    )

if df_anom.empty:
    st.info("Nenhuma anomalia detectada para os filtros atuais.")
else:
    total_alertas = len(df_anom)
    total_hidr = df_anom["meter_code"].nunique()
    st.metric("Total de alertas", total_alertas)
    st.metric("Hidrômetros afetados", total_hidr)

    st.dataframe(
        df_anom[["meter_code", "ts", "flow_lpm", "zscore", "is_anomaly"]],
        width="stretch",
        hide_index=True
    )


is_up = check_health()
st.markdown(
    f"**Status do servidor Ingestion:** {'🟢 Online' if is_up else '🔴 Offline'}"
)

if not is_up:
    st.stop()


# Barra lateral: controles
st.sidebar.header("Controles")
limit = st.sidebar.slider("Quantidade de leituras a carregar",
                          min_value=200, max_value=5000, value=1000, step=200)
activity_window = st.sidebar.slider(
    "Janela p/ sensor ativo (minutos)", min_value=1, max_value=30, value=5, step=1)
auto_refresh = st.sidebar.checkbox("Atualização automática", value=True)
refresh_sec = st.sidebar.slider(
    "Intervalo de atualização (segundos)", min_value=2, max_value=30, value=5, step=1)

# Área principal: dados
df = fetch_readings(limit=limit)
total_count_backend = fetch_count()

if df.empty:
    st.info("Nenhuma leitura disponível ainda. Aguarde o Edge enviar dados ou verifique o Ingestion.")
    st.stop() 
else:
    # KPIs
    active_now, total_unique = compute_active_sensors(
        df, window_minutes=activity_window)
    latest_ts = df["ts"].max()
    flow_min = float(df["flow_lpm"].min()
                     ) if df["flow_lpm"].notna().any() else 0.0
    flow_max = float(df["flow_lpm"].max()
                     ) if df["flow_lpm"].notna().any() else 0.0
    flow_avg = float(df["flow_lpm"].mean()
                     ) if df["flow_lpm"].notna().any() else 0.0

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("Sensores ativos (janela)", format_kpi(active_now))
    with c2:
        st.metric("Sensores únicos (total)", format_kpi(total_unique))
    with c3:
        st.metric("Vazão média (L/min)", format_kpi(flow_avg))
    with c4:
        st.metric("Vazão máx. (L/min)", format_kpi(flow_max))
    with c5:
        # Mostra contador total se o backend fornecer; caso contrário, mostra total de linhas carregadas
        total_readings = total_count_backend if total_count_backend is not None else len(
            df)
        st.metric("Leituras registradas", format_kpi(total_readings))

    st.markdown("---")

    # Filtros de visualização
    st.subheader("Série temporal de vazão (flow_lpm)")
    left, right = st.columns([2, 1])
    with right:
        meter_filter = st.selectbox(
            "Filtrar por hidrômetro (meter_code)",
            options=["<Todos>"] +
            sorted(df["meter_code"].dropna().unique().tolist()),
            index=0,
        )
        # Janela temporal relativa
        time_window_opt = st.selectbox(
            "Janela de tempo",
            options=["Últimos 15 min", "Última 1 hora", "Tudo"],
            index=0,
        )

    # Aplica filtros
    plot_df = df.copy()
    if meter_filter != "<Todos>":
        plot_df = plot_df[plot_df["meter_code"] == meter_filter]

    if not plot_df.empty:
        tmax = plot_df["ts"].max()
        if time_window_opt == "Últimos 15 min":
            tmin = tmax - timedelta(minutes=15)
            plot_df = plot_df[plot_df["ts"] >= tmin]
        elif time_window_opt == "Última 1 hora":
            tmin = tmax - timedelta(hours=1)
            plot_df = plot_df[plot_df["ts"] >= tmin]

    # ---------- Indicador de alerta por hidrômetro ----------


def has_alert(df: pd.DataFrame, meter: str) -> bool:
    """Retorna True se houver anomalia para o hidrômetro informado."""
    if df.empty or "meter_code" not in df.columns:
        return False
    return (df["meter_code"] == meter).any()


# Exemplo prático: mostra ícone ao lado de cada hidrômetro ativo
st.subheader("Status dos Hidrômetros")
if not df_anom.empty:
    hydr_list = sorted(df["meter_code"].dropna().unique().tolist())
    for meter_name in hydr_list:
        badge = "🔺" if has_alert(df_anom, meter_name) else "✅"
        st.write(f"{badge} **{meter_name}**")
else:
    st.info("Sem anomalias registradas até o momento.")

    # Gráfico
    if plot_df.empty or plot_df["flow_lpm"].isna().all():
        st.warning("Sem dados suficientes para plotar a série temporal.")
    else:
        # Indexa por tempo para facilitar o line_chart
        chart_df = plot_df.set_index("ts")[["flow_lpm"]]
        st.line_chart(chart_df, height=280, width="stretch")

    # Tabela compacta com últimas leituras
    st.subheader("Últimas leituras")
    show_n = st.slider("Quantidade de linhas na tabela", 5, 100, 20)
    st.dataframe(
        df.sort_values("ts", ascending=False)
        .head(show_n)[["ts", "meter_code", "flow_lpm", "pressure_bar", "temperature_c"]]
        .rename(
            columns={
                "ts": "Data/Hora",
                "meter_code": "Hidrômetro",
                "flow_lpm": "Vazão (L/min)",
                "pressure_bar": "Pressão (bar)",
                "temperature_c": "Temp. (°C)",
            }
        ),
        width="stretch", height=320,
    )

    st.caption(
        f"Atualizado por último em: {latest_ts.strftime('%d/%m/%Y %H:%M:%S') if isinstance(latest_ts, pd.Timestamp) else latest_ts}"
    )

# Atualização automática simples via rerun temporizado
if auto_refresh:
    # Evita bloqueio do app: espera e força nova execução do script
    time.sleep(refresh_sec)
    try:
        st.rerun()
    except Exception:
        st.experimental_rerun()
