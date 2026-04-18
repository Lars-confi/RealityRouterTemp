"""
Core routing logic implementing Expected Utility Theory framework
"""

import ast
import asyncio
import datetime
import hashlib
import json
import math
import re
import statistics
import time
from typing import Any, Dict, List, Optional, Union

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.adapters.generic_openai_adapter import GenericOpenAIAdapter
from src.config.settings import get_settings, load_models_from_config
from src.models.database import RoutingLog, SessionLocal, get_db, init_db
from src.models.routing import RoutingRequest, RoutingResponse
from src.router.load_balancer import load_balancer
from src.router.metrics import metrics_collector
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()

# Reality Check API Configuration
REALITY_CHECK_URL = (
    "https://llmrouter-api.jollysand-1b9ed42e.swedencentral.azurecontainerapps.io"
)
REALITY_CHECK_KEY = "f7a2b9c8d1e3f5a2b9c8d1e3f5a2b9c8"


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
    reality_check_id: Optional[Union[int, str]] = None
    feedback_required: bool = False


class ExpectedUtilityCalculator:
    """Calculator for Expected Utility Theory implementation"""

    def __init__(
        self,
        reward: float = 1.0,
        cost_sensitivity: float = 0.5,
        time_sensitivity: float = 0.5,
    ):
        self.reward = reward
        self.cost_sensitivity = cost_sensitivity
        self.time_sensitivity = time_sensitivity

        if time_sensitivity is None:
            self.time_sensitivity = 1.0 - cost_sensitivity

    def calculate_expected_utility(
        self, cost: float, time: float, probability: float
    ) -> float:
        return (
            probability * self.reward
            - self.cost_sensitivity * cost
            - self.time_sensitivity * time
        )


class RouterCore:
    """Main router core implementing Expected Utility Theory"""

    def __init__(self):
        self.models = {}
        self.metrics = {}
        self.utility_calculator = ExpectedUtilityCalculator()
        self.adapters = {}
        self.load_balancer = load_balancer

        init_db()
        self.load_configured_models()

        logger.info("Router core initialized with Expected Utility Theory framework")

    def load_configured_models(self):
        """Load models from configuration and dynamically discover them"""
        try:
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
                self.adapters[model_id] = GenericOpenAIAdapter(
                    model_name=model_info.get("name", model_id),
                    api_key=model_info.get("api_key"),
                    base_url=model_info.get("base_url"),
                    default_model=model_info.get("model", model_id),
                )

            # Auto-Discover Dynamic Models
            if not settings.enable_auto_discovery:
                logger.info("Auto-discovery is disabled.")
                return

            logger.info("Auto-discovering models from configured providers...")

            # 1. Custom/Local Models (Ollama or Generic)
            custom_url = settings.custom_llm_base_url
            custom_key = settings.custom_llm_api_key or "dummy"
            if custom_url:
                try:
                    if "11434" in custom_url:  # Ollama
                        ollama_url = (
                            custom_url.replace("/v1", "/api/tags")
                            if custom_url.endswith("/v1")
                            else f"{custom_url}/api/tags"
                        )
                        resp = httpx.get(ollama_url, timeout=3)
                        if resp.status_code == 200:
                            ollama_models = resp.json().get("models", [])
                            logger.info(
                                f"Ollama discovery: found {len(ollama_models)} models"
                            )
                            for m in ollama_models:
                                name = m.get("name")
                                if name and name not in self.models:
                                    self.add_model(name, name, 0.0, 1.0, 0.8)
                                    self.load_balancer.add_model(name, name, 1.0)
                                    base = (
                                        custom_url
                                        if custom_url.endswith("/v1")
                                        else f"{custom_url}/v1"
                                    )
                                    self.adapters[name] = GenericOpenAIAdapter(
                                        name, custom_key, base, name
                                    )
                    else:
                        resp = httpx.get(
                            f"{custom_url}/models",
                            headers={"Authorization": f"Bearer {custom_key}"},
                            timeout=3,
                        )
                        if resp.status_code == 200:
                            for m in resp.json().get("data", []):
                                name = m.get("id")
                                if name and name not in self.models:
                                    self.add_model(name, name, 0.001, 1.0, 0.8)
                                    self.load_balancer.add_model(name, name, 1.0)
                                    base = (
                                        custom_url
                                        if custom_url.endswith("/v1")
                                        else f"{custom_url}/v1"
                                    )
                                    self.adapters[name] = GenericOpenAIAdapter(
                                        name, custom_key, base, name
                                    )
                except Exception as e:
                    logger.warning(
                        f"Auto-discovery failed for custom URL {custom_url}: {e}"
                    )

            # 2. OpenAI
            openai_key = settings.openai_api_key
            if openai_key and openai_key != "dummy":
                try:
                    resp = httpx.get(
                        "https://api.openai.com/v1/models",
                        headers={"Authorization": f"Bearer {openai_key}"},
                        timeout=3,
                    )
                    if resp.status_code == 200:
                        for m in resp.json().get("data", []):
                            name = m.get("id")
                            if name and ("gpt" in name or "o1" in name):
                                if name not in self.models:
                                    cost = 0.01 if "gpt-4" in name else 0.002
                                    self.add_model(name, name, cost, 0.5, 0.9)
                                    self.load_balancer.add_model(name, name, 1.0)
                                    self.adapters[name] = GenericOpenAIAdapter(
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
                    resp = httpx.get(
                        "https://generativelanguage.googleapis.com/v1beta/openai/models",
                        headers={"Authorization": f"Bearer {gemini_key}"},
                        timeout=3,
                    )
                    if resp.status_code == 200:
                        for m in resp.json().get("data", []):
                            name = m.get("id")
                            if (
                                name
                                and ("gemini" in name or "gemma" in name)
                                and "embedding" not in name
                            ):
                                if name not in self.models:
                                    self.add_model(name, name, 0.00035, 0.4, 0.88)
                                    self.load_balancer.add_model(name, name, 1.0)
                                    self.adapters[name] = GenericOpenAIAdapter(
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

    def extract_coding_features(
        self, request: RoutingRequest, model_id: str = "unknown"
    ) -> Dict[str, Any]:
        """Extract 40 fixed-dimensional features for coding queries including model fingerprint"""
        query = request.query or ""
        params = request.parameters or {}
        messages = params.get("messages", [])

        f = {}

        # 1. Structural (AST)
        code = "\n".join(re.findall(r"```(?:\w+)?\n(.*?)\n```", query, re.DOTALL))
        nodes, height, loops, logic, funcs = 0, 0, 0, 0, 0
        try:
            if code.strip():
                tree = ast.parse(code)
                for node in ast.walk(tree):
                    nodes += 1
                    if isinstance(node, (ast.For, ast.While)):
                        loops += 1
                    if isinstance(node, (ast.If, ast.BoolOp, ast.Compare)):
                        logic += 1
                    if isinstance(
                        node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
                    ):
                        funcs += 1

                def get_h(n):
                    c = list(ast.iter_child_nodes(n))
                    return 1 + max([get_h(x) for x in c]) if c else 1

                height = get_h(tree)
        except:
            pass

        f["struct_nodes"] = float(nodes)
        f["struct_height"] = float(height)
        f["struct_loop_dens"] = loops / nodes if nodes > 0 else 0.0
        f["struct_logic_dens"] = logic / nodes if nodes > 0 else 0.0
        f["struct_func_dens"] = funcs / nodes if nodes > 0 else 0.0
        f["struct_dep_count"] = float(len(re.findall(r"^(import|from)\s", code, re.M)))

        # 2. State (Trace)
        it = params.get("iteration", 1)
        mx = params.get("max_iterations", 10)
        f["trace_iter_idx"] = float(it)
        f["trace_iter_ratio"] = it / mx if mx > 0 else 0.0
        h = {"r": 0, "w": 0, "e": 0, "s": 0}
        for m in messages:
            c = str(m.get("content", "")).lower()
            if "read" in c:
                h["r"] += 1
            if "write" in c:
                h["w"] += 1
            if "exec" in c:
                h["e"] += 1
            if "search" in c:
                h["s"] += 1
        tot = sum(h.values()) or 1
        f["trace_read_freq"] = h["r"] / tot
        f["trace_write_freq"] = h["w"] / tot
        f["trace_exec_freq"] = h["e"] / tot
        f["trace_search_freq"] = h["s"] / tot
        f["trace_err_flag"] = 1.0 if "error" in query.lower() else 0.0

        # 3. Metadata
        f["meta_pos_con"] = float(
            len(re.findall(r"\b(must|use|always)\b", query.lower()))
        )
        f["meta_neg_con"] = float(
            len(re.findall(r"\b(don't|never|avoid)\b", query.lower()))
        )
        ids = re.findall(r"[a-zA-Z_]\w*", query)
        f["meta_id_dens"] = len(ids) / len(query.split()) if query.split() else 0.0
        f["meta_grounding"] = 1.0 if re.search(r"(/|\\|\.\w{2,4})", query) else 0.0

        # 4. Semantic
        ql = query.lower()
        f["sem_gen"] = 1.0 if "generate" in ql or "implement" in ql else 0.0
        f["sem_fix"] = 1.0 if "fix" in ql or "bug" in ql else 0.0
        f["sem_refactor"] = 1.0 if "refactor" in ql or "improve" in ql else 0.0
        f["sem_docs"] = 1.0 if "document" in ql or "explain" in ql else 0.0

        # 5. Telemetry
        f["tele_p_len"] = float(len(query))
        f["tele_hist_depth"] = float(len(messages))
        f["tele_ctx_pressure"] = len(str(messages)) / 32768.0
        f["tele_avg_msg"] = (
            statistics.mean([len(str(m.get("content", ""))) for m in messages])
            if messages
            else 0.0
        )

        # 6. Model Fingerprint (8 dimensions)
        m_hs = hashlib.sha256(model_id.encode()).hexdigest()
        for i in range(8):
            chunk = m_hs[i * 8 : (i + 1) * 8]
            f[f"model_fp_{i}"] = int(chunk, 16) / 0xFFFFFFFF

        # 7. Query Signature Hash
        q_hs = hashlib.md5(query.encode()).hexdigest()
        for i in range(6):
            f[f"query_hash_{i}"] = int(q_hs[i * 2 : i * 2 + 2], 16) / 255.0

        return f

    async def get_ranked_models(
        self, request: RoutingRequest, strategy: str = "expected_utility"
    ) -> List[RoutingDecision]:
        """Select models and rank them using Reality Check calibration"""
        if not self.models:
            raise HTTPException(
                status_code=500, detail="No models available for routing"
            )

        db = SessionLocal()
        try:
            if strategy == "load_balanced":
                model_id = self.load_balancer.get_next_model("weighted", db)
                if model_id is None:
                    raise HTTPException(
                        status_code=500, detail="No suitable model found"
                    )
                m = self.models[model_id]
                return [
                    RoutingDecision(
                        model_id=model_id,
                        expected_utility=0.0,
                        cost=m["cost"],
                        time=m["time"],
                        probability=m["probability"],
                        name=m["name"],
                    )
                ]

            model_tasks = []
            for mid, info in self.models.items():
                recent = (
                    db.query(RoutingLog)
                    .filter(RoutingLog.model_id == mid, RoutingLog.time != None)
                    .order_by(RoutingLog.timestamp.desc())
                    .limit(20)
                    .all()
                )
                time_val = (
                    statistics.mean([l.time for l in recent])
                    if recent
                    else info["time"]
                )
                features = self.extract_coding_features(request, mid)
                model_tasks.append(
                    {
                        "id": mid,
                        "name": info["name"],
                        "cost": info["cost"],
                        "time": time_val,
                        "features": features,
                    }
                )

            async def call_rc(m):
                try:
                    async with httpx.AsyncClient() as client:
                        resp = await client.post(
                            f"{REALITY_CHECK_URL}/decide",
                            json={"features": m["features"]},
                            headers={"x-api-key": REALITY_CHECK_KEY},
                            timeout=5.0,
                        )
                        if resp.status_code == 200:
                            r = resp.json()
                            return {
                                **m,
                                "prob": r.get("prob_true", 0.5),
                                "rc_id": r.get("decision_id"),
                                "fb_req": r.get("decision", False),
                            }
                except:
                    pass
                return {**m, "prob": 0.5, "rc_id": None, "fb_req": False}

            results = await asyncio.gather(*[call_rc(m) for m in model_tasks])

            decisions = []
            feedback_candidates = []
            for r in results:
                utility = self.utility_calculator.calculate_expected_utility(
                    r["cost"], r["time"], r["prob"]
                )
                d = RoutingDecision(
                    model_id=r["id"],
                    expected_utility=utility,
                    cost=r["cost"],
                    time=r["time"],
                    probability=r["prob"],
                    name=r["name"],
                    reality_check_id=r["rc_id"],
                    feedback_required=r["fb_req"],
                )
                decisions.append(d)
                if r["fb_req"]:
                    feedback_candidates.append(d)

            decisions.sort(key=lambda x: x.expected_utility, reverse=True)

            if feedback_candidates:
                import random

                winner = random.choice(feedback_candidates)
                for i, d in enumerate(decisions):
                    if d.model_id == winner.model_id:
                        decisions.insert(0, decisions.pop(i))
                        break

            return decisions
        finally:
            db.close()

    def log_routing_decision(
        self,
        decision: RoutingDecision,
        request: RoutingRequest,
        response: Dict[str, Any],
        db: Session,
        routing_context: str = None,
        features: Dict[str, Any] = None,
        user_sentiment: str = None,
    ):
        try:
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
                response_text=response.get("text", ""),
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                request_payload=req_payload,
                response_payload=resp_payload,
                routing_context=routing_context,
            )

            # Retrieve the log entry we just created to update extra fields
            # We filter by model_id and query to ensure we get the right one
            log_entry = (
                db.query(RoutingLog)
                .filter(RoutingLog.model_id == decision.model_id)
                .filter(RoutingLog.query == request.query)
                .order_by(RoutingLog.timestamp.desc())
                .first()
            )

            if log_entry:
                if features:
                    log_entry.features_json = json.dumps(features)
                if user_sentiment:
                    log_entry.user_sentiment = user_sentiment
                if decision.reality_check_id:
                    log_entry.reality_check_id = str(decision.reality_check_id)
                db.commit()

            logger.info(f"Logged routing decision for model {decision.model_id}")
        except Exception as e:
            logger.error(f"Error logging routing decision: {str(e)}")

    async def assess_user_sentiment(self, request: RoutingRequest) -> Optional[str]:
        """Assess user sentiment based on conversation history for feedback"""
        try:
            messages = (request.parameters or {}).get("messages", [])
            # We need at least: [Previous User Query], [Assistant Response], [Current User Query]
            if len(messages) < 3:
                return None

            # The feedback is usually in the current user message (last one)
            # regarding the previous assistant message (second to last)
            def _get_text(content):
                if isinstance(content, str):
                    return content
                if isinstance(content, list) and content:
                    return str(content[0].get("text", ""))
                return ""

            prev_asst = _get_text(messages[-2].get("content", ""))
            curr_user = _get_text(messages[-1].get("content", ""))

            if not prev_asst or not curr_user:
                return None

            # Find a fast/cheap model to do the assessment
            cheapest_id = min(
                self.models.keys(), key=lambda m: self.models[m].get("cost", 0)
            )
            adapter = self.adapters.get(cheapest_id)
            if not adapter:
                return None

            # Refined prompt for more accurate sentiment detection
            prompt = (
                f"Analyze the following interaction to see if the user was satisfied with the assistant's last response.\n\n"
                f'Assistant\'s Response: "{prev_asst}"\n'
                f'User\'s Follow-up: "{curr_user}"\n\n'
                f"Determine if the user's follow-up indicates they were 'happy' with the previous answer, "
                f"'unhappy' (e.g., they corrected it, complained, or asked for a redo), or if it's 'indeterminate'.\n"
                f"Respond with EXACTLY one word: happy, unhappy, or indeterminate."
            )

            resp = await adapter.forward_request(
                RoutingRequest(
                    query=prompt, parameters={"max_tokens": 5, "temperature": 0}
                )
            )

            txt = str(resp.get("text", "")).lower().strip()
            if "happy" in txt:
                return "happy"
            if "unhappy" in txt:
                return "unhappy"
            return "indeterminate"
        except Exception as e:
            logger.debug(f"Sentiment assessment failed: {e}")
            return None

    async def route_request(
        self, request: RoutingRequest, strategy: str = "expected_utility"
    ) -> RoutingResponse:
        db = SessionLocal()
        try:
            ranked_decisions = await self.get_ranked_models(request, strategy)
            # Asynchronously assess sentiment and provide feedback for the PREVIOUS interaction
            sentiment = await self.assess_user_sentiment(request)

            if sentiment in ["happy", "unhappy"]:
                try:
                    # Look for the last successful routing decision that hasn't received feedback yet
                    last_log = (
                        db.query(RoutingLog)
                        .filter(RoutingLog.reality_check_id != None)
                        .filter(RoutingLog.user_sentiment == None)
                        .order_by(RoutingLog.timestamp.desc())
                        .first()
                    )

                    if last_log:
                        # Correctly attribute sentiment to the PREVIOUS log entry
                        last_log.user_sentiment = sentiment
                        db.commit()

                        logger.info(
                            f"Sending feedback to Reality Check for decision {last_log.reality_check_id}: {sentiment}"
                        )
                        async with httpx.AsyncClient() as client:
                            await client.post(
                                f"{REALITY_CHECK_URL}/feedback",
                                json={
                                    "decision_id": last_log.reality_check_id,
                                    "feedback": 1 if sentiment == "happy" else 0,
                                },
                                headers={"x-api-key": REALITY_CHECK_KEY},
                                timeout=2.0,
                            )
                except Exception as e:
                    logger.error(f"Error sending feedback to Reality Check: {e}")

            if ranked_decisions:
                print("\n" + "=" * 70)
                print(f" LLM REROUTER: RANKING MODELS ".center(70, "="))
                print("-" * 70)
                print(f"{'  Model Name (ID)':<42} | {'Utility':>10} | {'Prob':>8}")
                print("-" * 43 + "|" + "-" * 12 + "|" + "-" * 10)
                for d in ranked_decisions:
                    marker = ">>" if d == ranked_decisions[0] else "  "
                    label = d.name if len(d.name) <= 39 else d.name[:36] + "..."
                    print(
                        f"{marker} {label:<39} | {d.expected_utility:>10.4f} | {d.probability:>8.2f}"
                    )
                print("=" * 70 + "\n")

            routing_context = json.dumps([d.model_dump() for d in ranked_decisions])
            last_error = None

            for decision in ranked_decisions:
                adapter = self.adapters.get(decision.model_id)
                if not adapter:
                    continue
                try:
                    start_time = time.time()
                    response = await adapter.forward_request(request)
                    elapsed_time = time.time() - start_time
                    self.load_balancer.update_metrics(decision.model_id, success=True)

                    final_features = self.extract_coding_features(
                        request, decision.model_id
                    )
                    self.log_routing_decision(
                        decision.model_copy(update={"time": elapsed_time}),
                        request,
                        response,
                        db,
                        routing_context,
                        final_features,
                        None,  # Sentiment belongs to the previous response
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
                    logger.error(f"Model {decision.model_id} failed: {e}")
                    last_error = str(e)
                    self.load_balancer.update_metrics(decision.model_id, success=False)

                    self.log_routing_decision(
                        decision,
                        request,
                        {},
                        db,
                        routing_context,
                        self.extract_coding_features(request, decision.model_id),
                        None,  # Sentiment belongs to the previous response
                    )

            raise HTTPException(
                status_code=500, detail=f"All models failed. Last error: {last_error}"
            )
        except Exception as e:
            logger.error(f"Routing error: {e}")
            raise HTTPException(status_code=500, detail=f"Routing error: {str(e)}")
        finally:
            db.close()


class ChatCompletionRequest(BaseModel):
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
    id: str
    object: str = "chat.completion"
    choices: List[Dict[str, Any]]
    created: int
    model: str
    usage: Dict[str, Any]


@router.post("/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    try:
        query_text = ""
        if request.messages:
            last = request.messages[-1].get("content", "")
            query_text = (
                last
                if isinstance(last, str)
                else str(last[0].get("text", ""))
                if isinstance(last, list)
                else ""
            )

        is_streaming = request.stream
        params = request.model_dump(exclude_none=True)
        params["stream"] = False
        response = await router_core.route_request(
            RoutingRequest(query=query_text, parameters=params)
        )
        created_time = int(datetime.datetime.now().timestamp())

        if not is_streaming:
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

        async def stream_generator():
            chunk_id = f"chatcmpl-{response.model_id}"
            common = {
                "id": chunk_id,
                "object": "chat.completion.chunk",
                "created": created_time,
                "model": response.model_name,
            }
            yield f"data: {json.dumps({**common, 'choices': [{'index': 0, 'delta': {'role': 'assistant'}, 'finish_reason': None}]})}\n\n"
            yield f"data: {json.dumps({**common, 'choices': [{'index': 0, 'delta': {'content': response.response.get('text', '')}, 'finish_reason': None}]})}\n\n"
            yield f"data: {json.dumps({**common, 'choices': [{'index': 0, 'delta': {}, 'finish_reason': 'stop'}]})}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(stream_generator(), media_type="text/event-stream")
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/completions")
async def completions(request: ChatCompletionRequest):
    try:
        query_text = ""
        if request.messages:
            last = request.messages[-1].get("content", "")
            query_text = (
                last
                if isinstance(last, str)
                else str(last[0].get("text", ""))
                if isinstance(last, list)
                else ""
            )

        is_streaming = request.stream
        params = request.model_dump(exclude_none=True)
        params["stream"] = False
        response = await router_core.route_request(
            RoutingRequest(query=query_text, parameters=params)
        )
        created_time = int(datetime.datetime.now().timestamp())

        if not is_streaming:
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

        async def stream_generator():
            chunk = {
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
            }
            yield f"data: {json.dumps(chunk)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(stream_generator(), media_type="text/event-stream")
    except Exception as e:
        logger.error(f"Completions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models")
async def get_models():
    return router_core.models


@router.get("/metrics")
async def get_metrics():
    return router_core.metrics


router_core = RouterCore()
