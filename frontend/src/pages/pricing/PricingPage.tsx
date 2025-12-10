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
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  ArrowForward as ArrowForwardIcon,
  ExpandMore as ExpandMoreIcon,
  Star as StarIcon,
} from '@mui/icons-material';

const PricingPage: React.FC = () => {
  const navigate = useNavigate();
  const isAuthenticated = !!localStorage.getItem('access_token');

  const pricingTiers = [
    {
      name: 'Free',
      price: '$0',
      period: 'forever',
      description: 'Perfect for getting started with career insights',
      features: [
        'Resume analysis (basic)',
        'Limited job insights',
        'Access to 1 free mentor preview',
        'Basic skill gap analysis',
        'Community support',
      ],
      buttonText: 'Start Free',
      buttonVariant: 'outlined' as const,
      popular: false,
    },
    {
      name: 'Pro',
      price: 'Coming Soon',
      period: '',
      description: 'For professionals ready to accelerate their career',
      features: [
        'Full AI resume analysis',
        'Personalized job recommendations',
        'Access to Market Intelligence Engine',
        'Unlimited mentor previews',
        'Advanced skill gap analysis',
        'Priority support',
      ],
      buttonText: 'Coming Soon',
      buttonVariant: 'contained' as const,
      popular: true,
      disabled: true,
    },
    {
      name: 'Elite',
      price: 'Coming Soon',
      period: '',
      description: 'Complete career transformation with expert guidance',
      features: [
        'Everything in Pro',
        '1:1 mentor matching priority',
        'Career roadmap with AI + human review',
        'Job interview prep toolkit',
        'Personalized career coaching',
        'Dedicated support',
      ],
      buttonText: 'Coming Soon',
      buttonVariant: 'contained' as const,
      popular: false,
      disabled: true,
    },
  ];

  const faqs = [
    {
      question: 'What is included in the Free plan?',
      answer: 'The Free plan includes basic resume analysis, limited job insights, and access to one free mentor preview. It\'s perfect for getting started and exploring CareerBridge\'s core features.',
    },
    {
      question: 'When will Pro and Elite plans be available?',
      answer: 'We\'re currently finalizing the pricing structure for our Pro and Elite plans. Stay tuned for updates! You can sign up for our newsletter to be notified when these plans launch.',
    },
    {
      question: 'Can I cancel my subscription anytime?',
      answer: 'Yes, absolutely! All plans can be cancelled at any time with no penalties or fees. Your access will continue until the end of your current billing period.',
    },
    {
      question: 'Do you offer refunds?',
      answer: 'We offer a 30-day money-back guarantee for all paid plans. If you\'re not satisfied with your experience, contact our support team for a full refund.',
    },
    {
      question: 'What payment methods do you accept?',
      answer: 'We accept all major credit cards, debit cards, and PayPal. All payments are processed securely through our payment partners.',
    },
    {
      question: 'Can I upgrade or downgrade my plan later?',
      answer: 'Yes, you can change your plan at any time. Upgrades take effect immediately, while downgrades take effect at the end of your current billing period.',
    },
  ];

  return (
    <Box sx={{ width: '100%', maxWidth: '1200px', mx: 'auto', px: { xs: 2, sm: 3, md: 6 }, py: { xs: 4, md: 6 } }}>
      {/* Hero Section */}
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
            lineHeight: 1.2,
          }}
        >
          Simple, transparent pricing for your career success
        </Typography>
        <Typography
          variant="h5"
          component="p"
          sx={{
            fontSize: { xs: '1rem', md: '1.25rem' },
            color: 'rgba(255, 255, 255, 0.95)',
            maxWidth: '700px',
            mx: 'auto',
            lineHeight: 1.6,
          }}
        >
          Choose the plan that fits your goals. No hidden fees. Cancel anytime.
        </Typography>
      </Box>

      {/* Pricing Tiers Section */}
      <Box sx={{ mb: 10 }}>
        <Grid container spacing={4} justifyContent="center">
          {pricingTiers.map((tier, index) => (
            <Grid item xs={12} md={4} key={index}>
              <Card
                sx={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  position: 'relative',
                  border: tier.popular ? '2px solid' : '1px solid',
                  borderColor: tier.popular ? 'primary.main' : 'grey.200',
                  transition: 'all 0.3s',
                  '&:hover': {
                    transform: 'translateY(-8px)',
                    boxShadow: 8,
                  },
                }}
              >
                {tier.popular && (
                  <Chip
                    label="Most Popular"
                    color="primary"
                    icon={<StarIcon />}
                    sx={{
                      position: 'absolute',
                      top: 16,
                      right: 16,
                      fontWeight: 600,
                    }}
                  />
                )}
                <CardContent sx={{ flexGrow: 1, p: 4 }}>
                  <Typography
                    variant="h4"
                    component="h3"
                    sx={{
                      fontWeight: 700,
                      mb: 1,
                      color: 'text.primary',
                    }}
                  >
                    {tier.name}
                  </Typography>
                  <Box sx={{ mb: 2 }}>
                    <Typography
                      variant="h3"
                      component="span"
                      sx={{
                        fontWeight: 700,
                        color: 'primary.main',
                      }}
                    >
                      {tier.price}
                    </Typography>
                    {tier.period && (
                      <Typography
                        variant="body1"
                        component="span"
                        sx={{
                          color: 'text.secondary',
                          ml: 1,
                        }}
                      >
                        /{tier.period}
                      </Typography>
                    )}
                  </Box>
                  <Typography
                    variant="body2"
                    sx={{
                      color: 'text.secondary',
                      mb: 3,
                      minHeight: '40px',
                    }}
                  >
                    {tier.description}
                  </Typography>
                  <Box sx={{ mb: 3 }}>
                    {tier.features.map((feature, idx) => (
                      <Box
                        key={idx}
                        sx={{
                          display: 'flex',
                          alignItems: 'flex-start',
                          mb: 1.5,
                        }}
                      >
                        <CheckCircleIcon
                          sx={{
                            color: 'success.main',
                            fontSize: 20,
                            mr: 1.5,
                            mt: 0.25,
                            flexShrink: 0,
                          }}
                        />
                        <Typography
                          variant="body2"
                          sx={{
                            color: 'text.primary',
                            lineHeight: 1.5,
                          }}
                        >
                          {feature}
                        </Typography>
                      </Box>
                    ))}
                  </Box>
                </CardContent>
                <Box sx={{ p: 4, pt: 0 }}>
                  <Button
                    variant={tier.buttonVariant}
                    fullWidth
                    size="large"
                    onClick={() => {
                      if (!tier.disabled && tier.name === 'Free') {
                        navigate(isAuthenticated ? '/dashboard/assessment' : '/register');
                      }
                    }}
                    disabled={tier.disabled}
                    sx={{
                      textTransform: 'none',
                      fontWeight: 600,
                      py: 1.5,
                      ...(tier.buttonVariant === 'contained' && {
                        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                        '&:hover': {
                          background: 'linear-gradient(135deg, #5568d3 0%, #6a3d8f 100%)',
                        },
                        '&.Mui-disabled': {
                          background: 'grey.300',
                        },
                      }),
                    }}
                  >
                    {tier.buttonText}
                  </Button>
                </Box>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Box>

      {/* FAQ Section */}
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
          Frequently Asked Questions
        </Typography>
        <Box sx={{ maxWidth: '800px', mx: 'auto' }}>
          {faqs.map((faq, index) => (
            <Accordion
              key={index}
              sx={{
                mb: 2,
                '&:before': {
                  display: 'none',
                },
                boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                borderRadius: '8px !important',
                overflow: 'hidden',
              }}
            >
              <AccordionSummary
                expandIcon={<ExpandMoreIcon />}
                sx={{
                  px: 3,
                  py: 2,
                  '&:hover': {
                    bgcolor: 'grey.50',
                  },
                }}
              >
                <Typography
                  variant="h6"
                  sx={{
                    fontWeight: 600,
                    color: 'text.primary',
                  }}
                >
                  {faq.question}
                </Typography>
              </AccordionSummary>
              <AccordionDetails sx={{ px: 3, py: 2, pt: 0 }}>
                <Typography
                  variant="body1"
                  sx={{
                    color: 'text.secondary',
                    lineHeight: 1.7,
                  }}
                >
                  {faq.answer}
                </Typography>
              </AccordionDetails>
            </Accordion>
          ))}
        </Box>
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
          Start improving your career today.
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
          Join thousands of professionals who are using CareerBridge to advance their careers.
        </Typography>
        <Button
          variant="contained"
          size="large"
          onClick={() => navigate(isAuthenticated ? '/dashboard/assessment' : '/register')}
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
          Start Free Assessment
        </Button>
      </Box>
    </Box>
  );
};

export default PricingPage;

