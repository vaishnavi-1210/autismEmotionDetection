# Frontend Components Reference

## Main Components

### App.tsx
Main application component that manages page state and routing.

**Features:**
- Page state management (home, processing, results)
- Session management
- Material-UI theme configuration
- Header with application title
- Footer with information and privacy notice

### UploadComponent.tsx
Video upload interface with drag-and-drop support.

**Features:**
- Drag-and-drop zone for video files
- File format validation
- File size validation
- Progress indicator
- Error messages

**Props:**
- `onUploadSuccess: (response: VideoUploadResponse) => void`

### ProcessingComponent.tsx
Real-time processing status monitoring.

**Features:**
- Multi-stage progress indicator (4 stages)
- Real-time status polling
- Error handling
- Automatic completion detection
- Completion callback

**Props:**
- `sessionId: string`
- `onComplete?: (sessionId: string) => void`

### ResultsComponent.tsx
Emotion classification results display.

**Features:**
- Prominent emotion display
- Confidence scores visualization (Bar chart)
- Processing metadata display
- Export functionality (JSON/CSV)
- Session deletion
- Back to home button

**Props:**
- `sessionId: string`
- `onHome?: () => void`

### SessionHistory.tsx
Historical sessions list and management.

**Features:**
- Table view of all sessions
- Sortable and filterable
- Status chip indicators
- Batch operations
- Session deletion
- Refresh functionality

**Props:**
- `onSessionSelect?: (sessionId: string) => void`
- `refreshTrigger?: number`

## Services

### api.ts
REST API client service using Axios.

**Methods:**
- `healthCheck()` - API health status
- `uploadVideo(file: File)` - Upload video
- `processVideo(sessionId: string)` - Start processing
- `getStatus(sessionId: string)` - Get status
- `getResults(sessionId: string)` - Get results
- `listSessions()` - List all sessions
- `getSession(sessionId: string)` - Get session details
- `exportResults(sessionId: string, format: 'json' | 'csv')` - Export results
- `deleteSession(sessionId: string)` - Delete session

## Types

### VideoUploadResponse
Response from upload endpoint.

### SessionStatus
Current session information and status.

### ConfidenceScores
Emotion confidence score mapping.

### PredictionResult
Complete emotion prediction result.

### SessionListResponse
List of all sessions.

## Material-UI Components Used

- `Container` - Layout wrapper
- `Box` - Flex container
- `Paper` - Elevated card
- `Button` - Interactive button
- `Typography` - Text elements
- `Card` - Content cards
- `TextField` - Input fields
- `LinearProgress` - Progress bars
- `CircularProgress` - Loading spinner
- `Alert` - Message alerts
- `Chip` - Status indicators
- `Table` - Session history
- `Dialog` - Modal dialogs
- `AppBar` - Header
- `Toolbar` - Header content
- `Grid` - Responsive grid
- `IconButton` - Icon buttons
- `Tooltip` - Help tooltips

## Icons Used

From `@mui/icons-material`:
- `CloudUploadIcon` - Upload indicator
- `CheckCircleIcon` - Success indicator
- `ErrorIcon` - Error indicator
- `DownloadIcon` - Export action
- `DeleteIcon` - Delete action
- `HomeIcon` - Home navigation
- `RefreshIcon` - Refresh action
- `VisibilityIcon` - View action
- `SignalCellularAltIcon` - App logo

## Responsive Design

All components use Material-UI's responsive grid system:
- `xs` - Extra small (mobile)
- `sm` - Small (tablet)
- `md` - Medium (desktop)
- `lg` - Large (wide desktop)

## Data Flow

```
App
├── Home Page
│   ├── UploadComponent
│   │   └── onUploadSuccess → process video
│   └── SessionHistory
│       └── onSessionSelect → view results
├── Processing Page
│   ├── ProcessingComponent
│   │   └── onComplete → show results
└── Results Page
    └── ResultsComponent
        ├── Export options
        ├── Delete session
        └── Back to home
```

## Styling

- **Color Scheme**:
  - Primary: #1976d2 (Blue)
  - Secondary: #dc004e (Pink)
  - Success: #4caf50 (Green)
  - Background: #f5f5f5 (Light Gray)

- **Spacing**: Material Design 8px system
- **Typography**: Roboto font family
- **Elevation**: Material shadow system

---

**Last Updated**: April 6, 2026
