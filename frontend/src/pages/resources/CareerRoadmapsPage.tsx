import React from 'react';
import { Box, Typography, Button, Grid, Card, CardContent } from '@mui/material';
import { ArrowBack, Code, DataObject, Business } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

const CareerRoadmapsPage: React.FC = () => {
  const navigate = useNavigate();

  const roadmaps = [
    {
      title: 'Software Engineering',
      icon: <Code sx={{ fontSize: 48, color: 'primary.main' }} />,
      description: 'From junior developer to senior engineer: skills, technologies, and milestones.',
    },
    {
      title: 'Data Science',
      icon: <DataObject sx={{ fontSize: 48, color: 'primary.main' }} />,
      description: 'Master data analysis, machine learning, and AI to advance in data science.',
    },
    {
      title: 'Product Management',
      icon: <Business sx={{ fontSize: 48, color: 'primary.main' }} />,
      description: 'Build product strategy, user research, and leadership skills.',
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
          Career Roadmaps
        </Typography>
        <Typography
          variant="h5"
          sx={{
            fontSize: { xs: '1rem', md: '1.25rem' },
            color: 'rgba(255, 255, 255, 0.95)',
          }}
        >
          Step-by-step guides to advance in your field
        </Typography>
      </Box>

      <Grid container spacing={4}>
        {roadmaps.map((roadmap, index) => (
          <Grid item xs={12} md={4} key={index}>
            <Card sx={{ height: '100%', p: 4, textAlign: 'center' }}>
              <Box sx={{ mb: 2 }}>{roadmap.icon}</Box>
              <Typography variant="h5" sx={{ fontWeight: 600, mb: 2 }}>
                {roadmap.title}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {roadmap.description}
              </Typography>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export default CareerRoadmapsPage;

