import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  useNavigate,
  Link as RouterLink,
  useLocation,
} from 'react-router-dom';
import {
  Container,
  Paper,
  TextField,
  Button,
  Typography,
  Box,
  Link,
  Alert,
  CircularProgress,
} from '@mui/material';
import { LockOutlined } from '@mui/icons-material';
import { useForm } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';

import { loginUser, clearError } from '../../store/slices/authSlice';
import { RootState, AppDispatch } from '../../store';
import { getLandingPathByRole } from '../../utils/roleLanding';

// ========================
// Validation schema
// ========================

const schema = yup.object({
  login: yup.string().required('Username or email is required'),
  password: yup.string().required('Password is required'),
});

interface LoginFormData {
  login: string;
  password: string;
}

const LoginPage: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const navigate = useNavigate();
  const location = useLocation();

  const { loading, error } = useSelector((state: RootState) => state.auth);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: yupResolver(schema),
  });

  // Clear authentication errors on component unmount
  useEffect(() => {
    return () => {
      dispatch(clearError());
    };
  }, [dispatch]);

  // ========================
  // Login submit
  // ========================

  const onSubmit = async (data: LoginFormData) => {
    try {
      // 1. Dispatch login action and unwrap the result
      const result = await dispatch(
        loginUser({
          identifier: data.login,
          password: data.password,
        })
      ).unwrap();

      // 2. Extract user object (includes is_superuser, is_staff, role)
      const user = result.user;
      
      // 3. Determine the landing path using the robust helper (checks Django flags)
      const landingPath = getLandingPathByRole(user);

      // 4. Defensive check: If the role maps back to /login, 
      // it means the user is undefined or not configured in frontend
      if (landingPath === '/login') {
        console.error('[LOGIN] Access Denied: Unrecognized role configuration');
        // We let the authSlice error state handle the UI feedback if needed, 
        // or redirect to a general error/unauthorized page.
        return;
      }

      // 5. Final navigation logic (priority: intercepted route > role dashboard)
      const redirectTo = (location.state as any)?.redirectTo || landingPath;

      console.log(`[LOGIN] Success! Navigating to: ${redirectTo}`);
      navigate(redirectTo, { replace: true });
      
    } catch (e) {
      console.error('[LOGIN] Process failed:', e);
    }
  };

  // ========================
  // UI
  // ========================

  return (
    <Container component="main" maxWidth="xs">
      <Box
        sx={{
          marginTop: 8,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        <Paper
          elevation={3}
          sx={{
            padding: 4,
            width: '100%',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
          }}
        >
          <Box
            sx={{
              backgroundColor: 'primary.main',
              borderRadius: '50%',
              width: 56,
              height: 56,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              mb: 2,
            }}
          >
            <LockOutlined sx={{ color: 'white' }} />
          </Box>

          <Typography component="h1" variant="h5" gutterBottom>
            Sign In
          </Typography>

          <Typography
            variant="body2"
            color="text.secondary"
            align="center"
            sx={{ mb: 3 }}
          >
            Welcome to CareerBridge
          </Typography>

          {error && (
            <Alert severity="error" sx={{ width: '100%', mb: 2 }}>
              {error}
            </Alert>
          )}

          <Box
            component="form"
            onSubmit={handleSubmit(onSubmit)}
            sx={{ width: '100%' }}
          >
            <TextField
              margin="normal"
              fullWidth
              label="Username or Email"
              autoComplete="username"
              autoFocus
              {...register('login')}
              error={!!errors.login}
              helperText={errors.login?.message}
              disabled={loading}
            />

            <TextField
              margin="normal"
              fullWidth
              label="Password"
              type="password"
              autoComplete="current-password"
              {...register('password')}
              error={!!errors.password}
              helperText={errors.password?.message}
              disabled={loading}
            />

            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2 }}
              disabled={loading}
            >
              {loading ? <CircularProgress size={24} /> : 'Sign In'}
            </Button>

            <Box sx={{ textAlign: 'center' }}>
              <Link component={RouterLink} to="/register" variant="body2">
                Don&apos;t have an account? Sign Up
              </Link>
            </Box>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
};

export default LoginPage;