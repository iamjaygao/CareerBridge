"""
Model management API endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.api.dependencies import verify_api_key
from app.core.database import get_db
from app.services.model_service import ModelService

router = APIRouter(dependencies=[Depends(verify_api_key)])
logger = structlog.get_logger()

@router.get("/status")
async def get_model_status(
    db: AsyncSession = Depends(get_db)
):
    """Get model status and performance"""
    try:
        status = await ModelService.get_model_status(db)
        return status
    except Exception as e:
        logger.error("Get model status failed", error=str(e))
        return {"error": "Failed to retrieve model status"}

@router.post("/retrain")
async def retrain_model(
    db: AsyncSession = Depends(get_db)
):
    """Trigger model retraining"""
    try:
        result = await ModelService.retrain_model(db)
        return {"message": "Model retraining started", "task_id": result}
    except Exception as e:
        logger.error("Model retraining failed", error=str(e))
        return {"error": "Failed to start model retraining"} 
