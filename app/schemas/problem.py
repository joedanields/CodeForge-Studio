from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class AnalysisStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ProblemCreate(BaseModel):
    """Schema for creating a new problem."""
    title: str = Field(..., min_length=3, max_length=255, description="Problem title")
    description: str = Field(..., min_length=10, description="Detailed problem description")
    background: Optional[str] = Field(None, description="Additional background information")
    user_email: Optional[str] = Field(None, description="User email for notifications")


class ProblemUpdate(BaseModel):
    """Schema for updating an existing problem."""
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = Field(None, min_length=10)
    background: Optional[str] = None
    user_email: Optional[str] = None


class SolutionDetails(BaseModel):
    """Schema for individual solution details."""
    name: str
    algorithm: str
    time_complexity: str
    space_complexity: str
    pros: List[str]
    cons: List[str]
    use_cases: str
    real_world_examples: List[str]


class InnovativeSolution(BaseModel):
    """Schema for innovative solution proposals."""
    name: str
    core_idea: str
    how_it_differs: str
    advantages: List[str]
    disadvantages: List[str]
    feasibility_score: int = Field(..., ge=1, le=10)
    implementation_effort: str  # "Easy", "Medium", "Hard"
    

class HardwareConsiderations(BaseModel):
    """Schema for hardware-related analysis."""
    requirements: Dict[str, str]
    scalability: str
    optimization_opportunities: List[str]
    cost_performance_analysis: str
    existing_hardware_solutions: Optional[str]


class ImplementationRoadmap(BaseModel):
    """Schema for implementation roadmap phases."""
    phase1_foundation: str
    phase2_core_development: str
    phase3_testing_optimization: str
    phase4_deployment_monitoring: str


class AnalysisResult(BaseModel):
    """Schema for complete analysis result."""
    existing_solutions: List[SolutionDetails]
    comparative_analysis: Dict[str, Any]
    innovative_solutions: List[InnovativeSolution]
    recommended_solution: Dict[str, str]
    implementation_plan: Dict[str, Any]
    hardware_considerations: Optional[HardwareConsiderations]
    feasibility_assessment: Dict[str, Any]
    implementation_roadmap: ImplementationRoadmap


class ProblemResponse(BaseModel):
    """Schema for problem response."""
    id: int
    title: str
    description: str
    background: Optional[str]
    user_email: Optional[str]
    analysis_status: AnalysisStatus
    analysis_result: Optional[AnalysisResult]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class AnalysisSessionResponse(BaseModel):
    """Schema for analysis session response."""
    id: int
    problem_id: int
    status: AnalysisStatus
    ai_provider: Optional[str]
    model_used: Optional[str]
    tokens_used: Optional[int]
    processing_time_seconds: Optional[int]
    started_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]
    
    class Config:
        from_attributes = True


class AnalyzeRequest(BaseModel):
    """Schema for analysis request."""
    ai_provider: Optional[str] = Field("openai", description="AI provider to use")
    model: Optional[str] = Field("gpt-4", description="Model to use for analysis")
    include_hardware_analysis: bool = Field(True, description="Include hardware considerations")
    custom_requirements: Optional[str] = Field(None, description="Any custom analysis requirements")