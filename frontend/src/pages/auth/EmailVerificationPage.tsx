import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Typography,
  Button,
  Container,
  Paper,
  TextField,
  Alert,
  CircularProgress,
  Stepper,
  Step,
  StepLabel,
} from '@mui/material';
import {
  Email as EmailIcon,
  CheckCircle as CheckCircleIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useForm, Controller } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import authService from '../../services/auth/authService';
import { useNotification } from '../../components/common/NotificationProvider';
import ResponsiveContainer from '../../components/common/ResponsiveContainer';

const steps = ['Request Verification', 'Enter Code', 'Complete'];

const requestSchema = yup.object({
  email: yup.string().email('Invalid email address').required('Email is required'),
});

const verificationSchema = yup.object({
  token: yup.string().required('Verification code is required'),
});

const EmailVerificationPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { showSuccess, showError } = useNotification();
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [email, setEmail] = useState('');
  const [countdown, setCountdown] = useState(0);

  const token = searchParams.get('token');

  const requestForm = useForm({
    resolver: yupResolver(requestSchema),
    defaultValues: {
      email: '',
    },
  });

  const verificationForm = useForm({
    resolver: yupResolver(verificationSchema),
    defaultValues: {
      token: '',
    },
  });

  // Countdown timer
  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [countdown]);

  const handleVerifyToken = useCallback(async (verificationToken: string) => {
    setLoading(true);
    try {
      await authService.confirmEmailVerification(verificationToken);
      setActiveStep(2);
      showSuccess('Email verified successfully');
    } catch (error) {
      showError('Failed to verify email');
      setActiveStep(1);
    } finally {
      setLoading(false);
    }
  }, [showSuccess, showError]);

  // Auto-verify if token is in URL
  useEffect(() => {
    if (token) {
      handleVerifyToken(token);
    }
  }, [token, handleVerifyToken]);

  const handleRequestVerification = async (data: { email: string }) => {
    setLoading(true);
    try {
      await authService.requestEmailVerification(data.email);
      setEmail(data.email);
      setActiveStep(1);
      setCountdown(60); // 60 second countdown
      showSuccess('Verification email sent successfully');
    } catch (error) {
      showError('Failed to send verification email');
    } finally {
      setLoading(false);
    }
  };

  const handleManualVerification = async (data: { token: string }) => {
    await handleVerifyToken(data.token);
  };

  const handleResendVerification = async () => {
    if (!email) return;
    
    setLoading(true);
    try {
      await authService.requestEmailVerification(email);
      setCountdown(60);
      showSuccess('Verification email resent successfully');
    } catch (error) {
      showError('Failed to resend verification email');
    } finally {
      setLoading(false);
    }
  };


  const handleGoToLogin = () => {
    navigate('/login');
  };

  return (
    <ResponsiveContainer>
      <Container maxWidth="sm">
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '60vh',
          }}
        >
          <Paper
            elevation={3}
            sx={{
              p: 4,
              borderRadius: 2,
              width: '100%',
            }}
          >
            {/* Header */}
            <Box sx={{ textAlign: 'center', mb: 4 }}>
              <EmailIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
              <Typography variant="h4" gutterBottom>
                Email Verification
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Verify your email address to complete your account setup
              </Typography>
            </Box>

            {/* Stepper */}
            <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
              {steps.map((label) => (
                <Step key={label}>
                  <StepLabel>{label}</StepLabel>
                </Step>
              ))}
            </Stepper>

            {/* Step 1: Request Verification */}
            {activeStep === 0 && (
              <form onSubmit={requestForm.handleSubmit(handleRequestVerification)}>
                <Alert severity="info" sx={{ mb: 3 }}>
                  Enter your email address and we'll send you a verification code.
                </Alert>

                <Controller
                  name="email"
                  control={requestForm.control}
                  render={({ field, fieldState: { error } }) => (
                    <TextField
                      {...field}
                      fullWidth
                      label="Email Address"
                      type="email"
                      error={!!error}
                      helperText={error?.message}
                      sx={{ mb: 3 }}
                    />
                  )}
                />

                <Button
                  type="submit"
                  fullWidth
                  variant="contained"
                  size="large"
                  disabled={loading}
                  startIcon={loading ? <CircularProgress size={20} /> : <EmailIcon />}
                >
                  {loading ? 'Sending...' : 'Send Verification Code'}
                </Button>
              </form>
            )}

            {/* Step 2: Enter Code */}
            {activeStep === 1 && (
              <form onSubmit={verificationForm.handleSubmit(handleManualVerification)}>
                <Alert severity="info" sx={{ mb: 3 }}>
                  Check your email for the verification code and enter it below.
                </Alert>

                <Controller
                  name="token"
                  control={verificationForm.control}
                  render={({ field, fieldState: { error } }) => (
                    <TextField
                      {...field}
                      fullWidth
                      label="Verification Code"
                      error={!!error}
                      helperText={error?.message}
                      sx={{ mb: 3 }}
                    />
                  )}
                />

                <Button
                  type="submit"
                  fullWidth
                  variant="contained"
                  size="large"
                  disabled={loading}
                  startIcon={loading ? <CircularProgress size={20} /> : <CheckCircleIcon />}
                >
                  {loading ? 'Verifying...' : 'Verify Email'}
                </Button>

                {/* Resend Code */}
                <Box sx={{ textAlign: 'center', mt: 2 }}>
                  <Button
                    variant="text"
                    onClick={handleResendVerification}
                    disabled={countdown > 0 || loading}
                    startIcon={<RefreshIcon />}
                  >
                    {countdown > 0 ? `Resend in ${countdown}s` : 'Resend Code'}
                  </Button>
                </Box>
              </form>
            )}

            {/* Step 3: Complete */}
            {activeStep === 2 && (
              <Box sx={{ textAlign: 'center' }}>
                <CheckCircleIcon sx={{ fontSize: 64, color: 'success.main', mb: 2 }} />
                <Typography variant="h6" gutterBottom>
                  Email Verified Successfully
                </Typography>
                <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
                  Your email has been verified. You can now access all features of your account.
                </Typography>
              </Box>
            )}

            {/* Back to Login */}
            {activeStep < 2 && (
              <Box sx={{ textAlign: 'center', mt: 3 }}>
                <Button
                  variant="text"
                  onClick={handleGoToLogin}
                >
                  Back to Login
                </Button>
              </Box>
            )}
          </Paper>
        </Box>
      </Container>
    </ResponsiveContainer>
  );
};

export default EmailVerificationPage; 