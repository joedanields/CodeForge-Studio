from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any

Base = declarative_base()


class AnalysisStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Problem(Base):
    """Problem model for storing user-submitted problems."""
    
    __tablename__ = "problems"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    background = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Analysis tracking
    analysis_status = Column(SQLEnum(AnalysisStatus), default=AnalysisStatus.PENDING)
    analysis_result = Column(JSON, nullable=True)
    
    # User information (for future user system)
    user_id = Column(String(100), nullable=True, index=True)
    user_email = Column(String(255), nullable=True)
    
    def __repr__(self) -> str:
        return f"<Problem(id={self.id}, title='{self.title[:50]}...')>"


class AnalysisSession(Base):
    """Store analysis sessions and results."""
    
    __tablename__ = "analysis_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    problem_id = Column(Integer, nullable=False, index=True)
    
    # Analysis data
    prompt_used = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=True)
    structured_analysis = Column(JSON, nullable=True)
    
    # Metadata
    ai_provider = Column(String(50), nullable=True)  # "openai", "anthropic", etc.
    model_used = Column(String(100), nullable=True)
    tokens_used = Column(Integer, nullable=True)
    processing_time_seconds = Column(Integer, nullable=True)
    
    # Status and timestamps
    status = Column(SQLEnum(AnalysisStatus), default=AnalysisStatus.PENDING)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    
    def __repr__(self) -> str:
        return f"<AnalysisSession(id={self.id}, problem_id={self.problem_id}, status={self.status})>"