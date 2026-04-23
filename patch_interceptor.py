with open('llm-router/src/router/core.py', 'r') as f:
    code = f.read()

old_logic = """                    if (
                        has_tools
                        and not self.models[decision.model_id].get(
                            "supports_function_calling"
                        )
                        and not response.get("tool_calls")
                    ):"""

new_logic = """                    if (
                        has_tools
                        and not response.get("tool_calls")
                    ):"""

code = code.replace(old_logic, new_logic)

with open('llm-router/src/router/core.py', 'w') as f:
    f.write(code)
