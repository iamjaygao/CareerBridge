import React from 'react';
import { Box, Typography, Button, Grid, Card, CardContent, List, ListItem, ListItemIcon, ListItemText } from '@mui/material';
import { CheckCircle, ArrowForward, People, School, TrendingUp } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

const BecomeMentorPage: React.FC = () => {
  const navigate = useNavigate();
  const isAuthenticated = !!localStorage.getItem('access_token');

  const benefits = [
    'Help shape the next generation of professionals',
    'Build your personal brand and expand your network',
    'Flexible scheduling that fits your availability',
    'Competitive compensation for your expertise',
    'Access to CareerBridge mentor resources and training',
  ];

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
          Become a Mentor
        </Typography>
        <Typography
          variant="h5"
          sx={{
            fontSize: { xs: '1rem', md: '1.25rem' },
            color: 'rgba(255, 255, 255, 0.95)',
            maxWidth: '700px',
            mx: 'auto',
            mb: 3,
          }}
        >
          Share your expertise and help professionals advance their careers.
        </Typography>
        <Button
          variant="contained"
          size="large"
          onClick={() => navigate(isAuthenticated ? '/profile' : '/register')}
          endIcon={<ArrowForward />}
          sx={{
            bgcolor: 'white',
            color: 'primary.main',
            px: 4,
            py: 1.5,
            textTransform: 'none',
            fontWeight: 600,
            '&:hover': { bgcolor: 'rgba(255, 255, 255, 0.9)' },
          }}
        >
          Apply to Become a Mentor
        </Button>
      </Box>

      <Box sx={{ mb: 8 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 4, textAlign: 'center' }}>
          Why Become a Mentor?
        </Typography>
        <List>
          {benefits.map((benefit, index) => (
            <ListItem key={index} sx={{ py: 1.5 }}>
              <ListItemIcon>
                <CheckCircle sx={{ color: 'success.main' }} />
              </ListItemIcon>
              <ListItemText
                primary={benefit}
                primaryTypographyProps={{ variant: 'body1', sx: { fontWeight: 500 } }}
              />
            </ListItem>
          ))}
        </List>
      </Box>

      <Grid container spacing={4} sx={{ mb: 8 }}>
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%', p: 3, textAlign: 'center' }}>
            <People sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
              Make an Impact
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Guide professionals through critical career decisions and help them achieve their goals.
            </Typography>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%', p: 3, textAlign: 'center' }}>
            <School sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
              Share Your Expertise
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Leverage your industry knowledge and experience to help others grow.
            </Typography>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%', p: 3, textAlign: 'center' }}>
            <TrendingUp sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
              Build Your Network
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Connect with ambitious professionals and expand your influence in your industry.
            </Typography>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default BecomeMentorPage;

