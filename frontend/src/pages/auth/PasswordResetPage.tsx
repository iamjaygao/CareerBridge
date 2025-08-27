import React, { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Container,
  Paper,
  TextField,
  Alert,
  Stepper,
  Step,
  StepLabel,
  CircularProgress,
} from '@mui/material';
import {
  Email as EmailIcon,
  Lock as LockIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useForm, Controller } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import authService from '../../services/auth/authService';
import { useNotification } from '../../components/common/NotificationProvider';
import ResponsiveContainer from '../../components/common/ResponsiveContainer';

const steps = ['Request Reset', 'Reset Password', 'Complete'];

const requestSchema = yup.object({
  email: yup.string().email('Invalid email address').required('Email is required'),
});

const resetSchema = yup.object({
  new_password: yup
    .string()
    .min(8, 'Password must be at least 8 characters')
    .matches(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/, 'Password must contain at least one uppercase letter, one lowercase letter, and one number')
    .required('Password is required'),
  new_password_confirm: yup
    .string()
    .oneOf([yup.ref('new_password')], 'Passwords must match')
    .required('Please confirm your password'),
});

const PasswordResetPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { showSuccess, showError } = useNotification();
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);

  const token = searchParams.get('token');

  const requestForm = useForm({
    resolver: yupResolver(requestSchema),
    defaultValues: {
      email: '',
    },
  });

  const resetForm = useForm({
    resolver: yupResolver(resetSchema),
    defaultValues: {
      new_password: '',
      new_password_confirm: '',
    },
  });

  const handleRequestReset = async (data: { email: string }) => {
    setLoading(true);
    try {
      await authService.requestPasswordReset(data.email);
      setActiveStep(1);
      showSuccess('Password reset email sent successfully');
    } catch (error) {
      showError('Failed to send password reset email');
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async (data: { new_password: string; new_password_confirm: string }) => {
    if (!token) {
      showError('Invalid reset token');
      return;
    }

    setLoading(true);
    try {
      await authService.resetPassword(token, data.new_password, data.new_password_confirm);
      setActiveStep(2);
      showSuccess('Password reset successfully');
    } catch (error) {
      showError('Failed to reset password');
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
              <LockIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
              <Typography variant="h4" gutterBottom>
                Password Reset
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Reset your password to regain access to your account
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

            {/* Step 1: Request Reset */}
            {activeStep === 0 && (
              <form onSubmit={requestForm.handleSubmit(handleRequestReset)}>
                <Alert severity="info" sx={{ mb: 3 }}>
                  Enter your email address and we'll send you a link to reset your password.
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
                  {loading ? 'Sending...' : 'Send Reset Link'}
                </Button>
              </form>
            )}

            {/* Step 2: Reset Password */}
            {activeStep === 1 && (
              <form onSubmit={resetForm.handleSubmit(handleResetPassword)}>
                <Alert severity="info" sx={{ mb: 3 }}>
                  Check your email for the reset link and enter your new password below.
                </Alert>

                <Controller
                  name="new_password"
                  control={resetForm.control}
                  render={({ field, fieldState: { error } }) => (
                    <TextField
                      {...field}
                      fullWidth
                      label="New Password"
                      type="password"
                      error={!!error}
                      helperText={error?.message}
                      sx={{ mb: 3 }}
                    />
                  )}
                />

                <Controller
                  name="new_password_confirm"
                  control={resetForm.control}
                  render={({ field, fieldState: { error } }) => (
                    <TextField
                      {...field}
                      fullWidth
                      label="Confirm New Password"
                      type="password"
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
                  startIcon={loading ? <CircularProgress size={20} /> : <LockIcon />}
                >
                  {loading ? 'Resetting...' : 'Reset Password'}
                </Button>
              </form>
            )}

            {/* Step 3: Complete */}
            {activeStep === 2 && (
              <Box sx={{ textAlign: 'center' }}>
                <CheckCircleIcon sx={{ fontSize: 64, color: 'success.main', mb: 2 }} />
                <Typography variant="h6" gutterBottom>
                  Password Reset Complete
                </Typography>
                <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
                  Your password has been successfully reset. You can now log in with your new password.
                </Typography>
                <Button
                  variant="contained"
                  size="large"
                  onClick={handleGoToLogin}
                  fullWidth
                >
                  Go to Login
                </Button>
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

export default PasswordResetPage; 