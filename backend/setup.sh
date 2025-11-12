#!/bin/bash

# CodeForge AI Backend Development Setup Script

echo "=== CodeForge AI Backend Setup ==="

# Check if Python 3.11+ is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3.11 or later."
    exit 1
fi

# Check Python version
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
if [[ $(echo "$python_version < 3.11" | bc -l) -eq 1 ]]; then
    echo "Error: Python 3.11+ required. Current version: $python_version"
    exit 1
fi

echo "✓ Python $python_version detected"

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Copy environment file
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file and add your OpenAI API key"
fi

# Check if Redis is running
if ! command -v redis-cli &> /dev/null; then
    echo "⚠️  Redis not detected. Install Redis or use Docker:"
    echo "   Docker: docker run -d -p 6379:6379 redis:7-alpine"
    echo "   Ubuntu: sudo apt-get install redis-server"
    echo "   macOS: brew install redis"
else
    if redis-cli ping > /dev/null 2>&1; then
        echo "✓ Redis is running"
    else
        echo "⚠️  Redis is not running. Start it with: redis-server"
    fi
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your OpenAI API key"
echo "2. Start Redis if not running: redis-server"
echo "3. Run the development server: python -m uvicorn app.main:app --reload"
echo ""
echo "API Documentation: http://localhost:8000/docs"
echo "Health Check: http://localhost:8000/api/health"
echo ""
echo "For production deployment, use Docker:"
echo "  docker-compose up -d"