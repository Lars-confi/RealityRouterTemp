"""
Core routing logic implementing Expected Utility Theory framework
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional
from pydantic import BaseModel
import logging
from src.models.routing import RoutingRequest, RoutingResponse
from src.adapters.openai_adapter import OpenAIAdapter
from src.adapters.anthropic_adapter import AnthropicAdapter
from src.adapters.cohere_adapter import CohereAdapter
from src.utils.logger import setup_logger
from src.models.database import RoutingLog, init_db, get_db
from sqlalchemy.orm import Session

logger = setup_logger(__name__)

router = APIRouter()

class ModelMetrics(BaseModel):
    """Model performance metrics"""
    model_id: str
    cost: float  # Cost per million tokens
    time: float  # Average response time in seconds
    probability: float  # Success probability (0-1)
    name: str

class RoutingDecision(BaseModel):
    """Routing decision with expected utility"""
    model_id: str
    expected_utility: float
    cost: float
    time: float
    probability: float
    name: str

class ExpectedUtilityCalculator:
    """Calculator for Expected Utility Theory implementation"""
    
    def __init__(self, reward: float = 1.0, cost_sensitivity: float = 0.5, time_sensitivity: float = 0.5):
        """
        Initialize the calculator with parameters
        
        Args:
            reward: The inherent reward or value of getting a correct answer
            cost_sensitivity: Sensitivity to cost (how much utility you lose per cent spent)
            time_sensitivity: Sensitivity to time (how much utility you lose per second of delay)
        """
        self.reward = reward
        self.cost_sensitivity = cost_sensitivity
        self.time_sensitivity = time_sensitivity
        
        # Ensure time_sensitivity is calculated if not provided
        if time_sensitivity is None:
            self.time_sensitivity = 1.0 - cost_sensitivity
    
    def calculate_expected_utility(self, cost: float, time: float, probability: float) -> float:
        """
        Calculate expected utility using the formula:
        EU = p * R - α * c - β * t
        
        Args:
            cost: Token cost for the model
            time: Response time in seconds
            probability: Success probability (0-1)
            
        Returns:
            Expected utility value
        """
        return probability * self.reward - self.cost_sensitivity * cost - self.time_sensitivity * time

class RouterCore:
    """Main router core implementing Expected Utility Theory"""
    
    def __init__(self):
        """Initialize router with available models"""
        self.models = {}
        self.metrics = {}
        self.utility_calculator = ExpectedUtilityCalculator()
        
        # Initialize adapters for different LLM providers
        self.adapters = {
            'openai': OpenAIAdapter(),
            'anthropic': AnthropicAdapter(),
            'cohere': CohereAdapter()
        }
        
        # Initialize database
        init_db()
        
        logger.info("Router core initialized with Expected Utility Theory framework")
    
    def add_model(self, model_id: str, model_name: str, cost: float, time: float, probability: float):
        """
        Add a model to the routing system
        
        Args:
            model_id: Unique identifier for the model
            model_name: Name of the model
            cost: Cost per million tokens
            time: Average response time in seconds
            probability: Success probability (0-1)
        """
        self.models[model_id] = {
            'name': model_name,
            'cost': cost,
            'time': time,
            'probability': probability
        }
        self.metrics[model_id] = ModelMetrics(
            model_id=model_id,
            cost=cost,
            time=time,
            probability=probability,
            name=model_name
        )
        logger.info(f"Added model {model_name} (ID: {model_id}) to routing system")
    
    def get_best_model(self, request: RoutingRequest) -> RoutingDecision:
        """
        Select the best model based on Expected Utility Theory
        
        Args:
            request: Routing request with query information
            
        Returns:
            RoutingDecision with the best model and expected utility
        """
        if not self.models:
            raise HTTPException(status_code=500, detail="No models available for routing")
        
        best_model_id = None
        best_utility = float('-inf')
        best_metrics = None
        
        # Calculate expected utility for each model
        for model_id, model_info in self.models.items():
            cost = model_info['cost']
            time = model_info['time']
            probability = model_info['probability']
            
            utility = self.utility_calculator.calculate_expected_utility(cost, time, probability)
            
            logger.info(f"Model {model_id} utility: {utility:.4f}")
            
            if utility > best_utility:
                best_utility = utility
                best_model_id = model_id
                best_metrics = model_info
        
        if best_model_id is None:
            raise HTTPException(status_code=500, detail="No suitable model found for routing")
        
        return RoutingDecision(
            model_id=best_model_id,
            expected_utility=best_utility,
            cost=best_metrics['cost'],
            time=best_metrics['time'],
            probability=best_metrics['probability'],
            name=best_metrics['name']
        )
    
    def log_routing_decision(self, decision: RoutingDecision, request: RoutingRequest, response: Dict[str, Any], db: Session):
        """
        Log routing decision to database
        
        Args:
            decision: RoutingDecision that was made
            request: Original routing request
            response: Response from the model
            db: Database session
        """
        try:
            # Extract token usage from response if available
            prompt_tokens = response.get('usage', {}).get('prompt_tokens', 0) if response.get('usage') else 0
            completion_tokens = response.get('usage', {}).get('completion_tokens', 0) if response.get('usage') else 0
            total_tokens = response.get('usage', {}).get('total_tokens', 0) if response.get('usage') else 0
            
            # Create routing log entry
            log_entry = RoutingLog(
                query=request.query,
                model_id=decision.model_id,
                model_name=decision.name,
                expected_utility=decision.expected_utility,
                cost=decision.cost,
                time=decision.time,
                probability=decision.probability,
                response_text=response.get('text', ''),
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                success=True  # We assume success for now, but this could be enhanced
            )
            
            db.add(log_entry)
            db.commit()
            logger.info(f"Logged routing decision for model {decision.model_id}")
            
        except Exception as e:
            logger.error(f"Error logging routing decision: {str(e)}")
            # Don't fail the request for logging errors
    
    def route_request(self, request: RoutingRequest) -> RoutingResponse:
        """
        Route a request to the best model
        
        Args:
            request: Routing request with query information
            
        Returns:
            RoutingResponse with the selected model and routing information
        """
        try:
            # Get the best model based on expected utility
            decision = self.get_best_model(request)
            
            # Get the adapter for the selected model
            adapter = self.adapters.get(decision.model_id.split('_')[0])  # Simple approach
            
            if not adapter:
                raise HTTPException(status_code=500, detail=f"No adapter found for model {decision.model_id}")
            
            # Forward the request to the selected model
            response = adapter.forward_request(request)
            
            # Log the routing decision to database
            # Note: In a real implementation, we'd need to pass the database session properly
            # For now, we'll just log to console
            logger.info(f"Routing decision: {decision.model_id} selected with utility {decision.expected_utility}")
            
            return RoutingResponse(
                model_id=decision.model_id,
                model_name=decision.name,
                expected_utility=decision.expected_utility,
                cost=decision.cost,
                time=decision.time,
                probability=decision.probability,
                response=response
            )
            
        except Exception as e:
            logger.error(f"Error in routing request: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Routing error: {str(e)}")

# Initialize the router core
router_core = RouterCore()

@router.post("/route", response_model=RoutingResponse)
async def route_request(request: RoutingRequest):
    """
    Route a request to the best model based on Expected Utility Theory
    
    Args:
        request: Routing request with query information
        
    Returns:
        RoutingResponse with the selected model and routing information
    """
    try:
        response = router_core.route_request(request)
        return response
    except Exception as e:
        logger.error(f"Error routing request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models")
async def get_models():
    """
    Get list of available models
    
    Returns:
        List of available models with their metrics
    """
    return router_core.models

@router.get("/metrics")
async def get_metrics():
    """
    Get current routing metrics
    
    Returns:
        Current routing metrics
    """
    return router_core.metrics