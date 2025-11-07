from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from pi4.models.measurements import Measurement
from pi4.auth.dependencies import get_current_active_user

router = APIRouter(prefix="/measurements", tags=["measurements"])


class MeasurementCreate(BaseModel):
    temperature: float
    humidity: float


class MeasurementResponse(MeasurementCreate):
    id: int
    timestamp: datetime


class PaginatedMeasurementsResponse(BaseModel):
    measurements: List[MeasurementResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


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


@router.get("/", response_model=PaginatedMeasurementsResponse)
async def get_measurements(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, le=100, ge=1),
    current_user=Depends(get_current_active_user),
):
    """Get all measurements with optional time period filtering and pagination"""
    query = Measurement.all()

    if start_time:
        query = query.filter(timestamp__gte=start_time)
    if end_time:
        query = query.filter(timestamp__lte=end_time)

    # Get total count for pagination info
    total = await query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    measurements_query = query.offset(offset).limit(page_size)
    
    measurements = await measurements_query.all()

    return PaginatedMeasurementsResponse(
        measurements=[
            MeasurementResponse(
                id=m.id,
                temperature=m.temperature,
                humidity=m.humidity,
                timestamp=m.timestamp,
            )
            for m in measurements
        ],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size  # Ceiling division
    )
