import React from 'react';
import { Alert, AlertTitle, Box } from '@mui/material';

interface ErrorAlertProps {
  message: string;
  title?: string;
}

const ErrorAlert: React.FC<ErrorAlertProps> = ({ message, title = 'Error' }) => {
  return (
    <Box sx={{ my: 2 }}>
      <Alert severity="error">
        <AlertTitle>{title}</AlertTitle>
        {message}
      </Alert>
    </Box>
  );
};

export default ErrorAlert;