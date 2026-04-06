"""
Core routing logic implementing Expected Utility Theory framework
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel
import logging
import datetime
from src.models.routing import RoutingRequest, RoutingResponse
from src.adapters.openai_adapter import OpenAIAdapter
from src.adapters.anthropic_adapter import AnthropicAdapter
from src.adapters.cohere_adapter import CohereAdapter
from src.utils.logger import setup_logger
from src.models.database import RoutingLog, init_db, get_db
from sqlalchemy.orm import Session
from src.router.load_balancer import load_balancer
from src.config.settings import get_settings, load_models_from_config
from src.router.metrics import metrics_collector

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
        
        # Initialize load balancer
        self.load_balancer = load_balancer
        
        # Initialize database
        init_db()
        
        # Load models from configuration
        self.load_configured_models()
        
        logger.info("Router core initialized with Expected Utility Theory framework")
    
    def load_configured_models(self):
        """Load models from configuration"""
        try:
            models_config = load_models_from_config()
            
            for model_id, model_info in models_config.items():
                self.add_model(
                    model_id=model_id,
                    model_name=model_info['name'],
                    cost=model_info['cost'],
                    time=model_info['time'],
                    probability=model_info['probability']
                )
                
                # Add to load balancer
                self.load_balancer.add_model(
                    model_id=model_id,
                    model_name=model_info['name'],
                    weight=model_info.get('weight', 1.0)
                )
                
        except Exception as e:
            logger.error(f"Error loading configured models: {str(e)}")
            # Add default models as fallback
            self.add_default_models()
    
    def add_default_models(self):
        """Add default models if configuration fails"""
        default_models = {
            'openai_gpt-3.5-turbo': {
                'name': 'OpenAI GPT-3.5 Turbo',
                'cost': 0.002,
                'time': 0.5,
                'probability': 0.9
            },
            'anthropic_claude-haiku': {
                'name': 'Anthropic Claude Haiku',
                'cost': 0.00025,
                'time': 0.8,
                'probability': 0.85
            },
            'cohere_command-r-plus': {
                'name': 'Cohere Command R+',
                'cost': 0.001,
                'time': 1.0,
                'probability': 0.8
            }
        }
        
        for model_id, model_info in default_models.items():
            self.add_model(
                model_id=model_id,
                model_name=model_info['name'],
                cost=model_info['cost'],
                time=model_info['time'],
                probability=model_info['probability']
            )
            
            # Add to load balancer
            self.load_balancer.add_model(
                model_id=model_id,
                model_name=model_info['name'],
                weight=1.0
            )
    
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
    
    def get_best_model(self, request: RoutingRequest, strategy: str = "expected_utility") -> RoutingDecision:
        """
        Select the best model based on the specified strategy
        
        Args:
            request: Routing request with query information
            strategy: Selection strategy ("expected_utility", "load_balanced")
            
        Returns:
            RoutingDecision with the best model and expected utility
        """
        if not self.models:
            raise HTTPException(status_code=500, detail="No models available for routing")
        
        if strategy == "load_balanced":
            # Use load balancer to select model
            db = next(get_db())  # Get database session
            model_id = self.load_balancer.get_next_model("weighted", db)
            
            if model_id is None:
                raise HTTPException(status_code=500, detail="No suitable model found for routing")
            
            model_info = self.models[model_id]
            
            return RoutingDecision(
                model_id=model_id,
                expected_utility=0.0,  # We don't calculate utility for load balancing
                cost=model_info['cost'],
                time=model_info['time'],
                probability=model_info['probability'],
                name=model_info['name']
            )
        else:
            # Use Expected Utility Theory (default)
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
            
            # Collect metrics using the metrics collector
            metrics_collector.collect_routing_metrics(
                db=db,
                model_id=decision.model_id,
                cost=decision.cost,
                time=decision.time,
                probability=decision.probability,
                success=True,  # We assume success for now, but this could be enhanced
                query=request.query
            )
            
            logger.info(f"Logged routing decision for model {decision.model_id}")
            
        except Exception as e:
            logger.error(f"Error logging routing decision: {str(e)}")
            # Don't fail the request for logging errors
    
    def route_request(self, request: RoutingRequest, strategy: str = "expected_utility") -> RoutingResponse:
        """
        Route a request to the best model
        
        Args:
            request: Routing request with query information
            strategy: Selection strategy ("expected_utility", "load_balanced")
            
        Returns:
            RoutingResponse with the selected model and routing information
        """
        try:
            # Get the best model based on the specified strategy
            decision = self.get_best_model(request, strategy)
            
            # Get the adapter for the selected model
            adapter = self.adapters.get(decision.model_id.split('_')[0])  # Simple approach
            
            if not adapter:
                raise HTTPException(status_code=500, detail=f"No adapter found for model {decision.model_id}")
            
            # Forward the request to the selected model
            response = adapter.forward_request(request)
            
            # Update load balancer metrics
            self.load_balancer.update_metrics(decision.model_id, success=True)
            
            # Log the routing decision to database
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

# Support for standard LLM API endpoints
class ChatCompletionRequest(BaseModel):
    """Standard chat completion request model"""
    messages: List[Dict[str, Any]]
    model: Optional[str] = None
    temperature: Optional[float] = 1.0
    max_tokens: Optional[int] = None
    top_p: Optional[float] = 1.0
    frequency_penalty: Optional[float] = 0.0
    presence_penalty: Optional[float] = 0.0
    stop: Optional[Union[str, List[str]]] = None
    stream: Optional[bool] = False

class ChatCompletionResponse(BaseModel):
    """Standard chat completion response model"""
    id: str
    choices: List[Dict[str, Any]]
    created: int
    model: str
    usage: Dict[str, Any]

@router.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """
    Standard chat completions endpoint that routes to the best model
    
    Args:
        request: Standard chat completion request
        
    Returns:
        Standard chat completion response
    """
    try:
        # Convert standard request to internal routing request
        routing_request = RoutingRequest(
            query=request.messages[-1]['content'] if request.messages else "",
            parameters={
                "messages": request.messages,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "model": request.model
            }
        )
        
        # Route the request
        response = router_core.route_request(routing_request)
        
        # Convert to standard response format
        return {
            "id": f"chatcmpl-{response.model_id}",
            "choices": [
                {
                    "finish_reason": "stop",
                    "index": 0,
                    "message": {
                        "content": response.response.get("text", ""),
                        "role": "assistant"
                    }
                }
            ],
            "created": int(datetime.datetime.now().timestamp()),
            "model": response.model_name,
            "usage": response.response.get("usage", {})
        }
    except Exception as e:
        logger.error(f"Error in chat completions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/v1/completions")
async def completions(request: ChatCompletionRequest):
    """
    Standard completions endpoint that routes to the best model
    
    Args:
        request: Standard completions request
        
    Returns:
        Standard completions response
    """
    try:
        # Convert standard request to internal routing request
        routing_request = RoutingRequest(
            query=request.messages[-1]['content'] if request.messages else "",
            parameters={
                "prompt": request.messages[-1]['content'] if request.messages else "",
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "model": request.model
            }
        )
        
        # Route the request
        response = router_core.route_request(routing_request)
        
        # Convert to standard response format
        return {
            "id": f"cmpl-{response.model_id}",
            "choices": [
                {
                    "finish_reason": "stop",
                    "index": 0,
                    "text": response.response.get("text", "")
                }
            ],
            "created": int(datetime.datetime.now().timestamp()),
            "model": response.model_name,
            "usage": response.response.get("usage", {})
        }
    except Exception as e:
        logger.error(f"Error in completions: {str(e)}")
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