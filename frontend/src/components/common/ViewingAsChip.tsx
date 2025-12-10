import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Chip, IconButton, Tooltip } from '@mui/material';
import { Close as CloseIcon } from '@mui/icons-material';
import { useRole } from '../../contexts/RoleContext';

interface ViewingAsChipProps {
  /**
   * Custom sx styles for the Chip
   */
  sx?: object;
}

/**
 * Compact Chip component to display "Viewing as: <role>" next to avatar
 * Only shows when user is impersonating another role
 */
const ViewingAsChip: React.FC<ViewingAsChipProps> = ({ sx }) => {
  const navigate = useNavigate();
  const { isImpersonating, effectiveRole, resetOverrideRole } = useRole();

  // Only show when impersonating
  if (!isImpersonating || !effectiveRole) {
    return null;
  }

  const handleReset = () => {
    resetOverrideRole();
    navigate('/superadmin');
  };

  const roleLabels: Record<string, string> = {
    student: 'Student',
    mentor: 'Mentor',
    staff: 'Staff',
    admin: 'Admin',
    superadmin: 'Super Admin',
  };

  return (
    <Chip
      label={`Viewing as: ${roleLabels[effectiveRole] || effectiveRole}`}
      color="warning"
      size="small"
      variant="filled"
      onDelete={handleReset}
      deleteIcon={
        <Tooltip title="Reset to Superadmin">
          <IconButton
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              handleReset();
            }}
            sx={{
              color: 'inherit',
              '&:hover': {
                bgcolor: 'rgba(0, 0, 0, 0.1)',
              },
            }}
          >
            <CloseIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      }
      sx={{
        fontWeight: 600,
        fontSize: '0.75rem',
        height: '24px',
        '& .MuiChip-label': {
          px: 1.5,
          py: 0,
        },
        ...sx,
      }}
    />
  );
};

export default ViewingAsChip;

