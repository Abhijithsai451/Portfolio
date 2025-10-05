#!/bin/bash

# --- Configuration & Path Setup ---
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_PATH="$PROJECT_ROOT/venv"
WEB_REQUIREMENTS="$PROJECT_ROOT/web_service/requirements.txt"
CHAT_REQUIREMENTS="$PROJECT_ROOT/chat_service/requirements.txt"

echo "🚀 Starting Enhanced Portfolio AI Backend"
echo "=========================================="

# --- Pre-flight Checks and Setup ---

# 1. Check and potentially create .env file
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo "⚠️  .env file not found in project root. Please create one."
    echo "   You can use '.env.example' as a template if available."
    if [ -f "$PROJECT_ROOT/.env.example" ]; then
        cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
        echo "   Copied .env.example to .env"
    else
        echo "   No .env.example found to copy from. Create it manually."
    fi
fi

# 2. Change to the project root directory
cd "$PROJECT_ROOT" || { echo "❌ Failed to change to project root directory"; exit 1; }

# 3. Create 'logs' directory if it doesn't exist
if [ ! -d "logs" ]; then
    echo "📂 Creating 'logs' directory..."
    mkdir -p logs
fi

# 4. Check and potentially create knowledge_base.txt (now in chat_service)
if [ ! -f "$PROJECT_ROOT/chat_service/knowledge_base.txt" ]; then
    echo "⚠️  chat_service/knowledge_base.txt not found. Creating default..."
    cat > "$PROJECT_ROOT/chat_service/knowledge_base.txt" << EOF
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

# --- Virtual Environment Setup (for non-docker development) ---
# This part ensures all Python dependencies are installed in a venv
# if you choose to run services directly without Docker Compose.
if [ ! -d "$VENV_PATH" ]; then
    echo "🐍 Creating virtual environment..."
    python3.11 -m venv "$VENV_PATH"
    source "$VENV_PATH/bin/activate"
    pip install --upgrade pip setuptools wheel
    echo "Installing core_service requirements..."
    if [ -f "$WEB_REQUIREMENTS" ]; then
        pip install -r "$WEB_REQUIREMENTS"
    else
        echo "❌ Error: web_service/requirements.txt not found! Cannot install core dependencies."
    fi
    echo "Installing chat_service requirements..."
    if [ -f "$CHAT_REQUIREMENTS" ]; then
        pip install -r "$CHAT_REQUIREMENTS"
    else
        echo "❌ Error: chat_service/requirements.txt not found! Cannot install chat dependencies."
    fi
else
    source "$VENV_PATH/bin/activate"
    # For active development, it's good to ensure requirements are up-to-date
    echo "✅ Virtual environment activated: $(which python)"
    echo "Updating core_service requirements (if changed)..."
    if [ -f "$WEB_REQUIREMENTS" ]; then
        pip install -r "$WEB_REQUIREMENTS"
    fi
    echo "Updating chat_service requirements (if changed)..."
    if [ -f "$CHAT_REQUIREMENTS" ]; then
        pip install -r "$CHAT_REQUIREMENTS"
    fi
fi


# --- Starting Services ---
if [ "$1" = "--docker" ]; then
    echo "🐳 Starting ALL services with Docker Compose..."
    echo "   This will build images and start web_service, chat_service, and redis."
    echo "   Access core_service at http://localhost:8000"
    echo ""
    # Docker Compose automatically reads .env at the project root if env_file is configured in docker-compose.yml
    docker compose up --build
else
    echo "🔧 Starting development server for WEB SERVICE only..."
    echo "   For full functionality, you MUST ensure 'chat_service' and 'redis' are running separately."
    echo "   RECOMMENDED: Use './start.sh --docker' to run all services."
    echo ""

    # Load environment variables from .env for direct uvicorn run
    if [ -f "$PROJECT_ROOT/.env" ]; then
        export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
    fi

    # Set default values for critical environment variables if not found in .env or shell
    # These assume chat_service is available on port 8001 and Redis on 6379
    export WEB_SERVICE_URL="${WEB_SERVICE_URL:-http://localhost:8001}"
    export REDIS_URL="${REDIS_URL:-redis://localhost:6379}"

    echo "📊 Web service API Docs: http://localhost:8000/api/docs"
    echo "📈 Web Service Metrics: http://localhost:8000/api/metrics"
    echo "❤️  Web Service Health: http://localhost:8000/api/health"
    echo ""
    # Start core_service directly with reload for development
    uvicorn web_service.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
fi