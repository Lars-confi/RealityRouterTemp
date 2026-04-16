import re

with open("src/router/metrics.py", "r") as f:
    content = f.read()

# Just use regex to blast the function signature out since string replace is failing
pattern = re.compile(r'    def collect_routing_metrics\(self, db: Session, model_id: str, cost: float, time: float,\s*probability: float, success: bool, query: str\):\s*\"\"\"\s*Collect routing metrics for a single request\s*Args:.*?\s*query: The original query\s*\"\"\"\s*try:\s*# Create a new routing log entry\s*log_entry = RoutingLog\(\s*query=query,\s*model_id=model_id,\s*cost=cost,\s*time=time,\s*probability=probability,\s*success=success\s*\)', re.DOTALL)

good_func = """    def collect_routing_metrics(self, db: Session, model_id: str, model_name: str, expected_utility: float, 
                              cost: float, time: float, probability: float, success: bool, query: str,
                              response_text: str = None, prompt_tokens: int = 0, completion_tokens: int = 0, 
                              total_tokens: int = 0, request_payload: str = None, response_payload: str = None):
        \"\"\"
        Collect routing metrics for a single request
        \"\"\"
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
                response_payload=response_payload
            )"""

new_content = pattern.sub(good_func, content)

with open("src/router/metrics.py", "w") as f:
    f.write(new_content)

