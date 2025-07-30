import React from 'react';
import { Container, Typography, Box } from '@mui/material';

const RegisterPage: React.FC = () => {
  return (
    <Container>
      <Box sx={{ mt: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Register Page
        </Typography>
        <Typography variant="body1">
          Registration functionality will be implemented here.
        </Typography>
      </Box>
    </Container>
  );
};

export default RegisterPage; 