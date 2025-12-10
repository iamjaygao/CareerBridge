import React, { useState } from 'react';
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
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';
import { useNotification } from '../../components/common/NotificationProvider';
import PageHeader from '../../components/common/PageHeader';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ResponsiveContainer from '../../components/common/ResponsiveContainer';
import FileUpload from '../../components/common/FileUpload';

const ProfilePage: React.FC = () => {
  const { user, updateProfile, loading } = useAuth();
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

  if (loading) {
    return <LoadingSpinner />;
  }

  if (!user) {
    return <div>User not found</div>;
  }

  const handleEdit = () => {
    setIsEditing(true);
  };

  const handleCancel = () => {
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
    setIsEditing(false);
  };

  const handleSave = async () => {
    try {
      await updateProfile(formData);
      showSuccess('Profile updated successfully');
      setIsEditing(false);
    } catch (error) {
      showError('Failed to update profile');
    }
  };

  const handleAvatarSelect = (file: File) => {
    setAvatarFile(file);
  };

  const handleAvatarRemove = () => {
    setAvatarFile(null);
  };

  const handleAvatarUpload = async () => {
    if (!avatarFile) return;

    setUploadingAvatar(true);
    try {
      // TODO: Implement actual avatar upload to backend
      // const formData = new FormData();
      // formData.append('avatar', avatarFile);
      // await userService.uploadAvatar(formData);
      
      showSuccess('Avatar uploaded successfully');
      setAvatarDialogOpen(false);
      setAvatarFile(null);
    } catch (error) {
      showError('Failed to upload avatar');
    } finally {
      setUploadingAvatar(false);
    }
  };

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  return (
    <ResponsiveContainer>
      <PageHeader
        title="Profile"
        breadcrumbs={[{ label: 'Profile', path: '/profile' }]}
      />

      <Grid container spacing={3}>
        {/* Profile Card */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Box sx={{ position: 'relative', display: 'inline-block' }}>
                <Avatar
                  src={user.avatar}
                  sx={{
                    width: 120,
                    height: 120,
                    mx: 'auto',
                    mb: 2,
                    border: '4px solid',
                    borderColor: 'primary.main',
                  }}
                />
                <IconButton
                  sx={{
                    position: 'absolute',
                    bottom: 8,
                    right: 8,
                    bgcolor: 'background.paper',
                    '&:hover': { bgcolor: 'background.paper' },
                  }}
                  onClick={() => setAvatarDialogOpen(true)}
                >
                  <PhotoCameraIcon />
                </IconButton>
              </Box>

              <Typography variant="h5" gutterBottom>
                {user.first_name} {user.last_name}
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                @{user.username}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {user.email}
              </Typography>

              <Box sx={{ mt: 2 }}>
                <Chip
                  label={user.role}
                  color="primary"
                  size="small"
                  sx={{ mr: 1 }}
                />
                {user.is_verified && (
                  <Chip
                    label="Verified"
                    color="success"
                    size="small"
                  />
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Profile Details */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="h6">Profile Information</Typography>
                {!isEditing ? (
                  <Button
                    startIcon={<EditIcon />}
                    onClick={handleEdit}
                  >
                    Edit
                  </Button>
                ) : (
                  <Box>
                    <Button
                      startIcon={<SaveIcon />}
                      onClick={handleSave}
                      sx={{ mr: 1 }}
                    >
                      Save
                    </Button>
                    <Button
                      startIcon={<CancelIcon />}
                      onClick={handleCancel}
                    >
                      Cancel
                    </Button>
                  </Box>
                )}
              </Box>

              <Tabs value={tabValue} onChange={handleTabChange} sx={{ mb: 3 }}>
                <Tab icon={<PersonIcon />} label="Personal Info" />
                <Tab icon={<WorkIcon />} label="Professional" />
                <Tab icon={<SecurityIcon />} label="Security" />
              </Tabs>

              {/* Personal Info Tab */}
              {tabValue === 0 && (
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="First Name"
                      value={formData.first_name}
                      onChange={(e) => handleInputChange('first_name', e.target.value)}
                      disabled={!isEditing}
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="Last Name"
                      value={formData.last_name}
                      onChange={(e) => handleInputChange('last_name', e.target.value)}
                      disabled={!isEditing}
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="Username"
                      value={formData.username}
                      onChange={(e) => handleInputChange('username', e.target.value)}
                      disabled={!isEditing}
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="Email"
                      value={formData.email}
                      onChange={(e) => handleInputChange('email', e.target.value)}
                      disabled={!isEditing}
                      type="email"
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="Phone"
                      value={formData.phone}
                      onChange={(e) => handleInputChange('phone', e.target.value)}
                      disabled={!isEditing}
                      InputProps={{
                        startAdornment: <PhoneIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                      }}
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="Location"
                      value={formData.location}
                      onChange={(e) => handleInputChange('location', e.target.value)}
                      disabled={!isEditing}
                      InputProps={{
                        startAdornment: <LocationIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                      }}
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Bio"
                      value={formData.bio}
                      onChange={(e) => handleInputChange('bio', e.target.value)}
                      disabled={!isEditing}
                      multiline
                      rows={3}
                      placeholder="Tell us about yourself..."
                    />
                  </Grid>
                </Grid>
              )}

              {/* Professional Tab */}
              {tabValue === 1 && (
                <Grid container spacing={2}>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="LinkedIn URL"
                      value={formData.linkedin_url}
                      onChange={(e) => handleInputChange('linkedin_url', e.target.value)}
                      disabled={!isEditing}
                      InputProps={{
                        startAdornment: <LanguageIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                      }}
                      placeholder="https://linkedin.com/in/yourprofile"
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="GitHub URL"
                      value={formData.github_url}
                      onChange={(e) => handleInputChange('github_url', e.target.value)}
                      disabled={!isEditing}
                      InputProps={{
                        startAdornment: <LanguageIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                      }}
                      placeholder="https://github.com/yourusername"
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <Alert severity="info">
                      Add your professional profiles to help mentors and employers find you.
                    </Alert>
                  </Grid>
                </Grid>
              )}

              {/* Security Tab */}
              {tabValue === 2 && (
                <Grid container spacing={2}>
                  <Grid item xs={12}>
                    <Alert severity="info">
                      Security settings are managed in the Settings page.
                    </Alert>
                  </Grid>
                  <Grid item xs={12}>
                    <List>
                      <ListItem>
                        <ListItemIcon>
                          <SecurityIcon />
                        </ListItemIcon>
                        <ListItemText 
                          primary="Change Password"
                          secondary="Update your account password"
                        />
                        <Button variant="outlined" size="small">
                          Change
                        </Button>
                      </ListItem>
                      <ListItem>
                        <ListItemIcon>
                          <NotificationsIcon />
                        </ListItemIcon>
                        <ListItemText 
                          primary="Two-Factor Authentication"
                          secondary="Add an extra layer of security"
                        />
                        <Button variant="outlined" size="small">
                          Enable
                        </Button>
                      </ListItem>
                    </List>
                  </Grid>
                </Grid>
              )}

              <Divider sx={{ my: 3 }} />

              <Typography variant="h6" gutterBottom>
                Account Information
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Member since
                  </Typography>
                  <Typography variant="body1">
                    {user.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Last login
                  </Typography>
                  <Typography variant="body1">
                    {user.last_login ? new Date(user.last_login).toLocaleDateString() : 'N/A'}
                  </Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Avatar Upload Dialog */}
      <Dialog
        open={avatarDialogOpen}
        onClose={() => setAvatarDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Update Profile Picture</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Upload a new profile picture. Supported formats: JPG, PNG, GIF (max 5MB)
          </Typography>
          <FileUpload
            onFileSelect={handleAvatarSelect}
            onFileRemove={handleAvatarRemove}
            acceptedTypes={['image/jpeg', 'image/png', 'image/gif']}
            maxSize={5 * 1024 * 1024} // 5MB
            currentFile={avatarFile}
            loading={uploadingAvatar}
            title="Upload Profile Picture"
            subtitle="Drag and drop an image here, or click to select"
            buttonText="Choose Image"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAvatarDialogOpen(false)}>Cancel</Button>
          <Button 
            variant="contained" 
            onClick={handleAvatarUpload}
            disabled={!avatarFile || uploadingAvatar}
          >
            {uploadingAvatar ? 'Uploading...' : 'Upload'}
          </Button>
        </DialogActions>
      </Dialog>
    </ResponsiveContainer>
  );
};

export default ProfilePage; 