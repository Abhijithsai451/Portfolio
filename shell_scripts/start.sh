#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_PATH="$PROJECT_ROOT/venv"                    # ✅ CHANGED THIS LINE
REQUIREMENTS_PATH="$PROJECT_ROOT/backend/requirements.txt"
echo "🚀 Starting Enhanced Portfolio AI Backend"
echo "=========================================="

# Check environment
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo "⚠️  .env file not found in project root. Creating from .env.example..."
    cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
fi
# Change to the project root directory before running anything else
cd "$PROJECT_ROOT" || { echo "❌ Failed to change to project root directory"; exit 1; }

# Activate virtual environment
source "$PROJECT_ROOT/venv/bin/activate"

# Check knowledge base
if [ ! -f "$PROJECT_ROOT/backend/knowledge_base.txt" ]; then
    echo "⚠️  knowledge_base.txt not found. Creating default..."
    cat > knowledge_base.txt << EOF
Abhijith Sai - Portfolio Knowledge Base

Add your detailed information here including:
- Professional summary
- Technical skills
- Projects with descriptions
- Research publications
- Work experience
- Education
- Contact information
EOF
fi

# Setup virtual environment
if [ ! -d "$VENV_PATH" ]; then
    echo "🐍 Creating virtual environment..."
    python3 -m venv "$VENV_PATH"
    source "$VENV_PATH/bin/activate"
    pip install --upgrade pip setuptools wheel
    pip install -r "$REQUIREMENTS_PATH"
else
    source "$VENV_PATH/bin/activate"
fi
echo "✅ Virtual environment activated: $(which python)"
# Create logs directory if it doesn't exist
if [ ! -d "logs" ]; then
    echo "📂 Creating 'logs' directory..."
    mkdir -p logs
fi

# Check if using Docker
if [ "$1" = "--docker" ]; then
    echo "🐳 Starting with Docker Compose..."
    docker compose up --build
else
    echo "🔧 Starting development server..."
    echo "📊 API Documentation: http://localhost:8000/api/docs"
    echo "📈 Metrics: http://localhost:8000/api/metrics"
    echo "❤️  Health: http://localhost:8000/api/health"
    echo ""
    uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
fi