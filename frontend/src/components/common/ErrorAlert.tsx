import React from 'react';
import { Alert, AlertTitle, Box } from '@mui/material';
import type { ApiError } from '../../services/utils/errorHandler';
import { getUserFacingMessageFromApiError } from '../../services/utils/errorHandler';

interface ErrorAlertProps {
  error: ApiError;
  title?: string;
  overrideMessage?: string;
}

const ErrorAlert: React.FC<ErrorAlertProps> = ({ error, title = 'Error', overrideMessage }) => {
  const message = overrideMessage || getUserFacingMessageFromApiError(error);
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
