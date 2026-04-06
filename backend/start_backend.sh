#!/bin/bash

echo "🚀 Starting Autism Emotion Detection Backend"
echo "=============================================="
echo ""

# Check if requirements are installed
echo "📦 Checking Python dependencies..."

# Try to import key modules
python3 << 'PYEOF'
import sys

required_modules = {
    'fastapi': 'FastAPI',
    'uvicorn': 'Uvicorn',
    'pydantic': 'Pydantic',
    'cv2': 'OpenCV',
    'numpy': 'NumPy',
    'aiofiles': 'aiofiles'
}

missing = []
for module, name in required_modules.items():
    try:
        __import__(module)
        print(f"✓ {name}")
    except ImportError:
        print(f"✗ {name} - NOT INSTALLED")
        missing.append(module)

if missing:
    print(f"\n⚠️  Missing modules: {', '.join(missing)}")
    print("Run: pip install -r requirements.txt")
    sys.exit(1)
else:
    print("\n✓ All dependencies installed!")
PYEOF

INSTALL_STATUS=$?

if [ $INSTALL_STATUS -ne 0 ]; then
    echo ""
    echo "❌ Dependencies missing. Installing..."
    pip install -r requirements.txt
fi

echo ""
echo "✅ Starting FastAPI server..."
echo "🌐 Server will be available at: http://localhost:8000"
echo "📖 API Docs at: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python3 main.py
