from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from pi4.models.measurements import Measurement
from pi4.auth.dependencies import get_current_active_user
from tortoise import fields
from tortoise.functions import Min, Max, Avg

from datetime import datetime, timezone

router = APIRouter(prefix="/measurements", tags=["measurements"])


class MeasurementCreate(BaseModel):
    temperature: float
    humidity: float


class MeasurementResponse(MeasurementCreate):
    id: int
    timestamp: datetime


class MeasurementStatisticsResponse(BaseModel):
    """Response model for measurement statistics"""

    count: int
    temperature_min: float
    temperature_max: float
    temperature_avg: float
    humidity_min: float
    humidity_max: float
    humidity_avg: float
    earliest_timestamp: datetime
    latest_timestamp: datetime


class PaginatedMeasurementsResponse(BaseModel):
    measurements: List[MeasurementResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


@router.get("/statistics", response_model=MeasurementStatisticsResponse)
async def get_statistics(
    start_time: datetime,
    end_time: datetime,
    current_user=Depends(get_current_active_user),
):
    """Get statistics for measurements within a time range"""
    # Validate that start_time is before end_time
    # ⏰ Garantindo timezone UTC nas datas
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=timezone.utc)

    if start_time >= end_time:
        raise HTTPException(
            status_code=400, detail="start_time must be before end_time"
        )

    query = Measurement.filter(
        timestamp__gte=start_time, timestamp__lte=end_time
    )
    count = await query.count()

    if count == 0:
        # Return zeros for all stats if no data found
        return MeasurementStatisticsResponse(
            count=0,
            temperature_min=0.0,
            temperature_max=0.0,
            temperature_avg=0.0,
            humidity_min=0.0,
            humidity_max=0.0,
            humidity_avg=0.0,
            earliest_timestamp=start_time,
            latest_timestamp=end_time,
        )

    # Use aggregation functions to get min, max, and avg values
    stats = await query.annotate(
        temperature_min=Min("temperature"),
        temperature_max=Max("temperature"),
        temperature_avg=Avg("temperature"),
        humidity_min=Min("humidity"),
        humidity_max=Max("humidity"),
        humidity_avg=Avg("humidity"),
        earliest_timestamp=Min("timestamp"),
        latest_timestamp=Max("timestamp"),
    ).first()

    # Return the statistics
    return MeasurementStatisticsResponse(
        count=count,
        temperature_min=stats.temperature_min or 0.0,
        temperature_max=stats.temperature_max or 0.0,
        temperature_avg=stats.temperature_avg or 0.0,
        humidity_min=stats.humidity_min or 0.0,
        humidity_max=stats.humidity_max or 0.0,
        humidity_avg=stats.humidity_avg or 0.0,
        earliest_timestamp=stats.earliest_timestamp or start_time,
        latest_timestamp=stats.latest_timestamp or end_time,
    )


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
    min_interval_minutes: Optional[int] = Query(None, ge=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, le=100, ge=1),
    current_user=Depends(get_current_active_user),
):
    """Get all measurements with optional time period filtering, interval filtering and pagination"""
    # Build base query
    query = Measurement.all()

    if start_time:
        query = query.filter(timestamp__gte=start_time)
    if end_time:
        query = query.filter(timestamp__lte=end_time)

    # For interval filtering to work properly across pages,
    # we need to get all measurements first, then filter and paginate
    all_measurements = await query.order_by("timestamp").all()

    # Apply min_interval_minutes filter if specified
    if min_interval_minutes is not None and min_interval_minutes > 0:
        filtered_measurements = []
        last_timestamp = None

        for measurement in all_measurements:
            # If this is the first measurement, or if it's at least
            # min_interval_minutes after the last one
            if (
                last_timestamp is None
                or (measurement.timestamp - last_timestamp).total_seconds()
                >= min_interval_minutes * 60
            ):
                filtered_measurements.append(measurement)
                last_timestamp = measurement.timestamp

        measurements = filtered_measurements
    else:
        measurements = all_measurements

    # Get total count for pagination info
    total = len(measurements)

    # Apply pagination to the already filtered results
    offset = (page - 1) * page_size
    paginated_measurements = measurements[offset : offset + page_size]

    return PaginatedMeasurementsResponse(
        measurements=[
            MeasurementResponse(
                id=m.id,
                temperature=m.temperature,
                humidity=m.humidity,
                timestamp=m.timestamp,
            )
            for m in paginated_measurements
        ],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,  # Ceiling division
    )
