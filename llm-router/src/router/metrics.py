"""
Metrics collection for LLM routing system
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.models.database import ModelPerformance, RoutingLog, get_db
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
    timestamp: str


class ModelMetrics(BaseModel):
    """Model performance metrics"""

    model_id: str
    model_name: str
    total_requests: int
    total_cost: float
    average_time: float
    success_rate: float
    last_updated: str


class MetricsCollector:
    """Collects and manages routing metrics"""

    def __init__(self):
        """Initialize metrics collector"""
        self.metrics_storage = []

    def collect_routing_metrics(
        self,
        db: Session,
        model_id: str,
        model_name: str,
        expected_utility: float,
        cost: float,
        time: float,
        probability: float,
        success: bool,
        query: str,
        response_text: str = None,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0,
        request_payload: str = None,
        response_payload: str = None,
        routing_context: str = None,
    ):
        """
        Collect routing metrics for a single request
        """
        try:
            # Create a new routing log entry
            log_entry = RoutingLog(
                query=query,
                model_id=model_id,
                model_name=model_name,
                expected_utility=expected_utility,
                cost=cost,
                time=time,
                probability=probability,
                success=success,
                response_text=response_text,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                request_payload=request_payload,
                response_payload=response_payload,
                routing_context=routing_context,
            )

            db.add(log_entry)
            db.commit()
            db.refresh(log_entry)

            logger.info(f"Logged routing decision for model {model_id}")

            # Update model performance metrics
            self.update_model_performance(db, model_id, cost, time, success)

        except Exception as e:
            logger.error(f"Error collecting routing metrics: {str(e)}")

    def update_model_performance(
        self, db: Session, model_id: str, cost: float, time: float, success: bool
    ):
        """
        Update performance metrics for a specific model

        Args:
            db: Database session
            model_id: ID of the model
            cost: Cost of the request
            time: Time taken for the request
            success: Whether the request was successful
        """
        try:
            # Try to find existing performance record
            perf_record = (
                db.query(ModelPerformance).filter_by(model_id=model_id).first()
            )

            if perf_record:
                # Update existing record
                perf_record.total_requests += 1
                perf_record.total_cost += cost
                perf_record.average_time = (
                    perf_record.average_time * (perf_record.total_requests - 1) + time
                ) / perf_record.total_requests
                perf_record.last_updated = datetime.utcnow()

                if success:
                    perf_record.success_rate = (
                        perf_record.success_rate * (perf_record.total_requests - 1) + 1
                    ) / perf_record.total_requests
                else:
                    perf_record.success_rate = (
                        perf_record.success_rate * (perf_record.total_requests - 1) + 0
                    ) / perf_record.total_requests
            else:
                # Create new record
                perf_record = ModelPerformance(
                    model_id=model_id,
                    model_name=model_id,  # This should be updated with actual name
                    total_requests=1,
                    total_cost=cost,
                    average_time=time,
                    success_rate=1.0 if success else 0.0,
                )
                db.add(perf_record)

            db.commit()

        except Exception as e:
            logger.error(f"Error updating model performance: {str(e)}")


# Global metrics collector instance
metrics_collector = MetricsCollector()


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
                models={},
                timestamp=datetime.utcnow().isoformat(),
            )

        # Calculate statistics
        total_requests = len(logs)
        total_cost = sum(log.cost for log in logs)
        total_time = sum(log.time for log in logs)
        success_count = sum(1 for log in logs if log.success)

        # Group by model
        model_stats = {}
        for log in logs:
            model_id = log.model_id
            if model_id not in model_stats:
                model_stats[model_id] = {
                    "requests": 0,
                    "total_cost": 0.0,
                    "total_time": 0.0,
                    "success_count": 0,
                }
            model_stats[model_id]["requests"] += 1
            model_stats[model_id]["total_cost"] += log.cost
            model_stats[model_id]["total_time"] += log.time
            if log.success:
                model_stats[model_id]["success_count"] += 1

        # Calculate averages
        avg_cost = total_cost / total_requests if total_requests > 0 else 0.0
        avg_time = total_time / total_requests if total_requests > 0 else 0.0
        success_rate = success_count / total_requests if total_requests > 0 else 0.0

        return MetricsSummary(
            total_requests=total_requests,
            average_cost=avg_cost,
            average_time=avg_time,
            average_utility=0.0,  # This would require more complex calculation
            success_rate=success_rate,
            models=model_stats,
            timestamp=datetime.utcnow().isoformat(),
        )
    except Exception as e:
        logger.error(f"Error getting metrics summary: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving metrics: {str(e)}"
        )


@router.get("/models")
async def get_model_metrics(db: Session = Depends(get_db)):
    """
    Get metrics for all models

    Returns:
        List of model metrics
    """
    try:
        # Get all model performance records
        perf_records = db.query(ModelPerformance).all()

        model_metrics = []
        for record in perf_records:
            model_metrics.append(
                {
                    "model_id": record.model_id,
                    "model_name": record.model_name,
                    "total_requests": record.total_requests,
                    "total_cost": record.total_cost,
                    "average_time": record.average_time,
                    "success_rate": record.success_rate,
                    "last_updated": record.last_updated.isoformat()
                    if record.last_updated
                    else None,
                }
            )

        return model_metrics
    except Exception as e:
        logger.error(f"Error getting model metrics: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving model metrics: {str(e)}"
        )


@router.get("/history")
async def get_metrics_history():
    """
    Get complete history of routing metrics

    Returns:
        List of all metric entries
    """
    return metrics_collector.metrics_storage


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
            timestamp=datetime.fromisoformat(entry.timestamp),
            model_id=entry.model_id,
            cost=entry.cost,
            time=entry.time,
            probability=entry.probability,
            success=entry.success,
            query=entry.query,
        )

        db.add(db_entry)
        db.commit()
        db.refresh(db_entry)

        logger.info(f"Logged metric for model {entry.model_id}")
        return {
            "status": "success",
            "message": "Metric logged successfully",
            "id": db_entry.id,
        }
    except Exception as e:
        logger.error(f"Error logging metric: {str(e)}")
        return {"status": "error", "message": str(e)}
