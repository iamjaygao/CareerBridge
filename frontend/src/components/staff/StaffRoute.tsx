import React from 'react';
import { useSelector } from 'react-redux';
import { Outlet } from 'react-router-dom';

import { RootState } from '../../store';
import { canAccessStaff } from '../../utils/adminPermissions';
import { useRole } from '../../contexts/RoleContext';

import LoadingSpinner from '../common/LoadingSpinner';
import ForbiddenPage from '../../pages/error/ForbiddenPage';

/**
 * Protected route component for staff pages
 * - Allows staff / admin / superadmin
 * - Supports impersonation via activeRole
 * - Acts as a route guard (NOT a layout)
 */
const StaffRoute: React.FC = () => {
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

  // No staff access
  if (!canAccessStaff(user, activeRole)) {
    return <ForbiddenPage />;
  }

  // Authorized → render nested routes
  return <Outlet />;
};

export default StaffRoute;
