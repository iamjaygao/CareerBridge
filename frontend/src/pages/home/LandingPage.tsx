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
  Chip,
} from '@mui/material';
import {
  Assessment as AssessmentIcon,
  TrendingUp as TrendingUpIcon,
  People as PeopleIcon,
  ArrowForward as ArrowForwardIcon,
  AutoAwesome as AutoAwesomeIcon,
  Bolt as BoltIcon,
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

  const heroStats = [
    { label: 'Profiles analyzed', value: '50k+' },
    { label: 'Mentor sessions delivered', value: '18k+' },
    { label: 'Avg. job-fit lift', value: '34%' },
  ];

  const engines = [
    {
      title: 'Assessment Engine',
      description: 'Resume and job-fit scoring that turns ambiguity into a concrete plan.',
      icon: <AssessmentIcon sx={{ fontSize: 30 }} />,
      highlights: ['Fit score + gap list', 'ATS-ready resume notes', 'Role readiness report'],
    },
    {
      title: 'Market Intelligence',
      description: 'A live signal of which skills, roles, and locations are rising now.',
      icon: <TrendingUpIcon sx={{ fontSize: 30 }} />,
      highlights: ['Demand heatmap', 'Salary benchmarks', 'Skill priority order'],
    },
    {
      title: 'MentorBridge',
      description: 'Execution support from senior mentors who help you move fast.',
      icon: <PeopleIcon sx={{ fontSize: 30 }} />,
      highlights: ['Mock interviews', 'Resume review', 'Weekly checkpoints'],
    },
  ];

  const audiences = [
    {
      title: 'Students and Career Switchers',
      description: 'Find the roles you can win next and the skills to prioritize.',
      cta: 'Start free assessment',
      path: '/register',
    },
    {
      title: 'Mentors and Coaches',
      description: 'Showcase your expertise and guide high-intent candidates.',
      cta: 'Join as mentor',
      path: '/register',
    },
  ];

  const steps = [
    {
      title: 'Upload your resume',
      description: 'We parse it, score it, and map it to roles you want.',
    },
    {
      title: 'See your skill gaps',
      description: 'Get a ranked list of what to learn next and why.',
    },
    {
      title: 'Build your roadmap',
      description: 'Follow the plan or book a mentor to accelerate.',
    },
    {
      title: 'Track momentum',
      description: 'Weekly checkpoints keep you moving and accountable.',
    },
  ];

  const retentionPillars = [
    {
      title: 'Weekly focus',
      description: 'We translate the market into a one-week learning target.',
    },
    {
      title: 'Proof of progress',
      description: 'Track score improvements and interview readiness.',
    },
    {
      title: 'Real mentor feedback',
      description: 'Get clear, direct notes so you know what to fix.',
    },
  ];

  const testimonials = [
    {
      name: 'Sarah Chen',
      role: 'Software Engineer',
      company: 'Tech Corp',
      text: 'CareerBridge told me exactly which skills to learn. I landed my next role in 10 weeks.',
      rating: 5,
    },
    {
      name: 'Michael Rodriguez',
      role: 'Product Manager',
      company: 'StartupXYZ',
      text: 'The market intelligence made hiring signals obvious. No more guessing.',
      rating: 5,
    },
    {
      name: 'Emily Johnson',
      role: 'Data Scientist',
      company: 'DataCo',
      text: 'My mentor was blunt, in a good way. The feedback loop kept me on track.',
      rating: 5,
    },
  ];

  const faqs = [
    {
      question: 'Is the assessment really free?',
      answer: 'Yes. You can run a full assessment before you decide to book a mentor.',
    },
    {
      question: 'How fast do I get results?',
      answer: 'Most users receive their score and roadmap within minutes.',
    },
    {
      question: 'Can I use it if I am changing careers?',
      answer: 'Yes. We highlight adjacent roles and the fastest skill jumps.',
    },
  ];

  return (
    <Box
      sx={{
        position: 'relative',
        overflow: 'hidden',
        pb: { xs: 8, md: 12 },
        '& @keyframes fadeUp': {
          from: { opacity: 0, transform: 'translateY(18px)' },
          to: { opacity: 1, transform: 'translateY(0px)' },
        },
        '& @keyframes slowFloat': {
          '0%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(18px)' },
          '100%': { transform: 'translateY(0px)' },
        },
      }}
    >
      <Box
        sx={{
          position: 'absolute',
          top: -140,
          right: -140,
          width: 360,
          height: 360,
          borderRadius: '50%',
          background:
            'radial-gradient(circle at 30% 30%, rgba(66, 165, 245, 0.5) 0%, rgba(25, 118, 210, 0.25) 55%, rgba(25, 118, 210, 0) 70%)',
          animation: 'slowFloat 12s ease-in-out infinite',
        }}
      />
      <Box
        sx={{
          position: 'absolute',
          bottom: 120,
          left: -180,
          width: 360,
          height: 360,
          borderRadius: '50%',
          background:
            'radial-gradient(circle at 30% 30%, rgba(225, 245, 254, 0.9) 0%, rgba(144, 202, 249, 0.4) 55%, rgba(144, 202, 249, 0) 72%)',
          animation: 'slowFloat 14s ease-in-out infinite',
        }}
      />

      {/* Hero Section */}
      <Container maxWidth="xl" sx={{ pt: { xs: 6, md: 10 } }}>
        <Grid container spacing={6} alignItems="center">
          <Grid item xs={12} md={6}>
            <Chip
              icon={<AutoAwesomeIcon sx={{ color: 'primary.main' }} />}
              label="Career clarity engine"
              sx={{
                bgcolor: 'rgba(25, 118, 210, 0.08)',
                color: 'primary.main',
                fontWeight: 600,
                mb: 3,
              }}
            />
            <Typography
              variant="h1"
              sx={{
                fontWeight: 700,
                fontSize: { xs: '2.6rem', md: '3.6rem', lg: '4.2rem' },
                color: 'text.primary',
                lineHeight: 1.1,
                mb: 3,
                animation: 'fadeUp 0.7s ease both',
              }}
            >
              Know your next role.
              <br />
              Build the fastest path there.
            </Typography>
            <Typography
              variant="h6"
              sx={{
                color: 'text.secondary',
                fontSize: { xs: '1rem', md: '1.2rem' },
                lineHeight: 1.7,
                mb: 4,
                animation: 'fadeUp 0.7s ease both',
                animationDelay: '0.1s',
              }}
            >
              CareerBridge combines AI assessment, market signals, and mentor execution to
              keep your job search focused and on schedule.
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              <Button
                variant="contained"
                size="large"
                onClick={() => navigate('/register')}
                endIcon={<ArrowForwardIcon />}
                sx={{
                  bgcolor: 'primary.main',
                  color: 'white',
                  px: 4,
                  py: 1.4,
                  fontWeight: 600,
                  borderRadius: '999px',
                  boxShadow: '0 10px 24px rgba(25, 118, 210, 0.25)',
                  '&:hover': {
                    bgcolor: 'primary.dark',
                    transform: 'translateY(-2px)',
                  },
                  transition: 'all 0.2s ease',
                }}
              >
                Start free assessment
              </Button>
              <Button
                variant="outlined"
                size="large"
                onClick={() => navigate('/mentors')}
                sx={{
                  borderColor: 'rgba(25, 118, 210, 0.5)',
                  color: 'text.primary',
                  px: 3.5,
                  py: 1.4,
                  fontWeight: 600,
                  borderRadius: '999px',
                  '&:hover': {
                    borderColor: 'primary.main',
                    bgcolor: 'rgba(25, 118, 210, 0.08)',
                  },
                }}
              >
                Browse mentors
              </Button>
            </Box>
            <Box sx={{ mt: 4, display: 'flex', gap: 3, flexWrap: 'wrap' }}>
              {heroStats.map((stat) => (
                <Box key={stat.label}>
                  <Typography
                    variant="h6"
                    sx={{ fontWeight: 700, color: 'text.primary', mb: 0.5 }}
                  >
                    {stat.value}
                  </Typography>
                  <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                    {stat.label}
                  </Typography>
                </Box>
              ))}
            </Box>
          </Grid>
          <Grid item xs={12} md={6}>
            <Paper
              elevation={0}
              sx={{
                p: { xs: 3, md: 4 },
                borderRadius: 4,
                bgcolor: 'background.paper',
                border: '1px solid rgba(0, 0, 0, 0.06)',
                boxShadow: '0 24px 60px rgba(0, 0, 0, 0.12)',
                animation: 'fadeUp 0.8s ease both',
                animationDelay: '0.2s',
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 3 }}>
                <Box
                  sx={{
                    width: 44,
                    height: 44,
                    borderRadius: '50%',
                    bgcolor: 'rgba(25, 118, 210, 0.12)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <BoltIcon sx={{ color: 'primary.main' }} />
                </Box>
                <Box>
                  <Typography sx={{ fontWeight: 700, color: 'text.primary' }}>
                    Your signal dashboard
                  </Typography>
                  <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                    A snapshot of what matters this week
                  </Typography>
                </Box>
              </Box>
              <Grid container spacing={2}>
                {engines.map((engine, index) => (
                  <Grid item xs={12} key={engine.title}>
                    <Card
                      elevation={0}
                      sx={{
                        p: 2.5,
                        borderRadius: 3,
                        border: '1px solid rgba(25, 118, 210, 0.12)',
                        bgcolor: 'rgba(25, 118, 210, 0.05)',
                        animation: 'fadeUp 0.7s ease both',
                        animationDelay: `${0.2 + index * 0.1}s`,
                      }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1.5 }}>
                        <Box sx={{ color: 'primary.main' }}>{engine.icon}</Box>
                        <Typography sx={{ fontWeight: 700 }}>{engine.title}</Typography>
                      </Box>
                      <Typography variant="body2" sx={{ color: 'text.secondary', mb: 1.5 }}>
                        {engine.description}
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                        {engine.highlights.map((item) => (
                          <Chip
                            key={item}
                            label={item}
                            size="small"
                            sx={{
                              bgcolor: 'rgba(25, 118, 210, 0.12)',
                              color: 'primary.main',
                              fontWeight: 600,
                            }}
                          />
                        ))}
                      </Box>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </Paper>
          </Grid>
        </Grid>
      </Container>

      {/* Audience Section */}
      <Container maxWidth="lg" sx={{ mt: { xs: 10, md: 14 } }}>
        <Typography
          variant="h2"
          sx={{
            fontWeight: 700,
            fontSize: { xs: '2rem', md: '2.6rem' },
            mb: 3,
            textAlign: 'center',
          }}
        >
          Built for real career momentum
        </Typography>
        <Typography
          variant="body1"
          sx={{
            textAlign: 'center',
            color: 'text.secondary',
            maxWidth: 720,
            mx: 'auto',
            mb: 5,
          }}
        >
          Whether you are a student, a career switcher, or a mentor, the platform gives you
          a clear path and the support to move fast.
        </Typography>
        <Grid container spacing={3}>
          {audiences.map((audience, index) => (
            <Grid item xs={12} md={6} key={audience.title}>
              <Card
                elevation={0}
                sx={{
                  p: 4,
                  borderRadius: 4,
                  border: '1px solid rgba(0, 0, 0, 0.08)',
                  bgcolor: 'background.paper',
                  height: '100%',
                  animation: 'fadeUp 0.7s ease both',
                  animationDelay: `${0.1 + index * 0.1}s`,
                }}
              >
                <CardContent sx={{ p: 0 }}>
                  <Typography variant="h5" sx={{ fontWeight: 700, mb: 1 }}>
                    {audience.title}
                  </Typography>
                  <Typography sx={{ color: 'text.secondary', mb: 3 }}>
                    {audience.description}
                  </Typography>
                  <Button
                    variant="outlined"
                    onClick={() => navigate(audience.path)}
                    endIcon={<ArrowForwardIcon />}
                    sx={{
                      borderColor: 'rgba(25, 118, 210, 0.5)',
                      color: 'text.primary',
                      fontWeight: 600,
                      borderRadius: '999px',
                      px: 3,
                    }}
                  >
                    {audience.cta}
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Container>

      {/* How It Works */}
      <Container maxWidth="lg" sx={{ mt: { xs: 10, md: 14 } }}>
        <Box
          sx={{
            p: { xs: 4, md: 6 },
            borderRadius: 5,
            bgcolor: 'rgba(25, 118, 210, 0.06)',
          }}
        >
          <Typography
            variant="h3"
            sx={{
              fontWeight: 700,
              mb: 4,
              textAlign: 'center',
            }}
          >
            How it works
          </Typography>
          <Grid container spacing={3}>
            {steps.map((step, index) => (
              <Grid item xs={12} sm={6} key={step.title}>
                <Box
                  sx={{
                    display: 'flex',
                    gap: 2,
                    alignItems: 'flex-start',
                    animation: 'fadeUp 0.7s ease both',
                    animationDelay: `${0.1 + index * 0.1}s`,
                  }}
                >
                  <Box
                    sx={{
                      width: 36,
                      height: 36,
                      borderRadius: '50%',
                      bgcolor: 'primary.main',
                      color: 'white',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 700,
                    }}
                  >
                    {index + 1}
                  </Box>
                  <Box>
                    <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 0.5 }}>
                      {step.title}
                    </Typography>
                    <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                      {step.description}
                    </Typography>
                  </Box>
                </Box>
              </Grid>
            ))}
          </Grid>
        </Box>
      </Container>

      {/* Retention Section */}
      <Container maxWidth="lg" sx={{ mt: { xs: 10, md: 14 } }}>
        <Grid container spacing={4} alignItems="center">
          <Grid item xs={12} md={5}>
            <Typography
              variant="h3"
              sx={{
                fontWeight: 700,
                mb: 2,
              }}
            >
              Stay on track, week after week
            </Typography>
            <Typography sx={{ color: 'text.secondary', mb: 3 }}>
              We do not just assess. We keep your momentum alive with signals, guidance,
              and accountability.
            </Typography>
            <Button
              variant="contained"
              onClick={() => navigate('/assessment')}
              endIcon={<ArrowForwardIcon />}
              sx={{
                bgcolor: 'primary.main',
                color: 'white',
                fontWeight: 600,
                borderRadius: '999px',
                px: 3,
                boxShadow: '0 12px 24px rgba(25, 118, 210, 0.25)',
                '&:hover': { bgcolor: 'primary.dark' },
              }}
            >
              See the assessment
            </Button>
          </Grid>
          <Grid item xs={12} md={7}>
            <Grid container spacing={3}>
              {retentionPillars.map((pillar, index) => (
                <Grid item xs={12} md={4} key={pillar.title}>
                  <Card
                    elevation={0}
                    sx={{
                      p: 3,
                      borderRadius: 4,
                      border: '1px solid rgba(0, 0, 0, 0.08)',
                      bgcolor: 'background.paper',
                      height: '100%',
                      animation: 'fadeUp 0.7s ease both',
                      animationDelay: `${0.1 + index * 0.1}s`,
                    }}
                  >
                    <VerifiedUserIcon sx={{ color: 'primary.main', mb: 1 }} />
                    <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 1 }}>
                      {pillar.title}
                    </Typography>
                    <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                      {pillar.description}
                    </Typography>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Grid>
        </Grid>
      </Container>

      {/* Social Proof */}
      <Container maxWidth="lg" sx={{ mt: { xs: 10, md: 14 } }}>
        <Box sx={{ textAlign: 'center', mb: 5 }}>
          <Typography
            variant="h3"
            sx={{
              fontWeight: 700,
              mb: 2,
            }}
          >
            Loved by focused job seekers
          </Typography>
          <Typography sx={{ color: 'text.secondary' }}>
            People use CareerBridge to move faster and with more confidence.
          </Typography>
        </Box>
        <Grid container spacing={3} sx={{ mb: 5 }}>
          {heroStats.map((stat) => (
            <Grid item xs={12} md={4} key={stat.label}>
              <Paper
                elevation={0}
                sx={{
                  p: 3,
                  borderRadius: 3,
                  bgcolor: 'rgba(25, 118, 210, 0.08)',
                }}
              >
                <Typography variant="h4" sx={{ fontWeight: 700, color: 'primary.main' }}>
                  {stat.value}
                </Typography>
                <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                  {stat.label}
                </Typography>
              </Paper>
            </Grid>
          ))}
        </Grid>
        <Grid container spacing={3}>
          {testimonials.map((testimonial, index) => (
            <Grid item xs={12} md={4} key={testimonial.name}>
              <Card
                elevation={0}
                sx={{
                  p: 3,
                  borderRadius: 4,
                  border: '1px solid rgba(0, 0, 0, 0.08)',
                  bgcolor: 'background.paper',
                  height: '100%',
                  animation: 'fadeUp 0.7s ease both',
                  animationDelay: `${0.1 + index * 0.1}s`,
                }}
              >
                <Box sx={{ display: 'flex', mb: 2 }}>
                  {[...Array(testimonial.rating)].map((_, i) => (
                    <StarIcon key={i} sx={{ color: 'primary.main', fontSize: 20 }} />
                  ))}
                </Box>
                <Typography
                  variant="body2"
                  sx={{
                    mb: 3,
                    color: 'text.secondary',
                    lineHeight: 1.7,
                  }}
                >
                  "{testimonial.text}"
                </Typography>
                <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
                  {testimonial.name}
                </Typography>
                <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                  {testimonial.role} at {testimonial.company}
                </Typography>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Container>

      {/* FAQ */}
      <Container maxWidth="md" sx={{ mt: { xs: 10, md: 14 } }}>
        <Typography
          variant="h3"
          sx={{
            fontWeight: 700,
            textAlign: 'center',
            mb: 4,
          }}
        >
          Answers, before you ask
        </Typography>
        <Grid container spacing={3}>
          {faqs.map((faq, index) => (
            <Grid item xs={12} md={4} key={faq.question}>
              <Card
                elevation={0}
                sx={{
                  p: 3,
                  borderRadius: 3,
                  border: '1px solid rgba(0, 0, 0, 0.08)',
                  bgcolor: 'background.paper',
                  height: '100%',
                  animation: 'fadeUp 0.7s ease both',
                  animationDelay: `${0.1 + index * 0.1}s`,
                }}
              >
                <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 1 }}>
                  {faq.question}
                </Typography>
                <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                  {faq.answer}
                </Typography>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Container>

      {/* Final CTA */}
      <Container maxWidth="lg" sx={{ mt: { xs: 10, md: 14 } }}>
        <Box
          sx={{
            p: { xs: 5, md: 7 },
            borderRadius: 5,
            textAlign: 'center',
            background:
              'linear-gradient(130deg, rgba(13, 71, 161, 0.95) 0%, rgba(25, 118, 210, 0.9) 55%, rgba(66, 165, 245, 0.9) 120%)',
            color: 'white',
            boxShadow: '0 30px 60px rgba(25, 118, 210, 0.25)',
          }}
        >
          <Typography
            variant="h3"
            sx={{
              fontWeight: 700,
              mb: 2,
            }}
          >
            Ready to make your next move obvious?
          </Typography>
          <Typography sx={{ mb: 4, color: 'rgba(255,255,255,0.85)' }}>
            Start your free assessment, get your roadmap, and meet the mentors who can
            accelerate it.
          </Typography>
          <Button
            variant="contained"
            size="large"
            onClick={() => navigate('/register')}
            endIcon={<ArrowForwardIcon />}
            sx={{
              bgcolor: 'white',
              color: 'primary.main',
              fontWeight: 700,
              borderRadius: '999px',
              px: 4,
              '&:hover': { bgcolor: 'rgba(255,255,255,0.9)' },
            }}
          >
            Start free assessment
          </Button>
        </Box>
      </Container>
    </Box>
  );
};

export default LandingPage;
