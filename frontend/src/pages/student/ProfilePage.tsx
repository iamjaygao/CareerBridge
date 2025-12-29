import React, { useState, useEffect, useRef } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  Box,
  Typography,
  Card,
  CardContent,
  TextField,
  Button,
  Grid,
  Avatar,
  Divider,
  Alert,
} from '@mui/material';
import {
  Save as SaveIcon,
  Upload as UploadIcon,
  Lock as LockIcon,
  VerifiedUser as VerifiedUserIcon,
} from '@mui/icons-material';
import { RootState } from '../../store';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import authService from '../../services/auth/authService';
import { fetchUserProfile } from '../../store/slices/authSlice';

const StudentProfilePage: React.FC = () => {
  const dispatch = useDispatch();
  const { user } = useSelector((state: RootState) => state.auth);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [avatarUploading, setAvatarUploading] = useState(false);
  const [passwordSaving, setPasswordSaving] = useState(false);
  const [verifyingEmail, setVerifyingEmail] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [usernameStatus, setUsernameStatus] = useState<{ can_change: boolean; days_left: number } | null>(null);
  const [formData, setFormData] = useState({
    username: user?.username || '',
    email: user?.email || '',
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    phone: user?.phone || '',
    location: user?.location || '',
  });
  const [passwordForm, setPasswordForm] = useState({
    old_password: '',
    new_password: '',
    new_password_confirm: '',
  });
  const avatarInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    const hydrate = async () => {
      try {
        const status = await authService.getUsernameChangeStatus();
        setUsernameStatus(status);
      } catch {
        setUsernameStatus(null);
      } finally {
        setLoading(false);
      }
    };

    hydrate();
  }, []);

  useEffect(() => {
    setFormData({
      username: user?.username || '',
      email: user?.email || '',
      first_name: user?.first_name || '',
      last_name: user?.last_name || '',
      phone: user?.phone || '',
      location: user?.location || '',
    });
  }, [user]);

  const handleProfileSave = async () => {
    if (!user) return;
    if (usernameStatus && !usernameStatus.can_change && formData.username !== user.username) {
      setErrorMessage(`Username can be changed in ${usernameStatus.days_left} days.`);
      return;
    }
    setSaving(true);
    setSuccessMessage(null);
    setErrorMessage(null);
    try {
      await authService.updateProfile({
        username: formData.username,
        email: formData.email,
        first_name: formData.first_name,
        last_name: formData.last_name,
        phone: formData.phone,
        location: formData.location,
      });
      await dispatch(fetchUserProfile() as any);
      setSuccessMessage('Profile updated.');
    } catch (error: any) {
      setErrorMessage(error?.response?.data?.detail || 'Failed to update profile.');
    } finally {
      setSaving(false);
    }
  };

  const handleAvatarUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setAvatarUploading(true);
    setSuccessMessage(null);
    setErrorMessage(null);
    try {
      await authService.uploadAvatar(file);
      await dispatch(fetchUserProfile() as any);
      setSuccessMessage('Avatar updated.');
    } catch (error: any) {
      setErrorMessage(error?.response?.data?.error || 'Failed to upload avatar.');
    } finally {
      setAvatarUploading(false);
      if (avatarInputRef.current) {
        avatarInputRef.current.value = '';
      }
    }
  };

  const handlePasswordSave = async () => {
    setPasswordSaving(true);
    setSuccessMessage(null);
    setErrorMessage(null);
    try {
      await authService.changePassword(passwordForm);
      setPasswordForm({ old_password: '', new_password: '', new_password_confirm: '' });
      setSuccessMessage('Password updated.');
    } catch (error: any) {
      setErrorMessage(error?.response?.data?.detail || error?.response?.data?.non_field_errors?.[0] || 'Failed to update password.');
    } finally {
      setPasswordSaving(false);
    }
  };

  const handleResendVerification = async () => {
    if (!user?.email) return;
    setVerifyingEmail(true);
    setSuccessMessage(null);
    setErrorMessage(null);
    try {
      await authService.resendVerification(user.email);
      setSuccessMessage('Verification email sent. Please check your inbox.');
    } catch (error: any) {
      setErrorMessage(error?.response?.data?.email?.[0] || 'Failed to resend verification email.');
    } finally {
      setVerifyingEmail(false);
    }
  };

  if (loading) {
    return <LoadingSpinner message="Loading profile..." />;
  }

  return (
    <Box>
      {/* Page Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
          Profile
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Manage your personal information, security, and payouts
        </Typography>
        {successMessage && (
          <Alert severity="success" sx={{ mt: 2 }}>
            {successMessage}
          </Alert>
        )}
        {errorMessage && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {errorMessage}
          </Alert>
        )}
      </Box>

      <Grid container spacing={3}>
        {/* Profile Overview */}
        <Grid item xs={12} md={4} lg={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Avatar
                src={user?.avatar}
                sx={{
                  width: 120,
                  height: 120,
                  mx: 'auto',
                  mb: 2,
                  bgcolor: 'primary.main',
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                }}
              >
                {user?.first_name?.[0] || user?.username?.[0] || 'U'}
              </Avatar>
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                {user?.first_name || user?.last_name ? `${user?.first_name || ''} ${user?.last_name || ''}`.trim() : user?.username}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {user?.role || 'member'}
              </Typography>
              <Button
                variant="outlined"
                startIcon={<UploadIcon />}
                fullWidth
                onClick={() => avatarInputRef.current?.click()}
                disabled={avatarUploading}
              >
                {avatarUploading ? 'Uploading...' : 'Upload Photo'}
              </Button>
              <input
                ref={avatarInputRef}
                type="file"
                accept="image/*"
                onChange={handleAvatarUpload}
                style={{ display: 'none' }}
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Account Details */}
        <Grid item xs={12} md={8} lg={9}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                Account Details
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Username"
                    value={formData.username}
                    onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                    helperText={
                      usernameStatus && !usernameStatus.can_change
                        ? `Username change available in ${usernameStatus.days_left} days`
                        : 'Shown publicly'
                    }
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Email"
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    helperText="Used for login and notifications"
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="First Name"
                    value={formData.first_name}
                    onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Last Name"
                    value={formData.last_name}
                    onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Contact & Verification */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                Contact & Verification
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Email Status"
                    value={user?.email_verified ? 'Verified' : 'Unverified'}
                    disabled
                    helperText={user?.email_verified ? 'Your email is verified.' : 'Please verify your email.'}
                  />
                  {!user?.email_verified && (
                    <Button
                      variant="outlined"
                      size="small"
                      sx={{ mt: 1 }}
                      onClick={handleResendVerification}
                      disabled={verifyingEmail}
                    >
                      {verifyingEmail ? 'Sending...' : 'Resend Verification Email'}
                    </Button>
                  )}
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Phone Number"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    helperText="Add a number for account recovery"
                  />
                  <Button variant="outlined" size="small" sx={{ mt: 1 }} disabled>
                    Verify Phone (coming soon)
                  </Button>
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Location"
                    value={formData.location}
                    onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                    helperText="City, region, or timezone"
                  />
                </Grid>
                <Grid item xs={12}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <VerifiedUserIcon color="action" />
                    <Typography variant="body2" color="text.secondary">
                      Email verification and identity checks will appear here.
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Security */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <LockIcon color="action" />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Security
                </Typography>
              </Box>
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Current Password"
                    type="password"
                    value={passwordForm.old_password}
                    onChange={(e) => setPasswordForm({ ...passwordForm, old_password: e.target.value })}
                    helperText="Use at least 8 characters with a mix of letters and numbers."
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="New Password"
                    type="password"
                    value={passwordForm.new_password}
                    onChange={(e) => setPasswordForm({ ...passwordForm, new_password: e.target.value })}
                    helperText="Avoid reusing old passwords."
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Confirm New Password"
                    type="password"
                    value={passwordForm.new_password_confirm}
                    onChange={(e) => setPasswordForm({ ...passwordForm, new_password_confirm: e.target.value })}
                  />
                </Grid>
                <Grid item xs={12}>
                  <Button
                    variant="outlined"
                    fullWidth
                    onClick={handlePasswordSave}
                    disabled={passwordSaving}
                  >
                    {passwordSaving ? 'Saving...' : 'Update Password'}
                  </Button>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Save Button */}
        <Grid item xs={12}>
          <Divider sx={{ mb: 2 }} />
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
            <Button
              variant="contained"
              startIcon={<SaveIcon />}
              onClick={handleProfileSave}
              disabled={saving}
              sx={{
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                '&:hover': {
                  background: 'linear-gradient(135deg, #5568d3 0%, #6a3d8f 100%)',
                },
              }}
            >
              {saving ? 'Saving...' : 'Save Changes'}
            </Button>
          </Box>
        </Grid>
      </Grid>
    </Box>
  );
};

export default StudentProfilePage;
