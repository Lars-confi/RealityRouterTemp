import json
with open('llm-router/src/router/core.py', 'r') as f:
    code = f.read()

old_block = """            tool_calls = response.response.get("tool_calls")
            if tool_calls:
                delta_tool_calls = []
                for i, tc in enumerate(tool_calls):
                    delta_tool_calls.append(
                        {
                            "index": i,
                            "id": tc.get("id", ""),
                            "type": "function",
                            "function": {
                                "name": tc.get("function", {}).get("name", ""),
                                "arguments": tc.get("function", {}).get(
                                    "arguments", ""
                                ),
                            },
                        }
                    )
                yield f"data: {json.dumps({**common, 'choices': [{'index': 0, 'delta': {'tool_calls': delta_tool_calls}, 'finish_reason': None}]})}\\n\\n\""""
old_block = old_block.replace("\\n", "\n")

new_block = """            tool_calls = response.response.get("tool_calls")
            if tool_calls:
                # 1. Stream the ID and Name first (arguments MUST be omitted completely, not just empty strings)
                init_tool_calls = []
                for i, tc in enumerate(tool_calls):
                    init_tool_calls.append(
                        {
                            "index": i,
                            "id": tc.get("id", ""),
                            "type": "function",
                            "function": {
                                "name": tc.get("function", {}).get("name", "")
                            },
                        }
                    )
                yield f"data: {json.dumps({**common, 'choices': [{'index': 0, 'delta': {'tool_calls': init_tool_calls}, 'finish_reason': None}]})}\\n\\n"
                
                # 2. Stream the Arguments
                for i, tc in enumerate(tool_calls):
                    args = tc.get("function", {}).get("arguments", "")
                    if args:
                        yield f"data: {json.dumps({**common, 'choices': [{'index': 0, 'delta': {'tool_calls': [{'index': i, 'function': {'arguments': args}}]}, 'finish_reason': None}]})}\\n\\n\""""
new_block = new_block.replace("\\n", "\n")

if old_block in code:
    code = code.replace(old_block, new_block)
    with open('llm-router/src/router/core.py', 'w') as f:
        f.write(code)
    print("Patched stream correctly.")
else:
    print("Could not find old block to patch.")
