from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from pi3.models.measurements import Measurement
from pi3.auth.dependencies import get_current_active_user

router = APIRouter(prefix="/measurements", tags=["measurements"])


class MeasurementCreate(BaseModel):
    temperature: float
    humidity: float


class MeasurementResponse(MeasurementCreate):
    id: int
    timestamp: datetime


@router.post("/", response_model=MeasurementResponse)
async def create_measurement(
    measurement: MeasurementCreate,
    current_user=Depends(get_current_active_user),
):
    """Create a new measurement record"""
    db_measurement = await Measurement.create(
        temperature=measurement.temperature, humidity=measurement.humidity
    )
    return MeasurementResponse(
        id=db_measurement.id,
        temperature=db_measurement.temperature,
        humidity=db_measurement.humidity,
        timestamp=db_measurement.timestamp,
    )


@router.get("/{id}", response_model=MeasurementResponse)
async def get_measurement(
    id: int, current_user=Depends(get_current_active_user)
):
    """Get a measurement by ID"""
    measurement = await Measurement.filter(id=id).first()
    if not measurement:
        raise HTTPException(status_code=404, detail="Measurement not found")
    return MeasurementResponse(
        id=measurement.id,
        temperature=measurement.temperature,
        humidity=measurement.humidity,
        timestamp=measurement.timestamp,
    )


@router.get("/", response_model=List[MeasurementResponse])
async def get_measurements(
    start_time: datetime = None,
    end_time: datetime = None,
    current_user=Depends(get_current_active_user),
):
    """Get all measurements with optional time period filtering"""
    query = Measurement.all()

    if start_time:
        query = query.filter(timestamp__gte=start_time)
    if end_time:
        query = query.filter(timestamp__lte=end_time)

    measurements = await query.all()

    return [
        MeasurementResponse(
            id=m.id,
            temperature=m.temperature,
            humidity=m.humidity,
            timestamp=m.timestamp,
        )
        for m in measurements
    ]
