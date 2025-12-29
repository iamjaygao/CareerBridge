import React, { useState, useEffect, useRef } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  InputAdornment,
  Alert,
  Paper,
  CircularProgress,
} from '@mui/material';
import {
  Save as SaveIcon,
  Visibility as VisibilityIcon,
  Star as StarIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  ArrowBack as ArrowBackIcon,
} from '@mui/icons-material';
import { RootState } from '../../store';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import mentorService from '../../services/api/mentorService';
import { useNotification } from '../../components/common/NotificationProvider';
import { MentorService as MentorServiceType } from '../../types';
import authService from '../../services/auth/authService';
import { fetchUserProfile } from '../../store/slices/authSlice';

const MentorProfilePage: React.FC = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { user } = useSelector((state: RootState) => state.auth);
  const { showSuccess, showError } = useNotification();
  const [loading, setLoading] = useState(true);
  const [mentorProfile, setMentorProfile] = useState<any>(null);
  const [services, setServices] = useState<MentorServiceType[]>([]);
  const [servicesLoading, setServicesLoading] = useState(false);
  const [settingPrimary, setSettingPrimary] = useState<number | null>(null);
  const [payoutStatus, setPayoutStatus] = useState<any>(null);
  const [payoutLoading, setPayoutLoading] = useState(false);
  const [payoutLinkLoading, setPayoutLinkLoading] = useState(false);
  const [payoutSummary, setPayoutSummary] = useState<any>(null);
  const [payoutSummaryLoading, setPayoutSummaryLoading] = useState(false);
  const [serviceDialogOpen, setServiceDialogOpen] = useState(false);
  const [serviceDialogMode, setServiceDialogMode] = useState<'create' | 'edit'>('create');
  const [editingServiceId, setEditingServiceId] = useState<number | null>(null);
  const [avatarUploading, setAvatarUploading] = useState(false);
  const [serviceForm, setServiceForm] = useState({
    service_type: 'career_consultation',
    title: '',
    description: '',
    pricing_model: 'fixed',
    price: '',
    duration_minutes: '60',
  });

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
  });

  const [expertiseInput, setExpertiseInput] = useState('');
  const avatarInputRef = useRef<HTMLInputElement | null>(null);
  const parsePosition = (position: string) => {
    if (!position) {
      return { title: '', company: '' };
    }
    const atSeparator = position.includes(' at ') ? ' at ' : position.includes(' @ ') ? ' @ ' : '';
    if (!atSeparator) {
      return { title: position.trim(), company: '' };
    }
    const [title, company] = position.split(atSeparator);
    return { title: (title || '').trim(), company: (company || '').trim() };
  };

  const buildPosition = (title: string, company: string) => {
    const trimmedTitle = title.trim();
    const trimmedCompany = company.trim();
    if (trimmedTitle && trimmedCompany) {
      return `${trimmedTitle} at ${trimmedCompany}`;
    }
    return trimmedTitle || trimmedCompany;
  };

  const handleAvatarUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setAvatarUploading(true);
    try {
      await authService.uploadAvatar(file);
      await dispatch(fetchUserProfile() as any);
      showSuccess('Profile photo updated.');
    } catch (error: any) {
      showError(error?.response?.data?.error || 'Failed to upload profile photo.');
    } finally {
      setAvatarUploading(false);
      if (avatarInputRef.current) {
        avatarInputRef.current.value = '';
      }
    }
  };

  // Fetch mentor profile and services
  useEffect(() => {
    const fetchMentorData = async () => {
      try {
        // Fetch mentor's own profile
        const profile = await mentorService.getMyProfile();
        setMentorProfile(profile);
        try {
          const status = await mentorService.getStripeStatus();
          setPayoutStatus(status);
        } catch {
          setPayoutStatus(null);
        }
        try {
          setPayoutSummaryLoading(true);
          const summary = await mentorService.getPayoutSummary();
          setPayoutSummary(summary);
        } catch {
          setPayoutSummary(null);
        } finally {
          setPayoutSummaryLoading(false);
        }
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

  const handleOpenServiceDialog = () => {
    setServiceDialogMode('create');
    setEditingServiceId(null);
    setServiceForm({
      service_type: 'career_consultation',
      title: '',
      description: '',
      pricing_model: 'fixed',
      price: '',
      duration_minutes: '60',
    });
    setServiceDialogOpen(true);
  };

  const handleEditService = (service: MentorServiceType) => {
    setServiceDialogMode('edit');
    setEditingServiceId(service.id);
    setServiceForm({
      service_type: service.service_type || 'career_consultation',
      title: service.title || '',
      description: service.description || '',
      pricing_model: service.pricing_model || 'fixed',
      price: service.pricing_model === 'hourly'
        ? String(service.price_per_hour || '')
        : String(service.fixed_price || ''),
      duration_minutes: String(service.duration_minutes || 60),
    });
    setServiceDialogOpen(true);
  };

  const handleDeactivateService = async (serviceId: number) => {
    try {
      await mentorService.updateMentorService(serviceId, { is_active: false });
      setServices((prev) => prev.filter((item) => item.id !== serviceId));
      showSuccess('Service removed.');
    } catch (error: any) {
      const message = error?.response?.data?.detail || 'Failed to remove service.';
      showError(message);
    }
  };

  const handleSaveService = async () => {
    if (!mentorProfile?.id) {
      showError('Mentor profile not loaded.');
      return;
    }
    if (!serviceForm.title.trim()) {
      showError('Service title is required.');
      return;
    }
    if (!serviceForm.price || Number(serviceForm.price) <= 0) {
      showError('Service price must be greater than 0.');
      return;
    }
    const payload: any = {
      service_type: serviceForm.service_type,
      title: serviceForm.title.trim(),
      description: serviceForm.description.trim(),
      pricing_model: serviceForm.pricing_model,
      duration_minutes: Number(serviceForm.duration_minutes) || 60,
      is_active: true,
    };
    if (serviceForm.pricing_model === 'hourly') {
      payload.price_per_hour = Number(serviceForm.price);
    } else {
      payload.fixed_price = Number(serviceForm.price);
    }

    try {
      if (serviceDialogMode === 'create') {
        const created = await mentorService.createMentorService(mentorProfile.id, payload);
        setServices((prev) => [...prev, created]);
        showSuccess('Service created successfully.');
      } else if (editingServiceId) {
        const updated = await mentorService.updateMentorService(editingServiceId, payload);
        setServices((prev) => prev.map((item) => (item.id === updated.id ? updated : item)));
        showSuccess('Service updated successfully.');
      }
      setServiceDialogOpen(false);
    } catch (error: any) {
      const data = error?.response?.data;
      if (data && typeof data === 'object') {
        const fieldErrors = Object.entries(data)
          .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(', ') : String(value)}`)
          .join('; ');
        showError(fieldErrors || 'Failed to create service.');
      } else {
        showError('Failed to create service.');
      }
    }
  };

  const handleStripeSetup = async () => {
    try {
      setPayoutLoading(true);
      const status = await mentorService.getStripeStatus();
      if (!status?.stripe_account_id) {
        await mentorService.createStripeAccount();
      }
      const returnUrl = `${window.location.origin}/mentor/profile`;
      const refreshUrl = `${window.location.origin}/mentor/profile`;
      setPayoutLinkLoading(true);
      const link = await mentorService.createStripeAccountLink(returnUrl, refreshUrl);
      if (link?.url) {
        window.location.assign(link.url);
      }
    } catch (error: any) {
      showError(error?.response?.data?.error || 'Failed to start payout setup.');
    } finally {
      setPayoutLoading(false);
      setPayoutLinkLoading(false);
    }
  };

  useEffect(() => {
    if (!mentorProfile) return;
    const position = mentorProfile.current_position || mentorProfile.job_title || '';
    const { title, company } = parsePosition(position);
    setFormData((prev) => ({
      ...prev,
      headline: title || mentorProfile.headline || '',
      company,
      yearsOfExperience: mentorProfile.years_of_experience
        ? String(mentorProfile.years_of_experience)
        : '',
      bio: mentorProfile.bio || '',
      expertise: Array.isArray(mentorProfile.expertise)
        ? mentorProfile.expertise
        : Array.isArray(mentorProfile.specializations)
          ? mentorProfile.specializations
          : [],
      primary_focus: mentorProfile.primary_focus || '',
      session_focus: mentorProfile.session_focus || '',
    }));
  }, [mentorProfile]);

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

  const handleSave = async () => {
    try {
      const payload = {
        bio: formData.bio,
        years_of_experience: formData.yearsOfExperience
          ? Number(formData.yearsOfExperience)
          : 0,
        current_position: buildPosition(formData.headline, formData.company),
        primary_focus: formData.primary_focus,
        session_focus: formData.session_focus,
        specializations: formData.expertise,
      };
      await mentorService.updateMyProfile(payload);
      showSuccess('Profile saved successfully.');
    } catch (error: any) {
      const message = error?.response?.data?.detail || 'Failed to save profile.';
      showError(message);
    }
  };

  const handlePreviewProfile = () => {
    if (!mentorProfile?.id) {
      showError('Unable to preview profile right now.');
      return;
    }
    window.open(`/student/mentors/${mentorProfile.id}`, '_blank', 'noopener,noreferrer');
  };

  const formatCurrency = (value?: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 2,
    }).format(value || 0);
  };

  if (loading) {
    return <LoadingSpinner message="Loading profile..." />;
  }

  return (
    <Box>
      {/* Page Header */}
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
          <Typography variant="h4" sx={{ fontWeight: 700 }}>
            Mentor Profile
          </Typography>
          <Button
            variant="text"
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate('/mentor')}
          >
            Back to Dashboard
          </Button>
        </Box>
        <Typography variant="body2" color="text.secondary">
          Manage your public profile and mentor information
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Identity / Brand */}
        <Grid item xs={12}>
          <Box sx={{ mb: 1 }}>
            <Typography variant="overline" color="text.secondary">
              Mentor Identity
            </Typography>
            <Typography variant="h5" sx={{ fontWeight: 700 }}>
              Your public mentor brand
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Make a strong first impression for students browsing your profile.
            </Typography>
          </Box>
          <Card>
            <CardContent sx={{ p: 3 }}>
              <Grid container spacing={3} alignItems="center">
                <Grid item xs={12} md={4}>
                  <Box sx={{ textAlign: { xs: 'center', md: 'left' } }}>
                    <Avatar
                      src={user?.avatar}
                      sx={{
                        width: 120,
                        height: 120,
                        mx: { xs: 'auto', md: 0 },
                        mb: 2,
                        background:
                          'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                      }}
                    >
                      {user?.first_name?.[0] || user?.username?.[0] || 'M'}
                    </Avatar>
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>
                      {user?.first_name || user?.last_name
                        ? `${user?.first_name || ''} ${user?.last_name || ''}`.trim()
                        : user?.username || 'Mentor'}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      Add a profile photo to build trust with students.
                    </Typography>
                    <Button
                      variant="outlined"
                      fullWidth
                      onClick={() => avatarInputRef.current?.click()}
                      disabled={avatarUploading}
                    >
                      {avatarUploading ? 'Uploading...' : 'Add Profile Photo'}
                    </Button>
                    <input
                      ref={avatarInputRef}
                      type="file"
                      accept="image/*"
                      hidden
                      onChange={handleAvatarUpload}
                    />
                    <Typography
                      variant="caption"
                      color="text.secondary"
                      sx={{ display: 'block', mt: 1 }}
                    >
                      {user?.email || 'mentor@careerbridge.ai'}
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={12} md={8}>
                  <Grid container spacing={2}>
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        label="Display Name"
                        value={formData.name}
                        onChange={(e) =>
                          setFormData({ ...formData, name: e.target.value })
                        }
                      />
                    </Grid>
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        label="Headline (what students see first)"
                        value={formData.headline}
                        onChange={(e) =>
                          setFormData({ ...formData, headline: e.target.value })
                        }
                      />
                    </Grid>
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        select
                        label="Primary Focus"
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
                      <Typography variant="caption" color="text.secondary">
                        Shown as the main focus on your public mentor card.
                      </Typography>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <TextField
                        fullWidth
                        label="Company"
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
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Public Profile Content */}
        <Grid item xs={12}>
          <Box sx={{ mb: 1 }}>
            <Typography variant="overline" color="text.secondary">
              Public Profile Content
            </Typography>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              What students see before booking
            </Typography>
          </Box>
        </Grid>

        {/* Expertise */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent sx={{ p: 3 }}>
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
                  placeholder="Add an expertise area"
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
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                Services Overview
              </Typography>

              <TextField
                fullWidth
                label="Typical Session Experience"
                placeholder="60‑min mock interview + written feedback"
                value={formData.session_focus}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    session_focus: e.target.value,
                  })
                }
              />

              <Typography variant="caption" color="text.secondary">
                This appears on your public profile. Pricing comes from your services below.
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Services Management */}
        <Grid item xs={12}>
          <Card>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                Services Management
              </Typography>
              <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
                <Button variant="outlined" onClick={handleOpenServiceDialog}>
                  Create Service
                </Button>
              </Box>

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
                            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                              <Button
                                variant={isPrimary ? "outlined" : "contained"}
                                size="small"
                                onClick={() => handleSetPrimaryService(service.id)}
                                disabled={settingPrimary === service.id}
                                startIcon={settingPrimary === service.id ? <CircularProgress size={16} /> : <StarIcon />}
                              >
                                {settingPrimary === service.id ? 'Setting...' : isPrimary ? 'Primary' : 'Set as Primary'}
                              </Button>
                              <Button
                                variant="outlined"
                                size="small"
                                onClick={() => handleEditService(service)}
                                startIcon={<EditIcon />}
                              >
                                Edit
                              </Button>
                              <Button
                                variant="outlined"
                                size="small"
                                color="error"
                                onClick={() => handleDeactivateService(service.id)}
                                startIcon={<DeleteIcon />}
                              >
                                Delete
                              </Button>
                            </Box>
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

        {/* System / Payout */}
        <Grid item xs={12}>
          <Box sx={{ mb: 1 }}>
            <Typography variant="overline" color="text.secondary">
              System & Payout
            </Typography>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              One-time setup for getting paid
            </Typography>
          </Box>
          <Card sx={{ bgcolor: 'action.hover' }}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Connect your payout account once to receive earnings from sessions.
              </Typography>
              {payoutStatus?.payouts_enabled ? (
                <Alert severity="success" sx={{ mb: 2 }}>
                  Payouts are enabled.
                </Alert>
              ) : (
                <Alert severity="info" sx={{ mb: 2 }}>
                  Payouts are not enabled yet.
                </Alert>
              )}
              <Box sx={{ mb: 2 }}>
                {payoutSummaryLoading ? (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <CircularProgress size={16} />
                    <Typography variant="body2" color="text.secondary">
                      Loading payout summary...
                    </Typography>
                  </Box>
                ) : payoutSummary ? (
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6} md={3}>
                      <Typography variant="caption" color="text.secondary">
                        Pending (hold)
                      </Typography>
                      <Typography variant="h6">
                        {formatCurrency(payoutSummary.pending_total)}
                      </Typography>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Typography variant="caption" color="text.secondary">
                        Ready to pay
                      </Typography>
                      <Typography variant="h6">
                        {formatCurrency(payoutSummary.ready_total)}
                      </Typography>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Typography variant="caption" color="text.secondary">
                        Paid out
                      </Typography>
                      <Typography variant="h6">
                        {formatCurrency(payoutSummary.paid_total)}
                      </Typography>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Typography variant="caption" color="text.secondary">
                        Failed
                      </Typography>
                      <Typography variant="h6">
                        {formatCurrency(payoutSummary.failed_total)}
                      </Typography>
                    </Grid>
                    <Grid item xs={12}>
                      <Typography variant="body2" color="text.secondary">
                        {payoutSummary.payout_hold_days
                          ? `Payouts are held for ${payoutSummary.payout_hold_days} day(s) after completion.`
                          : 'Payouts are eligible immediately after completion.'}
                        {payoutSummary.payout_requires_admin_approval
                          ? ' Admin approval is required before release.'
                          : ''}
                        {payoutSummary.next_payout_at
                          ? ` Next payout window starts on ${new Date(payoutSummary.next_payout_at).toLocaleDateString()}.`
                          : ''}
                      </Typography>
                    </Grid>
                  </Grid>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    Payout summary is not available yet.
                  </Typography>
                )}
              </Box>
              <Button
                variant="outlined"
                onClick={handleStripeSetup}
                disabled={payoutLoading || payoutLinkLoading}
              >
                {payoutLinkLoading ? 'Opening Stripe...' : 'Connect Stripe'}
              </Button>
            </CardContent>
          </Card>
        </Grid>

        {/* Actions */}
        <Grid item xs={12}>
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2, pt: 1 }}>
            <Button
              variant="outlined"
              startIcon={<VisibilityIcon />}
              onClick={handlePreviewProfile}
              disabled={!mentorProfile?.id}
            >
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

      <Dialog open={serviceDialogOpen} onClose={() => setServiceDialogOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>{serviceDialogMode === 'create' ? 'Create Service' : 'Edit Service'}</DialogTitle>
        <DialogContent sx={{ pt: 1 }}>
          <Grid container spacing={2} sx={{ mt: 0 }}>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Service Type</InputLabel>
                <Select
                  value={serviceForm.service_type}
                  label="Service Type"
                  onChange={(e) =>
                    setServiceForm((prev) => ({ ...prev, service_type: e.target.value }))
                  }
                >
                  <MenuItem value="resume_review">Resume Review</MenuItem>
                  <MenuItem value="mock_interview">Mock Interview</MenuItem>
                  <MenuItem value="career_consultation">Career Consultation</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Pricing Model</InputLabel>
                <Select
                  value={serviceForm.pricing_model}
                  label="Pricing Model"
                  onChange={(e) =>
                    setServiceForm((prev) => ({ ...prev, pricing_model: e.target.value }))
                  }
                >
                  <MenuItem value="fixed">Fixed Price</MenuItem>
                  <MenuItem value="hourly">Hourly</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Service Title"
                value={serviceForm.title}
                onChange={(e) =>
                  setServiceForm((prev) => ({ ...prev, title: e.target.value }))
                }
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={3}
                label="Description"
                value={serviceForm.description}
                onChange={(e) =>
                  setServiceForm((prev) => ({ ...prev, description: e.target.value }))
                }
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                type="number"
                label={serviceForm.pricing_model === 'hourly' ? 'Price per hour' : 'Fixed price'}
                value={serviceForm.price}
                onChange={(e) =>
                  setServiceForm((prev) => ({ ...prev, price: e.target.value }))
                }
                InputProps={{
                  startAdornment: <InputAdornment position="start">$</InputAdornment>,
                }}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                type="number"
                label="Duration (minutes)"
                value={serviceForm.duration_minutes}
                onChange={(e) =>
                  setServiceForm((prev) => ({ ...prev, duration_minutes: e.target.value }))
                }
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setServiceDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleSaveService}>
            {serviceDialogMode === 'create' ? 'Create' : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default MentorProfilePage;
