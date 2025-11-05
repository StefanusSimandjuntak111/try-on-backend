"""Health check endpoints."""

from datetime import datetime

from fastapi import APIRouter

from app.core.logging import get_logger
from app.models.schemas import HealthResponse, ModelsHealthResponse
from app.ml.background.model import get_u2net_model
from app.ml.hrviton.model import get_hrviton_model
from app.ml.parsing.model import get_schp_model
from app.ml.pose.model import get_openpose_model

router = APIRouter()
logger = get_logger(__name__)


@router.get("", response_model=HealthResponse)
async def health_check():
    """Basic health check."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
    )


@router.get("/models", response_model=ModelsHealthResponse)
async def models_health():
    """Check ML models status."""
    models_status = {}
    
    # Check U2-Net
    try:
        u2net = get_u2net_model()
        models_status["u2net"] = {
            "status": "loaded" if u2net.model is not None else "not_loaded",
            "device": str(u2net.device),
            "checkpoint": u2net.checkpoint_path,
        }
    except Exception as e:
        logger.error("Failed to check U2-Net status", error=str(e))
        models_status["u2net"] = {
            "status": "error",
            "error": str(e),
        }
    
    # Check SCHP
    try:
        schp = get_schp_model()
        models_status["schp"] = {
            "status": "loaded" if schp.model is not None else "not_loaded",
            "device": str(schp.device),
            "checkpoint": schp.checkpoint_path,
        }
    except Exception as e:
        logger.error("Failed to check SCHP status", error=str(e))
        models_status["schp"] = {
            "status": "error",
            "error": str(e),
        }
    
    # Check OpenPose
    try:
        openpose = get_openpose_model()
        models_status["openpose"] = {
            "status": "loaded" if openpose.model is not None else "not_loaded",
            "device": str(openpose.device),
            "checkpoint": openpose.checkpoint_path,
        }
    except Exception as e:
        logger.error("Failed to check OpenPose status", error=str(e))
        models_status["openpose"] = {
            "status": "error",
            "error": str(e),
        }
    
    # Check HR-VITON
    try:
        hrviton = get_hrviton_model()
        models_status["hrviton"] = {
            "status": "loaded" if hrviton.model is not None else "not_loaded",
            "device": str(hrviton.device),
            "checkpoint": hrviton.checkpoint_path,
        }
    except Exception as e:
        logger.error("Failed to check HR-VITON status", error=str(e))
        models_status["hrviton"] = {
            "status": "error",
            "error": str(e),
        }
    
    # Determine overall status
    all_loaded = all(
        model.get("status") == "loaded" for model in models_status.values()
    )
    overall_status = "ready" if all_loaded else "partial" if models_status else "not_ready"
    
    return ModelsHealthResponse(
        status=overall_status,
        models=models_status,
    )


@router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    try:
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        from fastapi import Response
        
        # Return Prometheus metrics
        metrics_data = generate_latest()
        return Response(
            content=metrics_data,
            media_type=CONTENT_TYPE_LATEST,
        )
    except ImportError:
        # Return empty if prometheus_client not available
        return {"status": "prometheus_client not installed"}

