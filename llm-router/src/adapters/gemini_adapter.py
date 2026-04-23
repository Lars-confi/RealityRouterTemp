"""
Gemini adapter for LLM routing system
"""

import os
from typing import Any, Dict

import openai

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
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )

    async def forward_request(self, request: RoutingRequest) -> Dict[str, Any]:
        try:
            messages = [{"role": "user", "content": request.query}]

            model = getattr(
                self, "default_model", "gemini-1.5-flash"
            )  # This fallback will be updated to a current model

            params = {
                "model": model,
                "messages": messages,
                "max_tokens": 4096,
                "temperature": 0.7,
            }

            if request.parameters:
                temp_params = dict(request.parameters)

                # Extract tools and tool_choice if present
                tools = temp_params.pop("tools", None)
                tool_choice = temp_params.pop("tool_choice", None)

                if "messages" in temp_params:
                    params["messages"] = temp_params["messages"]
                    del temp_params["messages"]

                # NEVER overwrite the mapped model name
                if "model" in temp_params:
                    del temp_params["model"]

                params.update(temp_params)

                # Filter out parameters known to cause 400 errors on Gemini
                unsupported_params = [
                    "frequency_penalty",
                    "presence_penalty",
                    "logprobs",
                    "top_logprobs",
                    "logit_bias",
                    "seed",
                    "user",
                    "stream_options",
                    "parallel_tool_calls",
                    "response_format",
                ]
                for p in unsupported_params:
                    if p in params:
                        del params[p]

                if "max_completion_tokens" in params:
                    params["max_tokens"] = params.pop("max_completion_tokens")

            # Add tools and tool_choice if they were extracted
            # NOTE: Gemini 3.1 Preview fails on tools without "thought_signature" which the OpenAI compat layer doesn't handle.
            # We strip tools for 3.1 so the LLM Router's fallback JSON interceptor can process them instead.
            if tools:
                if "3.1" in str(model).lower():
                    pass # Let the core router handle tools for 3.1 via the fallback prompt
                else:
                    params["tools"] = tools
            if tool_choice:
                if "3.1" not in str(model).lower():
                    params["tool_choice"] = tool_choice

            response = await self.client.chat.completions.create(**params)

            message = response.choices[0].message
            result = {
                "text": message.content,
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
            if hasattr(message, "tool_calls") and message.tool_calls:
                result["tool_calls"] = []
                for tc in message.tool_calls:
                    result["tool_calls"].append(
                        {
                            "id": tc.id,
                            "type": tc.type,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                    )
            return result
        except Exception as e:
            raise Exception(f"Error calling Gemini API: {str(e)}")

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "name": "Google Gemini",
            "provider": "Gemini",
            "type": "chat",
            "description": "Google Gemini models via OpenAI compatibility",
        }
