"""
Load balancer for LLM routing system
"""
from typing import Dict, List, Optional
from src.models.database import get_db, RoutingLog
from sqlalchemy.orm import Session
import logging
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class LoadBalancer:
    """Load balancer for distributing requests across LLM models"""
    
    def __init__(self):
        """Initialize the load balancer"""
        self.models = {}
        self.current_index = 0
        self.request_counts = {}
        self.success_counts = {}
        self.total_requests = 0
        
        logger.info("Load balancer initialized")
    
    def add_model(self, model_id: str, model_name: str, weight: float = 1.0):
        """
        Add a model to the load balancer
        
        Args:
            model_id: Unique identifier for the model
            model_name: Name of the model
            weight: Weight for load distribution (higher = more requests)
        """
        self.models[model_id] = {
            'name': model_name,
            'weight': weight,
            'requests': 0,
            'successes': 0
        }
        self.request_counts[model_id] = 0
        self.success_counts[model_id] = 0
        logger.info(f"Added model {model_name} (ID: {model_id}) to load balancer")
    
    def get_next_model_round_robin(self) -> Optional[str]:
        """
        Get the next model using round-robin algorithm
        
        Returns:
            Model ID or None if no models available
        """
        if not self.models:
            return None
            
        model_ids = list(self.models.keys())
        model_id = model_ids[self.current_index]
        self.current_index = (self.current_index + 1) % len(model_ids)
        
        return model_id
    
    def get_next_model_weighted(self) -> Optional[str]:
        """
        Get the next model using weighted distribution
        
        Returns:
            Model ID or None if no models available
        """
        if not self.models:
            return None
            
        # Calculate total weight
        total_weight = sum(model['weight'] for model in self.models.values())
        
        if total_weight <= 0:
            # Fallback to round-robin if weights are invalid
            return self.get_next_model_round_robin()
        
        # Select model based on weights
        import random
        rand_value = random.uniform(0, total_weight)
        cumulative_weight = 0
        
        for model_id, model_info in self.models.items():
            cumulative_weight += model_info['weight']
            if rand_value <= cumulative_weight:
                return model_id
        
        # Fallback to last model
        return list(self.models.keys())[-1]
    
    def get_next_model_performance_based(self, db: Session) -> Optional[str]:
        """
        Get the next model based on performance metrics
        
        Args:
            db: Database session
            
        Returns:
            Model ID or None if no models available
        """
        if not self.models:
            return None
            
        # Get performance data from database
        try:
            # This is a simplified approach - in a real implementation,
            # we would query the database for recent performance metrics
            # For now, we'll use a simple heuristic
            
            # Calculate performance score for each model (lower is better for time, higher is better for success rate)
            model_scores = {}
            for model_id, model_info in self.models.items():
                # Simple performance score: (1 / average_time) * success_rate
                # We'll use a default value for now since we don't have real data
                avg_time = 0.5  # Default average time
                success_rate = 0.8  # Default success rate
                
                # In a real implementation, we would query the database for actual metrics
                # For now, we'll use a simple approach
                score = (1 / avg_time) * success_rate * model_info['weight']
                model_scores[model_id] = score
            
            # Select model with highest score
            best_model = max(model_scores, key=model_scores.get)
            return best_model
            
        except Exception as e:
            logger.error(f"Error calculating performance-based model selection: {str(e)}")
            # Fallback to weighted distribution
            return self.get_next_model_weighted()
    
    def get_next_model(self, strategy: str = "round_robin", db: Session = None) -> Optional[str]:
        """
        Get the next model based on the specified strategy
        
        Args:
            strategy: Selection strategy ("round_robin", "weighted", "performance_based")
            db: Database session (required for performance_based strategy)
            
        Returns:
            Model ID or None if no models available
        """
        if strategy == "round_robin":
            return self.get_next_model_round_robin()
        elif strategy == "weighted":
            return self.get_next_model_weighted()
        elif strategy == "performance_based":
            if db is None:
                logger.warning("Performance-based strategy requires database session")
                return self.get_next_model_weighted()
            return self.get_next_model_performance_based(db)
        else:
            logger.warning(f"Unknown strategy {strategy}, using round-robin")
            return self.get_next_model_round_robin()
    
    def update_metrics(self, model_id: str, success: bool = True):
        """
        Update metrics for a model
        
        Args:
            model_id: Model identifier
            success: Whether the request was successful
        """
        if model_id in self.models:
            self.models[model_id]['requests'] += 1
            self.request_counts[model_id] += 1
            self.total_requests += 1
            
            if success:
                self.models[model_id]['successes'] += 1
                self.success_counts[model_id] += 1
    
    def get_model_stats(self) -> Dict:
        """
        Get statistics for all models
        
        Returns:
            Dictionary with model statistics
        """
        stats = {}
        for model_id, model_info in self.models.items():
            total_requests = self.request_counts.get(model_id, 0)
            successes = self.success_counts.get(model_id, 0)
            success_rate = successes / total_requests if total_requests > 0 else 0.0
            
            stats[model_id] = {
                'name': model_info['name'],
                'requests': total_requests,
                'successes': successes,
                'success_rate': success_rate,
                'weight': model_info['weight']
            }
        
        return stats

# Global load balancer instance
load_balancer = LoadBalancer()