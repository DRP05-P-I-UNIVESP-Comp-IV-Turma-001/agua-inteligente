# ingestion/main.py
from __future__ import annotations

from datetime import datetime
from typing import Optional, List

import numpy as np
import pandas as pd
from fastapi import FastAPI, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, constr, condecimal
from sqlalchemy import (
    Column, Integer, String, DateTime, Float,
    create_engine, select, func
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# Importa a função analítica (já implementada no módulo analytics)
from analytics.processing import detect_anomalies

# ============================================================
# Configuração do banco SQLite local (arquivo na pasta ingestion/)
# ============================================================
SQLALCHEMY_DATABASE_URL = "sqlite:///./data.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class ReadingORM(Base):
    __tablename__ = "reading"
    id = Column(Integer, primary_key=True, index=True)
    meter_code = Column(String(64), index=True, nullable=False)
    flow_lpm = Column(Float, nullable=False)            # vazão em L/min
    pressure_bar = Column(Float, nullable=True)         # opcional
    temperature_c = Column(Float, nullable=True)        # opcional
    ts = Column(DateTime, nullable=False, index=True, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)

# ============================================================
# Schemas Pydantic (entrada/saída)
# ============================================================
MeterCodeStr = constr(strip_whitespace=True, min_length=1, max_length=64)


class ReadingIn(BaseModel):
    meter_code: MeterCodeStr = Field(..., description="Identificador do hidrômetro/sensor")
    flow_lpm: condecimal(gt=0, max_digits=8, decimal_places=3) = Field(..., description="Vazão em L/min")
    pressure_bar: Optional[condecimal(gt=0, max_digits=6, decimal_places=3)] = Field(None)
    temperature_c: Optional[condecimal(gt=-50, lt=100, max_digits=5, decimal_places=2)] = Field(None)
    ts: Optional[datetime] = Field(None, description="Carimbo UTC; se ausente, preenchido no servidor")


class ReadingOut(BaseModel):
    id: int
    meter_code: str
    flow_lpm: float
    pressure_bar: Optional[float]
    temperature_c: Optional[float]
    ts: datetime

    class Config:
        from_attributes = True  # FastAPI + Pydantic v2: mantém compatibilidade


# ============================================================
# App FastAPI + CORS
# ============================================================
app = FastAPI(title="Água Inteligente - Ingestion")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # em produção, restringir domínios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================
# Endpoints básicos
# ============================================================
@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/readings", response_model=ReadingOut, status_code=201)
def create_reading(payload: ReadingIn, db: Session = Depends(get_db)):
    ts = payload.ts or datetime.utcnow()
    row = ReadingORM(
        meter_code=payload.meter_code,
        flow_lpm=float(payload.flow_lpm),
        pressure_bar=float(payload.pressure_bar) if payload.pressure_bar is not None else None,
        temperature_c=float(payload.temperature_c) if payload.temperature_c is not None else None,
        ts=ts,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@app.get("/readings", response_model=List[ReadingOut])
def list_readings(
    db: Session = Depends(get_db),
    meter_code: Optional[str] = Query(None, description="Filtrar por hidrômetro"),
    since: Optional[datetime] = Query(None, description="Filtrar registros a partir deste instante UTC"),
    limit: int = Query(100, ge=1, le=5000, description="Quantidade máxima de registros"),
):
    stmt = select(ReadingORM).order_by(ReadingORM.ts.desc())
    if meter_code:
        stmt = stmt.filter(ReadingORM.meter_code == meter_code)
    if since:
        stmt = stmt.filter(ReadingORM.ts >= since)
    stmt = stmt.limit(limit)
    return list(db.execute(stmt).scalars())


@app.get("/readings/count")
def count_readings(
    db: Session = Depends(get_db),
    meter_code: Optional[str] = Query(None),
):
    stmt = select(func.count(ReadingORM.id))
    if meter_code:
        stmt = stmt.filter(ReadingORM.meter_code == meter_code)
    total = db.execute(stmt).scalar_one()
    return {"count": total}


# ============================================================
# Endpoint analítico: /analytics/anomalies
# Suporta comutação de método: z-score (padrão) ou IQR
# ============================================================
@app.get("/analytics/anomalies")
def get_anomalies(
    meter_code: Optional[str] = Query(None, description="Filtra por hidrômetro específico"),
    since: Optional[datetime] = Query(None, description="Considera apenas leituras a partir deste UTC"),
    limit: int = Query(200, ge=10, le=5000, description="Máximo de registros analisados"),
    # Parâmetros do método analítico
    method: str = Query("zscore", pattern="^(zscore|iqr)$", description="Método: zscore ou iqr"),
    window: int = Query(20, ge=5, le=240, description="Janela móvel para estatística"),
    zthr: float = Query(3.0, ge=0.5, le=10.0, description="Limiar |z| para z-score"),
    iqrk: float = Query(2.0, ge=0.1, le=6.0, description="Multiplicador do IQR para limites"),
    db: Session = Depends(get_db),
):
    """
    Retorna anomalias calculadas por hidrômetro.

    - method=zscore: usa média/desvio móvel por grupo com janela `window` e limiar `zthr`.
    - method=iqr: usa quartis móveis por grupo com janela `window` e fator `iqrk`.
    """
    # 1) Consulta base
    query = db.query(ReadingORM.meter_code, ReadingORM.flow_lpm, ReadingORM.ts)
    if meter_code:
        query = query.filter(ReadingORM.meter_code == meter_code)
    if since:
        query = query.filter(ReadingORM.ts >= since)

    rows = query.order_by(ReadingORM.ts.desc()).limit(limit).all()
    if not rows:
        return []

    # 2) DataFrame de trabalho
    df = pd.DataFrame(rows, columns=["meter_code", "flow_lpm", "ts"])
    # Garante datetime nativo (UTC assumido). A análise em analytics/ permanece em UTC.
    df["ts"] = pd.to_datetime(df["ts"], utc=True, errors="coerce")

    # 3) Detecção de anomalias
    if method == "iqr":
        result_df = detect_anomalies(df, window=window, method="iqr", iqr_k=iqrk)
    else:
        result_df = detect_anomalies(df, window=window, method="zscore", z_threshold=zthr)

    # 4) Filtra apenas as anomalias
    anomalies_df = result_df[result_df["is_anomaly"] == True].copy()  # noqa: E712

    # 5) Normalização e serialização segura
    # Converte floats e timestamps para formatos estáveis em JSON
    for col in ["flow_lpm", "zscore", "rolling_mean", "rolling_std"]:
        if col in anomalies_df.columns:
            anomalies_df[col] = pd.to_numeric(anomalies_df[col], errors="coerce")

    anomalies_df["ts"] = pd.to_datetime(anomalies_df["ts"], utc=True, errors="coerce")
    anomalies_df = anomalies_df.replace([np.inf, -np.inf], np.nan)
    anomalies_df = anomalies_df.dropna(subset=["ts", "flow_lpm"])

    # Serializa timestamp em ISO-8601 (UTC)
    anomalies_df["ts"] = anomalies_df["ts"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    # 6) Ordena por ts desc e limita resposta final
    anomalies_df = anomalies_df.sort_values("ts", ascending=False).head(limit)

    # 7) Retorno JSON enxuto
    cols = ["meter_code", "ts", "flow_lpm", "is_anomaly"]
    if "zscore" in anomalies_df.columns:
        cols.append("zscore")
    if "rolling_mean" in anomalies_df.columns:
        cols.append("rolling_mean")
    if "rolling_std" in anomalies_df.columns:
        cols.append("rolling_std")

    return anomalies_df[cols].to_dict(orient="records")
