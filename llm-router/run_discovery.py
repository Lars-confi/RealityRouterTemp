import asyncio
from src.router.discovery import discover_ollama_models

async def test():
    models = await discover_ollama_models()
    print(models)

if __name__ == "__main__":
    asyncio.run(test())
