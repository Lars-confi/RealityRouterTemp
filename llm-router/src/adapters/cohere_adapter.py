"""
Cohere adapter for LLM routing system
"""
import os
import cohere
from typing import Dict, Any
from src.adapters.base_adapter import BaseAdapter
from src.models.routing import RoutingRequest, RoutingResponse

class CohereAdapter(BaseAdapter):
    """Adapter for Cohere models"""
    
    def __init__(self, api_key: str = None):
        """
        Initialize the Cohere adapter
        
        Args:
            api_key: Cohere API key (will use environment variable if not provided)
        """
        super().__init__("Cohere", api_key)
        
        # Use environment variable if no key provided
        if not api_key:
            api_key = os.getenv("COHERE_API_KEY")
        
        if not api_key:
            raise ValueError("Cohere API key is required")
        
        self.api_key = api_key
        self.client = cohere.Client(api_key)
    
    def forward_request(self, request: RoutingRequest) -> Dict[str, Any]:
        """
        Forward a request to Cohere
        
        Args:
            request: RoutingRequest to forward
            
        Returns:
            Response from Cohere
        """
        try:
            # Prepare the prompt for the Cohere API
            response = self.client.chat(
                model="command-r-plus",  # Default model
                message=request.query,
                temperature=0.7,
                max_tokens=1000
            )
            
            # Format the response
            return {
                "text": response.text,
                "usage": {
                    "prompt_tokens": response.token_count.prompt_tokens,
                    "completion_tokens": response.token_count.completion_tokens,
                    "total_tokens": response.token_count.prompt_tokens + response.token_count.completion_tokens
                },
                "model": response.model,
                "finish_reason": "complete"
            }
            
        except Exception as e:
            raise Exception(f"Error calling Cohere API: {str(e)}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the Cohere model
        
        Returns:
            Model information
        """
        return {
            "name": "Cohere Command R+",
            "provider": "Cohere",
            "type": "chat",
            "description": "Cohere's Command R+ model for advanced reasoning tasks"
        }
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Estimate cost for Cohere model usage
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Estimated cost in USD
        """
        # Cost per million tokens (as of April 2024)
        input_cost_per_million = 1.00  # $1.00 per million tokens
        output_cost_per_million = 2.00  # $2.00 per million tokens
        
        input_cost = (input_tokens / 1_000_000) * input_cost_per_million
        output_cost = (output_tokens / 1_000_000) * output_cost_per_million
        
        return input_cost + output_cost