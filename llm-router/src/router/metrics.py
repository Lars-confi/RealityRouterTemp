"""
Metrics collection for LLM routing system
"""
from fastapi import APIRouter
from typing import Dict, List, Optional
from pydantic import BaseModel
import logging
from src.utils.logger import setup_logger

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
async def get_metrics_summary():
    """
    Get summary of routing metrics
    
    Returns:
        MetricsSummary with aggregated statistics
    """
    if not metrics_storage:
        return MetricsSummary(
            total_requests=0,
            average_cost=0.0,
            average_time=0.0,
            average_utility=0.0,
            success_rate=0.0,
            models={}
        )
    
    # Calculate statistics
    total_requests = len(metrics_storage)
    total_cost = sum(entry.cost for entry in metrics_storage)
    total_time = sum(entry.time for entry in metrics_storage)
    total_utility = sum(entry.cost * entry.time * entry.probability if entry.probability else 0 for entry in metrics_storage)
    success_count = sum(1 for entry in metrics_storage if entry.success)
    
    # Group by model
    model_stats = {}
    for entry in metrics_storage:
        model_id = entry.model_id
        if model_id not in model_stats:
            model_stats[model_id] = {
                'requests': 0,
                'total_cost': 0.0,
                'total_time': 0.0,
                'success_count': 0
            }
        model_stats[model_id]['requests'] += 1
        model_stats[model_id]['total_cost'] += entry.cost
        model_stats[model_id]['total_time'] += entry.time
        if entry.success:
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

@router.get("/history")
async def get_metrics_history():
    """
    Get complete history of routing metrics
    
    Returns:
        List of all metric entries
    """
    return metrics_storage

@router.post("/log")
async def log_metric(entry: MetricEntry):
    """
    Log a metric entry
    
    Args:
        entry: MetricEntry to log
        
    Returns:
        Success confirmation
    """
    try:
        metrics_storage.append(entry)
        logger.info(f"Logged metric for model {entry.model_id}")
        return {"status": "success", "message": "Metric logged successfully"}
    except Exception as e:
        logger.error(f"Error logging metric: {str(e)}")
        return {"status": "error", "message": str(e)}