"""
Metrics collection for LLM routing system
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
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
    total_cost: float
    total_prompt_tokens: int
    total_completion_tokens: int
    total_tokens: int
    average_cost: float
    average_time: float
    average_utility: float
    potential_max_cost: float
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
        confidence: float = None,
        entropy: float = None,
        logprobs_mean: float = None,
        logprobs_std: float = None,
        first_token_logprob: float = None,
        first_token_top_logprobs: str = None,
        second_token_logprob: float = None,
        second_token_top_logprobs: str = None,
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
                confidence=confidence,
                entropy=entropy,
                logprobs_mean=logprobs_mean,
                logprobs_std=logprobs_std,
                first_token_logprob=first_token_logprob,
                first_token_top_logprobs=first_token_top_logprobs,
                second_token_logprob=second_token_logprob,
                second_token_top_logprobs=second_token_top_logprobs,
            )

            db.add(log_entry)
            db.commit()
            db.refresh(log_entry)

            logger.info(f"Logged routing decision for model {model_id}")

            # Update model performance metrics
            self.update_model_performance(db, model_id, model_name, cost, time, success)

        except Exception as e:
            logger.error(f"Error collecting routing metrics: {str(e)}")

    def update_model_performance(
        self,
        db: Session,
        model_id: str,
        model_name: str,
        cost: float,
        time: float,
        success: bool,
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
                perf_record.model_name = model_name
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
                    model_name=model_name,
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
                total_cost=0.0,
                total_prompt_tokens=0,
                total_completion_tokens=0,
                total_tokens=0,
                average_cost=0.0,
                average_time=0.0,
                average_utility=0.0,
                potential_max_cost=0.0,
                success_rate=0.0,
                models={},
                timestamp=datetime.utcnow().isoformat(),
            )

        # Calculate statistics
        total_requests = len(logs)
        total_cost = sum(log.cost for log in logs)
        total_prompt_tokens = sum(log.prompt_tokens or 0 for log in logs)
        total_completion_tokens = sum(log.completion_tokens or 0 for log in logs)
        total_tokens = sum(log.total_tokens or 0 for log in logs)
        total_time = sum(log.time for log in logs)
        success_count = sum(1 for log in logs if log.success)

        # Group by model
        model_stats = {}
        for log in logs:
            model_id = log.model_id
            if model_id not in model_stats:
                model_stats[model_id] = {
                    "name": log.model_name,
                    "requests": 0,
                    "total_cost": 0.0,
                    "total_prompt_tokens": 0,
                    "total_completion_tokens": 0,
                    "total_tokens": 0,
                    "total_time": 0.0,
                    "success_count": 0,
                }
            model_stats[model_id]["requests"] += 1
            model_stats[model_id]["total_cost"] += log.cost
            model_stats[model_id]["total_prompt_tokens"] += log.prompt_tokens or 0
            model_stats[model_id]["total_completion_tokens"] += (
                log.completion_tokens or 0
            )
            model_stats[model_id]["total_tokens"] += log.total_tokens or 0
            model_stats[model_id]["total_time"] += log.time
            if log.success:
                model_stats[model_id]["success_count"] += 1

        # Calculate averages
        avg_cost = total_cost / total_requests if total_requests > 0 else 0.0
        avg_time = total_time / total_requests if total_requests > 0 else 0.0
        success_rate = success_count / total_requests if total_requests > 0 else 0.0

        # Estimate potential max cost (if used most expensive model for all tokens)
        max_unit_cost = 0.0
        for m_info in model_stats.values():
            if m_info["total_tokens"] > 0:
                unit_cost = m_info["total_cost"] / m_info["total_tokens"]
                if unit_cost > max_unit_cost:
                    max_unit_cost = unit_cost

        if max_unit_cost == 0:
            # Fallback if no token data: use max cost per request
            max_avg_cost = 0.0
            for m_info in model_stats.values():
                if m_info["requests"] > 0:
                    avg = m_info["total_cost"] / m_info["requests"]
                    if avg > max_avg_cost:
                        max_avg_cost = avg
            potential_max_cost = total_requests * max_avg_cost
        else:
            potential_max_cost = total_tokens * max_unit_cost

        return MetricsSummary(
            total_requests=total_requests,
            total_cost=total_cost,
            total_prompt_tokens=total_prompt_tokens,
            total_completion_tokens=total_completion_tokens,
            total_tokens=total_tokens,
            average_cost=avg_cost,
            average_time=avg_time,
            average_utility=0.0,
            potential_max_cost=potential_max_cost,
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


@router.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard():
    """
    Get a simple HTML dashboard for routing metrics
    """
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>LLM Router Dashboard</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 2em; background: #f4f7f6; color: #333; }
            .card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 30px; }
            h1 { color: #2c3e50; margin-bottom: 0.5em; }
            h2 { color: #34495e; border-bottom: 2px solid #eee; padding-bottom: 10px; margin-top: 0; }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; }
            .stat { background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #3498db; }
            .stat-savings { border-left-color: #27ae60; background: #ebfcf1; }
            .stat-value { font-size: 1.8em; font-weight: bold; color: #2980b9; margin: 5px 0; }
            .stat-savings .stat-value { color: #27ae60; }
            .stat-label { color: #7f8c8d; font-size: 0.85em; text-transform: uppercase; letter-spacing: 1px; }
            table { width: 100%; border-collapse: collapse; margin-top: 15px; }
            th, td { text-align: left; padding: 12px 15px; border-bottom: 1px solid #edf2f7; }
            th { background: #f8fafc; color: #64748b; font-weight: 600; text-transform: uppercase; font-size: 0.75em; }
            tr:last-child td { border-bottom: none; }
            tr:hover { background: #f8fafc; }
            .badge { padding: 4px 8px; border-radius: 4px; font-size: 0.8em; font-weight: 600; }
            .badge-success { background: #dcfce7; color: #166534; }
        </style>
    </head>
    <body>
        <div style="max-width: 1200px; margin: 0 auto;">
            <h1>LLM Router Control Center</h1>

            <div id="summary" class="card">
                <h2>System Health & Usage</h2>
                <div class="grid" id="summary-grid">
                    <div class="stat">Loading stats...</div>
                </div>
            </div>

            <div id="models" class="card">
                <h2>Model Performance & Unit Economics</h2>
                <div style="overflow-x: auto;">
                    <table id="models-table">
                        <thead>
                            <tr>
                                <th>Intelligence Provider</th>
                                <th>Calls</th>
                                <th>Total Cost</th>
                                <th>Avg Latency</th>
                                <th>Throughput (Tokens)</th>
                                <th>Reliability</th>
                            </tr>
                        </thead>
                        <tbody id="models-body"></tbody>
                    </table>
                </div>
            </div>
        </div>

        <script>
            async function loadData() {
                try {
                    const res = await fetch('/metrics/summary');
                    const data = await res.json();

                    // Update Summary Grid
                    const summaryGrid = document.getElementById('summary-grid');
                    const savings = Math.max(0, data.potential_max_cost - data.total_cost);
                    summaryGrid.innerHTML = `
                        <div class="stat"><div class="stat-label">Total Volume</div><div class="stat-value">${data.total_requests.toLocaleString()}</div><div class="stat-label">Requests</div></div>
                        <div class="stat"><div class="stat-label">Accrued Expense</div><div class="stat-value">$${data.total_cost.toFixed(4)}</div><div class="stat-label">Actual USD</div></div>
                        <div class="stat"><div class="stat-label">Potential Cost</div><div class="stat-value" style="color: #e74c3c;">$${data.potential_max_cost.toFixed(4)}</div><div class="stat-label">Max Model USD</div></div>
                        <div class="stat stat-savings"><div class="stat-label">Total Savings</div><div class="stat-value">$${savings.toFixed(4)}</div><div class="stat-label">Retained Value</div></div>
                        <div class="stat"><div class="stat-label">Success Density</div><div class="stat-value">${(data.success_rate * 100).toFixed(1)}%</div><div class="stat-label">Operational</div></div>
                    `;

                    // Update Table
                    const modelsBody = document.getElementById('models-body');
                    modelsBody.innerHTML = '';

                    const sortedModels = Object.entries(data.models).sort((a, b) => b[1].requests - a[1].requests);

                    for (const [id, stats] of sortedModels) {
                        const row = document.createElement('tr');
                        const rate = ((stats.success_count / stats.requests) * 100).toFixed(1);
                        row.innerHTML = `
                            <td>
                                <div style="font-weight: 600; color: #2c3e50;">${stats.name || id}</div>
                                <div style="font-size: 0.75em; color: #94a3b8;">${id}</div>
                            </td>
                            <td>${stats.requests.toLocaleString()}</td>
                            <td>$${stats.total_cost.toFixed(6)}</td>
                            <td>${stats.total_time ? (stats.total_time / stats.requests).toFixed(2) + 's' : 'N/A'}</td>
                            <td>
                                <div style="font-size: 0.85em;">P: ${stats.total_prompt_tokens.toLocaleString()}</div>
                                <div style="font-size: 0.85em;">C: ${stats.total_completion_tokens.toLocaleString()}</div>
                            </td>
                            <td>
                                <span class="badge ${rate > 90 ? 'badge-success' : ''}">${rate}%</span>
                            </td>
                        `;
                        modelsBody.appendChild(row);
                    }
                } catch (e) {
                    console.error("Dashboard sync failed", e);
                }
            }
            loadData();
            setInterval(loadData, 5000);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
