#!/bin/bash
cd "$(dirname "$0")"
echo "🎨 Autism Emotion Detection - Frontend Startup"
echo "=============================================="
echo ""
echo "📦 Installing Node dependencies..."
npm install
echo "✅ Dependencies installed"
echo ""
echo "🚀 Starting React dev server..."
echo "Visit: http://localhost:3000"
echo ""
npm run dev
