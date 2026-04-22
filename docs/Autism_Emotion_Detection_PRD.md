# Product Requirements Document (PRD)
## Autism Emotion Detection System

---

### Document Information
- **Product Name**: Autism Emotion Detection System
- **Version**: 1.0
- **Date**: April 6, 2026
- **Author**: Product Team
- **Status**: Draft

---

## 1. Executive Summary

### 1.1 Product Overview
A specialized application designed to detect and classify emotions in individuals with autism through video analysis. The system processes uploaded videos through multiple modalities (eye movement, skeletal structure, head movements) and uses deep learning models (BiLSTM + HGNN) to classify emotions into three distinct categories.

### 1.2 Problem Statement
Traditional emotion detection systems are not optimized for individuals with autism who may express emotions differently. There is a need for a specialized, multi-modal approach that can accurately detect and classify emotions for autism-specific behavioral analysis, therapy, and research purposes.

### 1.3 Target Users
- **Primary**: Therapists, behavioral analysts, and researchers working with autism patients
- **Secondary**: Special education teachers, caregivers, and clinical psychologists
- **Tertiary**: Parents monitoring progress in home settings

---

## 2. Goals & Objectives

### 2.1 Business Goals
- Provide accurate emotion detection for autism-specific behavioral patterns
- Enable non-invasive emotion analysis through video processing
- Support therapeutic interventions with data-driven insights
- Facilitate research in autism emotion recognition

### 2.2 Success Metrics
- **Accuracy**: Model prediction accuracy ≥ 85% on test dataset
- **Processing Time**: < 5 minutes for a 2-minute video
- **User Satisfaction**: > 80% user satisfaction score
- **Reliability**: System uptime > 95%
- **Usability**: Users can complete full workflow within 10 minutes (first-time use)

---

## 3. User Stories & Use Cases

### 3.1 Primary User Stories

**US-001: Video Upload**
> As a therapist, I want to upload a video of my patient so that I can analyze their emotional responses during therapy sessions.

**US-002: Real-time Processing Feedback**
> As a researcher, I want to see the processing status in real-time so that I know when results will be available.

**US-003: Emotion Classification Results**
> As a behavioral analyst, I want to see the classified emotion with confidence scores so that I can validate the system's output.

**US-004: Historical Analysis**
> As a caregiver, I want to view past analysis results so that I can track emotional patterns over time.

**US-005: Export Results**
> As a researcher, I want to export results in JSON/CSV format so that I can perform additional statistical analysis.

### 3.2 Use Case: Complete Emotion Analysis Workflow

```
Actor: Therapist
Precondition: User has a video file of patient interaction
Main Flow:
1. User navigates to the application
2. User uploads video file (drag-and-drop or file selector)
3. System validates video format and size
4. User initiates processing
5. System extracts coordinate data from video
6. System preprocesses three modalities (eye, skeleton, head)
7. System passes preprocessed data through BiLSTM for feature extraction
8. System feeds extracted features to HGNN model
9. System classifies emotion into one of three classes
10. System displays results with visualization
11. User reviews results and exports data
Postcondition: Emotion classification is stored and available for review
Alternative Flows:
- 3a. Invalid video format: System shows error and format requirements
- 6a. Processing fails: System shows error and retry option
```

---

## 4. Functional Requirements

### 4.1 Video Upload Module (FR-VU)

**FR-VU-001**: System SHALL accept video uploads via drag-and-drop interface  
**FR-VU-002**: System SHALL support the following video formats: MP4, AVI, MOV, MKV  
**FR-VU-003**: System SHALL validate video file size (max: 500 MB)  
**FR-VU-004**: System SHALL validate video duration (max: 10 minutes)  
**FR-VU-005**: System SHALL display upload progress indicator  
**FR-VU-006**: System SHALL generate unique session ID for each upload  
**FR-VU-007**: System SHALL store uploaded videos in local filesystem (`/data/uploads/{session_id}/`)

### 4.2 Coordinate Extraction Module (FR-CE)

**FR-CE-001**: System SHALL process uploaded video to extract emotion coordinates  
**FR-CE-002**: System SHALL output coordinate data in JSON format  
**FR-CE-003**: JSON output SHALL contain frame-by-frame coordinate information  
**FR-CE-004**: System SHALL store coordinate JSON in `/data/processed/{session_id}/coordinates.json`  
**FR-CE-005**: System SHALL handle processing errors gracefully with user notification

### 4.3 Modality Preprocessing Module (FR-MP)

**FR-MP-001**: System SHALL preprocess eye movement data from coordinate JSON  
**FR-MP-002**: System SHALL preprocess skeleton structure data from coordinate JSON  
**FR-MP-003**: System SHALL preprocess head movement data from coordinate JSON  
**FR-MP-004**: Each modality preprocessor SHALL normalize data to standard format  
**FR-MP-005**: System SHALL validate preprocessed data before passing to BiLSTM  
**FR-MP-006**: System SHALL store preprocessed features in `/data/features/{session_id}/`

### 4.4 BiLSTM Feature Extraction Module (FR-FE)

**FR-FE-001**: System SHALL load pre-trained BiLSTM model weights  
**FR-FE-002**: System SHALL process each of the 3 modality inputs through BiLSTM  
**FR-FE-003**: BiLSTM SHALL extract temporal features from sequence data  
**FR-FE-004**: System SHALL concatenate/combine features from all 3 modalities  
**FR-FE-005**: System SHALL handle variable-length video sequences  
**FR-FE-006**: Extracted features SHALL be stored for HGNN input

### 4.5 HGNN Classification Module (FR-CL)

**FR-CL-001**: System SHALL load pre-trained HGNN model weights  
**FR-CL-002**: HGNN SHALL accept combined features from BiLSTM as input  
**FR-CL-003**: HGNN SHALL classify emotion into one of 3 predefined classes  
**FR-CL-004**: System SHALL output classification result with confidence scores  
**FR-CL-005**: System SHALL store prediction results in `/data/results/{session_id}/prediction.json`

### 4.6 Results Display Module (FR-RD)

**FR-RD-001**: System SHALL display emotion classification result prominently  
**FR-RD-002**: System SHALL show confidence scores for each of the 3 classes  
**FR-RD-003**: System SHALL display processing metadata (duration, timestamp)  
**FR-RD-004**: System SHALL visualize emotion timeline if applicable  
**FR-RD-005**: System SHALL allow users to view uploaded video alongside results  
**FR-RD-006**: System SHALL provide export functionality (JSON, CSV formats)

### 4.7 Session Management (FR-SM)

**FR-SM-001**: System SHALL create unique session for each video upload  
**FR-SM-002**: System SHALL track processing status (uploaded, processing, completed, failed)  
**FR-SM-003**: System SHALL store session metadata (timestamp, filename, status)  
**FR-SM-004**: System SHALL allow users to view past sessions  
**FR-SM-005**: System SHALL implement session cleanup after 30 days (configurable)

### 4.8 Error Handling (FR-EH)

**FR-EH-001**: System SHALL display user-friendly error messages  
**FR-EH-002**: System SHALL log detailed errors for debugging  
**FR-EH-003**: System SHALL provide retry mechanism for failed processing  
**FR-EH-004**: System SHALL validate all inputs before processing  
**FR-EH-005**: System SHALL handle model loading failures gracefully

---

## 5. Non-Functional Requirements

### 5.1 Performance (NFR-P)

**NFR-P-001**: Video upload SHALL complete within 30 seconds for 100MB file  
**NFR-P-002**: Coordinate extraction SHALL process 1-minute video in < 2 minutes  
**NFR-P-003**: Complete pipeline (upload to result) SHALL finish in < 5 minutes for 2-minute video  
**NFR-P-004**: UI SHALL respond to user interactions within 200ms  
**NFR-P-005**: System SHALL support processing of videos up to 1080p resolution

### 5.2 Scalability (NFR-S)

**NFR-S-001**: System SHALL handle 10 concurrent sessions  
**NFR-S-002**: Local storage SHALL support minimum 100GB of data  
**NFR-S-003**: System SHALL implement queue mechanism for multiple uploads

### 5.3 Reliability (NFR-R)

**NFR-R-001**: System uptime SHALL be ≥ 95%  
**NFR-R-002**: Data loss probability SHALL be < 0.1%  
**NFR-R-003**: System SHALL auto-save processing state every 30 seconds  
**NFR-R-004**: System SHALL recover from crashes without data corruption

### 5.4 Usability (NFR-U)

**NFR-U-001**: First-time users SHALL complete workflow within 10 minutes  
**NFR-U-002**: UI SHALL follow accessibility standards (WCAG 2.1 Level AA)  
**NFR-U-003**: Error messages SHALL be clear and actionable  
**NFR-U-004**: System SHALL provide contextual help/tooltips  
**NFR-U-005**: Interface SHALL be intuitive without requiring extensive training

### 5.5 Security & Privacy (NFR-SP)

**NFR-SP-001**: All video data SHALL be stored locally (no cloud transmission)  
**NFR-SP-002**: System SHALL not require internet connectivity for core functionality  
**NFR-SP-003**: Uploaded videos SHALL be encrypted at rest (AES-256)  
**NFR-SP-004**: System SHALL implement file access permissions  
**NFR-SP-005**: Session data SHALL be anonymized (no PII in filenames/logs)  
**NFR-SP-006**: System SHALL comply with HIPAA guidelines for healthcare data

### 5.6 Maintainability (NFR-M)

**NFR-M-001**: Code SHALL follow PEP 8 (Python) and ESLint (JavaScript) standards  
**NFR-M-002**: All modules SHALL have comprehensive documentation  
**NFR-M-003**: System SHALL support model updates without code changes  
**NFR-M-004**: Logging SHALL capture sufficient detail for debugging  
**NFR-M-005**: Configuration SHALL be externalized (config files, not hardcoded)

### 5.7 Compatibility (NFR-C)

**NFR-C-001**: Frontend SHALL support Chrome 90+, Firefox 88+, Safari 14+, Edge 90+  
**NFR-C-002**: Backend SHALL run on Python 3.8+  
**NFR-C-003**: System SHALL support Windows 10+, macOS 11+, Ubuntu 20.04+  
**NFR-C-004**: System SHALL work on machines with minimum 8GB RAM, 4-core CPU

---

## 6. Technical Architecture

### 6.1 Technology Stack

#### Frontend
- **Framework**: React.js 18+ with TypeScript
- **UI Library**: Material-UI (MUI) v5
- **Video Handling**: react-dropzone, React Player
- **Visualization**: Recharts / Chart.js
- **State Management**: React Context API / Redux Toolkit
- **Build Tool**: Vite

#### Backend
- **Framework**: FastAPI (Python 3.8+)
- **Web Server**: Uvicorn (ASGI server)
- **API Documentation**: Auto-generated Swagger/OpenAPI

#### ML/Processing
- **Deep Learning**: PyTorch 2.0+ or TensorFlow 2.x
- **Video Processing**: OpenCV (cv2)
- **Numerical Computing**: NumPy, Pandas
- **Landmark Detection**: MediaPipe (if applicable)
- **Preprocessing**: scikit-learn

#### Storage
- **File System**: Local directory structure
- **Session Tracking**: File-based or Redis (optional)
- **Data Format**: JSON for intermediate outputs

#### Communication
- **Real-time Updates**: WebSockets (Socket.IO) or Server-Sent Events
- **API Protocol**: RESTful HTTP/HTTPS

#### Development & Deployment
- **Reverse Proxy**: Nginx
- **Process Management**: Supervisor / systemd
- **Environment**: Python venv / conda

### 6.2 System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (React)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Video Upload │  │   Progress   │  │   Results    │      │
│  │   Component  │  │   Monitor    │  │   Display    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                   REST API / WebSocket
                              │
┌─────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              API Endpoints & Routing                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                              │                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │             Processing Pipeline Manager               │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌──────────────────┐   ┌──────────────┐
│   Coordinate  │   │    Modality      │   │   BiLSTM     │
│  Extraction   │──▶│  Preprocessing   │──▶│   Feature    │
│    Module     │   │  (Eye/Skeleton/  │   │  Extraction  │
│               │   │     Head)        │   │              │
└───────────────┘   └──────────────────┘   └──────────────┘
                                                   │
                                                   ▼
                                           ┌──────────────┐
                                           │     HGNN     │
                                           │    Model     │
                                           │ (Pre-trained)│
                                           └──────────────┘
                                                   │
                                                   ▼
                                           ┌──────────────┐
                                           │   Emotion    │
                                           │Classification│
                                           │  (3 Classes) │
                                           └──────────────┘
```

### 6.3 Data Flow

```
1. Video Upload (MP4/AVI/MOV)
   ↓
2. Save to /data/uploads/{session_id}/video.mp4
   ↓
3. Coordinate Extraction
   → Output: /data/processed/{session_id}/coordinates.json
   ↓
4. Modality Preprocessing (Parallel)
   ├─ Eye Movement Features
   ├─ Skeleton Features
   └─ Head Movement Features
   → Output: /data/features/{session_id}/modality_*.npy
   ↓
5. BiLSTM Feature Extraction (Sequential)
   → Combined Features Vector
   ↓
6. HGNN Model Inference
   → Emotion Classification Probabilities
   ↓
7. Result Generation
   → Output: /data/results/{session_id}/prediction.json
   {
     "session_id": "uuid",
     "timestamp": "ISO-8601",
     "emotion_class": "Class_A",
     "confidence_scores": {
       "Class_A": 0.85,
       "Class_B": 0.10,
       "Class_C": 0.05
     },
     "processing_time": 245.3
   }
   ↓
8. Display Results to User
```

### 6.4 File System Structure

```
/data/
├── uploads/
│   └── {session_id}/
│       └── video.mp4
├── processed/
│   └── {session_id}/
│       └── coordinates.json
├── features/
│   └── {session_id}/
│       ├── eye_features.npy
│       ├── skeleton_features.npy
│       └── head_features.npy
├── results/
│   └── {session_id}/
│       └── prediction.json
├── sessions/
│   └── metadata.json
└── models/
    ├── bilstm_model.pth
    └── hgnn_model.pth
```

### 6.5 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/upload` | Upload video file |
| GET | `/api/v1/sessions` | List all sessions |
| GET | `/api/v1/session/{id}` | Get session details |
| POST | `/api/v1/process/{id}` | Start processing pipeline |
| GET | `/api/v1/status/{id}` | Get processing status |
| GET | `/api/v1/results/{id}` | Get prediction results |
| GET | `/api/v1/export/{id}` | Export results (JSON/CSV) |
| DELETE | `/api/v1/session/{id}` | Delete session data |
| WS | `/ws/status/{id}` | WebSocket for real-time updates |

---

## 7. User Interface Requirements

### 7.1 Main Dashboard
- **Header**: Application title, navigation menu
- **Upload Section**: Drag-and-drop area with file selector button
- **Session List**: Table/cards showing recent sessions with status
- **Quick Stats**: Total sessions, average processing time

### 7.2 Upload Screen
- **Drag-and-Drop Zone**: Visual feedback on hover
- **File Selector Button**: Alternative upload method
- **Video Preview**: Show uploaded video before processing
- **File Info**: Display filename, size, duration, format
- **Action Buttons**: "Process Video", "Cancel"

### 7.3 Processing Screen
- **Progress Indicator**: Multi-stage progress bar
  - Stage 1: Coordinate Extraction
  - Stage 2: Modality Preprocessing
  - Stage 3: Feature Extraction (BiLSTM)
  - Stage 4: Emotion Classification (HGNN)
- **Status Messages**: Real-time updates on current stage
- **Estimated Time**: Remaining time calculation
- **Cancel Button**: Ability to abort processing

### 7.4 Results Screen
- **Primary Result Card**: 
  - Detected emotion (large, prominent)
  - Confidence score (percentage)
  - Timestamp of analysis
- **Confidence Breakdown**:
  - Bar chart showing scores for all 3 classes
- **Video Playback**:
  - Uploaded video with playback controls
  - Optional: Overlay emotion annotations on timeline
- **Metadata Panel**:
  - Session ID
  - Upload time
  - Processing duration
  - Video specifications
- **Export Options**:
  - Download JSON
  - Download CSV
  - Copy to clipboard
- **Actions**:
  - "Analyze Another Video"
  - "Delete Session"

### 7.5 Session History
- **Table View**:
  - Columns: Date, Filename, Emotion, Confidence, Status, Actions
  - Sortable and filterable
  - Pagination for large datasets
- **Search**: Filter by date range, emotion class, filename

### 7.6 Wireframe Descriptions

**Home Screen Layout:**
```
┌─────────────────────────────────────────────────────┐
│  Autism Emotion Detection System          [Menu]    │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────────────────────────────────────┐  │
│  │                                               │  │
│  │      Drag & Drop Video Here                  │  │
│  │           or click to browse                 │  │
│  │                                               │  │
│  │       Supported: MP4, AVI, MOV, MKV          │  │
│  │           Max size: 500 MB                   │  │
│  │                                               │  │
│  └──────────────────────────────────────────────┘  │
│                                                      │
│  Recent Sessions                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │ Date       | File      | Emotion | Confidence│  │
│  │────────────┼───────────┼─────────┼───────────│  │
│  │ Apr 6 2026 | video1... | Happy   | 85%       │  │
│  │ Apr 5 2026 | video2... | Neutral | 72%       │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

**Results Screen Layout:**
```
┌─────────────────────────────────────────────────────┐
│  ← Back to Dashboard                                │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────────┐  ┌─────────────────────────┐ │
│  │                  │  │  Detected Emotion:      │ │
│  │  Video Player    │  │                         │ │
│  │                  │  │      HAPPY              │ │
│  │  [▶ Play/Pause] │  │                         │ │
│  │                  │  │  Confidence: 85%        │ │
│  │                  │  │                         │ │
│  └──────────────────┘  └─────────────────────────┘ │
│                                                      │
│  Confidence Breakdown                                │
│  ┌──────────────────────────────────────────────┐  │
│  │ Happy    ████████████████████ 85%            │  │
│  │ Neutral  ████ 10%                            │  │
│  │ Sad      █ 5%                                │  │
│  └──────────────────────────────────────────────┘  │
│                                                      │
│  [Export JSON] [Export CSV] [Analyze Another]       │
└─────────────────────────────────────────────────────┘
```

---

## 8. Data Requirements

### 8.1 Input Data

**Video Specifications:**
- **Formats**: MP4 (H.264), AVI, MOV, MKV
- **Resolution**: 480p - 1080p
- **Duration**: 10 seconds - 10 minutes
- **Frame Rate**: 24-60 fps
- **File Size**: Max 500 MB

**Coordinate JSON Schema:**
```json
{
  "video_metadata": {
    "filename": "string",
    "duration": "number (seconds)",
    "fps": "number",
    "resolution": "WxH"
  },
  "frames": [
    {
      "frame_number": "integer",
      "timestamp": "number (seconds)",
      "coordinates": {
        "eye": {
          "left": {"x": "float", "y": "float"},
          "right": {"x": "float", "y": "float"}
        },
        "skeleton": {
          "keypoints": [
            {"joint": "string", "x": "float", "y": "float", "confidence": "float"}
          ]
        },
        "head": {
          "position": {"x": "float", "y": "float", "z": "float"},
          "rotation": {"pitch": "float", "yaw": "float", "roll": "float"}
        }
      }
    }
  ]
}
```

### 8.2 Output Data

**Prediction Result Schema:**
```json
{
  "session_id": "uuid-string",
  "timestamp": "ISO-8601 datetime",
  "video_filename": "string",
  "emotion_class": "string (one of 3 predefined classes)",
  "confidence_scores": {
    "class_1": "float (0-1)",
    "class_2": "float (0-1)",
    "class_3": "float (0-1)"
  },
  "processing_metadata": {
    "upload_time": "ISO-8601",
    "start_time": "ISO-8601",
    "end_time": "ISO-8601",
    "total_duration": "number (seconds)",
    "stages": {
      "coordinate_extraction": "number (seconds)",
      "preprocessing": "number (seconds)",
      "feature_extraction": "number (seconds)",
      "classification": "number (seconds)"
    }
  },
  "model_versions": {
    "bilstm": "string",
    "hgnn": "string"
  }
}
```

### 8.3 Session Metadata Schema
```json
{
  "session_id": "uuid",
  "created_at": "ISO-8601",
  "status": "uploaded | processing | completed | failed",
  "video_metadata": {
    "original_filename": "string",
    "file_size": "number (bytes)",
    "duration": "number (seconds)",
    "format": "string"
  },
  "result": {
    "emotion_class": "string",
    "confidence": "number"
  },
  "error": {
    "message": "string",
    "stack": "string"
  }
}
```

---

## 9. Model Requirements

### 9.1 BiLSTM Model Specifications
- **Input**: Preprocessed features from 3 modalities
- **Architecture**: Bidirectional LSTM layers
- **Output**: Extracted temporal features
- **Format**: PyTorch .pth or TensorFlow SavedModel
- **Location**: `/data/models/bilstm_model.pth`
- **Version Control**: Model version stored in metadata

### 9.2 HGNN Model Specifications
- **Input**: Combined features from BiLSTM
- **Architecture**: Hypergraph Neural Network
- **Output**: 3-class probability distribution
- **Format**: PyTorch .pth or TensorFlow SavedModel
- **Location**: `/data/models/hgnn_model.pth`
- **Classes**: 3 predefined emotion classes (to be specified)

### 9.3 Model Management
- **Loading**: Models loaded once at application startup
- **Updates**: Support for hot-swapping models without restart
- **Versioning**: Track model versions in predictions
- **Fallback**: Graceful degradation if model loading fails

---

## 10. Processing Pipeline Details

### 10.1 Stage 1: Coordinate Extraction
**Input**: Video file (MP4, AVI, MOV, MKV)  
**Process**:
- Extract frames from video
- Detect facial landmarks (eye positions)
- Detect skeletal keypoints
- Calculate head pose (position and rotation)
- Aggregate frame-by-frame coordinates

**Output**: coordinates.json  
**Duration**: ~1-2 minutes for 1-minute video

### 10.2 Stage 2: Modality Preprocessing
**Input**: coordinates.json  
**Process**:
- **Eye Modality**: Extract eye movement vectors, blink rate, gaze direction
- **Skeleton Modality**: Normalize joint positions, calculate motion vectors
- **Head Modality**: Extract head position changes, rotation angles

**Output**: 3 separate feature arrays  
**Duration**: ~30 seconds

### 10.3 Stage 3: BiLSTM Feature Extraction
**Input**: 3 preprocessed modality arrays  
**Process**:
- Pass each modality through separate BiLSTM encoders
- Extract temporal dependencies
- Concatenate/fuse multi-modal features

**Output**: Combined feature vector  
**Duration**: ~1 minute

### 10.4 Stage 4: HGNN Classification
**Input**: Combined feature vector from BiLSTM  
**Process**:
- Forward pass through HGNN
- Generate class probabilities
- Select highest confidence class

**Output**: Emotion classification + confidence scores  
**Duration**: ~10 seconds

---

## 11. Error Handling & Edge Cases

### 11.1 Error Scenarios

| Error Code | Scenario | User Message | System Action |
|------------|----------|--------------|---------------|
| E001 | Invalid video format | "Please upload MP4, AVI, MOV, or MKV format" | Reject upload |
| E002 | File size exceeded | "Video exceeds 500 MB limit" | Reject upload |
| E003 | Video too long | "Video exceeds 10 minute limit" | Reject upload |
| E004 | Coordinate extraction failed | "Unable to detect face/body in video" | Abort processing, suggest retry |
| E005 | Model loading failed | "System error: Model unavailable" | Show maintenance message |
| E006 | Insufficient disk space | "Storage full. Please clear old sessions" | Prevent upload |
| E007 | Processing timeout | "Processing took too long. Please try shorter video" | Abort, cleanup |
| E008 | Corrupted video file | "Video file appears corrupted" | Reject upload |

### 11.2 Edge Cases
- **No face detected**: Notify user to ensure subject is visible
- **Multiple faces**: Process primary face (largest/center)
- **Partial occlusion**: Continue with available features
- **Low quality video**: Warn about potential accuracy impact
- **Variable lighting**: Preprocessing should normalize
- **Fast movements**: BiLSTM should handle temporal smoothing

---

## 12. Testing Requirements

### 12.1 Unit Testing
- All preprocessing functions
- Modality feature extractors
- JSON parsing and validation
- API endpoints
- File operations

### 12.2 Integration Testing
- End-to-end pipeline (upload to result)
- Model inference integration
- WebSocket communication
- File system operations

### 12.3 Performance Testing
- Process 10 concurrent uploads
- Measure end-to-end latency
- Memory usage profiling
- Model inference speed

### 12.4 User Acceptance Testing
- First-time user workflow
- Results accuracy validation (with ground truth)
- UI/UX feedback
- Error handling scenarios

### 12.5 Test Data
- **Minimum**: 30 test videos with ground truth labels
- **Diversity**: Various durations, resolutions, subjects
- **Edge Cases**: Poor lighting, occlusions, fast movements

---

## 13. Deployment Requirements

### 13.1 Development Environment
- Python 3.8+ with virtual environment
- Node.js 16+ for frontend development
- Git for version control
- IDE: VS Code / PyCharm recommended

### 13.2 Production Environment
- **OS**: Ubuntu 20.04+ / Windows 10+ / macOS 11+
- **CPU**: 4+ cores (8+ recommended)
- **RAM**: 8 GB minimum (16 GB recommended)
- **GPU**: Optional (CUDA-capable for faster processing)
- **Storage**: 100 GB minimum free space
- **Network**: Not required (offline operation)

### 13.3 Installation Steps
1. Clone repository
2. Install Python dependencies (`pip install -r requirements.txt`)
3. Install Node dependencies (`npm install`)
4. Download pre-trained models to `/data/models/`
5. Configure environment variables
6. Build frontend (`npm run build`)
7. Start backend (`python main.py`)
8. Access UI at `http://localhost:3000`

### 13.4 Configuration
- `.env` file for environment variables
- `config.yaml` for application settings
- Model paths configurable
- Storage paths configurable
- Port numbers configurable

---

## 14. Documentation Requirements

### 14.1 User Documentation
- Installation guide
- User manual with screenshots
- Video tutorial (5-10 minutes)
- FAQ section
- Troubleshooting guide

### 14.2 Developer Documentation
- Architecture overview
- API documentation (auto-generated Swagger)
- Code comments and docstrings
- Model architecture descriptions
- Deployment guide
- Contributing guidelines

### 14.3 Clinical Documentation
- Model validation report
- Accuracy metrics and limitations
- Recommended use cases
- Ethical considerations
- Privacy and data handling

---

## 15. Future Enhancements (Out of Scope for v1.0)

### 15.1 Planned for v2.0
- **Real-time webcam processing**: Live emotion detection
- **Multi-language support**: UI in multiple languages
- **Advanced visualizations**: Heatmaps, 3D skeleton overlay
- **Batch processing**: Process multiple videos simultaneously
- **Emotion timeline**: Frame-by-frame emotion tracking
- **Custom model training**: Allow users to fine-tune models

### 15.2 Under Consideration
- **Mobile app**: iOS/Android versions
- **Cloud deployment**: Optional cloud storage and processing
- **Multi-user support**: User accounts and role-based access
- **Integration APIs**: Export to EHR systems
- **Comparative analysis**: Compare multiple sessions
- **Report generation**: PDF reports with insights

---

## 16. Constraints & Assumptions

### 16.1 Constraints
- No internet connectivity required
- No database system (file-based storage only)
- No Docker containerization in v1.0
- Local deployment only (no cloud)
- Single user at a time (no concurrent user sessions)

### 16.2 Assumptions
- Pre-trained models (BiLSTM, HGNN) are provided and functional
- Models are already optimized for autism-specific emotion detection
- 3 emotion classes are predefined and validated
- Coordinate extraction code/module is available
- Users have basic computer literacy
- Videos contain clear view of subject's face and upper body
- Subjects are relatively stationary during recording

---

## 17. Success Criteria

### 17.1 Launch Criteria
- ✅ All FR requirements implemented
- ✅ NFR performance targets met
- ✅ End-to-end testing passed
- ✅ User documentation complete
- ✅ Model accuracy validated (≥85%)
- ✅ Security audit passed
- ✅ UAT feedback incorporated

### 17.2 Post-Launch Metrics (3 months)
- User adoption: 50+ active users
- User satisfaction: > 80% positive feedback
- Processing success rate: > 95%
- System uptime: > 95%
- Average processing time: < 5 minutes
- Bug reports: < 10 critical issues

---

## 18. Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Model accuracy insufficient | High | Medium | Extensive testing with diverse dataset, iterative model improvements |
| Processing too slow | High | Medium | GPU acceleration, code optimization, progress updates to manage expectations |
| Storage space fills up | Medium | High | Implement auto-cleanup, storage warnings, compression |
| Video compatibility issues | Medium | Medium | Comprehensive format testing, clear format requirements |
| User interface confusion | Medium | Low | User testing, iterative UI improvements, tooltips |
| Model loading failures | High | Low | Graceful error handling, model validation on startup |
| Privacy concerns | High | Low | Local storage only, encryption, clear privacy policy |

---

## 19. Timeline & Milestones

### Phase 1: Foundation (Weeks 1-2)
- Set up development environment
- Implement basic file upload UI
- Develop coordinate extraction integration
- Set up project structure

### Phase 2: Core Pipeline (Weeks 3-5)
- Implement modality preprocessing
- Integrate BiLSTM feature extraction
- Integrate HGNN classification
- Develop session management

### Phase 3: UI & Results (Weeks 6-7)
- Build results display interface
- Implement progress tracking
- Add session history
- Develop export functionality

### Phase 4: Testing & Refinement (Weeks 8-9)
- Comprehensive testing
- Performance optimization
- Bug fixes
- UI/UX improvements

### Phase 5: Documentation & Launch (Week 10)
- Complete documentation
- User acceptance testing
- Deployment preparation
- Launch

---

## 20. Appendices

### Appendix A: Glossary
- **BiLSTM**: Bidirectional Long Short-Term Memory neural network
- **HGNN**: Hypergraph Neural Network
- **Modality**: A specific type of input data (eye, skeleton, head)
- **Session**: A single video upload and processing instance
- **Coordinate JSON**: Structured data containing frame-by-frame spatial information

### Appendix B: References
- Autism emotion recognition research papers
- BiLSTM architecture documentation
- HGNN model papers
- FastAPI documentation
- React best practices

### Appendix C: Stakeholders
- **Product Owner**: [Name]
- **Technical Lead**: [Name]
- **ML Engineer**: [Name]
- **Frontend Developer**: [Name]
- **Clinical Advisor**: [Name]
- **QA Lead**: [Name]

### Appendix D: Open Questions
1. What are the specific 3 emotion classes? (Happy, Sad, Neutral? Or others?)
2. What is the expected accuracy of the current models?
3. Are there specific autism subtypes to focus on?
4. What is the target deployment scale (clinic, research lab, home use)?
5. Do we need real-time processing or is batch acceptable?
6. Should we support live webcam input in v1.0?

---

## Document Approval

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Product Owner | | | |
| Technical Lead | | | |
| Clinical Advisor | | | |
| QA Lead | | | |

---

**End of Document**
