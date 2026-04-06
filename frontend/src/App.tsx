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
  Alert
} from '@mui/material'
import VideoUpload from './components/VideoUpload.js'

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
})

function App() {
  const [page, setPage] = useState('home')
  const [message, setMessage] = useState('')

  React.useEffect(() => {
    // Test API connection
    fetch('/api/v1/health')
      .then(res => res.json())
      .then(data => setMessage(`✅ Backend Connected: ${data.status}`))
      .catch(err => setMessage(`⚠️ Backend Connection Error: ${err.message}`))
  }, [])

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
        <AppBar position="static">
          <Toolbar>
            <Typography component="span" sx={{ mr: 2, fontSize: 28, lineHeight: 1 }}>
              📶
            </Typography>
            <Typography variant="h6" component="div" sx={{ fontWeight: 600 }}>
              Autism Emotion Detection System
            </Typography>
          </Toolbar>
        </AppBar>

        <Box sx={{ flex: 1, py: 4 }}>
          <Container maxWidth="lg">
            <Paper elevation={3} sx={{ p: 4, borderRadius: 2 }}>
              <Typography variant="h4" gutterBottom>
                Welcome! 👋
              </Typography>
              
              {message && (
                <Alert severity={message.includes('✅') ? 'success' : 'warning'} sx={{ mb: 3 }}>
                  {message}
                </Alert>
              )}

              <Typography variant="body1" paragraph>
                The Autism Emotion Detection System is ready!
              </Typography>

              <VideoUpload />

              <Box sx={{ mt: 4, p: 3, backgroundColor: '#f3e5f5', borderRadius: 2 }}>
                <Typography variant="h6" gutterBottom>
                  🔗 API Documentation
                </Typography>
                <Typography variant="body2" color="textSecondary" paragraph>
                  View interactive API documentation and test endpoints
                </Typography>
                <Button 
                  variant="contained" 
                  color="secondary"
                  href="http://localhost:8000/docs"
                  target="_blank"
                >
                  Open Docs
                </Button>
              </Box>

              <Box sx={{ mt: 4, p: 2, backgroundColor: '#f5f5f5', borderRadius: 1 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Backend Status
                </Typography>
                <Typography variant="body2" color="textSecondary" component="div">
                  ✅ FastAPI Server: http://localhost:8000
                </Typography>
                <Typography variant="body2" color="textSecondary" component="div">
                  ✅ React Frontend: http://localhost:3000
                </Typography>
              </Box>
            </Paper>
          </Container>
        </Box>

        <Box component="footer" sx={{ py: 3, backgroundColor: '#f5f5f5', borderTop: '1px solid #e0e0e0' }}>
          <Container maxWidth="lg">
            <Typography variant="body2" color="textSecondary" align="center">
              © 2026 Autism Emotion Detection System v1.0.0 | All Rights Reserved
            </Typography>
          </Container>
        </Box>
      </Box>
    </ThemeProvider>
  )
}

export default App
