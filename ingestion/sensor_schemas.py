from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
from typing import Optional

class SensorPayload(BaseModel):
    pond_id: UUID
    ts: datetime = Field(default_factory=datetime.utcnow)
    do_mgl: float = Field(..., ge=0.0, le=20.0, description="Dissolved Oxygen in mg/L")
    ph: float = Field(..., ge=3.0, le=11.0, description="Pond pH level")
    temp_c: float = Field(..., ge=5.0, le=45.0, description="Water temperature in Celsius")
    nh3_mgl: float = Field(..., ge=0.0, le=5.0, description="Ammonia level in mg/L")
    turbidity: float = Field(..., ge=0.0, le=500.0, description="Turbidity in NTU")
    data_quality: Optional[str] = "VALID"

class SensorReadingResponse(BaseModel):
    status: str
    pond_id: UUID
    ts: datetime
    do_mgl: float
    ph: float
    temp_c: float
    nh3_mgl: float
    turbidity: float
    data_quality: str
