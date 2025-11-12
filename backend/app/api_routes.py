import time
import logging
from typing import Dict, Any
from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .models import (
    ProblemAnalysisRequest, 
    AnalysisResponse, 
    HealthResponse, 
    ErrorResponse,
    BackendType
)
from .analyzer import CodeForgeAnalyzer
from .config import settings

logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

router = APIRouter()

# Global analyzer instance
analyzer = CodeForgeAnalyzer()


async def get_analyzer() -> CodeForgeAnalyzer:
    """Dependency to get analyzer instance"""
    return analyzer


@router.post("/api/analyze", response_model=AnalysisResponse)
@limiter.limit(f"{settings.rate_limit_requests}/minute")
async def analyze_problem(
    request: ProblemAnalysisRequest,
    background_tasks: BackgroundTasks,
    analyzer: CodeForgeAnalyzer = Depends(get_analyzer)
):
    """
    Analyze a technical problem and return comprehensive analysis.
    
    This endpoint accepts a problem description and returns a detailed analysis
    including existing solutions, innovative approaches, and implementation recommendations.
    """
    start_time = time.time()
    
    try:
        # Perform blocking analysis
        result = await analyzer.analyze_blocking(
            request.problem_title,
            request.problem_description,
            request.backend
        )
        
        response = AnalysisResponse(
            problem_title=request.problem_title,
            problem_description=request.problem_description,
            analysis=result["analysis"],
            backend_used=request.backend,
            tokens_used=result.get("tokens_used"),
            processing_time=result["processing_time"],
            cached=result["cached"]
        )
        
        logger.info(f"Analysis completed for '{request.problem_title}' in {result['processing_time']:.2f}s (cached: {result['cached']})")
        
        return response
        
    except Exception as e:
        logger.error(f"Analysis failed for '{request.problem_title}': {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@router.get("/api/health", response_model=HealthResponse)
async def health_check(analyzer: CodeForgeAnalyzer = Depends(get_analyzer)):
    """
    Health check endpoint to verify service status.
    
    Returns the current status of the service and its dependencies.
    """
    services = {}
    
    # Check Redis connection
    try:
        if analyzer.redis_client:
            await analyzer.redis_client.ping()
            services["redis"] = "healthy"
        else:
            services["redis"] = "disconnected"
    except Exception as e:
        services["redis"] = f"error: {str(e)}"
    
    # Check OpenAI API (basic check)
    try:
        # We don't make an actual API call for health check to avoid costs
        if settings.openai_api_key and settings.openai_api_key != "your_openai_api_key_here":
            services["openai"] = "configured"
        else:
            services["openai"] = "not_configured"
    except Exception as e:
        services["openai"] = f"error: {str(e)}"
    
    overall_status = "healthy" if all(
        status in ["healthy", "configured"] for status in services.values()
    ) else "degraded"
    
    return HealthResponse(
        status=overall_status,
        services=services
    )


@router.get("/api/cache/stats")
async def get_cache_stats(analyzer: CodeForgeAnalyzer = Depends(get_analyzer)):
    """
    Get Redis cache statistics.
    
    Returns information about cache usage and performance.
    """
    if not analyzer.redis_client:
        raise HTTPException(status_code=503, detail="Redis not connected")
    
    try:
        info = await analyzer.redis_client.info()
        stats = {
            "connected_clients": info.get("connected_clients", 0),
            "used_memory": info.get("used_memory_human", "N/A"),
            "total_connections_received": info.get("total_connections_received", 0),
            "total_commands_processed": info.get("total_commands_processed", 0),
            "keyspace_hits": info.get("keyspace_hits", 0),
            "keyspace_misses": info.get("keyspace_misses", 0),
            "uptime_in_seconds": info.get("uptime_in_seconds", 0)
        }
        
        # Calculate hit ratio
        hits = stats["keyspace_hits"]
        misses = stats["keyspace_misses"]
        total = hits + misses
        hit_ratio = (hits / total * 100) if total > 0 else 0
        stats["hit_ratio_percent"] = round(hit_ratio, 2)
        
        return {"status": "success", "stats": stats}
        
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")


@router.delete("/api/cache/clear")
async def clear_cache(analyzer: CodeForgeAnalyzer = Depends(get_analyzer)):
    """
    Clear all cached analysis results.
    
    This endpoint removes all cached analysis from Redis.
    """
    if not analyzer.redis_client:
        raise HTTPException(status_code=503, detail="Redis not connected")
    
    try:
        # Get all analysis cache keys
        keys = await analyzer.redis_client.keys("analysis:*")
        
        if keys:
            deleted_count = await analyzer.redis_client.delete(*keys)
            logger.info(f"Cleared {deleted_count} cached analyses")
            return {
                "status": "success", 
                "message": f"Cleared {deleted_count} cached analyses"
            }
        else:
            return {
                "status": "success", 
                "message": "No cached analyses found"
            }
            
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


# Rate limit error handler
@router.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    """Handle rate limit exceeded errors"""
    return ErrorResponse(
        error="Rate limit exceeded",
        message=f"Too many requests. Limit: {settings.rate_limit_requests} per minute",
        error_code="RATE_LIMIT_EXCEEDED"
    )