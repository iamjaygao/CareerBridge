import React from 'react';
import { Outlet } from 'react-router-dom';
import { useSelector } from 'react-redux';

import { RootState } from '../../store';
import { canAccessAdmin } from '../../utils/adminPermissions';
import { useRole } from '../../contexts/RoleContext';

import LoadingSpinner from '../common/LoadingSpinner';
import ForbiddenPage from '../../pages/error/ForbiddenPage';

/**
 * Protected route component for admin pages
 * Supports role impersonation via activeRole (superadmin)
 * Acts as a route guard (NOT a layout)
 */
const AdminRoute: React.FC = () => {
  const { user, isAuthenticated, authLoaded } = useSelector(
    (state: RootState) => state.auth
  );
  const { activeRole } = useRole();

  // Still loading auth state
  if (!authLoaded) {
    return <LoadingSpinner message="Checking authentication..." />;
  }

  // Not logged in
  if (!isAuthenticated) {
    return <ForbiddenPage />;
  }

  // No admin access
  if (!canAccessAdmin(user, activeRole)) {
    return <ForbiddenPage />;
  }

  // Authorized → render nested routes
  return <Outlet />;
};

export default AdminRoute;
