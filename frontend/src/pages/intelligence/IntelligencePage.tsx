import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  Paper,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  CheckCircle as CheckCircleIcon,
  ArrowForward as ArrowForwardIcon,
  Analytics as AnalyticsIcon,
  ShowChart as ShowChartIcon,
  Insights as InsightsIcon,
  Assessment as AssessmentIcon,
  Psychology as PsychologyIcon,
  AttachMoney as AttachMoneyIcon,
} from '@mui/icons-material';

const IntelligencePage: React.FC = () => {
  const navigate = useNavigate();
  const isAuthenticated = !!localStorage.getItem('access_token');

  const features = [
    {
      icon: <AnalyticsIcon sx={{ fontSize: 40, color: 'primary.main' }} />,
      title: 'AI Job Trend Analysis',
      description: 'Get real-time insights into job market trends, emerging roles, and industry shifts powered by advanced AI algorithms.',
    },
    {
      icon: <PsychologyIcon sx={{ fontSize: 40, color: 'primary.main' }} />,
      title: 'Skill Gap Detection',
      description: 'Identify which skills are in high demand and discover gaps in your current skill set compared to market requirements.',
    },
    {
      icon: <InsightsIcon sx={{ fontSize: 40, color: 'primary.main' }} />,
      title: 'Personalized Career Recommendations',
      description: 'Receive AI-powered career path recommendations based on your profile, goals, and current market opportunities.',
    },
    {
      icon: <ShowChartIcon sx={{ fontSize: 40, color: 'primary.main' }} />,
      title: 'Real-time Job Market Data',
      description: 'Access up-to-date job market data including job postings, hiring trends, and industry growth patterns.',
    },
    {
      icon: <TrendingUpIcon sx={{ fontSize: 40, color: 'primary.main' }} />,
      title: 'Emerging Industry Forecasting',
      description: 'Stay ahead with predictions about emerging industries, technologies, and career opportunities.',
    },
    {
      icon: <AttachMoneyIcon sx={{ fontSize: 40, color: 'primary.main' }} />,
      title: 'Salary & Demand Insights',
      description: 'Understand salary ranges, compensation trends, and demand levels for roles matching your skills.',
    },
  ];

  const benefits = [
    'Real-time job market trends and industry insights',
    'AI-powered skill gap analysis with actionable recommendations',
    'Personalized career path recommendations based on market data',
    'Salary insights and compensation trend analysis',
    'Emerging industry and technology forecasting',
    'Job demand analysis to identify high-opportunity roles',
  ];

  return (
    <Box sx={{ width: '100%', maxWidth: '1200px', mx: 'auto', px: { xs: 2, sm: 3, md: 6 }, py: { xs: 4, md: 6 } }}>
      {/* Hero Banner Section */}
      <Box
        sx={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          py: { xs: 6, md: 8 },
          px: { xs: 3, md: 4 },
          borderRadius: { xs: 0, md: 3 },
          mb: 6,
        }}
      >
        <Box
          sx={{
            display: 'flex',
            flexDirection: { xs: 'column', md: 'row' },
            alignItems: { xs: 'flex-start', md: 'center' },
            justifyContent: 'space-between',
            gap: 3,
          }}
        >
          <Box sx={{ flex: 1, maxWidth: { md: '60%' } }}>
            <Typography
              variant="h2"
              component="h1"
              sx={{
                fontWeight: 700,
                fontSize: { xs: '2rem', md: '2.75rem' },
                color: 'white',
                mb: 2,
                lineHeight: 1.2,
              }}
            >
              Unlock Real-Time Market Intelligence for Your Career
            </Typography>
            <Typography
              variant="h5"
              component="p"
              sx={{
                fontSize: { xs: '1rem', md: '1.25rem' },
                color: 'rgba(255, 255, 255, 0.95)',
                mb: 3,
                lineHeight: 1.6,
              }}
            >
              Understand job trends, discover high-demand roles, and make smarter career decisions with AI-powered job market insights.
            </Typography>
            <Box
              sx={{
                display: 'flex',
                flexDirection: { xs: 'column', sm: 'row' },
                gap: 2,
                width: { xs: '100%', md: 'auto' },
              }}
            >
              <Button
                variant="contained"
                onClick={() => navigate(isAuthenticated ? '/dashboard/intelligence' : '/register')}
                endIcon={<ArrowForwardIcon />}
                sx={{
                  textTransform: 'none',
                  fontWeight: 600,
                  py: 1.5,
                  px: 4,
                  bgcolor: 'white',
                  color: 'primary.main',
                  fontSize: '1rem',
                  '&:hover': {
                    bgcolor: 'rgba(255, 255, 255, 0.9)',
                    transform: 'translateY(-2px)',
                    boxShadow: '0 8px 16px rgba(0,0,0,0.2)',
                  },
                  transition: 'all 0.3s',
                }}
              >
                {isAuthenticated ? 'Go to Intelligence Dashboard' : 'Start Free Assessment'}
              </Button>
              <Button
                variant="outlined"
                onClick={() => navigate('/login')}
                sx={{
                  textTransform: 'none',
                  fontWeight: 500,
                  py: 1.5,
                  px: 3,
                  borderColor: 'white',
                  color: 'white',
                  fontSize: '1rem',
                  '&:hover': {
                    borderColor: 'rgba(255, 255, 255, 0.8)',
                    bgcolor: 'rgba(255, 255, 255, 0.1)',
                  },
                }}
              >
                Sign In
              </Button>
            </Box>
          </Box>
        </Box>
      </Box>

      {/* Features Section */}
      <Box sx={{ mb: 8 }}>
        <Typography
          variant="h3"
          component="h2"
          align="center"
          sx={{
            fontWeight: 700,
            fontSize: { xs: '2rem', md: '2.5rem' },
            mb: 6,
            color: 'text.primary',
          }}
        >
          Powerful Market Intelligence Features
        </Typography>
        <Grid container spacing={4}>
          {features.map((feature, index) => (
            <Grid item xs={12} sm={6} md={4} key={index}>
              <Card
                sx={{
                  height: '100%',
                  p: 4,
                  textAlign: 'center',
                  transition: 'all 0.3s',
                  '&:hover': {
                    transform: 'translateY(-8px)',
                    boxShadow: 8,
                  },
                  border: '1px solid',
                  borderColor: 'grey.200',
                }}
              >
                <Box sx={{ mb: 2 }}>{feature.icon}</Box>
                <Typography
                  variant="h6"
                  component="h3"
                  sx={{
                    fontWeight: 600,
                    mb: 2,
                    color: 'text.primary',
                  }}
                >
                  {feature.title}
                </Typography>
                <Typography
                  variant="body2"
                  sx={{
                    color: 'text.secondary',
                    lineHeight: 1.6,
                  }}
                >
                  {feature.description}
                </Typography>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Box>

      {/* Benefits Section */}
      <Box sx={{ mb: 8 }}>
        <Grid container spacing={4} alignItems="center">
          <Grid item xs={12} md={6}>
            <Typography
              variant="h3"
              component="h2"
              sx={{
                fontWeight: 700,
                fontSize: { xs: '2rem', md: '2.5rem' },
                mb: 4,
                color: 'text.primary',
              }}
            >
              Make Data-Driven Career Decisions
            </Typography>
            <List>
              {benefits.map((benefit, index) => (
                <ListItem key={index} sx={{ py: 1.5, px: 0 }}>
                  <ListItemIcon sx={{ minWidth: 40 }}>
                    <CheckCircleIcon sx={{ color: 'success.main', fontSize: 28 }} />
                  </ListItemIcon>
                  <ListItemText
                    primary={benefit}
                    primaryTypographyProps={{
                      variant: 'body1',
                      sx: { fontWeight: 500 },
                    }}
                  />
                </ListItem>
              ))}
            </List>
            <Button
              variant="contained"
              size="large"
              onClick={() => navigate(isAuthenticated ? '/dashboard/intelligence' : '/register')}
              endIcon={<ArrowForwardIcon />}
              sx={{
                mt: 4,
                px: 4,
                py: 1.5,
                textTransform: 'none',
                fontWeight: 600,
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                '&:hover': {
                  background: 'linear-gradient(135deg, #5568d3 0%, #6a3d8f 100%)',
                  transform: 'translateY(-2px)',
                  boxShadow: '0 8px 16px rgba(102, 126, 234, 0.4)',
                },
                transition: 'all 0.3s',
              }}
            >
              {isAuthenticated ? 'Go to Intelligence Dashboard' : 'Start Your Free Assessment'}
            </Button>
          </Grid>
          <Grid item xs={12} md={6}>
            <Paper
              elevation={3}
              sx={{
                p: 4,
                background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
                borderRadius: 3,
                textAlign: 'center',
              }}
            >
              <TrendingUpIcon sx={{ fontSize: 80, color: 'primary.main', mb: 2 }} />
              <Typography variant="h5" sx={{ fontWeight: 600, mb: 2 }}>
                Real-Time Market Data
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Our Market Intelligence Engine continuously analyzes millions of job postings, salary data, and industry trends to provide you with the most up-to-date career insights.
              </Typography>
            </Paper>
          </Grid>
        </Grid>
      </Box>

      {/* Final CTA Section */}
      <Box
        sx={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          py: { xs: 6, md: 8 },
          px: { xs: 3, md: 6 },
          borderRadius: { xs: 0, md: 3 },
          textAlign: 'center',
        }}
      >
        <Typography
          variant="h3"
          component="h2"
          sx={{
            fontWeight: 700,
            fontSize: { xs: '2rem', md: '2.5rem' },
            color: 'white',
            mb: 2,
          }}
        >
          Make smarter career decisions with AI-powered insights.
        </Typography>
        <Typography
          variant="h6"
          sx={{
            color: 'rgba(255, 255, 255, 0.9)',
            mb: 4,
            maxWidth: '600px',
            mx: 'auto',
          }}
        >
          Start your free assessment and unlock real-time market intelligence to guide your career journey.
        </Typography>
        <Button
          variant="contained"
          size="large"
          onClick={() => navigate(isAuthenticated ? '/dashboard/intelligence' : '/register')}
          endIcon={<ArrowForwardIcon />}
          sx={{
            bgcolor: 'white',
            color: 'primary.main',
            px: 5,
            py: 1.5,
            fontSize: '1.1rem',
            fontWeight: 600,
            textTransform: 'none',
            borderRadius: '8px',
            '&:hover': {
              bgcolor: 'rgba(255, 255, 255, 0.9)',
              transform: 'translateY(-2px)',
              boxShadow: '0 8px 16px rgba(0,0,0,0.2)',
            },
            transition: 'all 0.3s',
          }}
        >
          {isAuthenticated ? 'Go to Intelligence Dashboard' : 'Start Free Assessment'}
        </Button>
      </Box>
    </Box>
  );
};

export default IntelligencePage;

