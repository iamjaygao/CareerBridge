import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Container, Typography, Link, Grid, IconButton } from '@mui/material';
import { 
  LinkedIn as LinkedInIcon, 
  Twitter as TwitterIcon, 
  Instagram as InstagramIcon, 
  YouTube as YouTubeIcon,
  Facebook as FacebookIcon,
} from '@mui/icons-material';
import { useSystemSettings } from '../../hooks/useSystemSettings';

const Footer: React.FC = () => {
  const navigate = useNavigate();
  const { settings, loading } = useSystemSettings();

  if (loading) {
    return null; // Don't show footer while loading
  }

  const platformName = settings?.platform_name || 'CareerBridge';
  const supportEmail = settings?.support_email || '';
  const officeAddress = settings?.office_address || '';
  const linkedinUrl = settings?.linkedin_url || '';
  const twitterUrl = settings?.twitter_url || '';
  const instagramUrl = settings?.instagram_url || '';
  const youtubeUrl = settings?.youtube_url || '';
  const facebookUrl = settings?.facebook_url || '';

  return (
    <Box
      component="footer"
      sx={{
        bgcolor: '#F8FAFC',
        py: 8,
        mt: 'auto',
        borderTop: '1px solid',
        borderColor: 'grey.200',
      }}
    >
      <Container maxWidth="xl">
        <Grid container spacing={4}>
          {/* Left Column - Brand Zone */}
          <Grid item xs={12} md={4}>
            <Typography
              variant="h6"
              sx={{
                fontWeight: 700,
                fontSize: '1.25rem',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                mb: 2,
              }}
            >
              {platformName}
            </Typography>
            <Typography
              variant="subtitle2"
              sx={{
                fontWeight: 600,
                fontSize: '0.875rem',
                color: 'text.primary',
                mb: 2,
              }}
            >
              The AI engine that tells you what to do next in your career.
            </Typography>
            <Typography
              variant="body2"
              sx={{
                color: 'text.secondary',
                fontSize: '0.875rem',
                lineHeight: 1.6,
                maxWidth: '320px',
              }}
            >
              CareerBridge combines AI assessment, market intelligence, and expert mentorship to guide every step of your career journey.
            </Typography>
            {(linkedinUrl || twitterUrl || instagramUrl || youtubeUrl || facebookUrl) && (
              <Box sx={{ display: 'flex', gap: 1, mt: 3 }}>
                {linkedinUrl && (
                  <IconButton 
                    component="a" 
                    href={linkedinUrl} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    size="small"
                    sx={{ color: 'text.secondary', '&:hover': { color: 'primary.main' } }}
                  >
                    <LinkedInIcon />
                  </IconButton>
                )}
                {twitterUrl && (
                  <IconButton 
                    component="a" 
                    href={twitterUrl} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    size="small"
                    sx={{ color: 'text.secondary', '&:hover': { color: 'primary.main' } }}
                  >
                    <TwitterIcon />
                  </IconButton>
                )}
                {instagramUrl && (
                  <IconButton 
                    component="a" 
                    href={instagramUrl} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    size="small"
                    sx={{ color: 'text.secondary', '&:hover': { color: 'primary.main' } }}
                  >
                    <InstagramIcon />
                  </IconButton>
                )}
                {youtubeUrl && (
                  <IconButton 
                    component="a" 
                    href={youtubeUrl} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    size="small"
                    sx={{ color: 'text.secondary', '&:hover': { color: 'primary.main' } }}
                  >
                    <YouTubeIcon />
                  </IconButton>
                )}
                {facebookUrl && (
                  <IconButton 
                    component="a" 
                    href={facebookUrl} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    size="small"
                    sx={{ color: 'text.secondary', '&:hover': { color: 'primary.main' } }}
                  >
                    <FacebookIcon />
                  </IconButton>
                )}
              </Box>
            )}
          </Grid>

          {/* Middle Column - Products */}
          <Grid item xs={12} sm={6} md={2}>
            <Typography
              variant="subtitle2"
              sx={{
                fontWeight: 600,
                fontSize: '0.875rem',
                mb: 2,
                color: 'text.primary',
              }}
            >
              Products
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Link
                component="button"
                onClick={() => navigate('/assessment')}
                sx={{
                  textAlign: 'left',
                  color: 'text.secondary',
                  fontSize: '0.875rem',
                  textDecoration: 'none',
                  '&:hover': { color: 'primary.main' },
                  cursor: 'pointer',
                }}
              >
                Assessment Engine
              </Link>
              <Link
                component="button"
                onClick={() => navigate('/intelligence')}
                sx={{
                  textAlign: 'left',
                  color: 'text.secondary',
                  fontSize: '0.875rem',
                  textDecoration: 'none',
                  '&:hover': { color: 'primary.main' },
                  cursor: 'pointer',
                }}
              >
                Market Intelligence Engine
              </Link>
              <Link
                component="button"
                onClick={() => navigate('/mentors')}
                sx={{
                  textAlign: 'left',
                  color: 'text.secondary',
                  fontSize: '0.875rem',
                  textDecoration: 'none',
                  '&:hover': { color: 'primary.main' },
                  cursor: 'pointer',
                }}
              >
                MentorBridge
              </Link>
            </Box>
          </Grid>

          {/* Resources Column */}
          <Grid item xs={12} sm={6} md={2}>
            <Typography
              variant="subtitle2"
              sx={{
                fontWeight: 600,
                fontSize: '0.875rem',
                mb: 2,
                color: 'text.primary',
              }}
            >
              Resources
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Link
                component="button"
                onClick={() => navigate('/resources')}
                sx={{
                  textAlign: 'left',
                  color: 'text.secondary',
                  fontSize: '0.875rem',
                  textDecoration: 'none',
                  '&:hover': { color: 'primary.main' },
                  cursor: 'pointer',
                }}
              >
                Blog / Insights
              </Link>
              <Link
                component="button"
                onClick={() => navigate('/resources/resume-tips')}
                sx={{
                  textAlign: 'left',
                  color: 'text.secondary',
                  fontSize: '0.875rem',
                  textDecoration: 'none',
                  '&:hover': { color: 'primary.main' },
                  cursor: 'pointer',
                }}
              >
                Resume Tips
              </Link>
              <Link
                component="button"
                onClick={() => navigate('/resources/interview-guide')}
                sx={{
                  textAlign: 'left',
                  color: 'text.secondary',
                  fontSize: '0.875rem',
                  textDecoration: 'none',
                  '&:hover': { color: 'primary.main' },
                  cursor: 'pointer',
                }}
              >
                Interview Guide
              </Link>
              <Link
                component="button"
                onClick={() => navigate('/resources/career-roadmaps')}
                sx={{
                  textAlign: 'left',
                  color: 'text.secondary',
                  fontSize: '0.875rem',
                  textDecoration: 'none',
                  '&:hover': { color: 'primary.main' },
                  cursor: 'pointer',
                }}
              >
                Career Roadmaps
              </Link>
            </Box>
          </Grid>

          {/* Company Column */}
          <Grid item xs={12} sm={6} md={2}>
            <Typography
              variant="subtitle2"
              sx={{
                fontWeight: 600,
                fontSize: '0.875rem',
                mb: 2,
                color: 'text.primary',
              }}
            >
              Company
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Link
                component="button"
                onClick={() => navigate('/about')}
                sx={{
                  textAlign: 'left',
                  color: 'text.secondary',
                  fontSize: '0.875rem',
                  textDecoration: 'none',
                  '&:hover': { color: 'primary.main' },
                  cursor: 'pointer',
                }}
              >
                About
              </Link>
              <Link
                component="button"
                onClick={() => navigate('/contact')}
                sx={{
                  textAlign: 'left',
                  color: 'text.secondary',
                  fontSize: '0.875rem',
                  textDecoration: 'none',
                  '&:hover': { color: 'primary.main' },
                  cursor: 'pointer',
                }}
              >
                Contact
              </Link>
              <Link
                component="button"
                onClick={() => navigate('/become-a-mentor')}
                sx={{
                  textAlign: 'left',
                  color: 'text.secondary',
                  fontSize: '0.875rem',
                  textDecoration: 'none',
                  '&:hover': { color: 'primary.main' },
                  cursor: 'pointer',
                }}
              >
                Become a Mentor
              </Link>
            </Box>
          </Grid>

          {/* Contact Info Column */}
          <Grid item xs={12} sm={6} md={2}>
            <Typography
              variant="subtitle2"
              sx={{
                fontWeight: 600,
                fontSize: '0.875rem',
                mb: 2,
                color: 'text.primary',
              }}
            >
              Contact
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              {supportEmail && (
                <Typography
                  variant="body2"
                  sx={{
                    color: 'text.secondary',
                    fontSize: '0.875rem',
                  }}
                >
                  {supportEmail}
                </Typography>
              )}
              {officeAddress && (
                <Typography
                  variant="body2"
                  sx={{
                    color: 'text.secondary',
                    fontSize: '0.875rem',
                    mt: 1,
                  }}
                >
                  {officeAddress}
                </Typography>
              )}
            </Box>
          </Grid>
        </Grid>

        {/* Copyright Bar */}
        <Box
          sx={{
            mt: 6,
            pt: 4,
            borderTop: '1px solid',
            borderColor: 'grey.200',
            textAlign: 'center',
          }}
        >
          <Typography
            variant="body2"
            sx={{
              color: 'text.secondary',
              fontSize: '0.813rem',
            }}
          >
            © {new Date().getFullYear()} {platformName}. All rights reserved.
          </Typography>
        </Box>
      </Container>
    </Box>
  );
};

export default Footer;
