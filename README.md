# autismEmotionDetection

Simple web app to upload a video, process it, and view behavior/emotion analysis results.

## Run the App (2 Terminals)

Use these exact commands on Windows.

Terminal 1 (Backend)
1. cd d:\Projects\autismEmotionDetection
2. d:/Projects/autismEmotionDetection/.venv/Scripts/python.exe backend/main.py

Terminal 2 (Frontend)
1. cd d:\Projects\autismEmotionDetection\frontend
2. npm run dev

Open in browser:
http://localhost:3000/

Backend API:
http://localhost:8000/

Health check:
http://localhost:8000/api/v1/health

## Workflow by Tech (Simple, No Model Internals)

1. User uploads video in the React + TypeScript UI (using react-dropzone).
2. Frontend sends the file to FastAPI backend endpoints.
3. FastAPI receives upload (python-multipart), creates a session, and stores files in data folders.
4. Backend processing runs video and feature pipeline (OpenCV, MediaPipe, NumPy, PyTorch, SciPy, scikit-learn, pandas, matplotlib, seaborn, Pillow).
5. Backend keeps writing progress/status updates to session metadata (JSON in data/sessions).
6. Frontend polls status and then fetches final result/animation from backend APIs.
7. User sees final output and can open/download animation and exports.

## Tech Used in This Project (Exact)

Frontend (used)
- React 18
- TypeScript 5
- Vite 7
- Material UI (@mui/material)
- Emotion (@emotion/react, @emotion/styled)
- react-dropzone

Backend/API (used)
- Python (.venv)
- FastAPI
- Uvicorn
- pydantic
- python-multipart
- aiofiles
- python-dotenv

Video/Processing libs (used)
- opencv-python
- mediapipe
- numpy
- torch
- scipy
- scikit-learn
- pandas
- matplotlib
- seaborn
- Pillow

Storage (used)
- Local file-based storage in data/ folders (JSON, NPY, MP4)

## Folder Flow (High Level)

- data/uploads: input videos
- data/processed: processed intermediate outputs
- data/animations: final animation video per session
- data/features: extracted feature files
- data/results: final prediction JSON
- data/sessions: metadata and progress tracking

## Future Scaling Plan (Simple)

1. Move from local data folders to shared/object storage.
2. Add queue + worker setup so multiple videos process in parallel.
3. Use a database for sessions/status instead of JSON-only metadata.
4. Add auth and multi-user workspace/project support.
5. Add monitoring, logs, retries, and alerts for stability.
6. Containerize frontend/backend/workers and deploy with autoscaling.
7. Add API versioning and rate limits for production clients.
