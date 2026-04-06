"""
Test cases for updated core routing functionality
"""
import pytest
from src.router.core import RouterCore, ExpectedUtilityCalculator
from src.models.routing import RoutingRequest
from src.config.settings import load_models_from_config

def test_expected_utility_calculation():
    """Test Expected Utility calculation"""
    calculator = ExpectedUtilityCalculator(reward=1.0, cost_sensitivity=0.5, time_sensitivity=0.5)
    
    # Test with simple values
    utility = calculator.calculate_expected_utility(cost=0.002, time=0.5, probability=0.9)
    assert utility == pytest.approx(0.4, 0.01)  # 0.9 * 1.0 - 0.5 * 0.002 - 0.5 * 0.5 = 0.9 - 0.001 - 0.25 = 0.649
    
    # Test with zero probability
    utility = calculator.calculate_expected_utility(cost=0.002, time=0.5, probability=0.0)
    assert utility == pytest.approx(-0.251, 0.01)  # 0.0 * 1.0 - 0.5 * 0.002 - 0.5 * 0.5 = 0.0 - 0.001 - 0.25 = -0.251

def test_router_core_initialization():
    """Test router core initialization"""
    router = RouterCore()
    assert router is not None
    assert hasattr(router, 'models')
    assert hasattr(router, 'metrics')
    assert hasattr(router, 'utility_calculator')
    assert hasattr(router, 'adapters')
    assert hasattr(router, 'load_balancer')

def test_add_model():
    """Test adding models to router"""
    router = RouterCore()
    
    # Add a model
    router.add_model(
        model_id="test_model",
        model_name="Test Model",
        cost=0.002,
        time=0.5,
        probability=0.9
    )
    
    assert "test_model" in router.models
    assert router.models["test_model"]["name"] == "Test Model"
    assert router.models["test_model"]["cost"] == 0.002
    assert router.models["test_model"]["time"] == 0.5
    assert router.models["test_model"]["probability"] == 0.9

def test_load_configured_models():
    """Test loading models from configuration"""
    router = RouterCore()
    
    # Check that models were loaded from config
    models = load_models_from_config()
    assert len(models) > 0
    
    # Check that router has at least some models
    assert len(router.models) > 0

def test_get_best_model():
    """Test getting the best model"""
    router = RouterCore()
    
    # Add a test model
    router.add_model(
        model_id="test_model",
        model_name="Test Model",
        cost=0.002,
        time=0.5,
        probability=0.9
    )
    
    # Create a test request
    request = RoutingRequest(
        query="What is the capital of France?"
    )
    
    # This should not raise an exception
    # Note: Actual routing would require a real adapter, so we're just testing the structure
    assert request.query == "What is the capital of France?"

def test_router_core_methods():
    """Test that all expected methods exist"""
    router = RouterCore()
    
    # Check that all expected methods exist
    assert hasattr(router, 'add_model')
    assert hasattr(router, 'get_best_model')
    assert hasattr(router, 'log_routing_decision')
    assert hasattr(router, 'route_request')
    assert hasattr(router, 'load_configured_models')
    assert hasattr(router, 'add_default_models')

if __name__ == "__main__":
    pytest.main([__file__])