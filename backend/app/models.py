from pydantic import BaseModel, Field, validator
from typing import Optional, Literal, Dict, Any
from enum import Enum
import time


class BackendType(str, Enum):
    openai = "openai"
    ollama = "ollama"


class ProblemAnalysisRequest(BaseModel):
    problem_title: str = Field(..., min_length=3, max_length=200, description="Title of the problem to analyze")
    problem_description: str = Field(..., min_length=50, max_length=5000, description="Detailed description of the problem")
    backend: BackendType = Field(default=BackendType.openai, description="AI backend to use for analysis")
    
    @validator('problem_description')
    def validate_description_length(cls, v):
        if len(v.strip()) < 50:
            raise ValueError('Problem description must be at least 50 characters long')
        if len(v.strip()) > 5000:
            raise ValueError('Problem description must not exceed 5000 characters')
        return v.strip()
    
    @validator('problem_title')
    def validate_title(cls, v):
        return v.strip()


class WebSocketMessage(BaseModel):
    action: str = Field(..., description="Action to perform (e.g., 'analyze')")
    problem_title: str = Field(..., min_length=3, max_length=200)
    problem_description: str = Field(..., min_length=50, max_length=5000)
    backend: BackendType = Field(default=BackendType.openai)


class StreamResponseType(str, Enum):
    status = "status"
    delta = "delta"
    complete = "complete"
    error = "error"


class StreamResponse(BaseModel):
    type: StreamResponseType
    content: Optional[str] = None
    message: Optional[str] = None
    progress: Optional[int] = None
    error_code: Optional[str] = None


class AnalysisResponse(BaseModel):
    problem_title: str
    problem_description: str
    analysis: str
    backend_used: BackendType
    tokens_used: Optional[int] = None
    processing_time: float
    cached: bool = False
    timestamp: float = Field(default_factory=time.time)


class HealthResponse(BaseModel):
    status: str
    timestamp: float = Field(default_factory=time.time)
    version: str = "1.0.0"
    services: Dict[str, str] = {}


class ErrorResponse(BaseModel):
    error: str
    message: str
    timestamp: float = Field(default_factory=time.time)
    error_code: Optional[str] = None