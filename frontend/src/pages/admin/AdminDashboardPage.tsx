import React from 'react';
import { Container, Typography, Box } from '@mui/material';

const AdminDashboardPage: React.FC = () => {
  return (
    <Container>
      <Box sx={{ mt: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Admin Dashboard
        </Typography>
        <Typography variant="body1">
          System administration and management tools.
        </Typography>
      </Box>
    </Container>
  );
};

export default AdminDashboardPage; 