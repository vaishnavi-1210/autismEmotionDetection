import React, { useState } from 'react'
import {
  Container,
  Box,
  AppBar,
  Toolbar,
  Typography,
  CssBaseline,
  ThemeProvider,
  createTheme,
  Paper,
  Button,
  Alert,
  Chip,
  Stack,
} from '@mui/material'
import VideoUpload from './components/VideoUpload'

const theme = createTheme({
  shape: {
    borderRadius: 18,
  },
  typography: {
    fontFamily: '"Manrope", "Segoe UI", sans-serif',
    h3: {
      fontWeight: 800,
      letterSpacing: '-0.03em',
    },
    h6: {
      fontWeight: 700,
    },
  },
  palette: {
    mode: 'light',
    primary: {
      main: '#1f3a5f',
    },
    secondary: {
      main: '#2a9d8f',
    },
    background: {
      default: '#eef2f7',
      paper: '#ffffff',
    },
    text: {
      primary: '#1d293d',
      secondary: '#4f5f79',
    },
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          boxShadow: '0 18px 40px rgba(19, 35, 64, 0.08)',
          border: '1px solid rgba(31, 58, 95, 0.08)',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          textTransform: 'none',
          fontWeight: 700,
        },
      },
    },
  },
})

function App() {
  const [message, setMessage] = useState('Checking backend connection...')
  const [isHealthy, setIsHealthy] = useState(false)

  React.useEffect(() => {
    fetch('/api/v1/health')
      .then(res => res.json())
      .then(data => {
        setMessage(`Backend connected: ${data.status}`)
        setIsHealthy(true)
      })
      .catch(err => {
        setMessage(`Backend connection error: ${err.message}`)
        setIsHealthy(false)
      })
  }, [])

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box
        sx={{
          minHeight: '100vh',
          background: 'linear-gradient(135deg, #edf2f8 0%, #f7f9fc 48%, #e9eff7 100%)',
          position: 'relative',
          overflow: 'hidden',
          '&::before': {
            content: '""',
            position: 'absolute',
            width: 420,
            height: 420,
            top: -180,
            right: -120,
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(42,157,143,0.17), rgba(42,157,143,0))',
            pointerEvents: 'none',
          },
          '&::after': {
            content: '""',
            position: 'absolute',
            width: 380,
            height: 380,
            bottom: -180,
            left: -120,
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(31,58,95,0.2), rgba(31,58,95,0))',
            pointerEvents: 'none',
          },
        }}
      >
        <AppBar
          position="sticky"
          elevation={0}
          sx={{
            backgroundColor: 'rgba(255, 255, 255, 0.78)',
            backdropFilter: 'blur(10px)',
            borderBottom: '1px solid rgba(31, 58, 95, 0.08)',
            color: 'text.primary',
          }}
        >
          <Toolbar sx={{ py: 0.5 }}>
            <Typography variant="h6" component="div">
              AutismIQ
            </Typography>
            <Box sx={{ flex: 1 }} />
            <Chip
              label={isHealthy ? 'System Online' : 'System Check'}
              size="small"
              color={isHealthy ? 'success' : 'warning'}
              variant="outlined"
            />
          </Toolbar>
        </AppBar>

        <Box sx={{ py: { xs: 4, md: 7 }, position: 'relative', zIndex: 1 }}>
          <Container maxWidth="lg">
            <Paper sx={{ p: { xs: 3, md: 5 } }}>
              <Stack spacing={1.5} sx={{ mb: 3.5 }}>
                <Typography variant="h3" sx={{ fontSize: { xs: '2rem', md: '2.6rem' } }}>
                  Behavior Intelligence Dashboard
                </Typography>
                <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 720 }}>
                  Upload one video, track end-to-end progress in a single clean timeline, and get the final model prediction in a focused result popup.
                </Typography>
              </Stack>

              {message && (
                <Alert
                  severity={isHealthy ? 'success' : 'warning'}
                  sx={{
                    mb: 3,
                    border: '1px solid',
                    borderColor: isHealthy ? 'success.light' : 'warning.light',
                    backgroundColor: isHealthy ? 'rgba(46,125,50,0.08)' : 'rgba(237,108,2,0.08)',
                  }}
                >
                  {message}
                </Alert>
              )}

              <VideoUpload />

              <Box
                sx={{
                  mt: 4,
                  display: 'flex',
                  justifyContent: 'space-between',
                  flexDirection: { xs: 'column', sm: 'row' },
                  gap: 2,
                  alignItems: { xs: 'flex-start', sm: 'center' },
                  borderTop: '1px solid rgba(31,58,95,0.12)',
                  pt: 3,
                }}
              >
                <Typography variant="body2" color="text.secondary">
                  Professional UI mode enabled. Processing logic remains unchanged.
                </Typography>
                <Button
                  variant="outlined"
                  color="primary"
                  href="http://localhost:8000/docs"
                  target="_blank"
                >
                  API Docs
                </Button>
              </Box>
            </Paper>
          </Container>
        </Box>

        <Box
          component="footer"
          sx={{
            py: 2.5,
            borderTop: '1px solid rgba(31,58,95,0.08)',
            backgroundColor: 'rgba(255, 255, 255, 0.76)',
            position: 'relative',
            zIndex: 1,
          }}
        >
          <Container maxWidth="lg">
            <Typography variant="body2" color="text.secondary" align="center">
              AutismIQ v1.0.0
            </Typography>
          </Container>
        </Box>
      </Box>
    </ThemeProvider>
  )
}

export default App
