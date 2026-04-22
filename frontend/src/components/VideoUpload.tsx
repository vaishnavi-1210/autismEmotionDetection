import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import {
  Alert,
  Box,
  Button,
  Card,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Fade,
  IconButton,
  LinearProgress,
  Stack,
  Typography,
} from '@mui/material'

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

// 4-stage pipeline configuration
const PIPELINE_STAGES = [
  { name: 'Upload', minProgress: 0, maxProgress: 25, label: 'Uploading video...' },
  { name: 'Extraction', minProgress: 25, maxProgress: 50, label: 'Extracting coordinates & generating animation...' },
  { name: 'Features', minProgress: 50, maxProgress: 85, label: 'Extracting features (skeleton, eye, head)...' },
  { name: 'Classification', minProgress: 85, maxProgress: 100, label: 'Running HGNN classification...' },
]

const UPLOAD_WEIGHT = 25

export const VideoUpload: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [overallProgress, setOverallProgress] = useState(0)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const [session, setSession] = useState<UploadResponse | null>(null)
  const [processingStatus, setProcessingStatus] = useState<ProcessingStatus | null>(null)
  const [prediction, setPrediction] = useState<PredictionResult | null>(null)

  const [animationDialogOpen, setAnimationDialogOpen] = useState(false)
  const [animationNonce, setAnimationNonce] = useState<number>(Date.now())
  const [animationError, setAnimationError] = useState<string | null>(null)
  const [resultDialogOpen, setResultDialogOpen] = useState(false)
  const [progressDialogOpen, setProgressDialogOpen] = useState(false)

  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const clearPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
  }, [])

  useEffect(() => {
    return () => {
      clearPolling()
    }
  }, [clearPolling])

  const resetStateForNewFile = useCallback(() => {
    clearPolling()
    setSession(null)
    setProcessingStatus(null)
    setPrediction(null)
    setOverallProgress(0)
    setResultDialogOpen(false)
    setAnimationDialogOpen(false)
    setProgressDialogOpen(false)
    setMessage(null)
  }, [clearPolling])

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      const nextFile = acceptedFiles[0] ?? null
      setSelectedFile(nextFile)
      if (nextFile) {
        resetStateForNewFile()
      }
    },
    [resetStateForNewFile],
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: false,
    maxFiles: 1,
    accept: {
      'video/mp4': ['.mp4'],
      'video/x-msvideo': ['.avi'],
      'video/quicktime': ['.mov'],
      'video/x-matroska': ['.mkv'],
    },
  })

  // Calculate progress for each stage
  const stageProgress = useMemo(() => {
    return PIPELINE_STAGES.map((stage) => {
      const stageRange = stage.maxProgress - stage.minProgress
      if (overallProgress < stage.minProgress) {
        return 0
      }
      if (overallProgress >= stage.maxProgress) {
        return 100
      }
      return ((overallProgress - stage.minProgress) / stageRange) * 100
    })
  }, [overallProgress])

  const currentStageIndex = useMemo(() => {
    for (let i = PIPELINE_STAGES.length - 1; i >= 0; i--) {
      if (overallProgress >= PIPELINE_STAGES[i].minProgress) {
        return i
      }
    }
    return 0
  }, [overallProgress])

  const updateProcessingProgress = useCallback((reportedProgress?: number) => {
    setOverallProgress((prev) => {
      if (typeof reportedProgress === 'number' && Number.isFinite(reportedProgress)) {
        const normalized = Math.max(0, Math.min(reportedProgress, 100))
        const mapped = UPLOAD_WEIGHT + (normalized / 100) * (100 - UPLOAD_WEIGHT)
        return Math.max(prev, Math.min(mapped, 99))
      }

      return Math.max(prev, UPLOAD_WEIGHT)
    })
  }, [])

  const inferProgressFromStage = useCallback((status: ProcessingStatus): number | undefined => {
    if (typeof status.progress === 'number' && Number.isFinite(status.progress)) {
      return status.progress
    }

    const stage = (status.current_stage || '').toLowerCase()
    if (!stage) {
      return undefined
    }

    if (stage.includes('complete')) return 100
    if (stage.includes('hgnn') || stage.includes('classif')) return 92
    if (stage.includes('head')) return 64
    if (stage.includes('eye')) return 50
    if (stage.includes('skeleton')) return 34
    if (stage.includes('animation ready') || stage.includes('landmarks extracted')) return 33
    if (stage.includes('extract') || stage.includes('landmark')) return 10
    return undefined
  }, [])

  const openAnimationDialog = useCallback(() => {
    setAnimationError(null)
    setAnimationNonce(Date.now())
    setAnimationDialogOpen(true)
  }, [])

  const pollStatus = useCallback(
    async (sessionId: string) => {
      try {
        const response = await fetch(`/api/v1/status/${sessionId}`, { cache: 'no-store' })
        if (!response.ok) {
          throw new Error(`Status error: ${response.status}`)
        }

        const status: ProcessingStatus = await response.json()
        setProcessingStatus(status)

        if (status.status === 'processing' || status.status === 'uploaded') {
          updateProcessingProgress(inferProgressFromStage(status))
          setProgressDialogOpen(true)
          return
        }

        if (status.status === 'completed') {
          clearPolling()
          setOverallProgress(100)
          setProgressDialogOpen(false)

          const resultsResponse = await fetch(`/api/v1/results/${sessionId}`, { cache: 'no-store' })
          if (!resultsResponse.ok) {
            throw new Error(`Result fetch error: ${resultsResponse.status}`)
          }

          const resultPayload: PredictionResult = await resultsResponse.json()
          setPrediction(resultPayload)
          setResultDialogOpen(true)
          setMessage({
            type: 'success',
            text: 'Analysis complete. Final model prediction is ready.',
          })
          return
        }

        if (status.status === 'failed') {
          clearPolling()
          setProgressDialogOpen(false)
          setMessage({
            type: 'error',
            text: `Processing failed: ${status.error || 'Unknown error'}`,
          })
        }
      } catch (error) {
        clearPolling()
        setProgressDialogOpen(false)
        setMessage({
          type: 'error',
          text: `Status polling failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
        })
      }
    },
    [clearPolling, inferProgressFromStage, updateProcessingProgress],
  )

  const startPolling = useCallback(
    (sessionId: string) => {
      if (pollRef.current) {
        return
      }

      pollRef.current = setInterval(() => {
        void pollStatus(sessionId)
      }, 1000)

      void pollStatus(sessionId)
    },
    [pollStatus],
  )

  const handleUpload = async () => {
    if (!selectedFile) {
      setMessage({ type: 'error', text: 'Please select a video file first.' })
      return
    }

    clearPolling()
    setUploading(true)
    setMessage(null)
    setSession(null)
    setProcessingStatus(null)
    setPrediction(null)
    setResultDialogOpen(false)
    setAnimationDialogOpen(false)
    setProgressDialogOpen(true)
    setOverallProgress(0)

    const formData = new FormData()
    formData.append('file', selectedFile)

    const xhr = new XMLHttpRequest()

    try {
      const uploadResponse = await new Promise<UploadResponse>((resolve, reject) => {
        xhr.upload.addEventListener('progress', (event) => {
          if (!event.lengthComputable) {
            return
          }

          const uploadPercent = (event.loaded / event.total) * 100
          const mappedProgress = (uploadPercent / 100) * UPLOAD_WEIGHT
          setOverallProgress((prev) => Math.max(prev, mappedProgress))
        })

        xhr.addEventListener('load', () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            const response: UploadResponse = JSON.parse(xhr.responseText)
            resolve(response)
            return
          }

          reject(new Error(`Upload failed: ${xhr.status} ${xhr.statusText}`))
        })

        xhr.addEventListener('error', () => {
          reject(new Error('Network error during upload.'))
        })

        xhr.open('POST', '/api/v1/upload')
        xhr.send(formData)
      })

      setSession(uploadResponse)
      setProcessingStatus({
        session_id: uploadResponse.session_id,
        status: uploadResponse.status || 'processing',
        created_at: new Date().toISOString(),
      })
      setOverallProgress((prev) => Math.max(prev, UPLOAD_WEIGHT))
      startPolling(uploadResponse.session_id)
    } catch (error) {
      setProgressDialogOpen(false)
      setMessage({
        type: 'error',
        text: `Upload failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
      })
    } finally {
      setUploading(false)
    }
  }

  const handleReset = () => {
    if (uploading || processingStatus?.status === 'processing') {
      return
    }

    setSelectedFile(null)
    resetStateForNewFile()
  }

  const stageText = useMemo(() => {
    if (uploading) {
      return 'Uploading video'
    }

    if (processingStatus?.status === 'processing') {
      return processingStatus.current_stage || 'Running model inference pipeline'
    }

    if (processingStatus?.status === 'completed') {
      return 'Analysis completed'
    }

    if (processingStatus?.status === 'failed') {
      return 'Processing failed'
    }

    if (session) {
      return 'Preparing analysis'
    }

    return 'Waiting for file upload'
  }, [uploading, processingStatus, session])

  const currentStatus = processingStatus?.status
  const isBusy = uploading || currentStatus === 'processing'
  const shouldShowProgress = isBusy || overallProgress > 0
  const backendProgress = processingStatus?.progress ?? 0
  const animationReady = Boolean(
    session
      && (
        processingStatus?.status === 'completed'
        || (processingStatus?.status === 'processing' && backendProgress >= 33)
      ),
  )
  const animationSrc = session
    ? `/api/v1/animation/${session.session_id}?v=${animationNonce}`
    : ''

  const predictedClassTone = useMemo(() => {
    if (!prediction?.emotion_class) {
      return {
        background: 'rgba(31, 58, 95, 0.08)',
        borderColor: 'rgba(31, 58, 95, 0.22)',
        textColor: '#1f3a5f',
      }
    }

    switch (prediction.emotion_class) {
      case 'JA':
        return {
          background: 'rgba(42, 157, 143, 0.14)',
          borderColor: 'rgba(42, 157, 143, 0.45)',
          textColor: '#1f6059',
        }
      case 'IM':
        return {
          background: 'rgba(227, 160, 8, 0.14)',
          borderColor: 'rgba(227, 160, 8, 0.45)',
          textColor: '#6f5400',
        }
      case 'TT':
        return {
          background: 'rgba(203, 67, 53, 0.12)',
          borderColor: 'rgba(203, 67, 53, 0.4)',
          textColor: '#7e2f26',
        }
      default:
        return {
          background: 'rgba(31, 58, 95, 0.08)',
          borderColor: 'rgba(31, 58, 95, 0.22)',
          textColor: '#1f3a5f',
        }
    }
  }, [prediction?.emotion_class])

  return (
    <Box sx={{ py: { xs: 1, md: 2 } }}>
      <Card sx={{ p: { xs: 2.25, md: 3.5 }, borderRadius: 4 }}>
        <Stack spacing={2.5}>
          <Box>
            <Typography variant="h5" sx={{ fontWeight: 800, mb: 0.6 }}>
              Upload and Analyze
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Single-flow experience: one upload, one progress dialog, one final prediction.
            </Typography>
          </Box>

          <Box
            {...getRootProps()}
            sx={{
              border: '1.5px dashed',
              borderColor: isDragActive ? 'secondary.main' : 'rgba(31,58,95,0.25)',
              borderRadius: 3,
              p: { xs: 3, md: 4 },
              textAlign: 'center',
              background: isDragActive
                ? 'linear-gradient(135deg, rgba(42,157,143,0.08), rgba(42,157,143,0.02))'
                : 'linear-gradient(135deg, rgba(31,58,95,0.04), rgba(255,255,255,0.6))',
              cursor: 'pointer',
              transition: 'all 220ms ease',
              '&:hover': {
                borderColor: 'secondary.main',
                transform: 'translateY(-2px)',
              },
            }}
          >
            <input {...getInputProps()} />
            <Box
              sx={{
                width: 56,
                height: 56,
                borderRadius: '50%',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 24,
                fontWeight: 700,
                color: 'primary.main',
                backgroundColor: 'rgba(31,58,95,0.1)',
                mb: 1,
              }}
            >
              UP
            </Box>
            <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
              {isDragActive ? 'Drop your video here' : 'Drag and drop your video'}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.7 }}>
              or click to browse. Supports MP4, AVI, MOV, MKV.
            </Typography>
          </Box>

          {selectedFile && (
            <Card
              variant="outlined"
              sx={{
                px: 2,
                py: 1.4,
                borderRadius: 2.5,
                borderColor: 'rgba(31,58,95,0.2)',
                backgroundColor: 'rgba(255,255,255,0.72)',
              }}
            >
              <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={2}>
                <Box>
                  <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
                    Selected Video
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {selectedFile.name} ({(selectedFile.size / (1024 * 1024)).toFixed(2)} MB)
                  </Typography>
                </Box>
                <Chip size="small" label="Ready" color="primary" variant="outlined" />
              </Stack>
            </Card>
          )}

          <Box sx={{ display: 'flex', gap: 1.4, flexWrap: 'wrap' }}>
            <Button
              variant="contained"
              color="primary"
              size="large"
              onClick={handleUpload}
              disabled={!selectedFile || isBusy}
              startIcon={isBusy ? <CircularProgress color="inherit" size={16} /> : undefined}
              sx={{ minWidth: 170 }}
            >
              {isBusy ? 'Processing' : 'Start Analysis'}
            </Button>
            <Button variant="outlined" size="large" onClick={handleReset} disabled={isBusy}>
              Reset
            </Button>
          </Box>

          {shouldShowProgress && !progressDialogOpen && (
            <Card
              variant="outlined"
              sx={{
                p: 2,
                borderRadius: 2.5,
                borderColor: 'rgba(31,58,95,0.18)',
                background: 'linear-gradient(135deg, rgba(31,58,95,0.04), rgba(42,157,143,0.03))',
              }}
            >
              <Stack spacing={1.2}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 2 }}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
                    {stageText}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ minWidth: 48, textAlign: 'right' }}>
                    {Math.round(overallProgress)}%
                  </Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={overallProgress}
                  sx={{
                    height: 9,
                    borderRadius: 8,
                    backgroundColor: 'rgba(31,58,95,0.12)',
                    '& .MuiLinearProgress-bar': {
                      borderRadius: 8,
                      transition: 'transform 450ms ease',
                    },
                  }}
                />
                {session?.session_id && (
                  <Typography variant="caption" color="text.secondary">
                    Session: {session.session_id.slice(0, 10)}...
                  </Typography>
                )}
              </Stack>
            </Card>
          )}

          <Fade in={Boolean(message)}>
            <Box>
              {message && (
                <Alert
                  severity={message.type}
                  sx={{
                    borderRadius: 2,
                    border: '1px solid',
                    borderColor: message.type === 'success' ? 'success.light' : 'error.light',
                  }}
                >
                  {message.text}
                </Alert>
              )}
            </Box>
          </Fade>

          {session && animationReady && (
            <Box sx={{ display: 'flex', gap: 1.2, flexWrap: 'wrap' }}>
              <Button variant="outlined" onClick={openAnimationDialog}>
                View Animation
              </Button>
              <Button
                variant="outlined"
                href={`/api/v1/animation/${session.session_id}`}
                download={`behavior_animation_${session.session_id}.mp4`}
              >
                Download Animation
              </Button>
              {processingStatus?.status === 'completed' && (
                <Button variant="outlined" onClick={() => setResultDialogOpen(true)}>
                  View Final Result
                </Button>
              )}
              <Button
                variant="outlined"
                href={`/api/v1/export/${session.session_id}?format=json`}
                download={`results_${session.session_id}.json`}
                disabled={processingStatus?.status !== 'completed'}
              >
                Download Result
              </Button>
            </Box>
          )}
        </Stack>
      </Card>

      {/* PROGRESS DIALOG - Shows all 4 stages */}
      <Dialog open={progressDialogOpen} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', pr: 1.5 }}>
          <Typography variant="h6" sx={{ fontWeight: 800 }}>
            Processing Progress
          </Typography>
        </DialogTitle>
        <DialogContent>
          <Stack spacing={3} sx={{ pt: 2 }}>
            {PIPELINE_STAGES.map((stage, index) => (
              <Box key={stage.name}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.8 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.2 }}>
                    <Box
                      sx={{
                        width: 32,
                        height: 32,
                        borderRadius: '50%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: 14,
                        fontWeight: 700,
                        backgroundColor: stageProgress[index] === 100 ? '#2a9d8f' : index < currentStageIndex ? '#2a9d8f' : 'rgba(31,58,95,0.12)',
                        color: stageProgress[index] === 100 || index < currentStageIndex ? 'white' : 'text.secondary',
                      }}
                    >
                      {stageProgress[index] === 100 || index < currentStageIndex ? '✓' : index + 1}
                    </Box>
                    <Box>
                      <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
                        {stage.name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {/* Show current_stage if we're in this stage */}
                        {index === currentStageIndex && processingStatus?.current_stage
                          ? processingStatus.current_stage
                          : stage.label}
                      </Typography>
                    </Box>
                  </Box>
                  <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 600 }}>
                    {Math.round(stageProgress[index])}%
                  </Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={stageProgress[index]}
                  sx={{
                    height: 6,
                    borderRadius: 6,
                    backgroundColor: 'rgba(31,58,95,0.12)',
                    '& .MuiLinearProgress-bar': {
                      borderRadius: 6,
                      backgroundColor: index < currentStageIndex ? '#2a9d8f' : '#1f3a5f',
                      transition: 'transform 450ms ease',
                    },
                  }}
                />
              </Box>
            ))}

            {session?.session_id && (
              <Box sx={{ pt: 1, borderTop: '1px solid rgba(31,58,95,0.12)' }}>
                <Typography variant="caption" color="text.secondary">
                  Session ID: {session.session_id.slice(0, 16)}...
                </Typography>
              </Box>
            )}

            {processingStatus?.current_stage && (
              <Box sx={{ mt: 1, p: 1.2, borderRadius: 1.5, backgroundColor: 'rgba(31,58,95,0.05)' }}>
                <Typography variant="caption" sx={{ fontWeight: 600, color: '#1f3a5f', display: 'block', mb: 0.4 }}>
                  Current Activity:
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {processingStatus.current_stage}
                </Typography>
              </Box>
            )}

            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>
                Overall: {Math.round(overallProgress)}%
              </Typography>
              <LinearProgress
                variant="determinate"
                value={overallProgress}
                sx={{
                  height: 7,
                  borderRadius: 6,
                  backgroundColor: 'rgba(31,58,95,0.1)',
                  '& .MuiLinearProgress-bar': {
                    borderRadius: 6,
                    backgroundColor: '#2a9d8f',
                    transition: 'transform 450ms ease',
                  },
                }}
              />
            </Box>

            {animationReady && (
              <Box sx={{ pt: 1 }}>
                <Button variant="outlined" onClick={openAnimationDialog}>
                  Open Animation
                </Button>
              </Box>
            )}
          </Stack>
        </DialogContent>
      </Dialog>

      {/* RESULT DIALOG */}
      <Dialog open={resultDialogOpen} onClose={() => setResultDialogOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', pr: 1.5 }}>
          <Typography variant="h6" sx={{ fontWeight: 800 }}>
            Final Prediction
          </Typography>
          <IconButton onClick={() => setResultDialogOpen(false)}>
            <Typography component="span" sx={{ lineHeight: 1 }}>
              x
            </Typography>
          </IconButton>
        </DialogTitle>
        <DialogContent>
          <Box
            sx={{
              mt: 1,
              px: 2,
              py: 2.5,
              borderRadius: 3,
              border: '1px solid',
              borderColor: predictedClassTone.borderColor,
              backgroundColor: predictedClassTone.background,
              textAlign: 'center',
            }}
          >
            <Typography variant="overline" color="text.secondary">
              Predicted Class
            </Typography>
            <Typography sx={{ mt: 0.6, fontSize: { xs: 34, md: 40 }, fontWeight: 800, color: predictedClassTone.textColor }}>
              {prediction?.emotion_class || '-'}
            </Typography>
            {prediction?.timestamp && (
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.6 }}>
                {new Date(prediction.timestamp).toLocaleString()}
              </Typography>
            )}
          </Box>
        </DialogContent>
        <DialogActions sx={{ px: 2.5, pb: 2.2 }}>
          {session && (
            <Button variant="outlined" onClick={openAnimationDialog}>
              View Animation
            </Button>
          )}
          <Button variant="contained" onClick={() => setResultDialogOpen(false)}>
            Done
          </Button>
        </DialogActions>
      </Dialog>

      {/* ANIMATION DIALOG */}
      <Dialog
        open={animationDialogOpen}
        onClose={() => setAnimationDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', pr: 1.5 }}>
          <Typography variant="h6" sx={{ fontWeight: 800 }}>
            2D Behavior Animation
          </Typography>
          <IconButton onClick={() => setAnimationDialogOpen(false)}>
            <Typography component="span" sx={{ lineHeight: 1 }}>
              x
            </Typography>
          </IconButton>
        </DialogTitle>
        <DialogContent dividers>
          {session ? (
            <>
              {animationError && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  {animationError}
                </Alert>
              )}
              <video
                key={animationSrc}
                width="100%"
                controls
                style={{ borderRadius: '10px', backgroundColor: '#000' }}
                onError={() => setAnimationError('Animation failed to load. Try reopening in a few seconds.')}
              >
                <source src={animationSrc} type="video/mp4" />
              Your browser does not support the video tag.
              </video>
            </>
          ) : (
            <Typography variant="body2" color="text.secondary">
              Animation is not available.
            </Typography>
          )}
        </DialogContent>
      </Dialog>
    </Box>
  )
}

export default VideoUpload
