from typing import List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
import asyncio
from datetime import datetime

from app.schemas import (
    ProblemCreate, 
    ProblemResponse, 
    ProblemUpdate,
    AnalyzeRequest,
    AnalysisSessionResponse
)
from app.services import ai_service, PromptTemplate

router = APIRouter()

# In-memory storage for demo (replace with database in production)
problems_db = {}
analysis_sessions_db = {}
problem_counter = 0
session_counter = 0


async def run_analysis_task(problem_id: int, analysis_request: AnalyzeRequest):
    """Background task to run AI analysis."""
    global session_counter, analysis_sessions_db, problems_db
    
    session_counter += 1
    session_id = session_counter
    
    # Create analysis session
    session = {
        "id": session_id,
        "problem_id": problem_id,
        "status": "processing",
        "ai_provider": analysis_request.ai_provider,
        "model_used": analysis_request.model,
        "started_at": datetime.utcnow(),
        "completed_at": None,
        "error_message": None,
        "tokens_used": None,
        "processing_time_seconds": None
    }
    analysis_sessions_db[session_id] = session
    
    try:
        # Update problem status
        if problem_id in problems_db:
            problems_db[problem_id]["analysis_status"] = "processing"
        
        # Get problem details
        problem = problems_db.get(problem_id)
        if not problem:
            raise ValueError("Problem not found")
        
        # Generate prompt
        prompt = PromptTemplate.get_analysis_prompt(
            title=problem["title"],
            description=problem["description"],
            background=problem.get("background")
        )
        
        # Run AI analysis
        result = await ai_service.analyze_problem(
            prompt=prompt,
            provider=analysis_request.ai_provider or "openai",
            model=analysis_request.model
        )
        
        # Update session with results
        session["completed_at"] = datetime.utcnow()
        session["tokens_used"] = result.get("tokens_used")
        session["processing_time_seconds"] = result.get("processing_time_seconds")
        
        if result["success"]:
            session["status"] = "completed"
            # Update problem with analysis result
            problems_db[problem_id]["analysis_status"] = "completed"
            problems_db[problem_id]["analysis_result"] = result["structured_analysis"]
        else:
            session["status"] = "failed"
            session["error_message"] = result["error"]
            problems_db[problem_id]["analysis_status"] = "failed"
            
    except Exception as e:
        session["status"] = "failed"
        session["error_message"] = str(e)
        session["completed_at"] = datetime.utcnow()
        if problem_id in problems_db:
            problems_db[problem_id]["analysis_status"] = "failed"


@router.post("/", response_model=ProblemResponse)
async def create_problem(problem: ProblemCreate):
    """Create a new problem submission."""
    global problem_counter, problems_db
    
    problem_counter += 1
    problem_id = problem_counter
    
    new_problem = {
        "id": problem_id,
        "title": problem.title,
        "description": problem.description,
        "background": problem.background,
        "user_email": problem.user_email,
        "analysis_status": "pending",
        "analysis_result": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    problems_db[problem_id] = new_problem
    
    return ProblemResponse(**new_problem)


@router.get("/{problem_id}", response_model=ProblemResponse)
async def get_problem(problem_id: int):
    """Get a specific problem by ID."""
    if problem_id not in problems_db:
        raise HTTPException(status_code=404, detail="Problem not found")
    
    return ProblemResponse(**problems_db[problem_id])


@router.get("/", response_model=List[ProblemResponse])
async def list_problems(skip: int = 0, limit: int = 20):
    """List all problems with pagination."""
    all_problems = list(problems_db.values())
    # Sort by created_at descending
    sorted_problems = sorted(all_problems, key=lambda x: x["created_at"], reverse=True)
    
    return [ProblemResponse(**p) for p in sorted_problems[skip:skip + limit]]


@router.put("/{problem_id}", response_model=ProblemResponse)
async def update_problem(problem_id: int, problem_update: ProblemUpdate):
    """Update an existing problem."""
    if problem_id not in problems_db:
        raise HTTPException(status_code=404, detail="Problem not found")
    
    problem = problems_db[problem_id]
    update_data = problem_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        problem[field] = value
    
    problem["updated_at"] = datetime.utcnow()
    
    return ProblemResponse(**problem)


@router.delete("/{problem_id}")
async def delete_problem(problem_id: int):
    """Delete a problem."""
    if problem_id not in problems_db:
        raise HTTPException(status_code=404, detail="Problem not found")
    
    del problems_db[problem_id]
    
    return {"message": "Problem deleted successfully"}


@router.post("/{problem_id}/analyze")
async def analyze_problem(
    problem_id: int, 
    analysis_request: AnalyzeRequest,
    background_tasks: BackgroundTasks
):
    """Trigger AI analysis for a problem."""
    if problem_id not in problems_db:
        raise HTTPException(status_code=404, detail="Problem not found")
    
    # Check available providers
    available_providers = ai_service.get_available_providers()
    if not available_providers:
        raise HTTPException(
            status_code=503, 
            detail="No AI providers available. Please configure API keys."
        )
    
    if analysis_request.ai_provider not in available_providers:
        raise HTTPException(
            status_code=400,
            detail=f"Provider '{analysis_request.ai_provider}' not available. "
                   f"Available providers: {available_providers}"
        )
    
    # Start background analysis
    background_tasks.add_task(run_analysis_task, problem_id, analysis_request)
    
    return {
        "message": "Analysis started",
        "problem_id": problem_id,
        "provider": analysis_request.ai_provider,
        "status": "processing"
    }


@router.get("/{problem_id}/analysis")
async def get_analysis_result(problem_id: int):
    """Get the analysis result for a problem."""
    if problem_id not in problems_db:
        raise HTTPException(status_code=404, detail="Problem not found")
    
    problem = problems_db[problem_id]
    
    return {
        "problem_id": problem_id,
        "status": problem["analysis_status"],
        "analysis_result": problem.get("analysis_result"),
        "last_updated": problem["updated_at"]
    }


@router.get("/{problem_id}/sessions", response_model=List[AnalysisSessionResponse])
async def get_analysis_sessions(problem_id: int):
    """Get all analysis sessions for a problem."""
    if problem_id not in problems_db:
        raise HTTPException(status_code=404, detail="Problem not found")
    
    sessions = [
        session for session in analysis_sessions_db.values()
        if session["problem_id"] == problem_id
    ]
    
    return [AnalysisSessionResponse(**session) for session in sessions]


@router.get("/providers/available")
async def get_available_providers():
    """Get list of available AI providers."""
    providers = ai_service.get_available_providers()
    
    return {
        "providers": providers,
        "default": "openai" if "openai" in providers else providers[0] if providers else None,
        "total": len(providers)
    }