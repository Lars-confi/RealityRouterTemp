"""
Gemini adapter for LLM routing system
"""
import os
import openai
from typing import Dict, Any
from src.adapters.base_adapter import BaseAdapter
from src.models.routing import RoutingRequest

class GeminiAdapter(BaseAdapter):
    """Adapter for Google Gemini models via OpenAI compatibility layer"""
    
    def __init__(self, api_key: str = None):
        super().__init__("Gemini", api_key)
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required")
        
        # Gemini is fully compatible with the standard OpenAI SDK using this base URL
        self.client = openai.AsyncOpenAI(
            api_key=self.api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
        
    async def forward_request(self, request: RoutingRequest) -> Dict[str, Any]:
        try:
            messages = [{"role": "user", "content": request.query}]
            
            model = "gemini-1.5-flash"
            if request.parameters and "model" in request.parameters:
                if "gemini" in request.parameters["model"]:
                    model = request.parameters["model"]
                    
            params = {
                "model": model,
                "messages": messages,
                "max_tokens": 1000,
                "temperature": 0.7
            }
            
            if request.parameters:
                if "messages" in request.parameters:
                    params["messages"] = request.parameters["messages"]
                    temp_params = dict(request.parameters)
                    del temp_params["messages"]
                    params.update(temp_params)
                else:
                    params.update(request.parameters)
                    
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
            raise Exception(f"Error calling Gemini API: {str(e)}")
            
    def get_model_info(self) -> Dict[str, Any]:
        return {
            "name": "Google Gemini",
            "provider": "Gemini",
            "type": "chat",
            "description": "Google Gemini models via OpenAI compatibility"
        }
        
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        # Cost estimate based on Gemini 1.5 Flash pricing
        input_cost = (input_tokens / 1_000_000) * 0.35
        output_cost = (output_tokens / 1_000_000) * 1.05
        return input_cost + output_cost
