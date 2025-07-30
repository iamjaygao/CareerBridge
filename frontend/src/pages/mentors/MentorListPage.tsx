import React from 'react';
import { Container, Typography, Box } from '@mui/material';

const MentorListPage: React.FC = () => {
  return (
    <Container>
      <Box sx={{ mt: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Find Mentors
        </Typography>
        <Typography variant="body1">
          Browse and connect with career mentors.
        </Typography>
      </Box>
    </Container>
  );
};

export default MentorListPage; 