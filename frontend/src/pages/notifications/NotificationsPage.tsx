import React, { useEffect, useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemButton,
  Chip,
  IconButton,
  Button,
  Divider,
  Menu,
  MenuItem,
  CircularProgress,
  Alert,
  Badge,
  Paper,
} from '@mui/material';
import {
  Notifications as NotificationsIcon,
  CheckCircle as ReadIcon,
  Circle as UnreadIcon,
  MoreVert as MoreIcon,
  Delete as DeleteIcon,
  MarkEmailRead as MarkAllReadIcon,
  FilterList as FilterIcon,
} from '@mui/icons-material';
import { useSelector, useDispatch } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { RootState } from '../../store';
import { fetchNotifications, markNotificationAsRead, getUnreadCount, deleteNotification } from '../../store/slices/notificationSlice';
import { useNotification } from '../../components/common/NotificationProvider';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import { formatDistanceToNow } from 'date-fns';

const NotificationsPage: React.FC = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { showNotification } = useNotification();
  const { notifications, loading, error, totalCount, unreadCount } = useSelector(
    (state: RootState) => state.notifications
  );
  const [filter, setFilter] = useState<'all' | 'unread' | 'read'>('all');
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedNotification, setSelectedNotification] = useState<number | null>(null);

  useEffect(() => {
    dispatch(fetchNotifications() as any);
    dispatch(getUnreadCount() as any);
  }, [dispatch]);

  const handleFilterChange = (newFilter: 'all' | 'unread' | 'read') => {
    setFilter(newFilter);
  };

  const handleMarkAsRead = async (notificationId: number) => {
    try {
      await dispatch(markNotificationAsRead([notificationId]) as any).unwrap();
      dispatch(getUnreadCount() as any); // Refresh unread count
      showNotification('Notification marked as read', 'success');
    } catch (error: any) {
      showNotification(error || 'Failed to mark notification as read', 'error');
    }
    setAnchorEl(null);
    setSelectedNotification(null);
  };

  const handleMarkAllAsRead = async () => {
    try {
      const unreadIds = (notifications || [])
        .filter((n) => n && !n.is_read && n.id)
        .map((n) => n.id);
      if (unreadIds.length === 0) {
        showNotification('No unread notifications', 'info');
        return;
      }
      await dispatch(markNotificationAsRead(unreadIds) as any).unwrap();
      dispatch(getUnreadCount() as any); // Refresh unread count
      showNotification('All notifications marked as read', 'success');
    } catch (error: any) {
      showNotification(error || 'Failed to mark all as read', 'error');
    }
    setAnchorEl(null);
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, notificationId: number) => {
    setAnchorEl(event.currentTarget);
    setSelectedNotification(notificationId);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedNotification(null);
  };

  const handleDelete = async (notificationId: number) => {
    try {
      await dispatch(deleteNotification(notificationId) as any).unwrap();
      dispatch(getUnreadCount() as any); // Refresh unread count
      showNotification('Notification deleted', 'success');
    } catch (error: any) {
      showNotification(error || 'Failed to delete notification', 'error');
    }
    setAnchorEl(null);
    setSelectedNotification(null);
  };

  const getNotificationIcon = (type?: string) => {
    if (!type) return '🔔';
    switch (type) {
      case 'appointment_reminder':
      case 'appointment_confirmed':
      case 'appointment_cancelled':
        return '📅';
      case 'mentor_response':
        return '👤';
      case 'payment_success':
      case 'payment_failed':
        return '💳';
      case 'system_announcement':
        return '📢';
      case 'resume_analysis_complete':
        return '📄';
      case 'job_match_found':
        return '💼';
      case 'referral_reward':
        return '🎁';
      case 'subscription_expiry':
        return '⏰';
      case 'welcome':
        return '👋';
      default:
        return '🔔';
    }
  };

  const getPriorityColor = (priority?: string) => {
    if (!priority) return 'default';
    switch (priority) {
      case 'critical':
      case 'urgent':
        return 'error';
      case 'high':
        return 'warning';
      case 'normal':
      case 'medium':
        return 'info';
      case 'low':
        return 'default';
      default:
        return 'default';
    }
  };

  const formatRoleName = (role?: string) => {
    if (!role) return '';
    const roleMap: Record<string, string> = {
      'superadmin': 'Super Admin',
      'admin': 'Admin',
      'staff': 'Staff',
      'mentor': 'Mentor',
      'student': 'Student',
    };
    return roleMap[role] || role.charAt(0).toUpperCase() + role.slice(1);
  };

  const filteredNotifications = (notifications || []).filter((notification) => {
    if (!notification) return false;
    if (filter === 'unread') return !notification.is_read;
    if (filter === 'read') return notification.is_read;
    return true;
  });

  if (loading && notifications.length === 0) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
        <LoadingSpinner />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Badge badgeContent={unreadCount || 0} color="error">
            <NotificationsIcon sx={{ fontSize: 32 }} />
          </Badge>
          <Box>
            <Typography variant="h4" component="h1" sx={{ fontWeight: 600 }}>
              Notifications
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {totalCount || 0} total • {unreadCount || 0} unread
            </Typography>
          </Box>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<MarkAllReadIcon />}
            onClick={handleMarkAllAsRead}
            disabled={!unreadCount || unreadCount === 0}
          >
            Mark All Read
          </Button>
        </Box>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => dispatch({ type: 'notifications/clearError' })}>
          {error}
        </Alert>
      )}

      {/* Filter Tabs */}
      <Paper sx={{ mb: 2, p: 1, display: 'flex', gap: 1 }}>
        <Chip
          label="All"
          onClick={() => handleFilterChange('all')}
          color={filter === 'all' ? 'primary' : 'default'}
          variant={filter === 'all' ? 'filled' : 'outlined'}
        />
        <Chip
          label={`Unread (${(notifications || []).filter((n) => n && !n.is_read).length})`}
          onClick={() => handleFilterChange('unread')}
          color={filter === 'unread' ? 'primary' : 'default'}
          variant={filter === 'unread' ? 'filled' : 'outlined'}
        />
        <Chip
          label={`Read (${(notifications || []).filter((n) => n && n.is_read).length})`}
          onClick={() => handleFilterChange('read')}
          color={filter === 'read' ? 'primary' : 'default'}
          variant={filter === 'read' ? 'filled' : 'outlined'}
        />
      </Paper>

      {/* Notifications List */}
      {filteredNotifications.length === 0 ? (
        <Card>
          <CardContent>
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <NotificationsIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" color="text.secondary">
                {filter === 'unread' ? 'No unread notifications' : filter === 'read' ? 'No read notifications' : 'No notifications'}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                {filter === 'unread' 
                  ? 'You\'re all caught up!' 
                  : 'Notifications will appear here when you receive them.'}
              </Typography>
            </Box>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <List sx={{ p: 0 }}>
            {filteredNotifications.map((notification, index) => (
              <React.Fragment key={notification.id}>
                <ListItem
                  sx={{
                    bgcolor: notification.is_read ? 'transparent' : 'action.hover',
                    '&:hover': { bgcolor: 'action.selected' },
                    transition: 'background-color 0.2s',
                  }}
                  secondaryAction={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {notification.priority && (
                        <Chip
                          label={notification.priority}
                          size="small"
                          color={getPriorityColor(notification.priority) as any}
                          sx={{ textTransform: 'capitalize' }}
                        />
                      )}
                      <IconButton
                        edge="end"
                        onClick={(e) => handleMenuOpen(e, notification.id)}
                        size="small"
                      >
                        <MoreIcon />
                      </IconButton>
                    </Box>
                  }
                >
                  <ListItemButton
                    onClick={() => {
                      if (notification.payload?.action === 'review_appointment' && notification.payload?.appointment_id) {
                        navigate(`/appointments/${notification.payload.appointment_id}?review=true`);
                      }
                      if (!notification.is_read) {
                        handleMarkAsRead(notification.id);
                      }
                    }}
                    sx={{ py: 2 }}
                  >
                    <Box sx={{ mr: 2, fontSize: 24 }}>
                      {getNotificationIcon(notification.notification_type)}
                    </Box>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                          <Typography
                            variant="subtitle1"
                            sx={{
                              fontWeight: notification.is_read ? 400 : 600,
                              color: notification.is_read ? 'text.secondary' : 'text.primary',
                            }}
                          >
                            {notification.title || 'Notification'}
                          </Typography>
                          {!notification.is_read && (
                            <UnreadIcon sx={{ fontSize: 12, color: 'primary.main' }} />
                          )}
                          {notification.is_read && (
                            <ReadIcon sx={{ fontSize: 12, color: 'success.main' }} />
                          )}
                        </Box>
                      }
                      secondary={
                        <Box>
                          {notification.message && (
                            <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                              {notification.message}
                            </Typography>
                          )}
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5, flexWrap: 'wrap' }}>
                            <Typography variant="caption" color="text.secondary">
                              {notification.created_at 
                                ? formatDistanceToNow(new Date(notification.created_at), { addSuffix: true })
                                : 'Recently'}
                            </Typography>
                            {notification.notification_type_display && (
                              <>
                                <Typography variant="caption" color="text.secondary">
                                  •
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                  {notification.notification_type_display}
                                </Typography>
                              </>
                            )}
                            {notification.target_role_display && (
                              <>
                                <Typography variant="caption" color="text.secondary">
                                  •
                                </Typography>
                                <Chip
                                  label={formatRoleName(notification.target_role)}
                                  size="small"
                                  variant="outlined"
                                  sx={{ height: 18, fontSize: '0.65rem' }}
                                />
                              </>
                            )}
                          </Box>
                        </Box>
                      }
                    />
                  </ListItemButton>
                </ListItem>
                {index < filteredNotifications.length - 1 && <Divider />}
              </React.Fragment>
            ))}
          </List>
        </Card>
      )}

      {/* Context Menu */}
      <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={handleMenuClose}>
        {selectedNotification && 
          notifications.find((n) => n.id === selectedNotification)?.is_read === false && (
            <MenuItem onClick={() => handleMarkAsRead(selectedNotification)}>
              <ReadIcon sx={{ mr: 1, fontSize: 20 }} />
              Mark as Read
            </MenuItem>
          )}
        <MenuItem onClick={() => selectedNotification && handleDelete(selectedNotification)}>
          <DeleteIcon sx={{ mr: 1, fontSize: 20 }} />
          Delete
        </MenuItem>
      </Menu>
    </Box>
  );
};

export default NotificationsPage;

