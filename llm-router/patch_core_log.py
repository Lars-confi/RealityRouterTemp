import re

with open("src/router/core.py", "r") as f:
    content = f.read()

old_metrics_call = """            # Collect metrics using the metrics collector
            metrics_collector.collect_routing_metrics(
                db=db,
                model_id=decision.model_id,
                cost=decision.cost,
                time=decision.time,
                probability=decision.probability,
                success=True,  # We assume success for now, but this could be enhanced
                query=request.query
            )"""

new_metrics_call = """            import json
            req_payload = json.dumps(request.parameters) if request.parameters else "{}"
            resp_payload = json.dumps(response) if response else "{}"
            is_success = bool(response)
            response_text = response.get('text', '') if response else ''
            
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
                response_payload=resp_payload
            )"""

content = content.replace(old_metrics_call, new_metrics_call)

with open("src/router/core.py", "w") as f:
    f.write(content)
