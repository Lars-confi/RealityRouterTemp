with open("src/router/metrics.py", "r") as f:
    content = f.read()

bad_func = """    def collect_routing_metrics(self, db: Session, model_id: str, cost: float, time: float,
                              probability: float, success: bool, query: str):
        \"\"\"
        Collect routing metrics for a single request

        Args:
            db: Database session
            model_id: ID of the model used
            cost: Cost of the request
            time: Time taken for the request
            probability: Success probability
            success: Whether the request was successful
            query: The original query
        \"\"\"
        try:
            # Create a new routing log entry
            log_entry = RoutingLog(
                query=query,
                model_id=model_id,
                cost=cost,
                time=time,
                probability=probability,
                success=success
            )"""

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

content = content.replace(bad_func, good_func)

with open("src/router/metrics.py", "w") as f:
    f.write(content)
