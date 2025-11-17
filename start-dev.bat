@echo off
REM Development startup script for CodeForge Studio (Windows)

echo 🚀 Starting CodeForge Studio Development Environment...

REM Check if UV is installed
uv --version >nul 2>&1
if errorlevel 1 (
    echo ❌ UV package manager not found. Please install it first:
    echo https://docs.astral.sh/uv/getting-started/installation/
    exit /b 1
)

REM Install Python dependencies
echo 📦 Installing Python dependencies...
uv sync

REM Copy environment file if it doesn't exist
if not exist .env (
    echo 📝 Creating environment file...
    copy .env.example .env
    echo ⚠️  Please edit .env file with your API keys before starting the servers
)

REM Start backend server
echo 🐍 Starting FastAPI backend server...
start "CodeForge Backend" cmd /k "uv run uvicorn app.main:app --reload --port 8000"

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

REM Check if Node.js is available and start frontend
node --version >nul 2>&1
if not errorlevel 1 (
    echo ⚛️  Starting React frontend server...
    cd frontend
    
    REM Install frontend dependencies if node_modules doesn't exist
    if not exist node_modules (
        echo 📦 Installing frontend dependencies...
        npm install
    )
    
    REM Start frontend server
    start "CodeForge Frontend" cmd /k "npm start"
    cd ..
    
    echo ✅ Development servers started!
    echo    Backend:  http://localhost:8000
    echo    Frontend: http://localhost:3000
    echo    API Docs: http://localhost:8000/docs
) else (
    echo ✅ Backend server started at http://localhost:8000
    echo 📖 API documentation available at http://localhost:8000/docs
    echo.
    echo ⚠️  Node.js not found. Frontend not started.
    echo    Install Node.js and run 'cd frontend && npm install && npm start'
)

echo.
echo Press any key to exit...
pause >nul