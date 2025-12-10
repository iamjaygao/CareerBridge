import React from 'react';
import { Box, Typography, TextField, Button, Grid, Paper } from '@mui/material';
import { Email, Phone, LocationOn, Send } from '@mui/icons-material';
import { useSystemSettings } from '../../hooks/useSystemSettings';
import LoadingSpinner from '../../components/common/LoadingSpinner';

const ContactPage: React.FC = () => {
  const { settings, loading } = useSystemSettings();

  if (loading) {
    return <LoadingSpinner message="Loading contact information..." />;
  }

  const contactTitle = settings?.contact_title || 'Contact Us';
  const contactDescription = settings?.contact_description || "Have questions? We'd love to hear from you.";
  const supportEmail = settings?.support_email || 'support@careerbridge.com';
  const supportPhone = settings?.support_phone || '';
  const officeAddress = settings?.office_address || '';

  return (
    <Box sx={{ width: '100%', maxWidth: '1200px', mx: 'auto', px: { xs: 2, sm: 3, md: 6 }, py: { xs: 4, md: 6 } }}>
      <Box
        sx={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          py: { xs: 6, md: 8 },
          px: { xs: 3, md: 4 },
          borderRadius: { xs: 0, md: 3 },
          mb: 8,
          textAlign: 'center',
        }}
      >
        <Typography
          variant="h2"
          component="h1"
          sx={{
            fontWeight: 700,
            fontSize: { xs: '2rem', md: '3rem' },
            color: 'white',
            mb: 2,
          }}
        >
          {contactTitle}
        </Typography>
        <Typography
          variant="h5"
          sx={{
            fontSize: { xs: '1rem', md: '1.25rem' },
            color: 'rgba(255, 255, 255, 0.95)',
            maxWidth: '700px',
            mx: 'auto',
          }}
        >
          {contactDescription}
        </Typography>
      </Box>

      <Grid container spacing={4}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 4 }}>
            <Typography variant="h5" sx={{ fontWeight: 600, mb: 3 }}>
              Get in Touch
            </Typography>
            <Box sx={{ mb: 3 }}>
              {supportEmail && (
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Email sx={{ mr: 2, color: 'primary.main' }} />
                  <Typography>{supportEmail}</Typography>
                </Box>
              )}
              {supportPhone && (
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Phone sx={{ mr: 2, color: 'primary.main' }} />
                  <Typography>{supportPhone}</Typography>
                </Box>
              )}
              {officeAddress && (
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <LocationOn sx={{ mr: 2, color: 'primary.main' }} />
                  <Typography>{officeAddress}</Typography>
                </Box>
              )}
            </Box>
          </Paper>
        </Grid>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 4 }}>
            <Typography variant="h5" sx={{ fontWeight: 600, mb: 3 }}>
              Send us a Message
            </Typography>
            <Box component="form" sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <TextField label="Name" fullWidth required />
              <TextField label="Email" type="email" fullWidth required />
              <TextField label="Subject" fullWidth required />
              <TextField label="Message" multiline rows={4} fullWidth required />
              <Button
                variant="contained"
                startIcon={<Send />}
                sx={{
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  textTransform: 'none',
                  py: 1.5,
                }}
              >
                Send Message
              </Button>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default ContactPage;
