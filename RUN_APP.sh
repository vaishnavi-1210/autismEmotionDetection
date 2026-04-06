#!/bin/bash

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "=========================================="
echo "🚀 Autism Emotion Detection System"
echo "=========================================="
echo ""

# Check Python
echo -e "${BLUE}✓ Checking Python...${NC}"
python3 --version

# Check Node.js
echo -e "${BLUE}✓ Checking Node.js...${NC}"
node --version
npm --version

echo ""
echo "=========================================="
echo "📦 Setup Instructions"
echo "=========================================="
echo ""

echo -e "${YELLOW}Step 1: Install Backend Dependencies${NC}"
echo "Run in Terminal 1:"
echo ""
echo "  cd backend"
echo "  pip install -r requirements.txt"
echo ""

echo -e "${YELLOW}Step 2: Start Backend Server${NC}"
echo "Run in Terminal 1:"
echo ""
echo "  cd backend"
echo "  python main.py"
echo ""
echo "Expected output:"
echo "  INFO:     Uvicorn running on http://0.0.0.0:8000"
echo ""

echo -e "${YELLOW}Step 3: Install Frontend Dependencies${NC}"
echo "Run in Terminal 2:"
echo ""
echo "  cd frontend"
echo "  npm install"
echo ""

echo -e "${YELLOW}Step 4: Start Frontend Server${NC}"
echo "Run in Terminal 2:"
echo ""
echo "  cd frontend"
echo "  npm run dev"
echo ""
echo "Expected output:"
echo "  VITE ready in XX ms"
echo "  ➜ Local:   http://localhost:3000/"
echo ""

echo "=========================================="
echo "🌐 Access Points"
echo "=========================================="
echo ""
echo -e "${GREEN}Frontend (React):${NC}"
echo "  http://localhost:3000"
echo ""
echo -e "${GREEN}Backend API:${NC}"
echo "  http://localhost:8000"
echo ""
echo -e "${GREEN}API Documentation (Swagger):${NC}"
echo "  http://localhost:8000/docs"
echo ""

echo "=========================================="
echo "📝 What to Do Next"
echo "=========================================="
echo ""
echo "1. Open TWO separate terminals"
echo "2. Terminal 1: Start Backend (see Step 1 & 2 above)"
echo "3. Terminal 2: Start Frontend (see Step 3 & 4 above)"
echo "4. Open browser to http://localhost:3000"
echo "5. Upload a video file to get started!"
echo ""
