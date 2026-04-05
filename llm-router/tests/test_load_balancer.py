"""
Test cases for load balancer functionality
"""
import pytest
from src.router.load_balancer import LoadBalancer

def test_load_balancer_initialization():
    """Test load balancer initialization"""
    lb = LoadBalancer()
    assert lb is not None
    assert hasattr(lb, 'models')
    assert hasattr(lb, 'request_counts')
    assert hasattr(lb, 'success_counts')

def test_add_model():
    """Test adding models to load balancer"""
    lb = LoadBalancer()
    
    # Add a model
    lb.add_model("test_model", "Test Model", weight=1.0)
    
    assert "test_model" in lb.models
    assert lb.models["test_model"]["name"] == "Test Model"
    assert lb.models["test_model"]["weight"] == 1.0

def test_round_robin_selection():
    """Test round-robin model selection"""
    lb = LoadBalancer()
    
    # Add multiple models
    lb.add_model("model1", "Model 1", weight=1.0)
    lb.add_model("model2", "Model 2", weight=1.0)
    lb.add_model("model3", "Model 3", weight=1.0)
    
    # Test round-robin selection
    model1 = lb.get_next_model_round_robin()
    model2 = lb.get_next_model_round_robin()
    model3 = lb.get_next_model_round_robin()
    model4 = lb.get_next_model_round_robin()  # Should cycle back
    
    assert model1 == "model1"
    assert model2 == "model2"
    assert model3 == "model3"
    assert model4 == "model1"  # Should cycle back

def test_weighted_selection():
    """Test weighted model selection"""
    lb = LoadBalancer()
    
    # Add models with different weights
    lb.add_model("model1", "Model 1", weight=2.0)  # Higher weight
    lb.add_model("model2", "Model 2", weight=1.0)  # Lower weight
    
    # Test that we can select models (we can't test exact distribution without more complex logic)
    model = lb.get_next_model_weighted()
    assert model is not None
    assert model in ["model1", "model2"]

def test_performance_based_selection():
    """Test performance-based model selection"""
    lb = LoadBalancer()
    
    # Add models
    lb.add_model("model1", "Model 1", weight=1.0)
    lb.add_model("model2", "Model 2", weight=1.0)
    
    # Test that we can select models (this will use weighted approach as fallback)
    model = lb.get_next_model_performance_based(None)
    assert model is not None
    assert model in ["model1", "model2"]

def test_update_metrics():
    """Test updating model metrics"""
    lb = LoadBalancer()
    
    # Add a model
    lb.add_model("test_model", "Test Model", weight=1.0)
    
    # Update metrics
    lb.update_metrics("test_model", success=True)
    lb.update_metrics("test_model", success=False)
    
    # Check that metrics were updated
    assert lb.request_counts["test_model"] == 2
    assert lb.success_counts["test_model"] == 1

def test_get_model_stats():
    """Test getting model statistics"""
    lb = LoadBalancer()
    
    # Add a model
    lb.add_model("test_model", "Test Model", weight=1.0)
    
    # Update metrics
    lb.update_metrics("test_model", success=True)
    
    # Get stats
    stats = lb.get_model_stats()
    assert "test_model" in stats
    assert stats["test_model"]["name"] == "Test Model"
    assert stats["test_model"]["requests"] == 1

if __name__ == "__main__":
    pytest.main([__file__])