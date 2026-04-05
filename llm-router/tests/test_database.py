"""
Test cases for database functionality
"""
import pytest
from src.models.database import init_db, RoutingLog, ModelPerformance
from sqlalchemy.orm import Session

def test_database_initialization():
    """Test database initialization"""
    # This should not raise an exception
    init_db()
    assert True  # If we get here, initialization worked

def test_routing_log_model():
    """Test RoutingLog model creation"""
    # Test that we can create a RoutingLog instance
    log = RoutingLog(
        query="Test query",
        model_id="test_model",
        model_name="Test Model",
        expected_utility=0.8,
        cost=0.002,
        time=0.5,
        probability=0.9,
        success=True
    )
    
    assert log.query == "Test query"
    assert log.model_id == "test_model"
    assert log.expected_utility == 0.8
    assert log.cost == 0.002
    assert log.time == 0.5
    assert log.probability == 0.9
    assert log.success == True

def test_model_performance_model():
    """Test ModelPerformance model creation"""
    # Test that we can create a ModelPerformance instance
    perf = ModelPerformance(
        model_id="test_model",
        model_name="Test Model",
        total_requests=100,
        total_cost=2.5,
        average_time=0.6,
        success_rate=0.85
    )
    
    assert perf.model_id == "test_model"
    assert perf.model_name == "Test Model"
    assert perf.total_requests == 100
    assert perf.total_cost == 2.5
    assert perf.average_time == 0.6
    assert perf.success_rate == 0.85

if __name__ == "__main__":
    pytest.main([__file__])