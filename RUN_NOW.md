❌ Upload failed: Upload failed: Internal Server Error# 🚀 RUN THE APP RIGHT NOW (Super Simple)

## Option 1: Easiest - Use the Scripts (Recommended)

**Open Terminal 1:**
```bash
cd "/Users/santhosh/Desktop/All Folders/autism-detector/backend"
bash install_and_run.sh
```

**Open Terminal 2:**
```bash
cd "/Users/santhosh/Desktop/All Folders/autism-detector/frontend"
bash install_and_run.sh
```

**Then open browser:**
```
http://localhost:3000
```

---

## Option 2: Manual Step-by-Step

### Terminal 1 - Backend

```bash
cd "/Users/santhosh/Desktop/All Folders/autism-detector/backend"

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python main.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Terminal 2 - Frontend

```bash
cd "/Users/santhosh/Desktop/All Folders/autism-detector/frontend"

# Install dependencies
npm install

# Start dev server
npm run dev
```

You should see:
```
➜ Local: http://localhost:3000/
```

### Browser

Open: `http://localhost:3000`

---

## 🎯 Expected Screen

You should see a welcome page that says:
- ✅ Autism Emotion Detection System
- ✅ Backend Connected
- Upload Video section
- API Documentation button

---

## 🆘 If Something Goes Wrong

### Backend won't start - Python/pip issue?

Replace the entire `requirements.txt` content with:
```
fastapi==0.104.1
uvicorn==0.24.0
python-multipart==0.0.6
opencv-python==4.8.1.78
mediapipe==0.10.33
numpy==1.24.3
torch==2.0.1
scipy==1.11.4
scikit-learn==1.3.2
pydantic==2.5.0
aiofiles==23.2.1
```

Then try installing again:
```bash
pip install -r requirements.txt
```

### Frontend won't start - Node issue?

Clear and reinstall:
```bash
cd frontend
rm -rf node_modules
npm install
npm run dev
```

### Getting "port already in use" error?

Kill the process using that port:
```bash
# For port 8000 (backend)
lsof -i :8000
kill -9 <PID>

# For port 3000 (frontend)
lsof -i :3000
kill -9 <PID>
```

---

## ✅ Success Checklist

- [ ] Terminal 1 shows "Uvicorn running on http://0.0.0.0:8000"
- [ ] Terminal 2 shows "➜ Local: http://localhost:3000/"
- [ ] Browser loads http://localhost:3000 with welcome page
- [ ] Welcome page says "✅ Backend Connected"

---

**If all ✅, you're ready to upload videos!**

