"""
Anthropic adapter for LLM routing system
"""
import os
import anthropic
from typing import Dict, Any
from src.adapters.base_adapter import BaseAdapter
from src.models.routing import RoutingRequest, RoutingResponse

class AnthropicAdapter(BaseAdapter):
    """Adapter for Anthropic models"""
    
    def __init__(self, api_key: str = None):
        """
        Initialize the Anthropic adapter
        
        Args:
            api_key: Anthropic API key (will use environment variable if not provided)
        """
        super().__init__("Anthropic", api_key)
        
        # Use environment variable if no key provided
        if not api_key:
            api_key = os.getenv("ANTHROPIC_API_KEY")
        
        if not api_key:
            raise ValueError("Anthropic API key is required")
        
        self.api_key = api_key
        self.client = anthropic.Anthropic(api_key=api_key)
    
    def forward_request(self, request: RoutingRequest) -> Dict[str, Any]:
        """
        Forward a request to Anthropic
        
        Args:
            request: RoutingRequest to forward
            
        Returns:
            Response from Anthropic
        """
        try:
            # Prepare the message for the Anthropic API
            message = self.client.messages.create(
                model="claude-3-haiku-20240307",  # Default model
                max_tokens=1000,
                temperature=0.7,
                messages=[
                    {
                        "role": "user",
                        "content": request.query
                    }
                ]
            )
            
            # Format the response
            return {
                "text": message.content[0].text,
                "usage": {
                    "prompt_tokens": message.usage.input_tokens,
                    "completion_tokens": message.usage.output_tokens,
                    "total_tokens": message.usage.input_tokens + message.usage.output_tokens
                },
                "model": message.model,
                "finish_reason": message.stop_reason
            }
            
        except Exception as e:
            raise Exception(f"Error calling Anthropic API: {str(e)}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the Anthropic model
        
        Returns:
            Model information
        """
        return {
            "name": "Anthropic Claude Haiku",
            "provider": "Anthropic",
            "type": "chat",
            "description": "Anthropic's Claude Haiku model for fast, efficient responses"
        }
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Estimate cost for Anthropic model usage
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Estimated cost in USD
        """
        # Cost per million tokens (as of April 2024)
        input_cost_per_million = 0.25  # $0.25 per million tokens
        output_cost_per_million = 1.25  # $1.25 per million tokens
        
        input_cost = (input_tokens / 1_000_000) * input_cost_per_million
        output_cost = (output_tokens / 1_000_000) * output_cost_per_million
        
        return input_cost + output_cost