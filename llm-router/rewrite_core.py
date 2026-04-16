import re

with open('src/router/core.py', 'r') as f:
    content = f.read()

# 1. Add imports
content = content.replace(
    'from src.adapters.cohere_adapter import CohereAdapter',
    'from src.adapters.cohere_adapter import CohereAdapter\nfrom src.adapters.huggingface_adapter import HuggingFaceAdapter\nfrom src.adapters.generic_openai_adapter import GenericOpenAIAdapter'
)

# 2. Add async imports
if 'import time' not in content:
    content = 'import time\n' + content

# 3. Add HuggingFace and GenericOpenAI to adapters
adapter_init = """        self.adapters = {
            'openai': OpenAIAdapter(),
            'anthropic': AnthropicAdapter(),
            'cohere': CohereAdapter(),
            'huggingface': HuggingFaceAdapter(),
            'generic': GenericOpenAIAdapter()
        }"""
content = re.sub(
    r"self\.adapters\s*=\s*\{.*?\}", 
    adapter_init, 
    content, 
    flags=re.DOTALL
)

# 4. Modify route_request to be async and handle failover
route_method_pattern = r'    def route_request\(self, request: RoutingRequest, strategy: str = "expected_utility"\) -> RoutingResponse:.*?(?=    class|\Z)'

# We need to replace get_best_model and route_request.
# Let's write a new block for them.
new_methods = '''
    def get_ranked_models(self, request: RoutingRequest, strategy: str = "expected_utility"):
        """Select models and rank them based on strategy"""
        if not self.models:
            raise HTTPException(status_code=500, detail="No models available for routing")
        
        # Estimate input tokens (simple approx: 1 token = 4 chars)
        input_tokens = len(request.query) // 4
        
        ranked_decisions = []
        
        if strategy == "load_balanced":
            db = next(get_db())
            model_id = self.load_balancer.get_next_model("weighted", db)
            if model_id is None:
                raise HTTPException(status_code=500, detail="No suitable model found for routing")
            model_info = self.models[model_id]
            return [RoutingDecision(
                model_id=model_id,
                expected_utility=0.0,
                cost=model_info['cost'],
                time=model_info['time'],
                probability=model_info['probability'],
                name=model_info['name']
            )]
            
        else:
            db = next(get_db())
            from src.models.database import RoutingLog
            
            for model_id, model_info in self.models.items():
                adapter_key = model_id.split('_')[0]
                adapter = self.adapters.get(adapter_key)
                
                # Dynamic cost calculation
                cost = model_info['cost']
                if adapter and hasattr(adapter, 'estimate_cost'):
                    # Assume 500 output tokens for estimate
                    cost = adapter.estimate_cost(input_tokens, 500)
                
                # Dynamic time calculation based on recent performance
                recent_logs = db.query(RoutingLog).filter(RoutingLog.model_id == model_id, RoutingLog.time != None).order_by(RoutingLog.timestamp.desc()).limit(20).all()
                if recent_logs:
                    time_val = sum(l.time for l in recent_logs) / len(recent_logs)
                else:
                    time_val = model_info['time']
                
                # Dynamic probability approximation based on complexity
                probability = model_info['probability']
                if input_tokens > 2000:  # Adjust probability down for very long contexts on weaker models
                    if 'gpt-4' not in model_id and 'claude-3-opus' not in model_id:
                        probability = max(0.1, probability - 0.2)
                
                utility = self.utility_calculator.calculate_expected_utility(cost, time_val, probability)
                
                ranked_decisions.append(RoutingDecision(
                    model_id=model_id,
                    expected_utility=utility,
                    cost=cost,
                    time=time_val,
                    probability=probability,
                    name=model_info['name']
                ))
            
            # Sort by highest utility first
            ranked_decisions.sort(key=lambda x: x.expected_utility, reverse=True)
            return ranked_decisions

    async def route_request(self, request: RoutingRequest, strategy: str = "expected_utility") -> RoutingResponse:
        """Route request to the best model with failover support"""
        try:
            ranked_decisions = self.get_ranked_models(request, strategy)
            if not ranked_decisions:
                raise HTTPException(status_code=500, detail="No models available after ranking")
                
            last_error = None
            
            # Failover loop
            for decision in ranked_decisions:
                adapter_key = decision.model_id.split('_')[0]
                adapter = self.adapters.get(adapter_key)
                
                if not adapter:
                    logger.warning(f"No adapter found for {decision.model_id}, trying next.")
                    continue
                
                try:
                    start_time = time.time()
                    response = await adapter.forward_request(request)
                    elapsed_time = time.time() - start_time
                    
                    # Log success
                    self.load_balancer.update_metrics(decision.model_id, success=True)
                    self.log_routing_decision(request, decision, True, elapsed_time, response)
                    
                    return RoutingResponse(
                        model_id=decision.model_id,
                        model_name=decision.name,
                        expected_utility=decision.expected_utility,
                        cost=decision.cost,
                        time=elapsed_time,
                        probability=decision.probability,
                        response=response
                    )
                except Exception as e:
                    logger.error(f"Model {decision.model_id} failed: {str(e)}. Attempting failover.")
                    last_error = str(e)
                    self.load_balancer.update_metrics(decision.model_id, success=False)
                    self.log_routing_decision(request, decision, False, time.time() - start_time, None)
                    
            raise HTTPException(status_code=500, detail=f"All models failed. Last error: {last_error}")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in routing request: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Routing error: {str(e)}")
'''

# Find where get_best_model is and replace everything up to route_request end
import re

# Match from get_best_model to log_routing_decision
match = re.search(r'    def get_best_model.*?    def log_routing_decision', content, re.DOTALL)
if match:
    content = content[:match.start()] + new_methods + '\n    def log_routing_decision' + content[match.end():]

# Ensure get_best_model removal also removes route_request definition correctly if it was later.
# Let's just use Python AST or simpler replacements.
