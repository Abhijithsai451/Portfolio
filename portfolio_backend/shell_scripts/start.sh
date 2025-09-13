#!/bin/bash
echo "🚀 Starting Enhanced Portfolio AI Backend"
echo "=========================================="

# Check environment
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
fi

# Check knowledge base
if [ ! -f "knowledge_base.txt" ]; then
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
if [ ! -d "venv" ]; then
    echo "🐍 Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Check if using Docker
if [ "$1" = "--docker" ]; then
    echo "🐳 Starting with Docker Compose..."
    docker-compose up --build
else
    echo "🔧 Starting development server..."
    echo "📊 API Documentation: http://localhost:8000/api/docs"
    echo "📈 Metrics: http://localhost:8000/api/metrics"
    echo "❤️  Health: http://localhost:8000/api/health"
    echo ""
    uvicorn main:app --reload --host 0.0.0.0 --port 8000 --log-level info
fi