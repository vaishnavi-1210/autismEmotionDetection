# 🚀 AutismIQ - Startup Guide & Verification

## ✅ Pre-Startup Checklist

### Backend Requirements
- [x] Python 3.8+ installed
- [x] Virtual environment: `./venv/Scripts/activate` (Windows)
- [x] Dependencies installed: `pip install -r backend/requirements.txt`
- [x] SEH models present:
  - ✅ `SEH backend code/triple_fusion_hgnn_final.pth`
  - ⚠️ BiLSTM models (optional - system uses untrained fallback)
    - `bilstm_skeleton_model.pth`
    - `bilstm_gaze_model.pth`
    - `bilstm_head_model.pth`

### Frontend Requirements
- [x] Node.js 16+ installed
- [x] npm dependencies: `npm install` (in `/frontend` directory)
- [x] Vite dev server configured

### Data Directory Structure
```
data/
├── uploads/          # Uploaded videos
├── processed/        # Extracted coordinates.json
├── features/         # Intermediate feature vectors (.npy)
├── results/          # Final predictions.json
└── sessions/         # metadata.json
```

---

## 🎯 Running the System

### Terminal 1: Backend API
```bash
cd backend
.\venv\Scripts\activate
python main.py
```
Expected: `Uvicorn running on http://0.0.0.0:8000`

### Terminal 2: Frontend Dev Server
```bash
cd frontend
npm run dev
```
Expected: `VITE v7.0.0 ready in XXX ms`
Open: http://localhost:5173

### Terminal 3: Health Check
```bash
curl http://localhost:8000/api/v1/health
```
Expected: `{"status":"healthy","timestamp":"...","data_dir":"..."}`

---

## 🔍 Testing the Full Pipeline

### 1. Manual API Test
```bash
# Upload a video
curl -X POST -F "file=@test_video.mp4" \
  http://localhost:8000/api/v1/upload

# Response:
# {
#   "session_id": "uuid-string",
#   "status": "processing"
# }
```

### 2. Check Processing Status
```bash
curl http://localhost:8000/api/v1/status/{session_id}

# Response shows:
# - status: uploading → processing → completed/failed
# - progress: 0-100 (if implemented)
# - current_stage: "Extracting Landmarks" etc.
```

### 3. Get Results
```bash
curl http://localhost:8000/api/v1/results/{session_id}

# Response:
# {
#   "emotion_class": "IM" | "TT" | "JA",
#   "confidence_scores": {"IM": 0.45, "TT": 0.35, "JA": 0.20},
#   "timestamp": "2026-04-07T...",
#   ...
# }
```

### 4. Download Artifacts
```bash
# Raw coordinates (landmarks)
curl http://localhost:8000/api/v1/coordinates/{session_id} > coords.json

# Intermediate features (256D vectors)
curl http://localhost:8000/api/v1/features/{session_id} > features.zip

# Export results
curl "http://localhost:8000/api/v1/export/{session_id}?format=csv" > results.csv
```

---

## 📊 Expected Workflow Output

### Phase 1: Coordinate Extraction
```
[session-id] AutismIQ: Starting coordinate extraction...
[session-id] Coordinate extraction finished in 5.23s
```
**Output**: `data/processed/{session_id}/coordinates.json`

### Phase 2: Feature Extraction (3 Modalities)
```
[session-id] AutismIQ: Starting modular feature extraction chain...
[session-id] Processing Skeleton
[session-id] Processing Eye Gaze
[session-id] Processing Head Gaze
[session-id] Feature chain completed in 8.45s
```
**Output**: `data/features/{session_id}/{{skel,eye,head}_feat.npy}`

### Phase 3: Classification (HGNN)
```
[session-id] AutismIQ: Starting standalone HGNN classification...
[session-id] AutismIQ Analysis Successful: IM
```
**Output**: `data/results/{session_id}/prediction.json`

---

## 🐛 Common Issues & Fixes

### Issue: "ModuleNotFoundError: No module named 'torch'"
**Fix**: `pip install torch` (or use `requirements.txt`)

### Issue: "CUDA out of memory"
**Fix**: Model runs on CPU by default. If needed, change `torch.device("cpu")` → CUDA in maam_compat.py:108

### Issue: "Coordinates file not found"
**Fix**: Ensure MediaPipe subprocess completed. Check `data/processed/{session_id}/extraction_error.txt`

### Issue: "BiLSTM models not found" (⚠️ Expected for now)
**Fix**: System uses untrained models and returns dummy 256D vectors. Download actual models and place in `SEH backend code/`

### Issue: Frontend blank page
**Fix**:
1. Check browser console for errors
2. Verify backend is running: `curl http://localhost:8000/api/v1/health`
3. Check CORS: Backend allows all origins in main.py:28-34

---

## 📝 Presentation Checklist

- [x] Backend API fully functional (routes, error handling)
- [x] Frontend dashboard loads and accepts uploads
- [x] Processing pipeline executes all 4 phases
- [x] Results display emotion classification + confidence scores
- [x] Data export (coordinates, features, predictions) works
- [x] Error handling and progress tracking implemented
- ⚠️ BiLSTM models (demo with untrained model fallback)

---

## 🎬 Demo Script (10-min Presentation)

1. **Show startup**
   - Start backend & frontend
   - Show health check passing

2. **Upload video**
   - Drag-drop or select a video in UI
   - Show real-time progress

3. **Explain pipeline**
   - Extraction: "MediaPipe extracts pose + gaze"
   - Features: "3 modalities (skeleton, eye, head) → 256D each"
   - Fusion: "Concatenate → 768D vector"
   - Classification: "HGNN predicts emotion class"

4. **Show results**
   - Display emotion class (IM/TT/JA)
   - Show confidence scores
   - Export raw data for research

5. **Discuss open source/research angle**
   - Clear code structure
   - Modular pipeline
   - Reproducible results

---

## 🔗 Quick Links
- 📁 Project: `d:/Projects/autismEmotionDetection`
- 🔧 Config: `backend/config.py`
- 🧠 Models: `SEH backend code/`
- 📚 API Docs: http://localhost:8000/docs (SwaggerUI)
- 🌐 Frontend: http://localhost:5173

---

**Last Updated**: April 7, 2026
**Status**: ✅ Ready for presentation (awaiting BiLSTM model files for full accuracy)
