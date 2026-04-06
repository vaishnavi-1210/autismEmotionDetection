#!/bin/bash

echo "🎨 Starting Autism Emotion Detection Frontend"
echo "=============================================="
echo ""

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing npm dependencies..."
    npm install
else
    echo "✓ npm dependencies already installed"
fi

echo ""
echo "✅ Starting React development server..."
echo "🌐 Frontend will be available at: http://localhost:3000"
echo "🔗 API will connect to: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop"
echo ""

npm run dev
