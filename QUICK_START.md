# Quick Start Guide - Autism Emotion Detection System

## Prerequisites

- Python 3.8+ (your .venv directory has Python 3.14.3)
- Node.js 16+ (for frontend)
- FFmpeg (for video processing) - optional but recommended

## Installation (One-Time Setup)

### Option 1: Automated Setup (Recommended)

**macOS/Linux:**
```bash
cd /Users/santhosh/Desktop/All\ Folders/autism-detector
chmod +x setup.sh
./setup.sh
```

**Windows:**
```cmd
cd "C:\Users\santhosh\Desktop\All Folders\autism-detector"
setup.bat
```

### Option 2: Manual Setup

#### Backend Setup

```bash
cd backend
pip install -r requirements.txt
```

#### Frontend Setup

```bash
cd frontend
npm install
```

## Running the Application

### Terminal 1: Start Backend Server

```bash
cd backend
python main.py
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

**Backend URL**: http://localhost:8000
**API Docs**: http://localhost:8000/docs

### Terminal 2: Start Frontend Server

```bash
cd frontend
npm run dev
```

Expected output:
```
  VITE v5.0.0  ready in XXX ms

  ➜  Local:   http://localhost:3000/
```

**Frontend URL**: http://localhost:3000

## Usage - Step by Step

1. **Open Browser**: Navigate to `http://localhost:3000`

2. **Upload Video**:
   - Click the upload area or drag & drop a video file
   - Supported formats: MP4, AVI, MOV, MKV
   - Max size: 500 MB
   - Max duration: 10 minutes

3. **Processing**:
   - System processes video through 4 stages
   - Real-time progress updates
   - Takes 2-5 minutes depending on video length

4. **View Results**:
   - Detected emotion is displayed prominently
   - View confidence scores for all emotion classes
   - See processing metadata and timing

5. **Export Results**:
   - Download results as JSON or CSV
   - Results are stored locally for future reference

6. **Session History**:
   - View all previous analysis sessions
   - Re-run analyses or delete old sessions

## API Endpoints Quick Reference

### Video Processing
```
POST   /api/v1/upload              - Upload video
POST   /api/v1/process/{id}        - Start processing
GET    /api/v1/status/{id}         - Check status
GET    /api/v1/results/{id}        - Get results
```

### Session Management
```
GET    /api/v1/sessions            - List all sessions
GET    /api/v1/session/{id}        - Get session details
DELETE /api/v1/session/{id}        - Delete session
```

### Data Export
```
GET    /api/v1/export/{id}?format=json    - Export as JSON
GET    /api/v1/export/{id}?format=csv     - Export as CSV
```

### Other
```
GET    /api/v1/health              - Health check
GET    /docs                        - API documentation (Swagger UI)
GET    /redoc                       - API documentation (ReDoc)
```

## Project Structure

```
backend/
├── main.py              # FastAPI application with endpoints
├── config.py            # Configuration settings
├── models.py            # Pydantic models for API
├── utils.py             # Utility functions
├── processing.py        # Video processing pipeline
└── requirements.txt     # Python dependencies

frontend/
├── src/
│   ├── components/      # React components
│   ├── services/        # API services
│   ├── types/           # TypeScript types
│   ├── App.tsx          # Main app component
│   └── main.tsx         # Entry point
├── package.json         # Node dependencies
├── vite.config.ts       # Vite configuration
└── tsconfig.json        # TypeScript configuration

data/
├── uploads/             # Uploaded videos
├── processed/          # Extracted coordinates
├── features/           # Preprocessed features
├── results/            # Prediction results
├── sessions/           # Session metadata
└── models/             # Model files
```

## Troubleshooting

### Backend won't start
- Check Python version: `python --version` (need 3.8+)
- Check port 8000 is free: `lsof -i :8000`
- Install dependencies: `pip install -r requirements.txt`

### Frontend won't load
- Check Node.js: `node --version` (need 16+)
- Clear cache: `rm -rf node_modules && npm install`
- Check port 3000 is free: `lsof -i :3000`

### Processing fails
- Ensure video has clear face/body visible
- Check disk space (need ~10GB for processing)
- Check RAM (need 8GB minimum)
- Review backend logs for specific error

### Model not loading
- Verify `triple_fusion_hgnn_final.pth` exists in `SEH backend code/`
- PyTorch should auto-download on first use

## Testing the System

1. Create a test video or use provided test video
2. Upload through the web interface
3. Monitor backend logs for processing stages
4. View results in the web interface
5. Download and verify exported JSON/CSV

## Performance Tips

1. Use SSD drives for faster I/O
2. Close other applications during processing
3. Use MP4 with H.264 codec (most efficient)
4. GPU not required but speeds up processing

## File Organization

All data is stored locally in `/data/` directory:

- **uploads/**: Raw video files
- **processed/**: Extracted coordinates in JSON
- **features/**: Preprocessed numpy arrays
- **results/**: Final emotion predictions
- **sessions/**: Session metadata and tracking

## Common Tasks

### View Processing Logs (Backend)
Check the terminal where backend is running for real-time logs.

### Access API Documentation
Open browser to `http://localhost:8000/docs` for interactive Swagger UI

### Stop Services
press `Ctrl+C` in each terminal

### Clear Old Sessions
Delete folders in `/data/uploads/`, `/data/processed/`, etc.

### Reset Data
```bash
rm -rf data/uploads/* data/processed/* data/features/* data/results/
```

## Next Steps

- Explore the API with Swagger UI: http://localhost:8000/docs
- Upload and process test videos
- Check results and export data
- Review backend logs for processing details
- Refer to full README.md for advanced configuration

## Support

Refer to README.md for:
- Detailed API documentation
- Advanced configuration options
- Performance tuning
- Security considerations
- Future enhancement plans

---

**Status**: ✅ Ready to Use  
**Version**: 1.0.0  
**Last Updated**: April 6, 2026
