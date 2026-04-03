import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  CardContent,
  Button,
  Typography,
  Avatar,
  Box,
  TextField,
  Divider,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Alert,
  Tabs,
  Tab,
  Grid,
} from '@mui/material';
import {
  Edit as EditIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
  PhotoCamera as PhotoCameraIcon,
  Person as PersonIcon,
  Security as SecurityIcon,
  Notifications as NotificationsIcon,
  Work as WorkIcon,
  LocationOn as LocationIcon,
  Phone as PhoneIcon,
  Language as LanguageIcon,
  ArrowBack as ArrowBackIcon,
} from '@mui/icons-material';
import axios from 'axios';
import { useDispatch } from 'react-redux';

import { useAuth } from '../../contexts/AuthContext';
import { fetchUserProfile } from '../../store/slices/authSlice';
import { useNotification } from '../../components/common/NotificationProvider';
import PageHeader from '../../components/common/PageHeader';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ResponsiveContainer from '../../components/common/ResponsiveContainer';
import FileUpload from '../../components/common/FileUpload';
import { getLandingPathByRole } from '../../utils/roleLanding';

const API_BASE_URL =
  process.env.REACT_APP_API_URL || '/api/v1';

const ProfilePage: React.FC = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { user, loading } = useAuth();
  const { showSuccess, showError } = useNotification();

  const [isEditing, setIsEditing] = useState(false);
  const [avatarDialogOpen, setAvatarDialogOpen] = useState(false);
  const [avatarFile, setAvatarFile] = useState<File | null>(null);
  const [uploadingAvatar, setUploadingAvatar] = useState(false);
  const [tabValue, setTabValue] = useState(0);

  const [formData, setFormData] = useState({
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    username: user?.username || '',
    email: user?.email || '',
    phone: user?.phone || '',
    location: user?.location || '',
    bio: user?.bio || '',
    linkedin_url: user?.linkedin_url || '',
    github_url: user?.github_url || '',
  });

  if (loading) return <LoadingSpinner />;
  if (!user) return <div>User not found</div>;

  const resetForm = () => {
    setFormData({
      first_name: user.first_name || '',
      last_name: user.last_name || '',
      username: user.username,
      email: user.email,
      phone: user.phone || '',
      location: user.location || '',
      bio: user.bio || '',
      linkedin_url: user.linkedin_url || '',
      github_url: user.github_url || '',
    });
  };

  const handleSave = async () => {
    try {
      await axios.put(
        `${API_BASE_URL}/users/me/`,
        formData,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          },
        }
      );

      await dispatch(fetchUserProfile() as any);

      showSuccess('Profile updated successfully');
      setIsEditing(false);
    } catch (error) {
      console.error(error);
      showError('Failed to update profile');
    }
  };

  const handleAvatarUpload = async () => {
    if (!avatarFile) return;

    const data = new FormData();
    data.append('avatar', avatarFile);

    setUploadingAvatar(true);
    try {
      await axios.post(
        `${API_BASE_URL}/users/avatar/`,
        data,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          },
        }
      );

      await dispatch(fetchUserProfile() as any);

      showSuccess('Avatar updated successfully');
      setAvatarDialogOpen(false);
      setAvatarFile(null);
    } catch (error) {
      console.error(error);
      showError('Failed to upload avatar');
    } finally {
      setUploadingAvatar(false);
    }
  };

  return (
    <ResponsiveContainer>
      <PageHeader
        title="Profile"
        breadcrumbs={[{ label: 'Profile', path: '/profile' }]}
        action={
          <Button
            variant="text"
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate(getLandingPathByRole(user?.role))}
          >
            Back to Dashboard
          </Button>
        }
      />

      <Grid container spacing={3}>
        {/* Left card */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Box sx={{ position: 'relative', display: 'inline-block' }}>
                <Avatar
                  src={user.avatar}
                  sx={{ width: 120, height: 120, mb: 2 }}
                />
                <IconButton
                  sx={{ position: 'absolute', bottom: 8, right: 8 }}
                  onClick={() => setAvatarDialogOpen(true)}
                >
                  <PhotoCameraIcon />
                </IconButton>
              </Box>

              <Typography variant="h5">
                {user.first_name} {user.last_name}
              </Typography>
              <Typography color="text.secondary">@{user.username}</Typography>
              <Typography color="text.secondary">{user.email}</Typography>

              <Box sx={{ mt: 2 }}>
                <Chip label={user.role} color="primary" size="small" />
                {user.is_verified && (
                  <Chip label="Verified" color="success" size="small" sx={{ ml: 1 }} />
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Right card */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="h6">Profile Information</Typography>
                {!isEditing ? (
                  <Button startIcon={<EditIcon />} onClick={() => setIsEditing(true)}>
                    Edit
                  </Button>
                ) : (
                  <Box>
                    <Button startIcon={<SaveIcon />} onClick={handleSave} sx={{ mr: 1 }}>
                      Save
                    </Button>
                    <Button
                      startIcon={<CancelIcon />}
                      onClick={() => {
                        resetForm();
                        setIsEditing(false);
                      }}
                    >
                      Cancel
                    </Button>
                  </Box>
                )}
              </Box>

              <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)} sx={{ mb: 3 }}>
                <Tab icon={<PersonIcon />} label="Personal" />
                <Tab icon={<WorkIcon />} label="Professional" />
                <Tab icon={<SecurityIcon />} label="Security" />
              </Tabs>

              {tabValue === 0 && (
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      label="First Name"
                      value={formData.first_name}
                      disabled={!isEditing}
                      onChange={(e) =>
                        setFormData({ ...formData, first_name: e.target.value })
                      }
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      label="Last Name"
                      value={formData.last_name}
                      disabled={!isEditing}
                      onChange={(e) =>
                        setFormData({ ...formData, last_name: e.target.value })
                      }
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <TextField fullWidth label="Username" value={formData.username} disabled />
                  </Grid>
                  <Grid item xs={6}>
                    <TextField fullWidth label="Email" value={formData.email} disabled />
                  </Grid>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      label="Phone"
                      value={formData.phone}
                      disabled={!isEditing}
                      onChange={(e) =>
                        setFormData({ ...formData, phone: e.target.value })
                      }
                      InputProps={{ startAdornment: <PhoneIcon sx={{ mr: 1 }} /> }}
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      label="Location"
                      value={formData.location}
                      disabled={!isEditing}
                      onChange={(e) =>
                        setFormData({ ...formData, location: e.target.value })
                      }
                      InputProps={{ startAdornment: <LocationIcon sx={{ mr: 1 }} /> }}
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      multiline
                      rows={3}
                      label="Bio"
                      value={formData.bio}
                      disabled={!isEditing}
                      onChange={(e) =>
                        setFormData({ ...formData, bio: e.target.value })
                      }
                    />
                  </Grid>
                </Grid>
              )}

              {tabValue === 1 && (
                <Grid container spacing={2}>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="LinkedIn URL"
                      value={formData.linkedin_url}
                      disabled={!isEditing}
                      onChange={(e) =>
                        setFormData({ ...formData, linkedin_url: e.target.value })
                      }
                      InputProps={{ startAdornment: <LanguageIcon sx={{ mr: 1 }} /> }}
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="GitHub URL"
                      value={formData.github_url}
                      disabled={!isEditing}
                      onChange={(e) =>
                        setFormData({ ...formData, github_url: e.target.value })
                      }
                      InputProps={{ startAdornment: <LanguageIcon sx={{ mr: 1 }} /> }}
                    />
                  </Grid>
                </Grid>
              )}

              {tabValue === 2 && (
                <Alert severity="info">
                  Security settings are managed in the Settings page.
                </Alert>
              )}

              <Divider sx={{ my: 3 }} />

              <Typography variant="body2" color="text.secondary">
                Member since:{' '}
                {user.created_at
                  ? new Date(user.created_at).toLocaleDateString()
                  : 'N/A'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Avatar dialog */}
      <Dialog open={avatarDialogOpen} onClose={() => setAvatarDialogOpen(false)}>
        <DialogTitle>Update Avatar</DialogTitle>
        <DialogContent>
          <FileUpload
            onFileSelect={setAvatarFile}
            onFileRemove={() => setAvatarFile(null)}
            currentFile={avatarFile}
            loading={uploadingAvatar}
            acceptedTypes={['image/jpeg', 'image/png']}
            maxSize={5 * 1024 * 1024}
            title="Upload Avatar"
            subtitle="JPG / PNG up to 5MB"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAvatarDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleAvatarUpload}
            disabled={!avatarFile || uploadingAvatar}
          >
            Upload
          </Button>
        </DialogActions>
      </Dialog>
    </ResponsiveContainer>
  );
};

export default ProfilePage;
