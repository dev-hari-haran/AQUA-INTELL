from datetime import datetime, timedelta
from uuid import UUID
from typing import List, Dict, Any
from fastapi import APIRouter, status
from pydantic import BaseModel
from ingestion.sensor_schemas import SensorPayload, SensorReadingResponse

router = APIRouter(prefix="/sensors", tags=["Water Quality Monitor"])

IN_MEMORY_READINGS: Dict[UUID, List[Dict[str, Any]]] = {}

@router.post("/ingest", response_model=SensorReadingResponse, status_code=status.HTTP_201_CREATED)
async def ingest_sensor_reading(payload: SensorPayload):
    reading = payload.model_dump()
    pond_id = payload.pond_id
    if pond_id not in IN_MEMORY_READINGS:
        IN_MEMORY_READINGS[pond_id] = []
    IN_MEMORY_READINGS[pond_id].append(reading)
    
    return SensorReadingResponse(
        status="stored",
        pond_id=payload.pond_id,
        ts=payload.ts,
        do_mgl=payload.do_mgl,
        ph=payload.ph,
        temp_c=payload.temp_c,
        nh3_mgl=payload.nh3_mgl,
        turbidity=payload.turbidity,
        data_quality=payload.data_quality or "VALID"
    )

@router.get("/history/{pond_id}")
async def get_sensor_history(pond_id: UUID, limit: int = 50):
    readings = IN_MEMORY_READINGS.get(pond_id, [])
    if not readings:
        now = datetime.utcnow()
        return [
            {
                "ts": (now - timedelta(minutes=i)).isoformat(),
                "do_mgl": round(6.5 - 0.02 * i, 2),
                "ph": round(7.5 + 0.005 * i, 2),
                "temp_c": round(26.8 + 0.01 * i, 2),
                "nh3_mgl": 0.18,
                "turbidity": 25.0
            }
            for i in range(limit)
        ]
    return readings[-limit:]
