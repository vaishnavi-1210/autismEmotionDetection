import React, { useState, useCallback, useEffect } from 'react'
import { useDropzone } from 'react-dropzone'
import {
  Box,
  Button,
  Typography,
  Card,
  LinearProgress,
  Alert,
  List,
  ListItem,
  ListItemText,
  CircularProgress,
  Chip,
  Grid,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
} from '@mui/material'
import CloseIcon from '@mui/icons-material/Close'

interface UploadResponse {
  session_id: string
  status: string
  filename: string
}

interface ProcessingStatus {
  session_id: string
  status: string
  created_at: string
  progress?: number
  current_stage?: string
  start_time?: string
  end_time?: string
  error?: string
}

interface PredictionResult {
  session_id: string
  timestamp: string
  emotion_class: string
  confidence_scores: {
    IM: number
    TT: number
    JA: number
  }
}

export const VideoUpload: React.FC = () => {
  const [files, setFiles] = useState<File[]>([])
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)
  const [uploadedSessions, setUploadedSessions] = useState<UploadResponse[]>([])
  const [processingStatus, setProcessingStatus] = useState<{
    [key: string]: ProcessingStatus
  }>({})
  const [predictions, setPredictions] = useState<{
    [key: string]: PredictionResult
  }>({})
  const [pollingInterval, setPollingInterval] = useState<{
    [key: string]: ReturnType<typeof setInterval>
  }>({})
  const [animationDialogOpen, setAnimationDialogOpen] = useState<{
    [key: string]: boolean
  }>({})

  const onDrop = useCallback((acceptedFiles: File[]) => {
    setFiles(acceptedFiles)
    setMessage(null)
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'video/*': ['.mp4'],
    },
  })

  // Poll for processing status
  const pollStatus = async (sessionId: string) => {
    try {
      const response = await fetch(`/api/v1/status/${sessionId}`)
      const status: ProcessingStatus = await response.json()

      setProcessingStatus((prev) => ({
        ...prev,
        [sessionId]: status,
      }))

      if (status.status === 'completed') {
        // Fetch results
        const resultsResponse = await fetch(`/api/v1/results/${sessionId}`)
        const results: PredictionResult = await resultsResponse.json()

        setPredictions((prev) => ({
          ...prev,
          [sessionId]: results,
        }))

        // Stop polling
        if (pollingInterval[sessionId]) {
          clearInterval(pollingInterval[sessionId])
          setPollingInterval((prev) => {
            const updated = { ...prev }
            delete updated[sessionId]
            return updated
          })
        }

        setMessage({
          type: 'success',
          text: `✅ Behavior Analysis Complete! Class: ${results.emotion_class}`,
        })
      } else if (status.status === 'failed') {
        if (pollingInterval[sessionId]) {
          clearInterval(pollingInterval[sessionId])
          setPollingInterval((prev) => {
            const updated = { ...prev }
            delete updated[sessionId]
            return updated
          })
        }

        setMessage({
          type: 'error',
          text: `❌ Processing failed: ${status.error || 'Unknown error'}`,
        })
      }
    } catch (error) {
      console.error('Error polling status:', error)
    }
  }

  // Start polling when upload completes
  useEffect(() => {
    uploadedSessions.forEach((session) => {
      if (!pollingInterval[session.session_id]) {
        const interval = setInterval(() => {
          pollStatus(session.session_id)
        }, 2000) // Poll every 2 seconds

        setPollingInterval((prev) => ({
          ...prev,
          [session.session_id]: interval,
        }))

        // Initial poll
        pollStatus(session.session_id)
      }
    })

    return () => {
      Object.values(pollingInterval).forEach(clearInterval)
    }
  }, [uploadedSessions])

  const handleUpload = async () => {
    if (files.length === 0) {
      setMessage({ type: 'error', text: 'Please select a video file' })
      return
    }

    setUploading(true)
    setProgress(0)

    try {
      for (let i = 0; i < files.length; i++) {
        const file = files[i]
        const formData = new FormData()
        formData.append('file', file)

        const xhr = new XMLHttpRequest()

        xhr.upload.addEventListener('loadstart', () => {
          setProgress((i / files.length) * 100)
        })

        xhr.upload.addEventListener('progress', (event) => {
          if (event.lengthComputable) {
            const percentComplete = (event.loaded / event.total) * 100
            setProgress((i / files.length) * 100 + percentComplete / files.length)
          }
        })

        await new Promise((resolve, reject) => {
          xhr.addEventListener('load', () => {
            if (xhr.status === 200) {
              const response: UploadResponse = JSON.parse(xhr.responseText)
              setUploadedSessions((prev) => [...prev, response])
              setMessage({
                type: 'success',
                text: `✅ Video uploaded! Analyzing behavior...`,
              })
              resolve(null)
            } else {
              reject(new Error(`Upload failed: ${xhr.statusText}`))
            }
          })

          xhr.addEventListener('error', () => {
            reject(new Error('Upload error'))
          })

          xhr.open('POST', '/api/v1/upload')
          xhr.send(formData)
        })
      }

      setFiles([])
      setProgress(100)
    } catch (error) {
      setMessage({
        type: 'error',
        text: `❌ Upload failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
      })
    } finally {
      setUploading(false)
    }
  }

  const getBehaviorColor = (classLabel: string): 'error' | 'warning' | 'success' => {
    switch (classLabel) {
      case 'JA':
        return 'success'
      case 'IM':
        return 'warning'
      case 'TT':
        return 'error'
      default:
        return 'warning'
    }
  }

  return (
    <Box sx={{ py: 4 }}>
      <Card sx={{ p: 4, borderRadius: 2 }}>
        <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
          📹 Upload Video for Behavior Analysis
        </Typography>

        <Box
          {...getRootProps()}
          sx={{
            border: '2px dashed #1976d2',
            borderRadius: 2,
            p: 4,
            textAlign: 'center',
            backgroundColor: isDragActive ? '#e3f2fd' : '#f5f5f5',
            cursor: 'pointer',
            transition: 'all 0.3s ease',
            '&:hover': {
              backgroundColor: '#e3f2fd',
              borderColor: '#1565c0',
            },
          }}
        >
          <input {...getInputProps()} />
          <Typography sx={{ fontSize: 48, color: '#1976d2', mb: 2, lineHeight: 1 }}>☁️⬆️</Typography>
          <Typography variant="h6" sx={{ mb: 1 }}>
            {isDragActive ? 'Drop video here' : 'Drag & drop video here'}
          </Typography>
          <Typography variant="body2" color="textSecondary">
            or click to select file
          </Typography>
          <Typography variant="caption" color="textSecondary" sx={{ display: 'block', mt: 1 }}>
            MP4 format recommended (Max 500MB, 10 minutes)
          </Typography>
        </Box>

        {files.length > 0 && (
          <Box sx={{ mt: 3 }}>
            <Typography variant="subtitle2" sx={{ mb: 2 }}>
              Selected File:
            </Typography>
            <List>
              {files.map((file, index) => (
                <ListItem key={index}>
                  <ListItemText
                    primary={file.name}
                    secondary={`${(file.size / (1024 * 1024)).toFixed(2)} MB`}
                  />
                </ListItem>
              ))}
            </List>
          </Box>
        )}

        {uploading && (
          <Box sx={{ mt: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <CircularProgress size={24} />
              <Box sx={{ flex: 1 }}>
                <LinearProgress variant="determinate" value={progress} />
              </Box>
              <Typography variant="body2">{Math.round(progress)}%</Typography>
            </Box>
          </Box>
        )}

        {message && (
          <Alert severity={message.type} sx={{ mt: 3 }}>
            {message.text}
          </Alert>
        )}

        <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
          <Button
            variant="contained"
            color="primary"
            onClick={handleUpload}
            disabled={files.length === 0 || uploading}
            size="large"
          >
            {uploading ? 'Uploading...' : 'Upload & Analyze'}
          </Button>
          <Button
            variant="outlined"
            onClick={() => {
              setFiles([])
              setMessage(null)
            }}
            disabled={uploading}
          >
            Clear
          </Button>
        </Box>

        {uploadedSessions.length > 0 && (
          <Box sx={{ mt: 4 }}>
            <Typography variant="h6" sx={{ mb: 3 }}>
              🎯 Analysis Results
            </Typography>

            {uploadedSessions.map((session) => {
              const status = processingStatus[session.session_id]
              const prediction = predictions[session.session_id]
              const isProcessing = status?.status === 'processing'
              const isCompleted = status?.status === 'completed'
              const isFailed = status?.status === 'failed'

              return (
                <Card key={session.session_id} sx={{ p: 3, mb: 3, backgroundColor: '#f9f9f9' }}>
                  <Grid container spacing={2} sx={{ mb: 2 }}>
                    <Grid item xs={12} sm={6}>
                      <Typography variant="subtitle2" sx={{ mb: 1 }}>
                        Session ID
                      </Typography>
                      <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
                        {session.session_id.substring(0, 8)}...
                      </Typography>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <Typography variant="subtitle2" sx={{ mb: 1 }}>
                        Status
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {isProcessing && (
                          <>
                            <CircularProgress size={18} thickness={5} />
                            <Typography variant="body2">Processing...</Typography>
                          </>
                        )}
                        {isCompleted && (
                          <>
                            <Typography sx={{ fontSize: 18, lineHeight: 1 }}>✅</Typography>
                            <Typography variant="body2">Complete</Typography>
                          </>
                        )}
                        {isFailed && (
                          <>
                            <Typography sx={{ fontSize: 18, lineHeight: 1 }}>❌</Typography>
                            <Typography variant="body2">Failed</Typography>
                          </>
                        )}
                      </Box>
                    </Grid>
                  </Grid>

                  {isProcessing && status?.current_stage && (
                    <Box sx={{ mt: 2, mb: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Typography variant="caption" color="textSecondary">
                          {status.current_stage}
                        </Typography>
                        <Typography variant="caption" color="textSecondary">
                          {status.progress || 0}%
                        </Typography>
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={status.progress || 0}
                        sx={{ height: 8, borderRadius: 4 }}
                      />
                    </Box>
                  )}

                  {/* Animation Display Section - Shows when extraction complete */}
                  {(isProcessing || isCompleted) && (
                    <Box sx={{ mt: 3, pt: 3, borderTop: '1px solid #ddd' }}>
                      <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 600 }}>
                        🎬 Behavior Animation
                      </Typography>
                      <Button
                        variant="contained"
                        color="info"
                        onClick={() =>
                          setAnimationDialogOpen((prev) => ({
                            ...prev,
                            [session.session_id]: true,
                          }))
                        }
                        sx={{ width: '100%', mb: 2 }}
                      >
                        View Animation
                      </Button>
                      <Button
                        variant="outlined"
                        href={`/api/v1/animation/${session.session_id}`}
                        download={`behavior_animation_${session.session_id}.mp4`}
                        sx={{ width: '100%' }}
                      >
                        ⬇️ Download Animation
                      </Button>
                    </Box>
                  )}

                  {/* Animation Modal */}
                  <Dialog
                    open={animationDialogOpen[session.session_id] || false}
                    onClose={() =>
                      setAnimationDialogOpen((prev) => ({
                        ...prev,
                        [session.session_id]: false,
                      }))
                    }
                    maxWidth="md"
                    fullWidth
                  >
                    <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography>2D Behavior Animation</Typography>
                      <IconButton
                        onClick={() =>
                          setAnimationDialogOpen((prev) => ({
                            ...prev,
                            [session.session_id]: false,
                          }))
                        }
                      >
                        <CloseIcon />
                      </IconButton>
                    </DialogTitle>
                    <DialogContent dividers>
                      <video
                        width="100%"
                        controls
                        style={{ borderRadius: '8px', backgroundColor: '#000' }}
                      >
                        <source src={`/api/v1/animation/${session.session_id}`} type="video/mp4" />
                        Your browser does not support the video tag.
                      </video>
                    </DialogContent>
                  </Dialog>

                  {/* Results Section - Shows when analysis complete */}
                  {isCompleted && prediction && (
                    <Box sx={{ mt: 3, pt: 3, borderTop: '1px solid #ddd' }}>
                      <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 600 }}>
                        📊 Behavior Classification
                      </Typography>

                      <Box sx={{ mb: 3 }}>
                        <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
                          Predicted Behavior Class:
                        </Typography>
                        <Chip
                          label={prediction.emotion_class}
                          color={getBehaviorColor(prediction.emotion_class)}
                          sx={{ fontSize: 16, padding: '20px 10px' }}
                        />
                      </Box>

                      <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                        Confidence Breakdown:
                      </Typography>

                      <Grid container spacing={2} sx={{ mb: 3 }}>
                        {Object.entries(prediction.confidence_scores).map(([className, score]) => (
                          <Grid item xs={12} sm={6} md={4} key={className}>
                            <Card sx={{ p: 2, backgroundColor: '#f5f5f5' }}>
                              <Typography variant="caption" color="textSecondary">
                                {className}
                              </Typography>
                              <Box sx={{ mt: 1 }}>
                                <LinearProgress variant="determinate" value={score * 100} />
                              </Box>
                              <Typography variant="body2" sx={{ mt: 1, textAlign: 'right' }}>
                                {(score * 100).toFixed(2)}%
                              </Typography>
                            </Card>
                          </Grid>
                        ))}
                      </Grid>

                      <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 600 }}>
                        📥 Export Results
                      </Typography>
                      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                        <Button
                          variant="outlined"
                          size="small"
                          href={`/api/v1/coordinates/${session.session_id}`}
                          download={`coordinates_${session.session_id}.json`}
                        >
                          Landmarks
                        </Button>
                        <Button
                          variant="outlined"
                          size="small"
                          href={`/api/v1/features/${session.session_id}`}
                          download={`features_${session.session_id}.zip`}
                        >
                          Features
                        </Button>
                        <Button
                          variant="outlined"
                          size="small"
                          href={`/api/v1/export/${session.session_id}?format=json`}
                          download={`results_${session.session_id}.json`}
                        >
                          Results
                        </Button>
                      </Box>
                    </Box>
                  )}

                  {isFailed && status?.error && (
                    <Alert severity="error" sx={{ mt: 2 }}>
                      {status.error}
                    </Alert>
                  )}
                </Card>
              )
            })}
          </Box>
        )}
      </Card>
    </Box>
  )
}

export default VideoUpload
