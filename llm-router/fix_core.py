import re

with open('src/router/core.py', 'r') as f:
    lines = f.readlines()

new_lines = []
in_adapters_init = False
in_get_best = False
in_route_req = False
in_log_routing = False

for i, line in enumerate(lines):
    if line.startswith('import logging'):
        new_lines.append('import time\n')
        new_lines.append(line)
        continue
        
    if line.startswith('from src.adapters.cohere_adapter import CohereAdapter'):
        new_lines.append(line)
        new_lines.append('from src.adapters.huggingface_adapter import HuggingFaceAdapter\n')
        new_lines.append('from src.adapters.generic_openai_adapter import GenericOpenAIAdapter\n')
        continue
        
    if 'self.adapters = {' in line:
        new_lines.append(line)
        new_lines.append("            'openai': OpenAIAdapter(),\n")
        new_lines.append("            'anthropic': AnthropicAdapter(),\n")
        new_lines.append("            'cohere': CohereAdapter(),\n")
        new_lines.append("            'huggingface': HuggingFaceAdapter(),\n")
        new_lines.append("            'generic': GenericOpenAIAdapter()\n")
        new_lines.append("        }\n")
        in_adapters_init = True
        continue
        
    if in_adapters_init:
        if '}' in line:
            in_adapters_init = False
        continue

    # Skip the old get_best_model completely
    if 'def get_best_model(self, request' in line:
        in_get_best = True
        
        # INSERT the new get_ranked_models right where get_best_model started
        new_methods = '''    def get_ranked_models(self, request: RoutingRequest, strategy: str = "expected_utility"):
        """Select models and rank them based on strategy"""
        if not self.models:
            raise HTTPException(status_code=500, detail="No models available for routing")
        
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
                
                cost = model_info['cost']
                if adapter and hasattr(adapter, 'estimate_cost'):
                    cost = adapter.estimate_cost(input_tokens, 500)
                
                recent_logs = db.query(RoutingLog).filter(RoutingLog.model_id == model_id, RoutingLog.time != None).order_by(RoutingLog.timestamp.desc()).limit(20).all()
                if recent_logs:
                    time_val = sum(l.time for l in recent_logs) / len(recent_logs)
                else:
                    time_val = model_info['time']
                
                probability = model_info['probability']
                if input_tokens > 2000:
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
            
            ranked_decisions.sort(key=lambda x: x.expected_utility, reverse=True)
            return ranked_decisions\n\n'''
        new_lines.append(new_methods)
        continue
        
    if in_get_best:
        if 'def log_routing_decision(self, ' in line:
            in_get_best = False
            new_lines.append(line)
        continue

    # Skip old route_request completely
    if 'def route_request(self, request' in line:
        in_route_req = True
        
        new_route_req = '''    async def route_request(self, request: RoutingRequest, strategy: str = "expected_utility") -> RoutingResponse:
        """Route request to the best model with failover support"""
        try:
            ranked_decisions = self.get_ranked_models(request, strategy)
            if not ranked_decisions:
                raise HTTPException(status_code=500, detail="No models available after ranking")
                
            last_error = None
            
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
            raise HTTPException(status_code=500, detail=f"Routing error: {str(e)}")\n\n'''
        new_lines.append(new_route_req)
        continue
        
    if in_route_req:
        if 'class ChatCompletionRequest' in line:
            in_route_req = False
            new_lines.append(line)
        continue

    # Await in chat_completions
    if 'response = router_core.route_request(routing_request)' in line:
        new_lines.append(line.replace('response = router_core', 'response = await router_core'))
        continue

    new_lines.append(line)

with open('src/router/core.py', 'w') as f:
    f.writelines(new_lines)

