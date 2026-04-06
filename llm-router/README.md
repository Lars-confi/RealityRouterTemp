# LLM Router

An intelligent routing system for Language Model requests that automatically routes to the most appropriate model based on various criteria using Expected Utility Theory.

## Value Proposition

The LLM Router solves the challenge of selecting the optimal language model for a given task by intelligently evaluating multiple factors including:
- **Performance**: Success probability of the model
- **Cost**: Token cost per million tokens
- **Time**: Average response time in seconds
- **Utility**: Expected utility calculated using Expected Utility Theory framework

This system automatically selects the best model for your request, balancing between cost, time, and performance to maximize the overall utility of your LLM usage.

## Features

- Intelligent routing based on Expected Utility Theory framework
- Load balancing across multiple models (round-robin, weighted, performance-based)
- Performance and cost optimization
- Real-time metrics collection and analytics
- Configurable routing rules and model parameters
- Support for multiple LLM providers (OpenAI, Anthropic, Cohere)
- Database logging for routing decisions and analytics
- RESTful API for easy integration

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd llm-router
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file in the project root with your API keys:
```
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
COHERE_API_KEY=your_cohere_key
DATABASE_URL=sqlite:///./llm_router.db
DEFAULT_STRATEGY=expected_utility
REWARD=1.0
COST_SENSITIVITY=0.5
TIME_SENSITIVITY=0.5
```

4. Initialize the database:
```bash
python -m src.main
```

## Usage

### Running the Application

To start the LLM Router API server:

```bash
python -m src.main
```

The server will start on `http://localhost:8000`

### API Endpoints

- `POST /v1/route` - Route a request to the best model
- `GET /v1/models` - Get list of available models
- `GET /metrics` - Get current routing metrics
- `GET /health` - Health check endpoint

### Example Request

```bash
curl -X POST "http://localhost:8000/v1/route" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Explain quantum computing in simple terms",
    "max_tokens": 100
  }'
```

### Configuration

The system can be configured using environment variables or a `.env` file. The following environment variables are supported:

```
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
COHERE_API_KEY=your_cohere_key
DATABASE_URL=sqlite:///./llm_router.db
DEFAULT_STRATEGY=expected_utility
REWARD=1.0
COST_SENSITIVITY=0.5
TIME_SENSITIVITY=0.5
```

The `DEFAULT_STRATEGY` can be set to either:
- `expected_utility` - Use Expected Utility Theory for routing decisions
- `load_balanced` - Use load balancing across models

## Project Structure

```
llm-router/
├── src/                 # Source code
│   ├── main.py          # Entry point
│   ├── router/          # Routing components
│   ├── adapters/        # LLM provider adapters
│   ├── models/          # Data models
│   ├── config/          # Configuration management
│   ├── utils/           # Utility functions
│   └── tests/           # Test files
├── config/              # Configuration files
├── docs/                # Documentation
├── requirements.txt     # Python dependencies
└── setup.py             # Project setup
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT