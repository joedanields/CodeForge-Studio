from fastapi import APIRouter

from app.api.api_v1.endpoints import problems

api_router = APIRouter()
api_router.include_router(problems.router, prefix="/problems", tags=["problems"])