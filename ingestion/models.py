from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from ingestion.db import Base

class Reading(Base):
    __tablename__ = "reading"
    id = Column(Integer, primary_key=True, index=True)
    meter_code = Column(String, index=True, nullable=False)
    ts_iso = Column(String, nullable=False)
    flow_l_min = Column(Float, nullable=False)
    volume_l_cum = Column(Float, nullable=True)
    battery_v = Column(Float, nullable=True)
    rssi_dbm = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
