from pydantic import BaseModel, Field

class ReadingIn(BaseModel):
    meter_code: str = Field(..., example="ISA-001")
    ts: str = Field(..., example="2025-11-01T21:20:00Z")
    flow_l_min: float = Field(..., example=12.3)
    volume_l_cum: float | None = Field(None)
    battery_v: float | None = Field(None)
    rssi_dbm: float | None = Field(None)

class ReadingOut(BaseModel):
    id: int
    meter_code: str
    ts_iso: str
    flow_l_min: float
    volume_l_cum: float | None
    battery_v: float | None
    rssi_dbm: float | None

    class Config:
        orm_mode = True
