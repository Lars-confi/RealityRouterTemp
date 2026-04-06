# LLMRerouter

A rerouter to maximize utility for LLM usage through different tools. This system intelligently routes requests to different language models based on Expected Utility Theory, optimizing for cost, time, and accuracy without requiring users to manually select specific models.

## Overview

The LLMRerouter is a smart routing system that automatically selects the most appropriate language model for each request. It works with standard LLM API endpoints, making it compatible with popular tools like VS Code, Zed, and various agent systems.

## API Endpoints

The system exposes standard LLM API endpoints that work with popular LLM providers:

- `POST /v1/completions` - For text completion requests
- `POST /v1/chat/completions` - For chat-based requests

All endpoints follow the standard OpenAI API format for compatibility, allowing seamless integration with existing tools and applications.

## How It Works

The routing happens transparently in the background:

1. **Request Reception**: Incoming requests are received via standard API endpoints
2. **Request Analysis**: Query is analyzed for complexity and requirements
3. **Model Evaluation**: All configured models are evaluated using Expected Utility Theory
4. **Decision Making**: Optimal model is selected based on calculated expected utility
5. **Request Forwarding**: Request is forwarded to selected model
6. **Response Handling**: Response is processed and returned to user
7. **Metrics Collection**: All decisions and outcomes are logged for analytics

## Usage

To use the LLMRerouter, simply point your LLM client or editor to the standard API endpoints:

For VS Code/VS Codium:
```json
{
  "llm.rerouter.url": "http://localhost:8000/v1/completions"
}
```

For Zed Editor:
```json
{
  "llm.codeRerouter.url": "http://localhost:8000/v1/completions"
}
```

The system will automatically route your requests to the most appropriate model based on cost, time, and accuracy considerations.