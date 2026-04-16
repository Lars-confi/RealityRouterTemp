"""
Core routing logic implementing Expected Utility Theory framework
"""

import datetime
import json
import time
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.adapters.generic_openai_adapter import GenericOpenAIAdapter
from src.config.settings import get_settings, load_models_from_config
from src.models.database import RoutingLog, get_db, init_db
from src.models.routing import RoutingRequest, RoutingResponse
from src.router.load_balancer import load_balancer
from src.router.metrics import metrics_collector
from src.utils.logger import setup_logger

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

    def __init__(
        self,
        reward: float = 1.0,
        cost_sensitivity: float = 0.5,
        time_sensitivity: float = 0.5,
    ):
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

    def calculate_expected_utility(
        self, cost: float, time: float, probability: float
    ) -> float:
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
        return (
            probability * self.reward
            - self.cost_sensitivity * cost
            - self.time_sensitivity * time
        )


class RouterCore:
    """Main router core implementing Expected Utility Theory"""

    def __init__(self):
        """Initialize router with available models"""
        self.models = {}
        self.metrics = {}
        self.utility_calculator = ExpectedUtilityCalculator()

        # Initialize adapters for different LLM providers
        self.adapters = {}

        # Initialize load balancer
        self.load_balancer = load_balancer

        # Initialize database
        init_db()

        # Load models from configuration
        self.load_configured_models()

        logger.info("Router core initialized with Expected Utility Theory framework")

    def load_configured_models(self):
        """Load models from configuration and dynamically discover them"""
        try:
            import os

            import requests

            settings = get_settings()

            # Load static user models if any
            config_models = load_models_from_config()
            for model_id, model_info in config_models.items():
                self.add_model(
                    model_id=model_id,
                    model_name=model_info.get("name", model_id),
                    cost=model_info.get("cost", 0.0),
                    time=model_info.get("time", 1.0),
                    probability=model_info.get("probability", 0.8),
                )
                self.load_balancer.add_model(
                    model_id, model_info.get("name", model_id), 1.0
                )
                # Use GenericOpenAIAdapter for all statically defined models
                self.adapters[model_id] = GenericOpenAIAdapter(
                    model_name=model_info.get("name", model_id),
                    api_key=model_info.get("api_key"),
                    base_url=model_info.get("base_url"),
                    default_model=model_info.get("model", model_id),
                )

            # Auto-Discover Dynamic Models
            if not settings.enable_auto_discovery:
                logger.info("Auto-discovery is disabled.")
                logger.info(f"Total configured models: {len(self.models)}")
                return

            logger.info("Auto-discovering models from configured providers...")

            # 1. Custom/Local Models (Ollama or Generic)
            custom_url = settings.custom_llm_base_url
            custom_key = settings.custom_llm_api_key or "dummy"
            if custom_url:
                try:
                    if "11434" in custom_url:  # Ollama
                        # First try to get the list of models from Ollama
                        ollama_url = (
                            custom_url.replace("/v1", "/api/tags")
                            if custom_url.endswith("/v1")
                            else f"{custom_url}/api/tags"
                        )
                        resp = requests.get(ollama_url, timeout=3)
                        if resp.status_code == 200:
                            ollama_models = resp.json().get("models", [])
                            logger.info(
                                f"Ollama discovery: found {len(ollama_models)} models"
                            )
                            for m in ollama_models:
                                name = m.get("name")
                                if name:
                                    # Use the exact name for both ID and name
                                    mid = name
                                    if mid not in self.models:
                                        self.add_model(mid, name, 0.0, 1.0, 0.8)
                                        self.load_balancer.add_model(mid, name, 1.0)
                                        # Ensure the base URL is properly formed for Ollama
                                        adapter_base_url = custom_url
                                        if not adapter_base_url.endswith("/v1"):
                                            adapter_base_url = f"{adapter_base_url}/v1"

                                        self.adapters[mid] = GenericOpenAIAdapter(
                                            name,
                                            custom_key,
                                            adapter_base_url,
                                            name,
                                        )
                    else:  # Generic OpenAI Compatible
                        resp = requests.get(
                            f"{custom_url}/models",
                            headers={"Authorization": f"Bearer {custom_key}"},
                            timeout=3,
                        )
                        if resp.status_code == 200:
                            for m in resp.json().get("data", []):
                                name = m.get("id")
                                if name and name not in self.models:
                                    mid = name
                                    self.add_model(mid, name, 0.001, 1.0, 0.8)
                                    self.load_balancer.add_model(mid, name, 1.0)
                                    adapter_base_url = custom_url
                                    if not adapter_base_url.endswith("/v1"):
                                        adapter_base_url = f"{adapter_base_url}/v1"

                                    self.adapters[mid] = GenericOpenAIAdapter(
                                        name,
                                        custom_key,
                                        adapter_base_url,
                                        name,
                                    )
                except Exception as e:
                    logger.warning(
                        f"Auto-discovery failed for custom URL {custom_url}: {e}"
                    )

            # 2. OpenAI
            openai_key = settings.openai_api_key
            if openai_key and openai_key != "dummy" and openai_key != "sk-dummy":
                try:
                    resp = requests.get(
                        "https://api.openai.com/v1/models",
                        headers={"Authorization": f"Bearer {openai_key}"},
                        timeout=3,
                    )
                    if resp.status_code == 200:
                        openai_models = resp.json().get("data", [])
                        logger.info(
                            f"OpenAI discovery: found {len(openai_models)} total models"
                        )
                        for m in openai_models:
                            name = m.get("id")
                            if name and ("gpt" in name or "o1" in name):
                                mid = name
                                if mid not in self.models:
                                    cost = 0.01 if "gpt-4" in name else 0.002
                                    prob = 0.95 if "gpt-4" in name else 0.9
                                    self.add_model(mid, name, cost, 0.5, prob)
                                    self.load_balancer.add_model(mid, name, 1.0)

                                    self.adapters[mid] = GenericOpenAIAdapter(
                                        name,
                                        openai_key,
                                        "https://api.openai.com/v1",
                                        name,
                                    )
                except Exception as e:
                    logger.warning(f"Auto-discovery failed for OpenAI: {e}")

            # 3. Gemini
            gemini_key = settings.gemini_api_key
            if gemini_key and gemini_key != "dummy":
                try:
                    resp = requests.get(
                        "https://generativelanguage.googleapis.com/v1beta/openai/models",
                        headers={"Authorization": f"Bearer {gemini_key}"},
                        timeout=3,
                    )
                    if resp.status_code == 200:
                        gemini_models = resp.json().get("data", [])
                        logger.info(
                            f"Gemini discovery: found {len(gemini_models)} total models"
                        )
                        for m in gemini_models:
                            name = m.get("id")
                            # Filter for relevant chat/text models
                            is_relevant = (
                                name
                                and ("gemini" in name or "gemma" in name)
                                and not any(
                                    x in name
                                    for x in [
                                        "embedding",
                                        "aqa",
                                        "imagen",
                                        "veo",
                                        "lyria",
                                        "vision",
                                    ]
                                )
                            )
                            if not is_relevant:
                                continue

                            mid = name
                            if mid not in self.models:
                                self.add_model(mid, name, 0.00035, 0.4, 0.88)
                                self.load_balancer.add_model(mid, name, 1.0)

                                self.adapters[mid] = GenericOpenAIAdapter(
                                    name,
                                    gemini_key,
                                    "https://generativelanguage.googleapis.com/v1beta/openai",
                                    name,
                                )
                except Exception as e:
                    logger.warning(f"Auto-discovery failed for Gemini: {e}")

            logger.info(f"Total configured and discovered models: {len(self.models)}")

        except Exception as e:
            logger.error(f"Error loading models: {str(e)}")

    def add_model(
        self,
        model_id: str,
        model_name: str,
        cost: float,
        time: float,
        probability: float,
    ):
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
            "name": model_name,
            "cost": cost,
            "time": time,
            "probability": probability,
        }
        self.metrics[model_id] = ModelMetrics(
            model_id=model_id,
            cost=cost,
            time=time,
            probability=probability,
            name=model_name,
        )
        logger.info(f"Added model {model_name} (ID: {model_id}) to routing system")

    def _estimate_probability(self, model_id: str, request: RoutingRequest) -> float:
        """
        Estimate the probability of a successful response.
        As specified in the architecture, initially this uses a random
        number generator sampling values from the uniform distribution on [0,1].
        """
        import random

        return random.uniform(0.0, 1.0)

    def get_ranked_models(
        self, request: RoutingRequest, strategy: str = "expected_utility"
    ):
        """Select models and rank them based on strategy"""
        if not self.models:
            raise HTTPException(
                status_code=500, detail="No models available for routing"
            )

        input_tokens = len(request.query) // 4
        ranked_decisions = []

        if strategy == "load_balanced":
            db = next(get_db())
            model_id = self.load_balancer.get_next_model("weighted", db)
            if model_id is None:
                raise HTTPException(
                    status_code=500, detail="No suitable model found for routing"
                )
            model_info = self.models[model_id]
            return [
                RoutingDecision(
                    model_id=model_id,
                    expected_utility=0.0,
                    cost=model_info["cost"],
                    time=model_info["time"],
                    probability=model_info["probability"],
                    name=model_info["name"],
                )
            ]
        else:
            db = next(get_db())

            for model_id, model_info in self.models.items():
                adapter_key = model_id.split("_")[0]
                adapter = self.adapters.get(model_id) or self.adapters.get(adapter_key)
                if not adapter:
                    pass  # logger.warning(f'Missing adapter for {model_id}')

                cost = model_info["cost"]
                if adapter and hasattr(adapter, "estimate_cost"):
                    cost = adapter.estimate_cost(input_tokens, 500)

                recent_logs = (
                    db.query(RoutingLog)
                    .filter(RoutingLog.model_id == model_id, RoutingLog.time != None)
                    .order_by(RoutingLog.timestamp.desc())
                    .limit(20)
                    .all()
                )
                if recent_logs:
                    time_val = sum(l.time for l in recent_logs) / len(recent_logs)
                else:
                    time_val = model_info["time"]

                probability = self._estimate_probability(model_id, request)

                utility = self.utility_calculator.calculate_expected_utility(
                    cost, time_val, probability
                )

                ranked_decisions.append(
                    RoutingDecision(
                        model_id=model_id,
                        expected_utility=utility,
                        cost=cost,
                        time=time_val,
                        probability=probability,
                        name=model_info["name"],
                    )
                )

            ranked_decisions.sort(key=lambda x: x.expected_utility, reverse=True)
            return ranked_decisions

    def log_routing_decision(
        self,
        decision: RoutingDecision,
        request: RoutingRequest,
        response: Dict[str, Any],
        db: Session,
        routing_context: str = None,
    ):
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
            prompt_tokens = (
                response.get("usage", {}).get("prompt_tokens", 0)
                if response.get("usage")
                else 0
            )
            completion_tokens = (
                response.get("usage", {}).get("completion_tokens", 0)
                if response.get("usage")
                else 0
            )
            total_tokens = (
                response.get("usage", {}).get("total_tokens", 0)
                if response.get("usage")
                else 0
            )

            req_payload = json.dumps(request.parameters) if request.parameters else "{}"
            resp_payload = json.dumps(response) if response else "{}"
            is_success = bool(response)
            response_text = response.get("text", "") if response else ""

            # Collect metrics using the metrics collector
            metrics_collector.collect_routing_metrics(
                db=db,
                model_id=decision.model_id,
                model_name=decision.name,
                expected_utility=decision.expected_utility,
                cost=decision.cost,
                time=decision.time,
                probability=decision.probability,
                success=is_success,
                query=request.query,
                response_text=response_text,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                request_payload=req_payload,
                response_payload=resp_payload,
                routing_context=routing_context,
            )

            logger.info(f"Logged routing decision for model {decision.model_id}")

        except Exception as e:
            logger.error(f"Error logging routing decision: {str(e)}")
            # Don't fail the request for logging errors

    async def route_request(
        self, request: RoutingRequest, strategy: str = "expected_utility"
    ) -> RoutingResponse:
        """Route request to the best model with failover support"""
        try:
            ranked_decisions = self.get_ranked_models(request, strategy)

            # Display real-time routing comparison in the server terminal
            if ranked_decisions:
                print("\n" + "=" * 70)
                print(f" LLM REROUTER: RANKING MODELS ".center(70, "="))
                print("-" * 70)
                print(f"{'  Model Name (ID)':<42} | {'Utility':>10} | {'Prob':>8}")
                print("-" * 43 + "|" + "-" * 12 + "|" + "-" * 10)
                for d in ranked_decisions:
                    marker = ">>" if d == ranked_decisions[0] else "  "
                    label = (
                        d.model_id
                        if d.name == d.model_id
                        else f"{d.name} ({d.model_id})"
                    )
                    label = (label[:39] + "...") if len(label) > 42 else label
                    print(
                        f"{marker} {label:<39} | {d.expected_utility:>10.4f} | {d.probability:>8.2f}"
                    )
                print("=" * 70 + "\n")

            routing_context = (
                json.dumps([d.model_dump() for d in ranked_decisions])
                if ranked_decisions
                else None
            )

            if not ranked_decisions:
                raise HTTPException(
                    status_code=500, detail="No models available after ranking"
                )

            last_error = None

            for decision in ranked_decisions:
                adapter_key = decision.model_id.split("_")[0]
                model_id = decision.model_id
                adapter = self.adapters.get(decision.model_id) or self.adapters.get(
                    adapter_key
                )
                if not adapter:
                    logger.warning(f"Missing adapter for {decision.model_id}")

                if not adapter:
                    logger.warning(
                        f"No adapter found for {decision.model_id}, trying next."
                    )
                    continue

                try:
                    start_time = time.time()
                    response = await adapter.forward_request(request)
                    elapsed_time = time.time() - start_time

                    self.load_balancer.update_metrics(decision.model_id, success=True)
                    db = next(get_db())
                    # Log actual elapsed time instead of predicted time
                    # Pydantic V2 model_copy with update
                    decision_with_actual_time = decision.model_copy(
                        update={"time": elapsed_time}
                    )
                    self.log_routing_decision(
                        decision_with_actual_time,
                        request,
                        response,
                        db,
                        routing_context,
                    )

                    return RoutingResponse(
                        model_id=decision.model_id,
                        model_name=decision.name,
                        expected_utility=decision.expected_utility,
                        cost=decision.cost,
                        time=elapsed_time,
                        probability=decision.probability,
                        response=response,
                    )
                except Exception as e:
                    logger.error(
                        f"Model {decision.model_id} failed: {str(e)}. Attempting failover."
                    )
                    last_error = str(e)
                    self.load_balancer.update_metrics(decision.model_id, success=False)
                    db = next(get_db())
                    self.log_routing_decision(
                        decision, request, {}, db, routing_context
                    )

            raise HTTPException(
                status_code=500, detail=f"All models failed. Last error: {last_error}"
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in routing request: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Routing error: {str(e)}")


# Global instance
# (RouterCore instantiated below)


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
    object: str = "chat.completion"
    choices: List[Dict[str, Any]]
    created: int
    model: str
    usage: Dict[str, Any]


@router.post("/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """
    Standard chat completions endpoint that routes to the best model
    """
    try:
        # Convert standard request to internal routing request
        query_text = ""
        if request.messages:
            last_content = request.messages[-1].get("content", "")
            if isinstance(last_content, str):
                query_text = last_content
            elif isinstance(last_content, list) and len(last_content) > 0:
                query_text = str(last_content[0].get("text", ""))

        is_streaming = request.stream
        params = request.model_dump(exclude_none=True)
        params["stream"] = False  # The internal call is never streaming for now

        routing_request = RoutingRequest(
            query=query_text,
            parameters=params,
        )

        # Route the request
        response = await router_core.route_request(routing_request)
        created_time = int(datetime.datetime.now().timestamp())

        if not is_streaming:
            # Convert to standard response format
            return {
                "id": f"chatcmpl-{response.model_id}",
                "object": "chat.completion",
                "created": created_time,
                "model": response.model_name,
                "system_fingerprint": "fp_llm_rerouter",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": response.response.get("text", ""),
                        },
                        "logprobs": None,
                        "finish_reason": "stop",
                    }
                ],
                "usage": response.response.get("usage", {}),
            }

        # Handle streaming
        async def stream_generator():
            chunk_id = f"chatcmpl-{response.model_id}"

            # 1. Role chunk
            role_chunk = {
                "id": chunk_id,
                "object": "chat.completion.chunk",
                "created": created_time,
                "model": response.model_name,
                "choices": [
                    {"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}
                ],
            }
            yield f"data: {json.dumps(role_chunk)}\n\n"

            # 2. Content chunk
            content = response.response.get("text", "")
            content_chunk = {
                "id": chunk_id,
                "object": "chat.completion.chunk",
                "created": created_time,
                "model": response.model_name,
                "choices": [
                    {"index": 0, "delta": {"content": content}, "finish_reason": None}
                ],
            }
            yield f"data: {json.dumps(content_chunk)}\n\n"

            # 3. Finish chunk
            finish_chunk = {
                "id": chunk_id,
                "object": "chat.completion.chunk",
                "created": created_time,
                "model": response.model_name,
                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
            }
            yield f"data: {json.dumps(finish_chunk)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(stream_generator(), media_type="text/event-stream")
    except Exception as e:
        logger.error(f"Error in chat completions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/completions")
async def completions(request: ChatCompletionRequest):
    """
    Standard completions endpoint that routes to the best model
    """
    try:
        # Convert standard request to internal routing request
        query_text = ""
        if request.messages:
            last_content = request.messages[-1].get("content", "")
            if isinstance(last_content, str):
                query_text = last_content
            elif isinstance(last_content, list) and len(last_content) > 0:
                query_text = str(last_content[0].get("text", ""))

        is_streaming = request.stream
        params = request.model_dump(exclude_none=True)
        params["stream"] = False  # Force non-streaming

        routing_request = RoutingRequest(
            query=query_text,
            parameters=params,
        )

        # Route the request
        response = await router_core.route_request(routing_request)
        created_time = int(datetime.datetime.now().timestamp())

        if not is_streaming:
            # Convert to standard response format
            return {
                "id": f"cmpl-{response.model_id}",
                "object": "text_completion",
                "created": created_time,
                "model": response.model_name,
                "choices": [
                    {
                        "text": response.response.get("text", ""),
                        "index": 0,
                        "logprobs": None,
                        "finish_reason": "stop",
                    }
                ],
                "usage": response.response.get("usage", {}),
            }

        # Handle streaming
        async def stream_generator():
            chunk_id = f"cmpl-{response.model_id}"

            content = response.response.get("text", "")
            chunk = {
                "id": chunk_id,
                "object": "text_completion",
                "created": created_time,
                "model": response.model_name,
                "choices": [
                    {
                        "text": content,
                        "index": 0,
                        "logprobs": None,
                        "finish_reason": "stop",
                    }
                ],
            }
            yield f"data: {json.dumps(chunk)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(stream_generator(), media_type="text/event-stream")
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


# Initialize single global instance
try:
    router_core = RouterCore()
except Exception as e:
    logger.error(f"Failed to initialize router core: {e}")
    router_core = None
