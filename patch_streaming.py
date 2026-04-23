import re

with open('llm-router/src/router/core.py', 'r') as f:
    code = f.read()

old_stream = """            tool_calls = response.response.get("tool_calls")
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
                yield f"data: {json.dumps({**common, 'choices': [{'index': 0, 'delta': {'tool_calls': delta_tool_calls}, 'finish_reason': None}]})}\\n\\n"

            yield f"data: {json.dumps({**common, 'choices': [{'index': 0, 'delta': {}, 'finish_reason': response.response.get('finish_reason', 'stop')}]})}\\n\\n"
            yield "data: [DONE]\\n\\n\"""

old_stream = old_stream.replace('\"""', '')
old_stream = old_stream.replace("\\n", "\n")

new_stream = """            tool_calls = response.response.get("tool_calls")
            if tool_calls:
                # Stream initialization chunk (id and name)
                init_tool_calls = []
                for i, tc in enumerate(tool_calls):
                    init_tool_calls.append(
                        {
                            "index": i,
                            "id": tc.get("id", ""),
                            "type": "function",
                            "function": {
                                "name": tc.get("function", {}).get("name", ""),
                                "arguments": ""
                            },
                        }
                    )
                yield f"data: {json.dumps({**common, 'choices': [{'index': 0, 'delta': {'tool_calls': init_tool_calls}, 'finish_reason': None}]})}\\n\\n"
                
                # Stream arguments chunk
                args_tool_calls = []
                for i, tc in enumerate(tool_calls):
                    args_tool_calls.append(
                        {
                            "index": i,
                            "function": {
                                "arguments": tc.get("function", {}).get("arguments", "")
                            },
                        }
                    )
                yield f"data: {json.dumps({**common, 'choices': [{'index': 0, 'delta': {'tool_calls': args_tool_calls}, 'finish_reason': None}]})}\\n\\n"

            yield f"data: {json.dumps({**common, 'choices': [{'index': 0, 'delta': {}, 'finish_reason': response.response.get('finish_reason', 'stop')}]})}\\n\\n"
            yield "data: [DONE]\\n\\n\"""

new_stream = new_stream.replace('\"""', '')
new_stream = new_stream.replace("\\n", "\n")

code = code.replace(old_stream, new_stream)

with open('llm-router/src/router/core.py', 'w') as f:
    f.write(code)
