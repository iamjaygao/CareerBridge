import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Button,
  Paper,
  IconButton,
} from '@mui/material';
import {
  ArrowForward as ArrowForwardIcon,
  Close as CloseIcon,
} from '@mui/icons-material';

interface RegistrationBannerProps {
  title: string;
  description: string;
  onClose?: () => void;
  showCloseButton?: boolean;
}

const RegistrationBanner: React.FC<RegistrationBannerProps> = ({
  title,
  description,
  onClose,
  showCloseButton = true,
}) => {
  const navigate = useNavigate();
  const [dismissed, setDismissed] = React.useState(false);

  const handleClose = () => {
    setDismissed(true);
    if (onClose) {
      onClose();
    }
  };

  if (dismissed) {
    return null;
  }

  return (
    <Paper
      elevation={3}
      sx={{
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white',
        p: 3,
        mb: 4,
        position: 'relative',
        borderRadius: 2,
      }}
    >
      {showCloseButton && (
        <IconButton
          onClick={handleClose}
          sx={{
            position: 'absolute',
            top: 8,
            right: 8,
            color: 'white',
            '&:hover': {
              bgcolor: 'rgba(255, 255, 255, 0.1)',
            },
          }}
        >
          <CloseIcon />
        </IconButton>
      )}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
        <Box sx={{ flex: 1, minWidth: 250 }}>
          <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
            {title}
          </Typography>
          <Typography variant="body2" sx={{ opacity: 0.9 }}>
            {description}
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <Button
            variant="outlined"
            onClick={() => navigate('/login')}
            sx={{
              borderColor: 'white',
              color: 'white',
              '&:hover': {
                borderColor: 'rgba(255, 255, 255, 0.8)',
                bgcolor: 'rgba(255, 255, 255, 0.1)',
              },
            }}
          >
            Sign In
          </Button>
          <Button
            variant="contained"
            onClick={() => navigate('/register')}
            endIcon={<ArrowForwardIcon />}
            sx={{
              bgcolor: 'white',
              color: 'primary.main',
              '&:hover': {
                bgcolor: 'rgba(255, 255, 255, 0.9)',
              },
            }}
          >
            Get Started Free
          </Button>
        </Box>
      </Box>
    </Paper>
  );
};

export default RegistrationBanner;

