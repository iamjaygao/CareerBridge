import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  Container,
  Paper,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
} from '@mui/material';
import {
  Assessment as AssessmentIcon,
  TrendingUp as TrendingUpIcon,
  People as PeopleIcon,
  Upload as UploadIcon,
  Analytics as AnalyticsIcon,
  Lightbulb as LightbulbIcon,
  Person as PersonIcon,
  CheckCircle as CheckCircleIcon,
  ArrowForward as ArrowForwardIcon,
  AutoAwesome as AutoAwesomeIcon,
  BarChart as BarChartIcon,
  Psychology as PsychologyIcon,
  VerifiedUser as VerifiedUserIcon,
  Star as StarIcon,
} from '@mui/icons-material';

const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const isAuthenticated = !!localStorage.getItem('access_token');
  const allowHomepage = new URLSearchParams(location.search).get('from') === 'portal';

  // If user is already logged in, redirect to dashboard
  React.useEffect(() => {
    if (isAuthenticated && !allowHomepage) {
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, allowHomepage, navigate]);

  const painPoints = [
    "You don't know which skills to learn next",
    "Job descriptions are overwhelming and unclear",
    "You're unsure if you're qualified for roles you want",
  ];

  const engines = [
    {
      title: 'Assessment Engine',
      subtitle: 'AI Resume Analysis & Job-Fit Scoring',
      icon: <AssessmentIcon sx={{ fontSize: 48, color: 'primary.main' }} />,
      features: [
        'AI-powered resume scoring',
        'Job description matching',
        'Skill gap analysis',
        'ATS optimization',
      ],
      color: '#667eea',
    },
    {
      title: 'Market Intelligence Engine',
      subtitle: 'Real-Time Job Market Insights',
      icon: <TrendingUpIcon sx={{ fontSize: 48, color: 'primary.main' }} />,
      features: [
        'Real-time job market trends',
        'In-demand skills analysis',
        'Salary insights',
        'Industry fit scoring',
      ],
      color: '#764ba2',
    },
    {
      title: 'MentorBridge',
      subtitle: 'Expert Mentorship & Execution Support',
      icon: <PeopleIcon sx={{ fontSize: 48, color: 'primary.main' }} />,
      features: [
        'Mock interviews',
        'Resume review',
        'Career guidance',
        'Action roadmap',
      ],
      color: '#667eea',
    },
  ];

  const howItWorks = [
    {
      step: 1,
      title: 'Upload Resume',
      description: 'Upload your resume and let our AI analyze your skills, experience, and qualifications.',
      icon: <UploadIcon />,
    },
    {
      step: 2,
      title: 'Get Assessment',
      description: 'Receive instant AI-powered scoring and job-fit analysis with detailed insights.',
      icon: <AnalyticsIcon />,
    },
    {
      step: 3,
      title: 'View Insights',
      description: 'See market trends, in-demand skills, and personalized recommendations.',
      icon: <LightbulbIcon />,
    },
    {
      step: 4,
      title: 'Connect with Mentor',
      description: 'Book sessions with expert mentors for personalized guidance and mock interviews.',
      icon: <PersonIcon />,
    },
    {
      step: 5,
      title: 'Get Action Roadmap',
      description: 'Receive a clear, actionable plan to achieve your career goals.',
      icon: <ArrowForwardIcon />,
    },
  ];

  const testimonials = [
    {
      name: 'Sarah Chen',
      role: 'Software Engineer',
      company: 'Tech Corp',
      text: 'CareerBridge told me exactly which skills to learn. I landed my dream job in 3 months.',
      rating: 5,
    },
    {
      name: 'Michael Rodriguez',
      role: 'Product Manager',
      company: 'StartupXYZ',
      text: 'The market intelligence helped me understand what employers really want. Game changer.',
      rating: 5,
    },
    {
      name: 'Emily Johnson',
      role: 'Data Scientist',
      company: 'DataCo',
      text: 'My mentor helped me prepare for interviews. The mock sessions were incredibly valuable.',
      rating: 5,
    },
  ];

  return (
    <Box sx={{ width: '100%', maxWidth: '1200px', mx: 'auto', px: { xs: 2, sm: 3, md: 6 }, py: { xs: 4, md: 6 } }}>
      {/* Hero Section */}
      <Box
        sx={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          py: { xs: 8, md: 12 },
          px: { xs: 3, md: 6 },
          borderRadius: { xs: 0, md: 3 },
          mb: 8,
          textAlign: 'center',
        }}
      >
        <Typography
          variant="h1"
          component="h1"
          sx={{
            fontWeight: 700,
            fontSize: { xs: '2.5rem', md: '3.5rem', lg: '4rem' },
            color: 'white',
            mb: 3,
            lineHeight: 1.2,
          }}
        >
          Find clarity in your career.
          <br />
          Know your next step.
        </Typography>
        <Typography
          variant="h5"
          component="p"
          sx={{
            fontSize: { xs: '1.1rem', md: '1.3rem' },
            color: 'rgba(255, 255, 255, 0.95)',
            mb: 5,
            maxWidth: '800px',
            mx: 'auto',
            lineHeight: 1.6,
          }}
        >
          CareerBridge analyzes your skills, the job market, and your goals — then tells you exactly what to do next.
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
          <Button
            variant="contained"
            size="large"
            onClick={() => navigate('/register')}
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
            Start Your Free Assessment
          </Button>
          <Button
            variant="outlined"
            size="large"
            onClick={() => navigate('/login')}
            sx={{
              borderColor: 'white',
              color: 'white',
              px: 4,
              py: 1.5,
              fontSize: '1.1rem',
              fontWeight: 600,
              textTransform: 'none',
              borderRadius: '8px',
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

      {/* Pain Point Section */}
      <Box sx={{ mb: 10, textAlign: 'center' }}>
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
          The job market is confusing.
          <br />
          We make your next step obvious.
        </Typography>
        <List sx={{ maxWidth: '600px', mx: 'auto' }}>
          {painPoints.map((point, index) => (
            <ListItem key={index} sx={{ py: 2, justifyContent: 'center' }}>
              <ListItemIcon sx={{ minWidth: 40 }}>
                <CheckCircleIcon sx={{ color: 'primary.main', fontSize: 28 }} />
              </ListItemIcon>
              <ListItemText
                primary={point}
                primaryTypographyProps={{
                  variant: 'h6',
                  sx: { fontWeight: 500, fontSize: { xs: '1rem', md: '1.125rem' } },
                }}
              />
            </ListItem>
          ))}
        </List>
      </Box>

      {/* Three Engine Sections */}
      <Box sx={{ mb: 10 }}>
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
          Three Engines. One Clear Path Forward.
        </Typography>
        <Grid container spacing={4}>
          {engines.map((engine, index) => (
            <Grid item xs={12} md={4} key={index}>
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
                <Box sx={{ mb: 3 }}>{engine.icon}</Box>
                <Typography
                  variant="h5"
                  component="h3"
                  sx={{
                    fontWeight: 700,
                    mb: 1,
                    color: 'text.primary',
                  }}
                >
                  {engine.title}
                </Typography>
                <Typography
                  variant="body1"
                  sx={{
                    mb: 3,
                    color: 'text.secondary',
                    fontWeight: 500,
                  }}
                >
                  {engine.subtitle}
                </Typography>
                <List dense>
                  {engine.features.map((feature, idx) => (
                    <ListItem key={idx} sx={{ py: 0.5, justifyContent: 'center' }}>
                      <ListItemIcon sx={{ minWidth: 32 }}>
                        <CheckCircleIcon sx={{ color: 'success.main', fontSize: 20 }} />
                      </ListItemIcon>
                      <ListItemText
                        primary={feature}
                        primaryTypographyProps={{
                          variant: 'body2',
                          sx: { fontSize: '0.9rem' },
                        }}
                      />
                    </ListItem>
                  ))}
                </List>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Box>

      {/* How It Works Section */}
      <Box sx={{ mb: 10 }}>
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
          How It Works
        </Typography>
        <Grid container spacing={4}>
          {howItWorks.map((step, index) => (
            <Grid item xs={12} sm={6} md={4} key={index}>
              <Card
                sx={{
                  height: '100%',
                  p: 3,
                  textAlign: 'center',
                  position: 'relative',
                  border: '1px solid',
                  borderColor: 'grey.200',
                }}
              >
                <Box
                  sx={{
                    position: 'absolute',
                    top: 16,
                    right: 16,
                    bgcolor: 'primary.main',
                    color: 'white',
                    borderRadius: '50%',
                    width: 32,
                    height: 32,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: 700,
                    fontSize: '0.875rem',
                  }}
                >
                  {step.step}
                </Box>
                <Box sx={{ mb: 2, color: 'primary.main' }}>{step.icon}</Box>
                <Typography
                  variant="h6"
                  component="h3"
                  sx={{
                    fontWeight: 600,
                    mb: 1,
                    color: 'text.primary',
                  }}
                >
                  {step.title}
                </Typography>
                <Typography
                  variant="body2"
                  sx={{
                    color: 'text.secondary',
                    lineHeight: 1.6,
                  }}
                >
                  {step.description}
                </Typography>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Box>

      {/* Social Proof Section */}
      <Box sx={{ mb: 10 }}>
        <Typography
          variant="h3"
          component="h2"
          align="center"
          sx={{
            fontWeight: 700,
            fontSize: { xs: '2rem', md: '2.5rem' },
            mb: 2,
            color: 'text.primary',
          }}
        >
          Trusted by Thousands of Professionals
        </Typography>
        <Typography
          variant="body1"
          align="center"
          sx={{
            mb: 6,
            color: 'text.secondary',
            fontSize: '1.1rem',
          }}
        >
          Join professionals who have found clarity and landed their dream jobs
        </Typography>

        {/* Stats */}
        <Grid container spacing={4} sx={{ mb: 6 }}>
          <Grid item xs={12} sm={4}>
            <Paper
              elevation={0}
              sx={{
                p: 3,
                textAlign: 'center',
                bgcolor: 'grey.50',
                borderRadius: 2,
              }}
            >
              <Typography
                variant="h3"
                sx={{
                  fontWeight: 700,
                  color: 'primary.main',
                  mb: 1,
                }}
              >
                10K+
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Active Users
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Paper
              elevation={0}
              sx={{
                p: 3,
                textAlign: 'center',
                bgcolor: 'grey.50',
                borderRadius: 2,
              }}
            >
              <Typography
                variant="h3"
                sx={{
                  fontWeight: 700,
                  color: 'primary.main',
                  mb: 1,
                }}
              >
                500+
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Expert Mentors
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Paper
              elevation={0}
              sx={{
                p: 3,
                textAlign: 'center',
                bgcolor: 'grey.50',
                borderRadius: 2,
              }}
            >
              <Typography
                variant="h3"
                sx={{
                  fontWeight: 700,
                  color: 'primary.main',
                  mb: 1,
                }}
              >
                50K+
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Resumes Analyzed
              </Typography>
            </Paper>
          </Grid>
        </Grid>

        {/* Testimonials */}
        <Grid container spacing={4}>
          {testimonials.map((testimonial, index) => (
            <Grid item xs={12} md={4} key={index}>
              <Card
                sx={{
                  height: '100%',
                  p: 3,
                  border: '1px solid',
                  borderColor: 'grey.200',
                }}
              >
                <Box sx={{ display: 'flex', mb: 2 }}>
                  {[...Array(testimonial.rating)].map((_, i) => (
                    <StarIcon key={i} sx={{ color: 'warning.main', fontSize: 20 }} />
                  ))}
                </Box>
                <Typography
                  variant="body1"
                  sx={{
                    mb: 3,
                    fontStyle: 'italic',
                    color: 'text.secondary',
                    lineHeight: 1.6,
                  }}
                >
                  "{testimonial.text}"
                </Typography>
                <Box>
                  <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                    {testimonial.name}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {testimonial.role} at {testimonial.company}
                  </Typography>
                </Box>
              </Card>
            </Grid>
          ))}
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
          Ready to know your next step?
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
          Start your free assessment and get a clear, actionable roadmap to your career goals.
        </Typography>
        <Button
          variant="contained"
          size="large"
          onClick={() => navigate('/register')}
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
          Start Your Free Assessment
        </Button>
      </Box>
    </Box>
  );
};

export default LandingPage;
