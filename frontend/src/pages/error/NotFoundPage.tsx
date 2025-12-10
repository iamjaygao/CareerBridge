import React from 'react';
import {
  Box,
  Typography,
  Button,
  Container,
  Paper,
} from '@mui/material';
import {
  Home as HomeIcon,
  ArrowBack as ArrowBackIcon,
  Search as SearchIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

const NotFoundPage: React.FC = () => {
  const navigate = useNavigate();

  const handleGoHome = () => {
    navigate('/dashboard');
  };

  const handleGoBack = () => {
    navigate(-1);
  };

  const handleSearch = () => {
    navigate('/');
  };

  return (
    <Box sx={{ width: '100%', maxWidth: '1200px', mx: 'auto', px: { xs: 2, sm: 3, md: 6 }, py: { xs: 4, md: 6 } }}>
      <Container maxWidth="md">
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '60vh',
            textAlign: 'center',
          }}
        >
          <Paper
            elevation={3}
            sx={{
              p: 6,
              borderRadius: 2,
              maxWidth: 500,
              width: '100%',
            }}
          >
            {/* 404 Icon */}
            <Box
              sx={{
                fontSize: '6rem',
                fontWeight: 'bold',
                color: 'primary.main',
                mb: 2,
                lineHeight: 1,
              }}
            >
              404
            </Box>

            {/* Title */}
            <Typography variant="h4" gutterBottom>
              Page Not Found
            </Typography>

            {/* Description */}
            <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
              Sorry, the page you are looking for doesn't exist or has been moved.
              Please check the URL or try one of the options below.
            </Typography>

            {/* Action Buttons */}
            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
              <Button
                variant="contained"
                startIcon={<HomeIcon />}
                onClick={handleGoHome}
                size="large"
              >
                Go Home
              </Button>
              <Button
                variant="outlined"
                startIcon={<ArrowBackIcon />}
                onClick={handleGoBack}
                size="large"
              >
                Go Back
              </Button>
              <Button
                variant="outlined"
                startIcon={<SearchIcon />}
                onClick={handleSearch}
                size="large"
              >
                Search
              </Button>
            </Box>

            {/* Helpful Links */}
            <Box sx={{ mt: 4, pt: 3, borderTop: 1, borderColor: 'divider' }}>
              <Typography variant="h6" gutterBottom>
                Popular Pages
              </Typography>
              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
                <Button
                  variant="text"
                  onClick={() => navigate('/mentors')}
                  size="small"
                >
                  Find Mentors
                </Button>
                <Button
                  variant="text"
                  onClick={() => navigate('/assessment')}
                  size="small"
                >
                  Assessment Engine
                </Button>
                <Button
                  variant="text"
                  onClick={() => navigate('/appointments')}
                  size="small"
                >
                  Appointments
                </Button>
                <Button
                  variant="text"
                  onClick={() => navigate('/profile')}
                  size="small"
                >
                  Profile
                </Button>
              </Box>
            </Box>
          </Paper>
        </Box>
      </Container>
    </Box>
  );
};

export default NotFoundPage; 