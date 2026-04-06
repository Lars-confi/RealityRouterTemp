# LLM Router Project - Detailed Implementation Guide

## Project Overview

This document provides a comprehensive implementation guide for the LLM Router project, following the Python-based architecture described in the documentation. The system is designed as a modular, scalable system for intelligent routing of requests to different language models using Expected Utility Theory for optimal decision making.

## Phase 1: Project Setup and Core Infrastructure

### Implementation Instructions

1. **Create project directory structure**
   ```bash
   mkdir -p llm-router/src/{router,adapters,config,utils,database}
   mkdir -p llm-router/tests
   mkdir -p llm-router/docs
   ```

2. **Initialize Python project**
   ```bash
   cd llm-router
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install fastapi uvicorn pydantic python-dotenv openai anthropic cohere requests numpy pandas pytest pytest-asyncio
   ```

3. **Create setup.py**
   ```python
   # llm-router/setup.py
   from setuptools import setup, find_packages
   
   setup(
       name="llm-router",
       version="1.0.0",
       packages=find_packages(),
       install_requires=[
           "fastapi==0.104.1",
           "uvicorn==0.24.0",
           "pydantic==2.5.0",
           "python-dotenv==1.0.0",
           "openai==1.3.5",
           "anthropic==0.7.0",
           "cohere==5.0.0",
           "requests==2.31.0",
           "numpy==1.24.3",
           "pandas==2.0.3",
           "pytest==7.4.0",
           "pytest-asyncio==0.21.0",
       ],
       entry_points={
           "console_scripts": [
               "llm-router=src.main:main",
           ],
       },
       python_requires=">=3.8",
   )
   ```

4. **Create requirements.txt**
   ```txt
   # llm-router/requirements.txt
   fastapi==0.104.1
   uvicorn==0.24.0
   pydantic==2.5.0
   python-dotenv==1.0.0
   openai==1.3.5
   anthropic==0.7.0
   cohere==5.0.0
   requests==2.31.0
   numpy==1.24.3
   pandas==2.0.3
   pytest==7.4.0
   pytest-asyncio==0.21.0
   ```

5. **Create .gitignore**
   ```gitignore
   # llm-router/.gitignore
   __pycache__/
   *.pyc
   .pytest_cache/
   .venv/
   venv/
   env/
   .env
   .DS_Store
   *.log
   .coverage
   htmlcov/
   ```

6. **Create basic configuration files**
   ```bash
   # Create config directory and files
   mkdir -p llm-router/config
   touch llm-router/config/settings.json
   touch llm-router/config/routing_rules.json
   ```

### Testing Requirements

- Unit tests for project initialization and setup
- Test that all directories are created correctly
- Verify that dependencies are properly installed
- Test configuration file parsing
- Test environment variable loading

### Commit/Push Procedures

1. Create a new branch for this phase:
   ```bash
   git checkout -b feature/setup-phase
   ```

2. Commit the changes:
   ```bash
   git add .
   git commit -m "feat: Initialize project structure and dependencies"
   ```

3. Push to remote repository:
   ```bash
   git push origin feature/setup-phase
   ```

## Phase 2: Core Router Components

### Implementation Instructions

1. **Create main application entry point**
   ```python
   # llm-router/src/main.py
   from fastapi import FastAPI
   from src.router.core import router as core_router
   from src.utils.logger import setup_logger
   
   app = FastAPI(title="LLM Router", version="1.0.0")
   logger = setup_logger(__name__)
   
   # Include routers
   app.include_router(core_router, prefix="/v1")
   
   @app.get("/health")
   async def health_check():
       return {"status": "healthy"}
   
   if __name__ == "__main__":
       import uvicorn
       uvicorn.run(app, host="0.0.0.0", port=3000)
   ```

2. **Create core router logic**
   ```python
   # llm-router/src/router/core.py
   from fastapi import APIRouter, HTTPException
   from pydantic import BaseModel
   from typing import Optional, Dict, Any
   from src.utils.logger import setup_logger
   from src.config.settings import get_settings
   from src.router.metrics import collect_metrics
   from src.router.load_balancer import load_balance
   
   logger = setup_logger(__name__)
   settings = get_settings()
   
   router = APIRouter()
   
   class CompletionRequest(BaseModel):
       prompt: str
       model: Optional[str] = None
       max_tokens: Optional[int] = 150
       temperature: Optional[float] = 0.7
       # Add other OpenAI-compatible parameters
   
   class ChatMessage(BaseModel):
       role: str
       content: str
   
   class ChatCompletionRequest(BaseModel):
       messages: list[ChatMessage]
       model: Optional[str] = None
       max_tokens: Optional[int] = 150
       temperature: Optional[float] = 0.7
       # Add other OpenAI-compatible parameters
   
   @router.post("/completions")
   async def completions(request: CompletionRequest):
       try:
           # Parse request
           logger.info(f"Processing completion request: {request}")
           
           # Determine best model using Expected Utility Theory
           best_model = determine_best_model(request)
           
           # Route to selected model
           response = route_to_model(best_model, request)
           
           # Collect metrics
           collect_metrics(request, best_model, response)
           
           return response
       except Exception as e:
           logger.error(f"Error in completions: {str(e)}")
           raise HTTPException(status_code=500, detail=str(e))
   
   @router.post("/chat/completions")
   async def chat_completions(request: ChatCompletionRequest):
       try:
           # Parse request
           logger.info(f"Processing chat completion request: {request}")
           
           # Determine best model using Expected Utility Theory
           best_model = determine_best_model(request)
           
           # Route to selected model
           response = route_to_model(best_model, request)
           
           # Collect metrics
           collect_metrics(request, best_model, response)
           
           return response
       except Exception as e:
           logger.error(f"Error in chat_completions: {str(e)}")
           raise HTTPException(status_code=500, detail=str(e))
   
   def determine_best_model(request):
       """Determine the best model using Expected Utility Theory"""
       # Implementation will be added in later phases
       # This is a placeholder for now
       return "default_model"
   
   def route_to_model(model_name, request):
       """Route request to specific model"""
       # Implementation will be added in later phases
       # This is a placeholder for now
       return {"response": "placeholder response"}
   ```

3. **Create logger utility**
   ```python
   # llm-router/src/utils/logger.py
   import logging
   import sys
   from datetime import datetime
   
   def setup_logger(name):
       """Setup logger with structured formatting"""
       logger = logging.getLogger(name)
       logger.setLevel(logging.INFO)
       
       # Create console handler
       console_handler = logging.StreamHandler(sys.stdout)
       console_handler.setLevel(logging.INFO)
       
       # Create formatter
       formatter = logging.Formatter(
           '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
       )
       console_handler.setFormatter(formatter)
       
       # Add handler to logger
       logger.addHandler(console_handler)
       
       return logger
   ```

### Testing Requirements

- Unit tests for request parsing and validation
- Test routing decision algorithms
- Test model selection criteria
- Test error handling and logging mechanisms
- Test configuration loading and validation
- Integration tests for API endpoints

### Commit/Push Procedures

1. Create a new branch for this phase:
   ```bash
   git checkout -b feature/core-router-phase
   ```

2. Commit the changes:
   ```bash
   git add .
   git commit -m "feat: Implement core router components with FastAPI framework"
   ```

3. Push to remote repository:
   ```bash
   git push origin feature/core-router-phase
   ```

## Phase 3: Model Adapters

### Implementation Instructions

1. **Create OpenAI adapter**
   ```python
   # llm-router/src/adapters/openai_adapter.py
   import openai
   from typing import Dict, Any
   from src.utils.logger import setup_logger
   from src.adapters.base_adapter import BaseAdapter
   
   logger = setup_logger(__name__)
   
   class OpenAIAdapter(BaseAdapter):
       def __init__(self, api_key: str):
           self.api_key = api_key
           openai.api_key = api_key
           self.client = openai.OpenAI(api_key=api_key)
   
       def complete(self, prompt: str, **kwargs) -> Dict[str, Any]:
           try:
               response = self.client.completions.create(
                   prompt=prompt,
                   **kwargs
               )
               return {
                   "response": response.choices[0].text,
                   "usage": response.usage,
                   "model": response.model
               }
           except Exception as e:
               logger.error(f"OpenAI completion error: {str(e)}")
               raise
   
       def chat_complete(self, messages: list, **kwargs) -> Dict[str, Any]:
           try:
               response = self.client.chat.completions.create(
                   messages=messages,
                   **kwargs
               )
               return {
                   "response": response.choices[0].message.content,
                   "usage": response.usage,
                   "model": response.model
               }
           except Exception as e:
               logger.error(f"OpenAI chat completion error: {str(e)}")
               raise
   ```

2. **Create Anthropic adapter**
   ```python
   # llm-router/src/adapters/anthropic_adapter.py
   import anthropic
   from typing import Dict, Any
   from src.utils.logger import setup_logger
   from src.adapters.base_adapter import BaseAdapter
   
   logger = setup_logger(__name__)
   
   class AnthropicAdapter(BaseAdapter):
       def __init__(self, api_key: str):
           self.api_key = api_key
           self.client = anthropic.Anthropic(api_key=api_key)
   
       def complete(self, prompt: str, **kwargs) -> Dict[str, Any]:
           try:
               response = self.client.completions.create(
                   prompt=prompt,
                   **kwargs
               )
               return {
                   "response": response.completion,
                   "usage": response.usage,
                   "model": response.model
               }
           except Exception as e:
               logger.error(f"Anthropic completion error: {str(e)}")
               raise
   
       def chat_complete(self, messages: list, **kwargs) -> Dict[str, Any]:
           try:
               response = self.client.messages.create(
                   messages=messages,
                   **kwargs
               )
               return {
                   "response": response.content[0].text,
                   "usage": response.usage,
                   "model": response.model
               }
           except Exception as e:
               logger.error(f"Anthropic chat completion error: {str(e)}")
               raise
   ```

3. **Create Cohere adapter**
   ```python
   # llm-router/src/adapters/cohere_adapter.py
   import cohere
   from typing import Dict, Any
   from src.utils.logger import setup_logger
   from src.adapters.base_adapter import BaseAdapter
   
   logger = setup_logger(__name__)
   
   class CohereAdapter(BaseAdapter):
       def __init__(self, api_key: str):
           self.api_key = api_key
           self.client = cohere.Client(api_key)
   
       def complete(self, prompt: str, **kwargs) -> Dict[str, Any]:
           try:
               response = self.client.generate(
                   prompt=prompt,
                   **kwargs
               )
               return {
                   "response": response.generations[0].text,
                   "usage": response.meta,
                   "model": response.model
               }
           except Exception as e:
               logger.error(f"Cohere completion error: {str(e)}")
               raise
   
       def chat_complete(self, messages: list, **kwargs) -> Dict[str, Any]:
           try:
               response = self.client.chat(
                   messages=messages,
                   **kwargs
               )
               return {
                   "response": response.text,
                   "usage": response.meta,
                   "model": response.model
               }
           except Exception as e:
               logger.error(f"Cohere chat completion error: {str(e)}")
               raise
   ```

4. **Create base adapter class**
   ```python
   # llm-router/src/adapters/base_adapter.py
   from abc import ABC, abstractmethod
   from typing import Dict, Any
   
   class BaseAdapter(ABC):
       @abstractmethod
       def complete(self, prompt: str, **kwargs) -> Dict[str, Any]:
           pass
       
       @abstractmethod
       def chat_complete(self, messages: list, **kwargs) -> Dict[str, Any]:
           pass
   ```

### Testing Requirements

- Test OpenAI adapter functionality
- Test Anthropic adapter functionality
- Test Cohere adapter functionality
- Test generic adapter framework
- Test adapter error handling and recovery
- Integration tests between adapters and router

### Commit/Push Procedures

1. Create a new branch for this phase:
   ```bash
   git checkout -b feature/model-adapters-phase
   ```

2. Commit the changes:
   ```bash
   git add .
   git commit -m "feat: Implement model adapters for OpenAI, Anthropic, and Cohere"
   ```

3. Push to remote repository:
   ```bash
   git push origin feature/model-adapters-phase
   ```

## Phase 4: Load Balancer and Metrics

### Implementation Instructions

1. **Create load balancer**
   ```python
   # llm-router/src/router/load_balancer.py
   import random
   from typing import List, Dict, Any
   from src.utils.logger import setup_logger
   
   logger = setup_logger(__name__)
   
   class LoadBalancer:
       def __init__(self):
           self.models = []
           self.weights = []
   
       def add_model(self, model_name: str, weight: float = 1.0):
           """Add a model to the load balancer"""
           self.models.append(model_name)
           self.weights.append(weight)
   
       def get_next_model(self) -> str:
           """Get next model using weighted round-robin"""
           if not self.models:
               raise ValueError("No models available in load balancer")
           
           # Use weighted random selection
           model = random.choices(self.models, weights=self.weights)[0]
           logger.info(f"Selected model: {model}")
           return model
   
       def get_model_by_performance(self, metrics: Dict[str, Any]) -> str:
           """Select model based on performance metrics"""
           # Implementation of performance-based routing
           # This would use historical performance data to make decisions
           return self.get_next_model()
   ```

2. **Create metrics collection**
   ```python
   # llm-router/src/router/metrics.py
   import time
   import sqlite3
   from typing import Dict, Any
   from src.utils.logger import setup_logger
   
   logger = setup_logger(__name__)
   
   class MetricsCollector:
       def __init__(self, db_path: str = "metrics.db"):
           self.db_path = db_path
           self.init_database()
   
       def init_database(self):
           """Initialize metrics database"""
           conn = sqlite3.connect(self.db_path)
           cursor = conn.cursor()
           
           cursor.execute('''
               CREATE TABLE IF NOT EXISTS routing_logs (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   timestamp TEXT,
                   request_type TEXT,
                   selected_model TEXT,
                   cost REAL,
                   time_taken REAL,
                   success BOOLEAN,
                   error_message TEXT
               )
           ''')
           
           conn.commit()
           conn.close()
   
       def collect_metrics(self, request: Dict[str, Any], model: str, response: Dict[str, Any]):
           """Collect metrics for routing decision"""
           try:
               # Calculate time taken
               time_taken = response.get('time_taken', 0)
               
               # Calculate cost (simplified)
               cost = self.calculate_cost(response)
               
               # Store in database
               conn = sqlite3.connect(self.db_path)
               cursor = conn.cursor()
               
               cursor.execute('''
                   INSERT INTO routing_logs 
                   (timestamp, request_type, selected_model, cost, time_taken, success)
                   VALUES (?, ?, ?, ?, ?, ?)
               ''', (
                   time.time(),
                   request.get('type', 'unknown'),
                   model,
                   cost,
                   time_taken,
                   True  # success
               ))
               
               conn.commit()
               conn.close()
               
               logger.info(f"Metrics collected for model {model}")
           except Exception as e:
               logger.error(f"Error collecting metrics: {str(e)}")
   
       def calculate_cost(self, response: Dict[str, Any]) -> float:
           """Calculate cost based on response data"""
           # Simplified cost calculation
           # In a real implementation, this would use token counts and pricing
           return 0.001  # Placeholder value
   ```

### Testing Requirements

- Test load balancing algorithms
- Test performance-based routing
- Test metrics collection functionality
- Test health checks and rate limiting
- Test database integration for metrics
- Performance tests under load conditions

### Commit/Push Procedures

1. Create a new branch for this phase:
   ```bash
   git checkout -b feature/load-balancer-phase
   ```

2. Commit the changes:
   ```bash
   git add .
   git commit -m "feat: Implement load balancer and metrics collection"
   ```

3. Push to remote repository:
   ```bash
   git push origin feature/load-balancer-phase
   ```

## Phase 5: Configuration Management

### Implementation Instructions

1. **Create configuration manager**
   ```python
   # llm-router/src/config/settings.py
   import os
   import json
   from typing import Dict, Any
   from pydantic import BaseModel
   from dotenv import load_dotenv
   
   load_dotenv()
   
   class ModelConfig(BaseModel):
       name: str
       provider: str
       api_key: str
       cost_per_token: float
       latency: float
       success_rate: float
       enabled: bool = True
   
   class RouterSettings(BaseModel):
       default_model: str = "gpt-3.5-turbo"
       cost_sensitivity: float = 0.5
       time_sensitivity: float = 0.5
       reward: float = 1.0
       models: list[ModelConfig] = []
   
   def get_settings() -> RouterSettings:
       """Get router settings from environment or config file"""
       # Try to load from environment variables first
       try:
           settings = RouterSettings(
               default_model=os.getenv("DEFAULT_MODEL", "gpt-3.5-turbo"),
               cost_sensitivity=float(os.getenv("COST_SENSITIVITY", "0.5")),
               time_sensitivity=float(os.getenv("TIME_SENSITIVITY", "0.5")),
               reward=float(os.getenv("REWARD", "1.0")),
               models=[]
           )
           return settings
       except Exception as e:
           # Fallback to default settings
           return RouterSettings()
   
   def load_config_file(config_path: str = "config/settings.json") -> RouterSettings:
       """Load configuration from JSON file"""
       try:
           with open(config_path, 'r') as f:
               config_data = json.load(f)
           return RouterSettings(**config_data)
       except Exception as e:
           print(f"Error loading config file: {str(e)}")
           return get_settings()
   ```

2. **Create routing rules configuration**
   ```python
   # llm-router/src/config/routing_rules.py
   import json
   from typing import Dict, Any
   
   def load_routing_rules(config_path: str = "config/routing_rules.json") -> Dict[str, Any]:
       """Load routing rules from JSON file"""
       try:
           with open(config_path, 'r') as f:
               rules = json.load(f)
           return rules
       except Exception as e:
           print(f"Error loading routing rules: {str(e)}")
           return {}
   ```

### Testing Requirements

- Test configuration file parsing
- Test environment-based settings
- Test hot-reloading capabilities
- Test validation and default value handling
- Test configuration manager with all components
- Integration tests for configuration with router

### Commit/Push Procedures

1. Create a new branch for this phase:
   ```bash
   git checkout -b feature/configuration-phase
   ```

2. Commit the changes:
   ```bash
   git add .
   git commit -m "feat: Implement configuration management system"
   ```

3. Push to remote repository:
   ```bash
   git push origin feature/configuration-phase
   ```

## Phase 6: Database Integration

### Implementation Instructions

1. **Create database schema**
   ```python
   # llm-router/src/database/schema.py
   import sqlite3
   import os
   
   def init_database(db_path: str = "llm_router.db"):
       """Initialize database schema"""
       conn = sqlite3.connect(db_path)
       cursor = conn.cursor()
       
       # Routing logs table
       cursor.execute('''
           CREATE TABLE IF NOT EXISTS routing_logs (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               timestamp TEXT,
               request_type TEXT,
               selected_model TEXT,
               cost REAL,
               time_taken REAL,
               success BOOLEAN,
               error_message TEXT,
               request_data TEXT,
               response_data TEXT
           )
       ''')
       
       # Model performance metrics table
       cursor.execute('''
           CREATE TABLE IF NOT EXISTS model_metrics (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               model_name TEXT,
               timestamp TEXT,
               avg_response_time REAL,
               avg_cost REAL,
               success_rate REAL,
               total_requests INTEGER,
               total_cost REAL
           )
       ''')
       
       # Configuration table
       cursor.execute('''
           CREATE TABLE IF NOT EXISTS configurations (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               config_type TEXT,
               config_data TEXT,
               updated_at TEXT
           )
       ''')
       
       conn.commit()
       conn.close()
   
   def get_db_connection(db_path: str = "llm_router.db"):
       """Get database connection"""
       conn = sqlite3.connect(db_path)
       conn.row_factory = sqlite3.Row
       return conn
   ```

2. **Create database manager**
   ```python
   # llm-router/src/database/manager.py
   import sqlite3
   from typing import Dict, Any
   from src.database.schema import get_db_connection
   
   class DatabaseManager:
       def __init__(self, db_path: str = "llm_router.db"):
           self.db_path = db_path
           self.init_database()
   
       def init_database(self):
           """Initialize database schema"""
           from src.database.schema import init_database
           init_database(self.db_path)
   
       def log_routing_decision(self, decision_data: Dict[str, Any]):
           """Log routing decision to database"""
           conn = get_db_connection(self.db_path)
           cursor = conn.cursor()
           
           cursor.execute('''
               INSERT INTO routing_logs 
               (timestamp, request_type, selected_model, cost, time_taken, success, error_message, request_data, response_data)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
           ''', (
               decision_data.get('timestamp'),
               decision_data.get('request_type'),
               decision_data.get('selected_model'),
               decision_data.get('cost'),
               decision_data.get('time_taken'),
               decision_data.get('success'),
               decision_data.get('error_message'),
               str(decision_data.get('request_data')),
               str(decision_data.get('response_data'))
           ))
           
           conn.commit()
           conn.close()
   
       def update_model_metrics(self, model_name: str, metrics: Dict[str, Any]):
           """Update model performance metrics"""
           conn = get_db_connection(self.db_path)
           cursor = conn.cursor()
           
           cursor.execute('''
               INSERT INTO model_metrics 
               (model_name, timestamp, avg_response_time, avg_cost, success_rate, total_requests, total_cost)
               VALUES (?, ?, ?, ?, ?, ?, ?)
           ''', (
               model_name,
               metrics.get('timestamp'),
               metrics.get('avg_response_time'),
               metrics.get('avg_cost'),
               metrics.get('success_rate'),
               metrics.get('total_requests'),
               metrics.get('total_cost')
           ))
           
           conn.commit()
           conn.close()
   ```

### Testing Requirements

- Test database schema creation
- Test routing logs storage
- Test model performance metrics storage
- Test configuration data storage
- Test data retention policies
- Integration tests with all components
- Performance tests for database operations

### Commit/Push Procedures

1. Create a new branch for this phase:
   ```bash
   git checkout -b feature/database-phase
   ```

2. Commit the changes:
   ```bash
   git add .
   git commit -m "feat: Implement database integration for routing logs and metrics"
   ```

3. Push to remote repository:
   ```bash
   git push origin feature/database-phase
   ```

## Phase 7: API Endpoints

### Implementation Instructions

1. **Complete API endpoint implementation**
   ```python
   # llm-router/src/router/core.py (updated)
   from fastapi import APIRouter, HTTPException
   from pydantic import BaseModel
   from typing import Optional, Dict, Any
   from src.utils.logger import setup_logger
   from src.config.settings import get_settings
   from src.router.metrics import MetricsCollector
   from src.router.load_balancer import LoadBalancer
   from src.adapters.openai_adapter import OpenAIAdapter
   from src.adapters.anthropic_adapter import AnthropicAdapter
   from src.adapters.cohere_adapter import CohereAdapter
   from src.database.manager import DatabaseManager
   
   logger = setup_logger(__name__)
   settings = get_settings()
   metrics_collector = MetricsCollector()
   load_balancer = LoadBalancer()
   db_manager = DatabaseManager()
   
   router = APIRouter()
   
   # Model adapters mapping
   model_adapters = {
       "openai": OpenAIAdapter,
       "anthropic": AnthropicAdapter,
       "cohere": CohereAdapter
   }
   
   class CompletionRequest(BaseModel):
       prompt: str
       model: Optional[str] = None
       max_tokens: Optional[int] = 150
       temperature: Optional[float] = 0.7
       # Add other OpenAI-compatible parameters
   
   class ChatMessage(BaseModel):
       role: str
       content: str
   
   class ChatCompletionRequest(BaseModel):
       messages: list[ChatMessage]
       model: Optional[str] = None
       max_tokens: Optional[int] = 150
       temperature: Optional[float] = 0.7
       # Add other OpenAI-compatible parameters
   
   @router.post("/completions")
   async def completions(request: CompletionRequest):
       try:
           logger.info(f"Processing completion request: {request}")
           
           # Determine best model using Expected Utility Theory
           best_model = determine_best_model(request)
           
           # Route to selected model
           response = route_to_model(best_model, request)
           
           # Collect metrics
           metrics_collector.collect_metrics(request, best_model, response)
           
           # Log decision to database
           db_manager.log_routing_decision({
               "timestamp": time.time(),
               "request_type": "completion",
               "selected_model": best_model,
               "cost": response.get("cost", 0),
               "time_taken": response.get("time_taken", 0),
               "success": True,
               "request_data": request.dict(),
               "response_data": response
           })
           
           return response
       except Exception as e:
           logger.error(f"Error in completions: {str(e)}")
           # Log error to database
           db_manager.log_routing_decision({
               "timestamp": time.time(),
               "request_type": "completion",
               "selected_model": "error",
               "cost": 0,
               "time_taken": 0,
               "success": False,
               "error_message": str(e),
               "request_data": request.dict(),
               "response_data": None
           })
           raise HTTPException(status_code=500, detail=str(e))
   
   @router.post("/chat/completions")
   async def chat_completions(request: ChatCompletionRequest):
       try:
           logger.info(f"Processing chat completion request: {request}")
           
           # Determine best model using Expected Utility Theory
           best_model = determine_best_model(request)
           
           # Route to selected model
           response = route_to_model(best_model, request)
           
           # Collect metrics
           metrics_collector.collect_metrics(request, best_model, response)
           
           # Log decision to database
           db_manager.log_routing_decision({
               "timestamp": time.time(),
               "request_type": "chat_completion",
               "selected_model": best_model,
               "cost": response.get("cost", 0),
               "time_taken": response.get("time_taken", 0),
               "success": True,
               "request_data": request.dict(),
               "response_data": response
           })
           
           return response
       except Exception as e:
           logger.error(f"Error in chat_completions: {str(e)}")
           # Log error to database
           db_manager.log_routing_decision({
               "timestamp": time.time(),
               "request_type": "chat_completion",
               "selected_model": "error",
               "cost": 0,
               "time_taken": 0,
               "success": False,
               "error_message": str(e),
               "request_data": request.dict(),
               "response_data": None
           })
           raise HTTPException(status_code=500, detail=str(e))
   
   @router.get("/metrics")
   async def get_metrics():
       """Get system metrics"""
       # Implementation for metrics endpoint
       return {"status": "metrics endpoint ready"}
   
   @router.get("/health")
   async def health_check():
       """Health check endpoint"""
       return {"status": "healthy"}
   
   def determine_best_model(request):
       """Determine the best model using Expected Utility Theory"""
       # This is a simplified implementation
       # In a real implementation, this would use the full Expected Utility Theory framework
       return "gpt-3.5-turbo"
   
   def route_to_model(model_name, request):
       """Route request to specific model"""
       # Implementation for routing to specific model
       # This would use the appropriate adapter based on model_name
       return {"response": "placeholder response"}
   ```

### Testing Requirements

- Test all API endpoints with different request types
- Test error responses for invalid requests
- Test authentication and authorization
- Verify API compatibility with OpenAI format
- Test rate limiting and throttling
- Integration tests for all endpoints
- Performance tests for API endpoints

### Commit/Push Procedures

1. Create a new branch for this phase:
   ```bash
   git checkout -b feature/api-endpoints-phase
   ```

2. Commit the changes:
   ```bash
   git add .
   git commit -m "feat: Implement complete API endpoints with health and metrics"
   ```

3. Push to remote repository:
   ```bash
   git push origin feature/api-endpoints-phase
   ```

## Phase 8: Testing and Documentation

### Implementation Instructions

1. **Create comprehensive test suite**
   ```python
   # llm-router/tests/test_router.py
   import pytest
   from src.router.core import router
   from fastapi.testclient import TestClient
   
   client = TestClient(router)
   
   def test_health_endpoint():
       response = client.get("/health")
       assert response.status_code == 200
       assert response.json() == {"status": "healthy"}
   
   def test_completions_endpoint():
       response = client.post("/v1/completions", json={"prompt": "Hello"})
       assert response.status_code == 200
       # Add more assertions based on expected behavior
   
   def test_chat_completions_endpoint():
       response = client.post("/v1/chat/completions", json={
           "messages": [{"role": "user", "content": "Hello"}]
       })
       assert response.status_code == 200
       # Add more assertions based on expected behavior
   ```

2. **Create integration tests**
   ```python
   # llm-router/tests/test_integration.py
   import pytest
   from src.router.core import determine_best_model
   from src.adapters.openai_adapter import OpenAIAdapter
   
   def test_model_selection():
       # Test that model selection logic works
       pass
   
   def test_adapter_integration():
       # Test that adapters work correctly
       pass
   ```

3. **Create performance tests**
   ```python
   # llm-router/tests/test_performance.py
   import pytest
   import time
   from src.router.core import router
   from fastapi.testclient import TestClient
   
   client = TestClient(router)
   
   def test_response_time():
       start_time = time.time()
       response = client.post("/v1/completions", json={"prompt": "Hello"})
       end_time = time.time()
       assert end_time - start_time < 5.0  # Response should be under 5 seconds
   ```

4. **Update documentation**
   ```markdown
   # llm-router/docs/usage.md
   # Usage Guide
   
   ## Getting Started
   
   To start using the LLM Router, follow these steps:
   
   1. Install dependencies:
      ```bash
      pip install -r requirements.txt
      ```
   
   2. Set up environment variables:
      ```bash
      export OPENAI_API_KEY="your_openai_key"
      export ANTHROPIC_API_KEY="your_anthropic_key"
      ```
   
   3. Run the application:
      ```bash
      python src/main.py
      ```
   
   ## API Endpoints
   
   ### Completions
   ```
   POST /v1/completions
   ```
   
   ### Chat Completions
   ```
   POST /v1/chat/completions
   ```
   
   ### Health Check
   ```
   GET /health
   ```
   
   ### Metrics
   ```
   GET /metrics
   ```
   ```

### Testing Requirements

- Unit tests for all components
- Integration tests for component interactions
- End-to-end tests for complete workflows
- Performance tests for load scenarios
- Security tests for vulnerabilities
- Test coverage of 90%+ for core components
- API compatibility testing with OpenAI format

### Commit/Push Procedures

1. Create a new branch for this phase:
   ```bash
   git checkout -b feature/testing-phase
   ```

2. Commit the changes:
   ```bash
   git add .
   git commit -m "test: Add comprehensive test suite and documentation"
   ```

3. Push to remote repository:
   ```bash
   git push origin feature/testing-phase
   ```

## Final Integration and Deployment

### Implementation Instructions

1. **Create Dockerfile**
   ```dockerfile
   # llm-router/Dockerfile
   FROM python:3.9-slim
   
   WORKDIR /app
   
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   COPY . .
   
   EXPOSE 3000
   
   CMD ["python", "src/main.py"]
   ```

2. **Create docker-compose.yml**
   ```yaml
   # llm-router/docker-compose.yml
   version: '3.8'
   
   services:
     llm-router:
       build: .
       ports:
         - "3000:3000"
       environment:
         - OPENAI_API_KEY=${OPENAI_API_KEY}
         - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
       volumes:
         - ./config:/app/config
         - ./logs:/app/logs
   ```

3. **Update README.md with deployment instructions**
   ```markdown
   # LLM Router
   
   An intelligent routing system for Language Model requests that automatically routes to the most appropriate model based on various criteria.
   
   ## Features
   
   - Intelligent routing based on model capabilities
   - Load balancing across multiple models
   - Performance and cost optimization
   - Real-time metrics collection
   - Configurable routing rules
   
   ## Installation
   
   ### Using Docker (Recommended)
   
   ```bash
   docker-compose up
   ```
   
   ### Manual Installation
   
   ```bash
   pip install -r requirements.txt
   python src/main.py
   ```
   
   ## Usage
   
   ### API Endpoints
   
   - `POST /v1/completions` - For text completion requests
   - `POST /v1/chat/completions` - For chat-based requests
   - `GET /health` - Health check endpoint
   - `GET /metrics` - Metrics and statistics endpoint
   
   All endpoints follow the standard OpenAI API format for compatibility.
   
   ## Configuration
   
   Configuration is managed through environment variables and JSON files in the config directory.
   
   ## Contributing
   
   1. Fork the repository
   2. Create a feature branch
   3. Commit your changes
   4. Push to the branch
   5. Create a Pull Request
   ```

### Testing Requirements

- Integration tests for Docker deployment
- Test all deployment scenarios
- Performance testing in containerized environment
- Security testing for containerized deployment
- Test database persistence in containers

### Commit/Push Procedures

1. Create a final branch for integration:
   ```bash
   git checkout -b feature/final-integration
   ```

2. Commit the changes:
   ```bash
   git add .
   git commit -m "feat: Final integration with Docker deployment and documentation"
   ```

3. Push to remote repository:
   ```bash
   git push origin feature/final-integration
   ```

## Summary

This implementation guide provides a comprehensive roadmap for building the LLM Router project with specific coding instructions, testing requirements, and commit/push procedures for each phase. The project follows a phased approach that ensures proper development, testing, and deployment of all components.

Each phase builds upon the previous one, starting with project setup and ending with comprehensive testing and deployment. The guide includes specific implementation details, testing strategies, and version control procedures to ensure successful completion of the LLM routing system.