import json

response_text = "Here's what a more realistic approach would look like, based on the current code structure:"
tool_calls = [
    {
        "id": "call_123",
        "type": "function",
        "function": {
            "name": "edit_file",
            "arguments": '{"path": "test.py", "code": "print(1)"}'
        }
    }
]

common = {
    "id": "chatcmpl-123",
    "object": "chat.completion.chunk",
    "created": 123456,
    "model": "qwen",
}

chunks = []

chunks.append(f"data: {json.dumps({**common, 'choices': [{'index': 0, 'delta': {'role': 'assistant'}, 'finish_reason': None}]})}")

if response_text:
    chunks.append(f"data: {json.dumps({**common, 'choices': [{'index': 0, 'delta': {'content': response_text}, 'finish_reason': None}]})}")

if tool_calls:
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
    chunks.append(f"data: {json.dumps({**common, 'choices': [{'index': 0, 'delta': {'tool_calls': init_tool_calls}, 'finish_reason': None}]})}")
    
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
    chunks.append(f"data: {json.dumps({**common, 'choices': [{'index': 0, 'delta': {'tool_calls': args_tool_calls}, 'finish_reason': None}]})}")

chunks.append(f"data: {json.dumps({**common, 'choices': [{'index': 0, 'delta': {}, 'finish_reason': 'tool_calls'}]})}")
chunks.append("data: [DONE]")

for c in chunks:
    print(c)
