"""
Metrics collection for LLM routing system
"""
from fastapi import APIRouter, Depends
from typing import Dict, List, Optional
from pydantic import BaseModel
import logging
from src.utils.logger import setup_logger
from src.models.database import get_db, RoutingLog, ModelPerformance
from sqlalchemy.orm import Session

logger = setup_logger(__name__)

router = APIRouter()

class MetricEntry(BaseModel):
    """Single metric entry"""
    timestamp: str
    model_id: str
    cost: float
    time: float
    probability: float
    success: bool
    query: str

class MetricsSummary(BaseModel):
    """Summary of metrics"""
    total_requests: int
    average_cost: float
    average_time: float
    average_utility: float
    success_rate: float
    models: Dict[str, Dict]

# In-memory storage for metrics (in production, this would be a database)
metrics_storage: List[MetricEntry] = []

@router.get("/summary")
async def get_metrics_summary(db: Session = Depends(get_db)):
    """
    Get summary of routing metrics from database
    
    Returns:
        MetricsSummary with aggregated statistics
    """
    try:
        # Get all routing logs from database
        logs = db.query(RoutingLog).all()
        
        if not logs:
            return MetricsSummary(
                total_requests=0,
                average_cost=0.0,
                average_time=0.0,
                average_utility=0.0,
                success_rate=0.0,
                models={}
            )
        
        # Calculate statistics
        total_requests = len(logs)
        total_cost = sum(log.cost for log in logs)
        total_time = sum(log.time for log in logs)
        total_utility = sum(log.expected_utility for log in logs)
        success_count = sum(1 for log in logs if log.success)
        
        # Group by model
        model_stats = {}
        for log in logs:
            model_id = log.model_id
            if model_id not in model_stats:
                model_stats[model_id] = {
                    'requests': 0,
                    'total_cost': 0.0,
                    'total_time': 0.0,
                    'success_count': 0
                }
            model_stats[model_id]['requests'] += 1
            model_stats[model_id]['total_cost'] += log.cost
            model_stats[model_id]['total_time'] += log.time
            if log.success:
                model_stats[model_id]['success_count'] += 1
        
        # Calculate averages
        avg_cost = total_cost / total_requests if total_requests > 0 else 0.0
        avg_time = total_time / total_requests if total_requests > 0 else 0.0
        avg_utility = total_utility / total_requests if total_requests > 0 else 0.0
        success_rate = success_count / total_requests if total_requests > 0 else 0.0
        
        return MetricsSummary(
            total_requests=total_requests,
            average_cost=avg_cost,
            average_time=avg_time,
            average_utility=avg_utility,
            success_rate=success_rate,
            models=model_stats
        )
    except Exception as e:
        logger.error(f"Error getting metrics summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving metrics: {str(e)}")

@router.get("/history")
async def get_metrics_history():
    """
    Get complete history of routing metrics
    
    Returns:
        List of all metric entries
    """
    return metrics_storage

@router.post("/log")
async def log_metric(entry: MetricEntry, db: Session = Depends(get_db)):
    """
    Log a metric entry to database
    
    Args:
        entry: MetricEntry to log
        db: Database session
        
    Returns:
        Success confirmation
    """
    try:
        # Convert MetricEntry to RoutingLog model
        db_entry = RoutingLog(
            timestamp=entry.timestamp,
            model_id=entry.model_id,
            cost=entry.cost,
            time=entry.time,
            probability=entry.probability,
            success=entry.success,
            query=entry.query
        )
        
        db.add(db_entry)
        db.commit()
        db.refresh(db_entry)
        
        logger.info(f"Logged metric for model {entry.model_id}")
        return {"status": "success", "message": "Metric logged successfully", "id": db_entry.id}
    except Exception as e:
        logger.error(f"Error logging metric: {str(e)}")
        return {"status": "error", "message": str(e)}