import asyncio
from litellm import acompletion

async def main():
    try:
        response = await acompletion(
            model="ollama/qwen3-coder:30b",
            base_url="http://localhost:11434/v1",
            messages=[{"role": "user", "content": "What is the weather in Boston?"}],
            tools=[{
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get weather",
                    "parameters": {"type": "object", "properties": {"location": {"type": "string"}}}
                }
            }]
        )
        print(response)
    except Exception as e:
        print("Error:", e)

asyncio.run(main())
