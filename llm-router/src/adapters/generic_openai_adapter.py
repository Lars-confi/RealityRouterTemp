"""
Generic OpenAI-compatible adapter for LLM routing system
"""
import os
from typing import Dict, Any
import openai
from src.adapters.base_adapter import BaseAdapter
from src.models.routing import RoutingRequest

class GenericOpenAIAdapter(BaseAdapter):
    """Adapter for OpenAI-compatible models (Ollama, Together, vLLM, etc)"""
    
    def __init__(self, model_name: str = "Generic OpenAI", api_key: str = None, base_url: str = None, default_model: str = None):
        """
        Initialize the adapter
        """
        super().__init__(model_name, api_key)
        
        self.api_key = api_key or os.getenv("CUSTOM_LLM_API_KEY", "sk-dummy")
        self.base_url = base_url or os.getenv("CUSTOM_LLM_BASE_URL", "http://localhost:11434/v1")
        self.default_model = default_model or os.getenv("CUSTOM_LLM_MODEL", "llama2")
        
        # Initialize OpenAI async client pointing to the custom base URL
        base = self.base_url
        if "11434" in base and not base.endswith("v1"):
            base = base.rstrip("/") + "/v1"
            
        self.client = openai.AsyncOpenAI(
            api_key=self.api_key,
            base_url=base
        )
    
    async def forward_request(self, request: RoutingRequest) -> Dict[str, Any]:
        try:
            messages = [{"role": "user", "content": request.query}]
            
            req_model = self.default_model
            # If the user explicitly requested a model, let's just use what we have configured for THIS adapter
            params = {
                "model": req_model,
                "messages": messages,
                "max_tokens": 1000,
                "temperature": 0.7
            }
            
            if request.parameters:
                temp_params = dict(request.parameters)
                if "messages" in temp_params:
                    params["messages"] = temp_params["messages"]
                    del temp_params["messages"]
                    
                # NEVER overwrite the mapped model name for custom endpoints
                # Otherwise if the user requested 'gpt-3.5' and we routed to 'llama3',
                # passing 'gpt-3.5' to Ollama will result in a 404.
                if "model" in temp_params:
                    del temp_params["model"]
                    
                params.update(temp_params)
            
            response = await self.client.chat.completions.create(**params)
            
            return {
                "text": response.choices[0].message.content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0
                },
                "model": response.model,
                "finish_reason": response.choices[0].finish_reason
            }
            
        except Exception as e:
            raise Exception(f"Error calling Custom OpenAI API: {str(e)}")
    
    def get_model_info(self) -> Dict[str, Any]:
        return {
            "name": self.model_name,
            "provider": "Custom OpenAI-Compatible",
            "type": "chat",
            "description": "Custom LLM API implementation"
        }
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        # Default to very cheap/free for self-hosted
        return 0.0

