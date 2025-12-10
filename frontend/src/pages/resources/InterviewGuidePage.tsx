import React from 'react';
import { Box, Typography, Button, Card, CardContent, Accordion, AccordionSummary, AccordionDetails } from '@mui/material';
import { ArrowBack, ExpandMore } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

const InterviewGuidePage: React.FC = () => {
  const navigate = useNavigate();

  const questions = [
    {
      question: 'Tell me about yourself',
      answer: 'Start with a brief overview of your professional background, highlight relevant experience, and connect it to the role you\'re applying for.',
    },
    {
      question: 'Why do you want this job?',
      answer: 'Show genuine interest by discussing how the role aligns with your career goals and how you can contribute to the company.',
    },
    {
      question: 'What are your strengths?',
      answer: 'Choose 2-3 strengths relevant to the role and provide specific examples of how you\'ve demonstrated them.',
    },
    {
      question: 'What are your weaknesses?',
      answer: 'Be honest but strategic. Choose a real weakness and explain how you\'re working to improve it.',
    },
  ];

  return (
    <Box sx={{ width: '100%', maxWidth: '1200px', mx: 'auto', px: { xs: 2, sm: 3, md: 6 }, py: { xs: 4, md: 6 } }}>
      <Button
        startIcon={<ArrowBack />}
        onClick={() => navigate('/resources')}
        sx={{ mb: 4, textTransform: 'none' }}
      >
        Back to Resources
      </Button>

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
          Interview Guide
        </Typography>
        <Typography
          variant="h5"
          sx={{
            fontSize: { xs: '1rem', md: '1.25rem' },
            color: 'rgba(255, 255, 255, 0.95)',
          }}
        >
          Master job interviews with proven strategies
        </Typography>
      </Box>

      <Card sx={{ p: 4 }}>
        <Typography variant="h5" sx={{ fontWeight: 600, mb: 3 }}>
          Common Interview Questions
        </Typography>
        {questions.map((item, index) => (
          <Accordion key={index} sx={{ mb: 2 }}>
            <AccordionSummary expandIcon={<ExpandMore />}>
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                {item.question}
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Typography variant="body1" sx={{ lineHeight: 1.8 }}>
                {item.answer}
              </Typography>
            </AccordionDetails>
          </Accordion>
        ))}
      </Card>
    </Box>
  );
};

export default InterviewGuidePage;

