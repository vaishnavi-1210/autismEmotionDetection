#!/bin/bash
cd "$(dirname "$0")"
echo "🚀 Autism Emotion Detection - Backend Startup"
echo "==========================================="
echo ""
echo "📦 Creating virtual environment..."
python3 -m venv venv
echo "✅ Virtual environment created"
echo ""
echo "📦 Installing dependencies..."
python3 -m venv venv --upgrade-deps
/bin/bash -c "source venv/bin/activate && pip install -r requirements.txt"
echo "✅ Dependencies installed"
echo ""
echo "🚀 Starting FastAPI server..."
echo "Visit: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""
/bin/bash -c "source venv/bin/activate && python main.py"
