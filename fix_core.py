import re

with open("llm-router/src/router/core.py", "r") as f:
    content = f.read()

# Replace p_cost, c_cost = pricing_manager.get_model_pricing
content = content.replace(
    "p_cost, c_cost = pricing_manager.get_model_pricing(model_id)",
    "p_cost, c_cost, supports_function_calling, max_input_tokens, max_tokens = pricing_manager.get_model_pricing(model_id)"
)

content = content.replace(
    "p_cost, c_cost = pricing_manager.get_model_pricing(\n                                        name\n                                    )",
    "p_cost, c_cost, supports_function_calling, max_input_tokens, max_tokens = pricing_manager.get_model_pricing(name)"
)

# In the first add_model:
content = content.replace(
    """                    completion_cost=model_info.get("completion_cost")
                    if model_info.get("completion_cost") is not None
                    else c_cost,
                )""",
    """                    completion_cost=model_info.get("completion_cost")
                    if model_info.get("completion_cost") is not None
                    else c_cost,
                    supports_function_calling=supports_function_calling,
                    max_input_tokens=max_input_tokens,
                    max_tokens=max_tokens,
                )"""
)

# In auto-discovery add_model (one line):
content = content.replace(
    "name, name, cost, 1.0, 0.8, None, p_cost, c_cost",
    "name, name, cost, 1.0, 0.8, None, p_cost, c_cost, supports_function_calling, max_input_tokens, max_tokens"
)
content = content.replace(
    "name, name, cost, 0.5, 0.9, None, p_cost, c_cost",
    "name, name, cost, 0.5, 0.9, None, p_cost, c_cost, supports_function_calling, max_input_tokens, max_tokens"
)

# And the multiline one for Gemini
content = content.replace(
    """                                    self.add_model(
                                        name,
                                        name,
                                        cost,
                                        0.4,
                                        0.88,
                                        None,
                                        p_cost,
                                        c_cost,
                                    )""",
    """                                    self.add_model(
                                        name,
                                        name,
                                        cost,
                                        0.4,
                                        0.88,
                                        None,
                                        p_cost,
                                        c_cost,
                                        supports_function_calling,
                                        max_input_tokens,
                                        max_tokens,
                                    )"""
)

# Modify add_model signature
content = content.replace(
    """    def add_model(
        self,
        model_id: str,
        model_name: str,
        cost: float,
        time: float,
        probability: float,
        concurrency_limit: Optional[int] = None,
        prompt_cost: Optional[float] = None,
        completion_cost: Optional[float] = None,
    ):""",
    """    def add_model(
        self,
        model_id: str,
        model_name: str,
        cost: float,
        time: float,
        probability: float,
        concurrency_limit: Optional[int] = None,
        prompt_cost: Optional[float] = None,
        completion_cost: Optional[float] = None,
        supports_function_calling: bool = False,
        max_input_tokens: Optional[int] = None,
        max_tokens: Optional[int] = None,
    ):"""
)

# Modify add_model body
content = content.replace(
    """            "completion_cost": completion_cost if completion_cost is not None else cost,
            "time": time,
            "probability": probability,
            "concurrency_limit": concurrency_limit,
        }""",
    """            "completion_cost": completion_cost if completion_cost is not None else cost,
            "time": time,
            "probability": probability,
            "concurrency_limit": concurrency_limit,
            "supports_function_calling": supports_function_calling,
            "max_input_tokens": max_input_tokens,
            "max_tokens": max_tokens,
        }"""
)

with open("llm-router/src/router/core.py", "w") as f:
    f.write(content)
