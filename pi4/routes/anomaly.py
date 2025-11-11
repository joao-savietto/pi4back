from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from pi4.auth.dependencies import get_current_active_user
from pi4.services.anomaly_service import anomaly_service
from pi4.models.measurements import Measurement

router = APIRouter(prefix="/anomaly", tags=["anomaly"])


class AnomalyDetectionResponse(BaseModel):
    """Response model for anomaly detection"""

    is_anomalous: bool
    reconstruction_error: Optional[float] = None
    threshold: Optional[float] = None
    message: str = ""


@router.post("/detect", response_model=AnomalyDetectionResponse)
async def detect_anomaly(
    current_user=Depends(get_current_active_user),
):
    """Detect if the latest measurement is anomalous using the trained model"""

    # Ensure service has loaded the model
    if anomaly_service.model is None:
        loaded = anomaly_service.load_model()
        if not loaded:
            raise HTTPException(
                status_code=500,
                detail="Failed to load anomaly detection model",
            )

    try:
        # Fetch latest measurement from database
        latest_measurement = await Measurement.all().order_by("-timestamp").first()
        
        if not latest_measurement:
            raise HTTPException(
                status_code=404,
                detail="No measurements found in database"
            )

        # Perform the anomaly detection using the service with latest data
        result = await anomaly_service.predict_anomaly(
            latest_measurement.temperature, latest_measurement.humidity
        )

        message = "Anomalous" if result["is_anomalous"] else "Normal"

        return AnomalyDetectionResponse(
            is_anomalous=result["is_anomalous"],
            reconstruction_error=result["reconstruction_error"],
            threshold=result["threshold"],
            message=message,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/detect-batch", response_model=List[AnomalyDetectionResponse])
async def detect_anomaly_batch(
    current_user=Depends(get_current_active_user),
):
    """Detect anomalies for the most recent measurements"""

    # Ensure service has loaded the model
    if anomaly_service.model is None:
        loaded = anomaly_service.load_model()
        if not loaded:
            raise HTTPException(
                status_code=500,
                detail="Failed to load anomaly detection model",
            )

    try:
        # Fetch latest 5 measurements from database (you can adjust the count as needed)
        recent_measurements = await Measurement.all().order_by(
            "-timestamp"
        ).limit(5).all()
        
        if not recent_measurements:
            raise HTTPException(
                status_code=404,
                detail="No measurements found in database"
            )

        results = []
        for measurement in recent_measurements:
            try:
                result = await anomaly_service.predict_anomaly(
                    measurement.temperature, measurement.humidity
                )
                message = "Anomalous" if result["is_anomalous"] else "Normal"

                response = AnomalyDetectionResponse(
                    is_anomalous=result["is_anomalous"],
                    reconstruction_error=result["reconstruction_error"],
                    threshold=result["threshold"],
                    message=message,
                )
                results.append(response)
            except Exception as e:
                # Continue with other measurements if one fails
                results.append(
                    AnomalyDetectionResponse(
                        is_anomalous=False,
                        message=f"Error processing measurement: {str(e)}",
                    )
                )

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Initialize model on startup (optional, but more efficient)
@router.on_event("startup")
async def initialize_model():
    """Initialize the anomaly detection model when the app starts"""
    anomaly_service.load_model()
