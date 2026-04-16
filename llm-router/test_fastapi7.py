import asyncio
from httpx import AsyncClient, ASGITransport
from src.main import app

async def test():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/chat/completions", json={
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "Hello!"}]
        })
        print(f"Status for /chat/completions: {response.status_code}")
        if response.status_code != 200:
            print(response.json())

if __name__ == "__main__":
    import logging
    logging.getLogger("src.router").setLevel(logging.CRITICAL)
    asyncio.run(test())
