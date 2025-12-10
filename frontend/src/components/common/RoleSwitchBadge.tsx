import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Chip, IconButton, Tooltip } from '@mui/material';
import { Close as CloseIcon } from '@mui/icons-material';
import { useRole } from '../../contexts/RoleContext';

const RoleSwitchBadge: React.FC = () => {
  const navigate = useNavigate();
  const { isImpersonating, effectiveRole, resetOverrideRole } = useRole();

  // Only show banner when impersonating (override_role exists in localStorage)
  const overrideRole = localStorage.getItem('override_role');
  if (!overrideRole || !isImpersonating || !effectiveRole) {
    return null;
  }

  const handleReset = () => {
    resetOverrideRole();
    navigate('/superadmin'); // Navigate to superadmin dashboard
  };

  const roleLabels: Record<string, string> = {
    student: 'Student',
    mentor: 'Mentor',
    staff: 'Staff',
    admin: 'Admin',
  };

  return (
    <Box
      sx={{
        position: 'fixed',
        top: 16,
        right: 16,
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        gap: 1,
      }}
    >
      <Chip
        label={`Viewing as: ${roleLabels[effectiveRole] || effectiveRole}`}
        color="warning"
        sx={{
          fontWeight: 600,
          '& .MuiChip-label': {
            px: 2,
          },
        }}
      />
      <Tooltip title="Reset to Superadmin">
        <IconButton
          size="small"
          onClick={handleReset}
          sx={{
            bgcolor: 'warning.main',
            color: 'white',
            '&:hover': {
              bgcolor: 'warning.dark',
            },
          }}
        >
          <CloseIcon fontSize="small" />
        </IconButton>
      </Tooltip>
    </Box>
  );
};

export default RoleSwitchBadge;

