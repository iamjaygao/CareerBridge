import React from 'react';
import { Container, Typography, Box } from '@mui/material';

const ResumeListPage: React.FC = () => {
  return (
    <Container>
      <Box sx={{ mt: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          My Resumes
        </Typography>
        <Typography variant="body1">
          Upload and manage your resumes for analysis.
        </Typography>
      </Box>
    </Container>
  );
};

export default ResumeListPage; 