import asyncio
from httpx import AsyncClient
import os

async def ping():
    url = "http://100.81.4.19:11434/v1/chat/completions"
    payload = {
        "model": "gemma4:31b",
        "messages": [{"role": "user", "content": "hello"}]
    }
    print(f"Pinging {url}...")
    try:
        async with AsyncClient(timeout=5) as client:
            resp = await client.post(url, json=payload)
            print(f"Status: {resp.status_code}")
            print(f"Response: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(ping())
