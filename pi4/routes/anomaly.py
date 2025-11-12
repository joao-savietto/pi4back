from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from pi4.auth.dependencies import get_current_active_user
from pi4.models.measurements import Measurement
from pi4.services.anomaly_service import anomaly_service

router = APIRouter(prefix="/anomaly", tags=["anomaly"])


class TemperatureHumidityDetails(BaseModel):
    value: float
    normal_min: float
    normal_max: float
    deviation_from_mean: float


class AnomalyClassification(BaseModel):
    type: str
    confidence: float
    details: Dict[str, TemperatureHumidityDetails]


class ErrorAnalysis(BaseModel):
    reconstruction_error: float
    threshold: float
    error_ratio_to_threshold: float
    is_significantly_anomalous: bool


class Diagnosis(BaseModel):
    classification: AnomalyClassification
    error_analysis: ErrorAnalysis


class AnomalyDetectionResponse(BaseModel):
    """Response model for anomaly detection"""

    is_anomalous: bool
    reconstruction_error: Optional[float] = None
    threshold: Optional[float] = None
    message: str = ""
    diagnosis: Optional[Diagnosis] = None


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
        latest_measurement = (
            await Measurement.all().order_by("-timestamp").first()
        )

        if not latest_measurement:
            raise HTTPException(
                status_code=404, detail="No measurements found in database"
            )

        # Perform the anomaly detection using the service with latest data
        result = await anomaly_service.predict_anomaly(
            latest_measurement.temperature, latest_measurement.humidity
        )

        message = "Anomalous" if result["is_anomalous"] else "Normal"

        # Include diagnosis if available
        diagnosis = None
        if result.get("diagnosis"):
            diagnosis_data = result["diagnosis"]
            diagnosis = Diagnosis(
                classification=AnomalyClassification(
                    type=diagnosis_data["classification"]["type"],
                    confidence=diagnosis_data["classification"]["confidence"],
                    details=diagnosis_data["classification"]["details"],
                ),
                error_analysis=ErrorAnalysis(
                    reconstruction_error=diagnosis_data["error_analysis"][
                        "reconstruction_error"
                    ],
                    threshold=diagnosis_data["error_analysis"]["threshold"],
                    error_ratio_to_threshold=diagnosis_data["error_analysis"][
                        "error_ratio_to_threshold"
                    ],
                    is_significantly_anomalous=diagnosis_data[
                        "error_analysis"
                    ]["is_significantly_anomalous"],
                ),
            )

        return AnomalyDetectionResponse(
            is_anomalous=result["is_anomalous"],
            reconstruction_error=result["reconstruction_error"],
            threshold=result["threshold"],
            message=message,
            diagnosis=diagnosis,
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
        recent_measurements = (
            await Measurement.all().order_by("-timestamp").limit(5).all()
        )

        if not recent_measurements:
            raise HTTPException(
                status_code=404, detail="No measurements found in database"
            )

        results = []
        for measurement in recent_measurements:
            try:
                result = await anomaly_service.predict_anomaly(
                    measurement.temperature, measurement.humidity
                )
                message = "Anomalous" if result["is_anomalous"] else "Normal"

                # Include diagnosis if available
                diagnosis = None
                if result.get("diagnosis"):
                    diagnosis_data = result["diagnosis"]
                    diagnosis = Diagnosis(
                        classification=AnomalyClassification(
                            type=diagnosis_data["classification"]["type"],
                            confidence=diagnosis_data["classification"][
                                "confidence"
                            ],
                            details=diagnosis_data["classification"][
                                "details"
                            ],
                        ),
                        error_analysis=ErrorAnalysis(
                            reconstruction_error=diagnosis_data[
                                "error_analysis"
                            ]["reconstruction_error"],
                            threshold=diagnosis_data["error_analysis"][
                                "threshold"
                            ],
                            error_ratio_to_threshold=diagnosis_data[
                                "error_analysis"
                            ]["error_ratio_to_threshold"],
                            is_significantly_anomalous=diagnosis_data[
                                "error_analysis"
                            ]["is_significantly_anomalous"],
                        ),
                    )

                response = AnomalyDetectionResponse(
                    is_anomalous=result["is_anomalous"],
                    reconstruction_error=result["reconstruction_error"],
                    threshold=result["threshold"],
                    message=message,
                    diagnosis=diagnosis,
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
