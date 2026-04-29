# Autism Emotion Detection

A comprehensive web application designed to analyze video inputs for behavior and emotion detection. The system leverages state-of-the-art computer vision models, including OpenCV and MediaPipe, processed through a robust PyTorch AI pipeline to extract insights, visualizing them in an intuitive React frontend.

## 🛠️ Prerequisites

Before you start, make sure you have the following installed on your Windows system:
- **[Python 3.10+](https://www.python.org/downloads/)**
- **[Node.js 18+](https://nodejs.org/en/)** and **npm**

*Note: You do not need to download the .venv or 
ode_modules folders. The steps below will generate them for you automatically.*

---

## 🚀 Running the App in VS Code (Windows)

The easiest way to run this on Windows is by using the integrated terminal in VS Code.

### Step 1: Open Terminal 1 (Backend)

Open VS Code, press ` Ctrl +  ` to open the terminal (or go to **Terminal > New Terminal** from the top menu). Ensure it is a **PowerShell** terminal.

1. Create your secure virtual environment (only do this the first time):
   `powershell
   python -m venv .venv
   `
2. Activate the environment:
   `powershell
   .\.venv\Scripts\Activate.ps1
   `
3. Install the required Python packages (only do this the first time):
   `powershell
   pip install -r backend/requirements.txt
   `
4. Start the backend Server:
   `powershell
   python backend/main.py
   `
*The backend API is now running on http://localhost:8000/*

### Step 2: Open Terminal 2 (Frontend)

Click the **+** icon in the VS Code terminal panel to open a **second** terminal tab.

1. Navigate to the frontend folder:
   `powershell
   cd frontend
   `
2. Install the necessary Node packages (only do this the first time):
   `powershell
   npm install
   `
3. Start the React frontend:
   `powershell
   npm run dev
   `

*The frontend React app is now running! Open your browser and visit **http://localhost:3000** to use the application.*

---

## 📁 System Architecture & Technologies

- **Frontend:** React 18, Vite 7, TypeScript, Material UI
- **Backend API:** FastAPI, Uvicorn, Python 3
- **AI & Data Processing:** OpenCV, MediaPipe, PyTorch, Scikit-learn, NumPy
