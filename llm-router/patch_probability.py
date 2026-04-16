import re

with open('src/router/core.py', 'r') as f:
    content = f.read()

new_method = '''
    def _estimate_probability(self, model_id: str, request: RoutingRequest) -> float:
        """
        Estimate the probability of a successful response.
        As specified in the architecture, initially this uses a random 
        number generator sampling values from the uniform distribution on [0,1].
        """
        import random
        return random.uniform(0.0, 1.0)

    def get_ranked_models(self, request: RoutingRequest, strategy: str = "expected_utility"):'''

content = content.replace('    def get_ranked_models(self, request: RoutingRequest, strategy: str = "expected_utility"):', new_method)

old_prob_code = '''                probability = model_info['probability']
                if input_tokens > 2000:
                    if 'gpt-4' not in model_id and 'claude-3-opus' not in model_id:
                        probability = max(0.1, probability - 0.2)'''

new_prob_code = '''                probability = self._estimate_probability(model_id, request)'''

content = content.replace(old_prob_code, new_prob_code)

with open('src/router/core.py', 'w') as f:
    f.write(content)

