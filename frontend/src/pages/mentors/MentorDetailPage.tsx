import React from 'react';
import { Container, Typography, Box } from '@mui/material';

const MentorDetailPage: React.FC = () => {
  return (
    <Container>
      <Box sx={{ mt: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Mentor Profile
        </Typography>
        <Typography variant="body1">
          View mentor details and book sessions.
        </Typography>
      </Box>
    </Container>
  );
};

export default MentorDetailPage; 