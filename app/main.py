from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from app.core.config import settings
from app.api.api_v1.api import api_router

app = FastAPI(
    title="CodeForge Studio API",
    description="AI-powered problem analysis and solution platform",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main application page."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>CodeForge Studio</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #333; text-align: center; margin-bottom: 30px; }
            .subtitle { text-align: center; color: #666; margin-bottom: 40px; }
            .feature { margin-bottom: 20px; padding: 15px; background: #f8f9fa; border-radius: 5px; }
            .api-link { text-align: center; margin-top: 30px; }
            a { color: #007bff; text-decoration: none; }
            a:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 CodeForge Studio</h1>
            <p class="subtitle">AI-powered problem analysis and solution platform</p>
            
            <div class="feature">
                <h3>📝 Problem Submission</h3>
                <p>Submit your problems with detailed descriptions for comprehensive AI analysis.</p>
            </div>
            
            <div class="feature">
                <h3>🤖 AI Analysis</h3>
                <p>Get detailed analysis including existing solutions, innovations, and implementation roadmaps.</p>
            </div>
            
            <div class="feature">
                <h3>📊 Solution Comparison</h3>
                <p>Compare different approaches with complexity analysis and trade-off evaluations.</p>
            </div>
            
            <div class="feature">
                <h3>🎯 Implementation Guidance</h3>
                <p>Receive step-by-step implementation plans with technology recommendations.</p>
            </div>
            
            <div class="api-link">
                <p><a href="/docs">📚 API Documentation</a> | <a href="/redoc">📖 ReDoc</a></p>
            </div>
        </div>
    </body>
    </html>
    """

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "CodeForge Studio API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)