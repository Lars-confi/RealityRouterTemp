"""
OpenAI adapter for LLM routing system
"""

import os
from typing import Any, Dict

import openai

from src.adapters.base_adapter import BaseAdapter
from src.models.routing import RoutingRequest, RoutingResponse


class OpenAIAdapter(BaseAdapter):
    """Adapter for OpenAI models"""

    def __init__(self, api_key: str = None):
        """
        Initialize the OpenAI adapter

        Args:
            api_key: OpenAI API key (will use environment variable if not provided)
        """
        super().__init__("OpenAI", api_key)

        # Use environment variable if no key provided
        if not api_key:
            api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise ValueError("OpenAI API key is required")

        self.api_key = api_key

        # Initialize OpenAI async client
        self.client = openai.AsyncOpenAI(api_key=api_key)

    async def forward_request(self, request: RoutingRequest) -> Dict[str, Any]:
        """
        Forward a request to OpenAI

        Args:
            request: RoutingRequest to forward

        Returns:
            Response from OpenAI
        """
        try:
            # Prepare the messages for the OpenAI API
            messages = [{"role": "user", "content": request.query}]

            # Prepare parameters
            params = {
                "model": "gpt-3.5-turbo",  # Default model
                "messages": messages,
                "max_tokens": 1000,
                "temperature": 0.7,
            }

            # Add any additional parameters from the request
            if request.parameters:
                # If messages are provided in parameters, use those instead
                if "messages" in request.parameters:
                    params["messages"] = request.parameters["messages"]
                    # Remove it from parameters so we don't duplicate when updating
                    temp_params = dict(request.parameters)
                    del temp_params["messages"]
                    params.update(temp_params)
                else:
                    params.update(request.parameters)

            # Make the API call asynchronously
            response = await self.client.chat.completions.create(**params)

            # Format the response
            return {
                "text": response.choices[0].message.content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens
                    if response.usage
                    else 0,
                    "completion_tokens": response.usage.completion_tokens
                    if response.usage
                    else 0,
                    "total_tokens": response.usage.total_tokens
                    if response.usage
                    else 0,
                },
                "model": response.model,
                "finish_reason": response.choices[0].finish_reason,
            }

        except Exception as e:
            raise Exception(f"Error calling OpenAI API: {str(e)}")

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the OpenAI model

        Returns:
            Model information
        """
        return {
            "name": "OpenAI GPT-3.5 Turbo",
            "provider": "OpenAI",
            "type": "chat",
            "description": "OpenAI's GPT-3.5 Turbo model for conversational AI",
        }

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Estimate cost for OpenAI model usage

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Estimated cost in USD
        """
        # Cost per million tokens (as of April 2024)
        input_cost_per_million = 0.50  # $0.50 per million tokens
        output_cost_per_million = 1.50  # $1.50 per million tokens

        input_cost = (input_tokens / 1_000_000) * input_cost_per_million
        output_cost = (output_tokens / 1_000_000) * output_cost_per_million

        return input_cost + output_cost
