# 🚀 MASTER STARTUP GUIDE

## ⚡ Super Quick Start (Copy-Paste Ready)

### For macOS/Linux Users:

**Terminal 1 - Backend:**
```bash
cd "/Users/santhosh/Desktop/All Folders/autism-detector/backend"
pip install -r requirements.txt
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd "/Users/santhosh/Desktop/All Folders/autism-detector/frontend"
npm install
npm run dev
```

**Then open browser:**
```
http://localhost:3000
```

### For Windows Users:

**Command Prompt 1 - Backend:**
```cmd
cd "C:\Users\santhosh\Desktop\All Folders\autism-detector\backend"
pip install -r requirements.txt
python main.py
```

**Command Prompt 2 - Frontend:**
```cmd
cd "C:\Users\santhosh\Desktop\All Folders\autism-detector\frontend"
npm install
npm run dev
```

**Then open browser:**
```
http://localhost:3000
```

---

## 📊 Expected Output

### Backend (Terminal 1)
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Application startup complete
```

### Frontend (Terminal 2)
```
VITE v5.0.0  ready in 123 ms

➜  Local:   http://localhost:3000/
➜  press h to show help
```

---

## ✅ Verification Checklist

Once both servers are running:

- [ ] Backend is running on http://localhost:8000
- [ ] Frontend is running on http://localhost:3000
- [ ] Can open http://localhost:3000 in browser
- [ ] Can see the upload interface
- [ ] Can view API docs at http://localhost:8000/docs

---

## 🎯 Step-by-Step Instructions

### Step 1: Prepare Terminals

1. Open **Terminal 1** (or Command Prompt on Windows)
2. Open **Terminal 2** (new window)

### Step 2: Frontend Setup (Terminal 2)

```bash
# Navigate to frontend directory
cd "/Users/santhosh/Desktop/All Folders/autism-detector/frontend"

# Install dependencies (first time only)
npm install

# Start development server
npm run dev
```

Wait for output like:
```
➜  Local:   http://localhost:3000/
```

### Step 3: Backend Setup (Terminal 1)

```bash
# Navigate to backend directory
cd "/Users/santhosh/Desktop/All Folders/autism-detector/backend"

# Install Python dependencies (first time only)
pip install -r requirements.txt

# Start Flask server
python main.py
```

Wait for output like:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 4: Open in Browser

Navigate to:
```
http://localhost:3000
```

You should see the Autism Emotion Detection System interface!

---

## 🔧 Troubleshooting

### Backend won't start

**Problem:** `ModuleNotFoundError` or `ImportError`

**Solution:**
```bash
cd backend
pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

**Problem:** Port 8000 already in use

**Solution:**
```bash
# Find what's using port 8000
lsof -i :8000

# Kill the process (example PID 12345)
kill -9 12345
```

### Frontend won't start

**Problem:** `npm: command not found`

**Solution:**
- Download Node.js from https://nodejs.org/
- Verify installation: `node --version`

**Problem:** Port 3000 already in use

**Solution:**
```bash
# Find what's using port 3000
lsof -i :3000

# Kill the process
kill -9 <PID>
```

### Can't connect to API

**Problem:** Frontend shows "Failed to connect to API"

**Solution:**
1. Verify backend is running on port 8000
2. Check browser console for errors (F12)
3. Try visiting http://localhost:8000/docs
4. Check backend terminal for error messages

### Module import errors

**For Windows:**
```cmd
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**For macOS/Linux:**
```bash
python3 -m pip install --upgrade pip
pip3 install -r requirements.txt
```

---

## 📱 Using the Application

1. **Upload Video:** Drag & drop or click to select
2. **Select Video:** Choose MP4, AVI, MOV, or MKV file (max 500MB)
3. **Processing:** System automatically starts processing
4. **Wait:** Takes 2-5 minutes depending on video length
5. **Results:** View emotion detection and confidence scores
6. **Export:** Download results as JSON or CSV

---

## 🌐 Access Points

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:3000 | Main web interface |
| Backend API | http://localhost:8000 | API server |
| API Docs | http://localhost:8000/docs | Interactive Swagger UI |
| API ReDoc | http://localhost:8000/redoc | Alternative API docs |

---

## 🛑 Stopping the Application

**In both terminals:**
- Press `Ctrl+C` (or `Cmd+C` on macOS) to stop each server

**Or:**
- Close the terminal window to stop the server

---

## 💾 Data Location

All data is stored locally in:
```
/Users/santhosh/Desktop/All Folders/autism-detector/data/
├── uploads/          # Uploaded videos
├── processed/        # Extracted coordinates
├── features/         # Preprocessed features
├── results/          # Emotion predictions
└── sessions/         # Session metadata
```

---

## 📝 Useful Commands

**Check if ports are free:**
```bash
# Check port 3000 (frontend)
lsof -i :3000

# Check port 8000 (backend)
lsof -i :8000
```

**Update dependencies:**
```bash
# Backend
cd backend
pip install -r requirements.txt --upgrade

# Frontend
cd frontend
npm update
```

**Clear cache & reinstall:**
```bash
# Frontend
cd frontend
rm -rf node_modules
npm install

# Backend
cd backend
pip cache purge
pip install -r requirements.txt
```

---

## 🎉 You're All Set!

Everything is installed and ready to go. Just follow the quick start steps above and you'll be processing videos in minutes!

**Questions?** Check these files:
- `START_HERE.md` - Quick orientation
- `README.md` - Full documentation
- `QUICK_START.md` - Setup guide
- `IMPLEMENTATION_SUMMARY.md` - Architecture details

---

**Happy analyzing! 🎥🧠**
