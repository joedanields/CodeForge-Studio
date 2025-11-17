#!/bin/bash

# Development startup script for CodeForge Studio

echo "🚀 Starting CodeForge Studio Development Environment..."

# Check if UV is installed
if ! command -v uv &> /dev/null; then
    echo "❌ UV package manager not found. Please install it first:"
    echo "curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
uv sync

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating environment file..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your API keys before starting the servers"
fi

# Start backend server in background
echo "🐍 Starting FastAPI backend server..."
uv run uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start frontend if Node.js is available
if command -v node &> /dev/null && command -v npm &> /dev/null; then
    echo "⚛️  Starting React frontend server..."
    cd frontend
    
    # Install frontend dependencies if node_modules doesn't exist
    if [ ! -d "node_modules" ]; then
        echo "📦 Installing frontend dependencies..."
        npm install
    fi
    
    # Start frontend server
    npm start &
    FRONTEND_PID=$!
    cd ..
    
    echo "✅ Development servers started!"
    echo "   Backend:  http://localhost:8000"
    echo "   Frontend: http://localhost:3000"
    echo "   API Docs: http://localhost:8000/docs"
    echo ""
    echo "Press Ctrl+C to stop all servers"
    
    # Wait for interrupt
    trap "echo '🛑 Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
    wait
else
    echo "✅ Backend server started at http://localhost:8000"
    echo "📖 API documentation available at http://localhost:8000/docs"
    echo ""
    echo "⚠️  Node.js not found. Frontend not started."
    echo "   Install Node.js and run 'cd frontend && npm install && npm start'"
    echo ""
    echo "Press Ctrl+C to stop the backend server"
    
    # Wait for interrupt
    trap "echo '🛑 Stopping server...'; kill $BACKEND_PID 2>/dev/null; exit" INT
    wait $BACKEND_PID
fi