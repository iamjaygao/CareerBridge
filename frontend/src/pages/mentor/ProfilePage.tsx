import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import {
  Box,
  Typography,
  Card,
  CardContent,
  TextField,
  Button,
  Grid,
  Avatar,
  Chip,
  FormControlLabel,
  Switch,
  Checkbox,
  FormGroup,
  FormControl,
  InputLabel,
  InputAdornment,
} from '@mui/material';
import {
  Save as SaveIcon,
  Visibility as VisibilityIcon,
} from '@mui/icons-material';
import { RootState } from '../../store';
import LoadingSpinner from '../../components/common/LoadingSpinner';

const MentorProfilePage: React.FC = () => {
  const { user } = useSelector((state: RootState) => state.auth);
  const [loading, setLoading] = useState(true);
  const [formData, setFormData] = useState({
    name: user?.first_name && user?.last_name ? `${user.first_name} ${user.last_name}` : user?.username || '',
    headline: '',
    company: '',
    yearsOfExperience: '',
    bio: '',
    expertise: [] as string[],
    services: {
      resumeReview: false,
      mockInterview: false,
      careerChat: false,
      portfolioReview: false,
    },
    hourlyRate: '',
    showPublicly: true,
  });
  const [expertiseInput, setExpertiseInput] = useState('');

  useEffect(() => {
    setTimeout(() => {
      setFormData({
        ...formData,
        headline: 'Senior Software Engineer',
        company: 'Tech Corp',
        yearsOfExperience: '10',
        bio: 'Experienced software engineer with expertise in full-stack development...',
        expertise: ['Software Engineering', 'Career Development', 'Technical Interviews'],
        services: {
          resumeReview: true,
          mockInterview: true,
          careerChat: true,
          portfolioReview: false,
        },
        hourlyRate: '75',
      });
      setLoading(false);
    }, 500);
  }, []);

  const handleAddExpertise = () => {
    if (expertiseInput.trim() && !formData.expertise.includes(expertiseInput.trim())) {
      setFormData({
        ...formData,
        expertise: [...formData.expertise, expertiseInput.trim()],
      });
      setExpertiseInput('');
    }
  };

  const handleRemoveExpertise = (expertise: string) => {
    setFormData({
      ...formData,
      expertise: formData.expertise.filter(e => e !== expertise),
    });
  };

  const handleSave = () => {
    // Placeholder for save functionality
    alert('Profile saved successfully!');
  };

  if (loading) {
    return <LoadingSpinner message="Loading profile..." />;
  }

  return (
    <Box>
      {/* Page Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
          Mentor Profile
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Manage your public profile and mentor information
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Profile Picture */}
        <Grid item xs={12} md={4}>
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
                {user?.first_name?.[0] || user?.username?.[0] || 'M'}
              </Avatar>
              <Button variant="outlined" fullWidth>
                Upload Photo
              </Button>
            </CardContent>
          </Card>
        </Grid>

        {/* Profile Information */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                Basic Information
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Headline / Title"
                    placeholder="e.g., Senior Software Engineer"
                    value={formData.headline}
                    onChange={(e) => setFormData({ ...formData, headline: e.target.value })}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Current Company"
                    value={formData.company}
                    onChange={(e) => setFormData({ ...formData, company: e.target.value })}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Years of Experience"
                    value={formData.yearsOfExperience}
                    onChange={(e) => setFormData({ ...formData, yearsOfExperience: e.target.value })}
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    multiline
                    rows={4}
                    label="Short Bio"
                    placeholder="Tell students about your background and expertise..."
                    value={formData.bio}
                    onChange={(e) => setFormData({ ...formData, bio: e.target.value })}
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Expertise & Skills */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                Expertise Tags / Skills
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                {formData.expertise.map((exp) => (
                  <Chip
                    key={exp}
                    label={exp}
                    onDelete={() => handleRemoveExpertise(exp)}
                    color="primary"
                  />
                ))}
              </Box>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <TextField
                  placeholder="Add expertise tag"
                  value={expertiseInput}
                  onChange={(e) => setExpertiseInput(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleAddExpertise();
                    }
                  }}
                  sx={{ flexGrow: 1 }}
                />
                <Button variant="outlined" onClick={handleAddExpertise}>
                  Add
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Services Offered */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                Services Offered
              </Typography>
              <FormGroup>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={formData.services.resumeReview}
                      onChange={(e) => setFormData({
                        ...formData,
                        services: { ...formData.services, resumeReview: e.target.checked },
                      })}
                    />
                  }
                  label="Resume Review"
                />
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={formData.services.mockInterview}
                      onChange={(e) => setFormData({
                        ...formData,
                        services: { ...formData.services, mockInterview: e.target.checked },
                      })}
                    />
                  }
                  label="Mock Interview"
                />
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={formData.services.careerChat}
                      onChange={(e) => setFormData({
                        ...formData,
                        services: { ...formData.services, careerChat: e.target.checked },
                      })}
                    />
                  }
                  label="Career Chat"
                />
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={formData.services.portfolioReview}
                      onChange={(e) => setFormData({
                        ...formData,
                        services: { ...formData.services, portfolioReview: e.target.checked },
                      })}
                    />
                  }
                  label="Portfolio Review"
                />
              </FormGroup>
            </CardContent>
          </Card>
        </Grid>

        {/* Pricing & Visibility */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                Pricing & Visibility
              </Typography>
              <TextField
                fullWidth
                type="number"
                label="Hourly Rate"
                value={formData.hourlyRate}
                onChange={(e) => setFormData({ ...formData, hourlyRate: e.target.value })}
                InputProps={{
                  startAdornment: <InputAdornment position="start">$</InputAdornment>,
                }}
                sx={{ mb: 2 }}
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.showPublicly}
                    onChange={(e) => setFormData({ ...formData, showPublicly: e.target.checked })}
                  />
                }
                label="Show profile publicly"
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Action Buttons */}
        <Grid item xs={12}>
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
            <Button
              variant="outlined"
              startIcon={<VisibilityIcon />}
            >
              Preview Public Profile
            </Button>
            <Button
              variant="contained"
              startIcon={<SaveIcon />}
              onClick={handleSave}
              sx={{
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                '&:hover': {
                  background: 'linear-gradient(135deg, #5568d3 0%, #6a3d8f 100%)',
                },
              }}
            >
              Save Profile
            </Button>
          </Box>
        </Grid>
      </Grid>
    </Box>
  );
};

export default MentorProfilePage;

