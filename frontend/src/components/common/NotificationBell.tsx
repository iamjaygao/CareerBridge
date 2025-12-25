import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { IconButton, Badge } from '@mui/material';
import { Notifications as NotificationsIcon } from '@mui/icons-material';
import { useUnreadNotificationCount } from '../../hooks/useUnreadNotificationCount';
import { RootState } from '../../store';
import { getLandingPathByRole } from '../../utils/roleLanding';

interface NotificationBellProps {
  /**
   * Custom sx styles for the IconButton
   */
  sx?: object;
  /**
   * Whether to show the bell only when authenticated
   * @default true
   */
  showOnlyWhenAuthenticated?: boolean;
}

/**
 * Reusable NotificationBell component
 * Displays unread notification count and navigates to /notifications on click
 */
const NotificationBell: React.FC<NotificationBellProps> = ({
  sx = {
    color: 'text.primary',
    '&:hover': { bgcolor: 'grey.100' },
  },
  showOnlyWhenAuthenticated = true,
}) => {
  const navigate = useNavigate();
  const { user } = useSelector((state: RootState) => state.auth);
  const { unreadCount } = useUnreadNotificationCount({
    autoRefresh: true,
    refreshInterval: 30000,
  });

  const handleClick = () => {
    const role = user?.role;
    const basePath = getLandingPathByRole(role);
    navigate(`${basePath}/notifications`);
  };

  return (
    <IconButton onClick={handleClick} sx={sx} aria-label="Notifications">
      <Badge badgeContent={unreadCount > 0 ? unreadCount : undefined} color="error">
        <NotificationsIcon />
      </Badge>
    </IconButton>
  );
};

export default NotificationBell;

