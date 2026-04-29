# Autism Emotion Detection

A comprehensive web application designed to analyze video inputs for behavior and emotion detection. The system leverages state-of-the-art computer vision models, including OpenCV and MediaPipe, processed through a robust PyTorch AI pipeline to extract insights, visualizing them in an intuitive React frontend.

## 🚀 Features
- **Video Upload & Processing:** Drag-and-drop React UI for capturing user videos.
- **Advanced AI Pipeline:** Facial, spatial (skeleton), and coordinate extraction via MediaPipe and OpenCV.
- **Deep Learning Inference:** Fused Bi-LSTM models and HGNN models built in PyTorch for precise behavioral and emotional analysis.
- **Real-time Status Polling:** View the progress of the automated backend pipeline natively on the frontend.
- **2D Animation & Export:** Auto-generates diagnostic animations (skeletal and facial markers) and result exports.

---

## 🛠️ Prerequisites

Before you start, make sure you have the following installed on your system:
- **[Python 3.10+](https://www.python.org/downloads/)** (Backend processing and AI models)
- **[Node.js 18+](https://nodejs.org/en/)** and **npm** access (Frontend interface)

> **Important note on Virtual Environments**: You should **never** commit or share the \.venv\ or ode_modules\ folder. They are platform-specific (Windows vs Mac vs Linux) and contain large compiled binaries. Follow the instructions below to easily recreate exactly the same environment on any computer!

---

## ⚙️ Installation & Setup

We recommend running the application using two separate terminals—one for the FastAPI backend and one for the React frontend.

### 1. Setting up the Backend
The backend runs on Python and FastAPI. We will set up a virtual environment and install dependencies.

1. Open **Terminal 1** and navigate to the project root directory:
   \\ash
   cd path/to/autismEmotionDetection
   \2. Create a Python virtual environment:
   \\ash
   # Windows
   python -m venv .venv
   
   # macOS/Linux
   python3 -m venv .venv
   \3. Activate the virtual environment:
   \\ash
   # Windows (Command Prompt)
   .venv\Scripts\activate.bat
   
   # Windows (PowerShell)
   .\.venv\Scripts\Activate.ps1
   
   # macOS/Linux
   source .venv/bin/activate
   \4. Install all required dependencies from equirements.txt\:
   \\ash
   pip install -r backend/requirements.txt
   \
### 2. Setting up the Frontend
The frontend runs on React and Vite.

1. Open **Terminal 2** and navigate to the frontend directory:
   \\ash
   cd path/to/autismEmotionDetection/frontend
   \2. Install the necessary Node packages:
   \\ash
   npm install
   \
---

## 🏃‍♂️ Running the Application

Once both environments are correctly set up, start up the local servers!

**Terminal 1 (Backend):**
With your \.venv\ activated in the project root folder:
\\ash
python backend/main.py
\*(The backend API will run on \http://localhost:8000/\)*

**Terminal 2 (Frontend):**
From within the \rontend\ directory:
\\ash
npm run dev
\*(The frontend React app will be accessible at \http://localhost:3000/\)*

You're done! Visit **http://localhost:3000** in your browser to start using the app.

---

## 📁 System Architecture & Technologies

### Frontend
- **Framework:** React 18, Vite 7, TypeScript 5
- **UI & Styling:** Material UI (\@mui/material\), Emotion
- **Upload Component:** eact-dropzone
### Backend API
- **Framework:** FastAPI, Uvicorn, Python 3
- **Data Parsing:** Pydantic, Python-Multipart

### AI & Data Processing
- **Computer Vision:** OpenCV (\opencv-python\), MediaPipe
- **Machine Learning:** PyTorch, Scikit-learn, NumPy, SciPy
- **Visualization:** Matplotlib, Seaborn, Pillow

---

## 📂 Project Structure

- \ackend/\: Core FastAPI server, AI model integration, and MediaPipe feature extraction scripts.
- \rontend/\: React SPA configuration and source code.
- \data/\: Local file storage directory for uploads, intermediate processed outputs, extracted coordinate features, and final diagnostic results.
- \docs/\: Setup guides, PRDs, bugfix logs, and presentation materials.

---

## 🔮 Future Roadmap
1. Cloud storage integration (S3/GCS) to replace local file-system.
2. Background task queues (Celery/Redis) for parallel video processing.
3. Persistent relational database mapping for user/session continuity.
