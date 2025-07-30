import React from 'react';
import { Container, Typography, Box } from '@mui/material';

const AppointmentListPage: React.FC = () => {
  return (
    <Container>
      <Box sx={{ mt: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          My Appointments
        </Typography>
        <Typography variant="body1">
          Manage your scheduled sessions with mentors.
        </Typography>
      </Box>
    </Container>
  );
};

export default AppointmentListPage; 