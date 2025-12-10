import { useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '../store';
import { getUnreadCount } from '../store/slices/notificationSlice';

/**
 * Hook to get and manage unread notification count
 * Automatically fetches count on mount and provides refresh function
 */
export const useUnreadNotificationCount = (options?: { 
  autoRefresh?: boolean; 
  refreshInterval?: number;
}) => {
  const dispatch = useDispatch();
  const unreadCount = useSelector((state: RootState) => state.notifications.unreadCount);
  const loading = useSelector((state: RootState) => state.notifications.loading);
  const { autoRefresh = true, refreshInterval = 30000 } = options || {};

  // Fetch unread count on mount
  useEffect(() => {
    dispatch(getUnreadCount() as any);
  }, [dispatch]);

  // Auto-refresh unread count at intervals
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      dispatch(getUnreadCount() as any);
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [dispatch, autoRefresh, refreshInterval]);

  // Manual refresh function
  const refresh = () => {
    dispatch(getUnreadCount() as any);
  };

  return {
    unreadCount: unreadCount || 0,
    loading,
    refresh,
  };
};

