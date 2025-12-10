import React from 'react';
import { Box, Typography, Button, Card, CardContent, List, ListItem, ListItemIcon, ListItemText } from '@mui/material';
import { ArrowBack, CheckCircle } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

const ResumeTipsPage: React.FC = () => {
  const navigate = useNavigate();

  const tips = [
    'Use action verbs to describe your accomplishments (e.g., "Led", "Developed", "Improved")',
    'Quantify your achievements with specific numbers and metrics',
    'Tailor your resume to match the job description keywords',
    'Keep your resume to 1-2 pages for most roles',
    'Use a clean, professional format that is ATS-friendly',
    'Include relevant skills and certifications',
    'Proofread carefully for grammar and spelling errors',
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
          Resume Tips
        </Typography>
        <Typography
          variant="h5"
          sx={{
            fontSize: { xs: '1rem', md: '1.25rem' },
            color: 'rgba(255, 255, 255, 0.95)',
          }}
        >
          Expert advice to make your resume stand out
        </Typography>
      </Box>

      <Card sx={{ p: 4 }}>
        <Typography variant="h5" sx={{ fontWeight: 600, mb: 3 }}>
          Essential Resume Writing Tips
        </Typography>
        <List>
          {tips.map((tip, index) => (
            <ListItem key={index} sx={{ py: 1.5 }}>
              <ListItemIcon>
                <CheckCircle sx={{ color: 'success.main' }} />
              </ListItemIcon>
              <ListItemText
                primary={tip}
                primaryTypographyProps={{ variant: 'body1' }}
              />
            </ListItem>
          ))}
        </List>
      </Card>
    </Box>
  );
};

export default ResumeTipsPage;

