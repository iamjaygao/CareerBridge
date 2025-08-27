import React from 'react';
import { Box, Typography, Button, SxProps, Theme } from '@mui/material';

interface EmptyStateProps {
  title: string;
  description?: string;
  icon?: React.ReactNode;
  action?: {
    label: string;
    onClick: () => void;
  };
  sx?: SxProps<Theme>;
}

const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  icon,
  action,
  sx = {},
}) => {
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        textAlign: 'center',
        py: 8,
        px: 2,
        ...sx,
      }}
    >
      {icon && (
        <Box
          sx={{
            mb: 2,
            color: 'text.secondary',
            '& > svg': {
              fontSize: 64,
            },
          }}
        >
          {icon}
        </Box>
      )}

      <Typography variant="h6" gutterBottom>
        {title}
      </Typography>

      {description && (
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{ mb: action ? 4 : 0, maxWidth: 'sm' }}
        >
          {description}
        </Typography>
      )}

      {action && (
        <Button
          variant="contained"
          onClick={action.onClick}
        >
          {action.label}
        </Button>
      )}
    </Box>
  );
};

export default EmptyState;