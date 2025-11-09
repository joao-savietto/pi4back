from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from pi4.auth.dependencies import get_current_active_user
from pi4.services.anomaly_service import anomaly_service

router = APIRouter(prefix="/anomaly", tags=["anomaly"])


class AnomalyDetectionRequest(BaseModel):
    """Request model for anomaly detection"""

    temperature: float
    humidity: float


class AnomalyDetectionResponse(BaseModel):
    """Response model for anomaly detection"""

    is_anomalous: bool
    reconstruction_error: Optional[float] = None
    threshold: Optional[float] = None
    message: str = ""


@router.post("/detect", response_model=AnomalyDetectionResponse)
async def detect_anomaly(
    measurement: AnomalyDetectionRequest,
    current_user=Depends(get_current_active_user),
):
    """Detect if a single measurement is anomalous using the trained model"""

    # Ensure service has loaded the model
    if anomaly_service.model is None:
        loaded = anomaly_service.load_model()
        if not loaded:
            raise HTTPException(
                status_code=500,
                detail="Failed to load anomaly detection model",
            )

    try:
        # Perform the anomaly detection using the service
        result = anomaly_service.predict_anomaly(
            measurement.temperature, measurement.humidity
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
    measurements: List[AnomalyDetectionRequest],
    current_user=Depends(get_current_active_user),
):
    """Detect anomalies for a batch of measurements"""

    # Ensure service has loaded the model
    if anomaly_service.model is None:
        loaded = anomaly_service.load_model()
        if not loaded:
            raise HTTPException(
                status_code=500,
                detail="Failed to load anomaly detection model",
            )

    results = []
    for measurement in measurements:
        try:
            result = anomaly_service.predict_anomaly(
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


# Initialize model on startup (optional, but more efficient)
@router.on_event("startup")
async def initialize_model():
    """Initialize the anomaly detection model when the app starts"""
    anomaly_service.load_model()
