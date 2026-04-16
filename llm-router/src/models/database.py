"""
Database models for LLM routing system
"""

import os
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Create the base class for database models
Base = declarative_base()


class RoutingLog(Base):
    """Database model for routing logs"""

    __tablename__ = "routing_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    query = Column(Text, nullable=False)
    model_id = Column(String(100), nullable=False)
    model_name = Column(String(100), nullable=False)
    expected_utility = Column(Float, nullable=False)
    cost = Column(Float, nullable=False)
    time = Column(Float, nullable=False)
    probability = Column(Float, nullable=False)
    success = Column(Boolean, default=True)
    response_text = Column(Text)
    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)
    total_tokens = Column(Integer)
    request_payload = Column(Text)
    response_payload = Column(Text)
    routing_context = Column(Text)

    def __repr__(self):
        return f"<RoutingLog(id={self.id}, model={self.model_name}, timestamp={self.timestamp})>"


class ModelPerformance(Base):
    """Database model for model performance metrics"""

    __tablename__ = "model_performance"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(String(100), unique=True, nullable=False)
    model_name = Column(String(100), nullable=False)
    total_requests = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)
    average_time = Column(Float, default=0.0)
    success_rate = Column(Float, default=0.0)
    last_updated = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ModelPerformance(id={self.id}, model={self.model_name})>"


# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./llm_router.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize the database"""
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully")
