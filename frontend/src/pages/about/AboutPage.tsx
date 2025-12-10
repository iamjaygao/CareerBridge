import React from 'react';
import { Box, Typography, Container, Grid, Card, CardContent } from '@mui/material';
import { People, School, TrendingUp } from '@mui/icons-material';

const AboutPage: React.FC = () => {
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
          About CareerBridge
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
          The AI engine that tells you what to do next in your career.
        </Typography>
      </Box>

      <Box sx={{ mb: 8 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 4 }}>
          Our Mission
        </Typography>
        <Typography variant="body1" sx={{ fontSize: '1.1rem', lineHeight: 1.8, mb: 4 }}>
          CareerBridge was founded to solve a critical problem: the job market is confusing, and career decisions are overwhelming. 
          We combine AI-powered assessment, real-time market intelligence, and expert mentorship to give you clear, actionable guidance 
          for every step of your career journey.
        </Typography>
        <Typography variant="body1" sx={{ fontSize: '1.1rem', lineHeight: 1.8 }}>
          Our platform helps thousands of professionals make smarter career decisions by providing personalized insights, 
          skill gap analysis, and direct access to industry experts who can guide you toward your goals.
        </Typography>
      </Box>

      <Grid container spacing={4} sx={{ mb: 8 }}>
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%', p: 3 }}>
            <People sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
            <Typography variant="h5" sx={{ fontWeight: 600, mb: 2 }}>
              Expert Mentorship
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Connect with experienced professionals who provide personalized guidance and support.
            </Typography>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%', p: 3 }}>
            <School sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
            <Typography variant="h5" sx={{ fontWeight: 600, mb: 2 }}>
              AI-Powered Insights
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Get instant, data-driven recommendations based on your skills and career goals.
            </Typography>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%', p: 3 }}>
            <TrendingUp sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
            <Typography variant="h5" sx={{ fontWeight: 600, mb: 2 }}>
              Market Intelligence
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Access real-time job market trends and industry insights to make informed decisions.
            </Typography>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default AboutPage;

