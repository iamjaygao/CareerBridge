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
  Alert,
  Paper,
  CircularProgress,
} from '@mui/material';
import {
  Save as SaveIcon,
  Visibility as VisibilityIcon,
  Star as StarIcon,
} from '@mui/icons-material';
import { RootState } from '../../store';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import mentorService from '../../services/api/mentorService';
import { useNotification } from '../../components/common/NotificationProvider';
import { MentorService as MentorServiceType } from '../../types';

const MentorProfilePage: React.FC = () => {
  const { user } = useSelector((state: RootState) => state.auth);
  const { showSuccess, showError } = useNotification();
  const [loading, setLoading] = useState(true);
  const [mentorProfile, setMentorProfile] = useState<any>(null);
  const [services, setServices] = useState<MentorServiceType[]>([]);
  const [servicesLoading, setServicesLoading] = useState(false);
  const [settingPrimary, setSettingPrimary] = useState<number | null>(null);

  const [formData, setFormData] = useState({
    name:
      user?.first_name && user?.last_name
        ? `${user.first_name} ${user.last_name}`
        : user?.username || '',
    headline: '',
    company: '',
    yearsOfExperience: '',
    bio: '',
    expertise: [] as string[],

    // ✅ 新增：Mentor Card 核心字段
    primary_focus: '',
    session_focus: '',

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

  // Fetch mentor profile and services
  useEffect(() => {
    const fetchMentorData = async () => {
      try {
        // Fetch mentor's own profile
        const profile = await mentorService.getMyProfile();
        setMentorProfile(profile);
      } catch (error: any) {
        // If GET doesn't work on update endpoint, try alternative approach
        console.error('Failed to fetch mentor profile:', error);
        // Could try fetching via detail endpoint if we have mentor_id from user
      } finally {
        setLoading(false);
      }
    };

    fetchMentorData();
  }, []);

  // Fetch services when mentor profile is available
  useEffect(() => {
    const fetchServices = async () => {
      if (!mentorProfile?.id) return;
      
      try {
        setServicesLoading(true);
        const servicesData = await mentorService.getMyServices(mentorProfile.id);
        setServices(servicesData || []);
      } catch (error) {
        console.error('Failed to fetch services:', error);
        showError('Failed to load services');
      } finally {
        setServicesLoading(false);
      }
    };

    fetchServices();
  }, [mentorProfile?.id, showError]);

  const handleSetPrimaryService = async (serviceId: number) => {
    try {
      setSettingPrimary(serviceId);
      await mentorService.updateMyProfile({ primary_service_id: serviceId });
      showSuccess('Primary service updated successfully');
      
      // Update local state
      setMentorProfile((prev: any) => ({
        ...prev,
        primary_service_id: serviceId,
      }));
    } catch (error: any) {
      const errorMessage = error.response?.data?.primary_service_id?.[0] || 
                          error.response?.data?.detail || 
                          'Failed to set primary service';
      showError(errorMessage);
    } finally {
      setSettingPrimary(null);
    }
  };

  // ✅ 模拟从后台加载数据（安全写法）
  useEffect(() => {
    setTimeout(() => {
      setFormData((prev) => ({
        ...prev,
        headline: 'Senior Software Engineer',
        company: 'Tech Corp',
        yearsOfExperience: '10',
        bio: 'Experienced software engineer with expertise in full-stack development...',
        expertise: [
          'Software Engineering',
          'Career Development',
          'Technical Interviews',
        ],
        services: {
          resumeReview: true,
          mockInterview: true,
          careerChat: true,
          portfolioReview: false,
        },
        hourlyRate: '75',

        // ✅ 关键字段（Mentor Card 用）
        primaryFocus: 'System Design Interviews',
        sessionFocus: '60-min mock interview + written feedback',
      }));
    }, 500);
  }, []);

  const handleAddExpertise = () => {
    if (
      expertiseInput.trim() &&
      !formData.expertise.includes(expertiseInput.trim())
    ) {
      setFormData((prev) => ({
        ...prev,
        expertise: [...prev.expertise, expertiseInput.trim()],
      }));
      setExpertiseInput('');
    }
  };

  const handleRemoveExpertise = (exp: string) => {
    setFormData((prev) => ({
      ...prev,
      expertise: prev.expertise.filter((e) => e !== exp),
    }));
  };

  const handleSave = () => {
    alert('Profile saved successfully!');
    // TODO: POST 到后端
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
        {/* Avatar */}
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
                  background:
                    'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
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

        {/* Basic Info */}
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
                    onChange={(e) =>
                      setFormData({ ...formData, name: e.target.value })
                    }
                  />
                </Grid>

                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Headline / Title"
                    value={formData.headline}
                    onChange={(e) =>
                      setFormData({ ...formData, headline: e.target.value })
                    }
                  />
                </Grid>

                {/* ✅ Primary Focus */}
                <Grid item xs={12}>
                  <FormControl fullWidth>
                    <InputLabel shrink>Primary Focus</InputLabel>
                    <TextField
                      select
                      value={formData.primary_focus}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          primary_focus: e.target.value,
                        })
                      }
                      SelectProps={{ native: true }}
                    >
                      <option value=""></option>
                      <option value="System Design Interviews">
                        System Design Interviews
                      </option>
                      <option value="Backend Interview Prep">
                        Backend Interview Prep
                      </option>
                      <option value="Resume Review (New Grad)">
                        Resume Review (New Grad)
                      </option>
                      <option value="Career Planning">
                        Career Planning
                      </option>
                      <option value="International Student Job Search">
                        International Student Job Search
                      </option>
                    </TextField>
                  </FormControl>
                  <Typography variant="caption" color="text.secondary">
                    Shown as the main focus on your public mentor card.
                  </Typography>
                </Grid>

                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Current Company"
                    value={formData.company}
                    onChange={(e) =>
                      setFormData({ ...formData, company: e.target.value })
                    }
                  />
                </Grid>

                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Years of Experience"
                    value={formData.yearsOfExperience}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        yearsOfExperience: e.target.value,
                      })
                    }
                  />
                </Grid>

                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    multiline
                    rows={4}
                    label="Short Bio"
                    value={formData.bio}
                    onChange={(e) =>
                      setFormData({ ...formData, bio: e.target.value })
                    }
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Expertise */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                Expertise Tags
              </Typography>

              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
                {formData.expertise.map((exp) => (
                  <Chip
                    key={exp}
                    label={exp}
                    onDelete={() => handleRemoveExpertise(exp)}
                  />
                ))}
              </Box>

              <Box sx={{ display: 'flex', gap: 1 }}>
                <TextField
                  placeholder="Add expertise tag"
                  value={expertiseInput}
                  onChange={(e) => setExpertiseInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleAddExpertise();
                    }
                  }}
                  fullWidth
                />
                <Button variant="outlined" onClick={handleAddExpertise}>
                  Add
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Services */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                Services Offered
              </Typography>

              <FormGroup>
                {[
                  ['resumeReview', 'Resume Review'],
                  ['mockInterview', 'Mock Interview'],
                  ['careerChat', 'Career Consultation'],
                  ['portfolioReview', 'Portfolio Review'],
                ].map(([key, label]) => (
                  <FormControlLabel
                    key={key}
                    control={
                      <Checkbox
                        checked={(formData.services as any)[key]}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            services: {
                              ...formData.services,
                              [key]: e.target.checked,
                            },
                          })
                        }
                      />
                    }
                    label={label}
                  />
                ))}
              </FormGroup>

              {/* ✅ Session Focus */}
              <TextField
                fullWidth
                label="Typical Session Experience"
                placeholder="e.g. 60-min mock interview + written feedback"
                value={formData.session_focus}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    session_focus: e.target.value,
                  })
                }
                sx={{ mt: 2 }}
              />

              <Typography variant="caption" color="text.secondary">
                Displayed on your mentor card before booking.
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Pricing */}
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
                onChange={(e) =>
                  setFormData({ ...formData, hourlyRate: e.target.value })
                }
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">$</InputAdornment>
                  ),
                }}
                sx={{ mb: 2 }}
              />

              <FormControlLabel
                control={
                  <Switch
                    checked={formData.showPublicly}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        showPublicly: e.target.checked,
                      })
                    }
                  />
                }
                label="Show profile publicly"
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Services Management */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                Services Management
              </Typography>

              {/* Alert if primary_service_id is missing */}
              {(!mentorProfile?.primary_service_id && services.length > 0) && (
                <Alert severity="warning" sx={{ mb: 3 }}>
                  Please set a Primary SKU to help students find your main service quickly.
                </Alert>
              )}

              {servicesLoading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                  <CircularProgress />
                </Box>
              ) : services.length === 0 ? (
                <Typography color="text.secondary">
                  No active services found. Create services to get started.
                </Typography>
              ) : (
                <Grid container spacing={2}>
                  {services.map((service) => {
                    const isPrimary = mentorProfile?.primary_service_id === service.id;
                    return (
                      <Grid item xs={12} key={service.id}>
                        <Paper
                          sx={{
                            p: 2,
                            border: isPrimary ? 2 : 1,
                            borderColor: isPrimary ? 'primary.main' : 'divider',
                            bgcolor: isPrimary ? 'action.selected' : 'background.paper',
                          }}
                        >
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                            <Box sx={{ flex: 1 }}>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                                <Typography variant="h6">{service.title}</Typography>
                                {isPrimary && (
                                  <Chip
                                    icon={<StarIcon />}
                                    label="Primary"
                                    color="primary"
                                    size="small"
                                  />
                                )}
                              </Box>
                              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                                {service.description}
                              </Typography>
                              <Typography variant="body2" color="primary" fontWeight="medium">
                                {service.display_price || 
                                  (service.pricing_model === 'hourly' 
                                    ? `$${service.price_per_hour}/hour`
                                    : service.pricing_model === 'fixed'
                                    ? `$${service.fixed_price}`
                                    : 'Price not set')}
                              </Typography>
                            </Box>
                            <Button
                              variant={isPrimary ? "outlined" : "contained"}
                              size="small"
                              onClick={() => handleSetPrimaryService(service.id)}
                              disabled={settingPrimary === service.id}
                              startIcon={settingPrimary === service.id ? <CircularProgress size={16} /> : <StarIcon />}
                            >
                              {settingPrimary === service.id ? 'Setting...' : isPrimary ? 'Primary' : 'Set as Primary'}
                            </Button>
                          </Box>
                        </Paper>
                      </Grid>
                    );
                  })}
                </Grid>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Actions */}
        <Grid item xs={12}>
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
            <Button variant="outlined" startIcon={<VisibilityIcon />}>
              Preview Public Profile
            </Button>
            <Button
              variant="contained"
              startIcon={<SaveIcon />}
              onClick={handleSave}
              sx={{
                background:
                  'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
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
