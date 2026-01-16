import React from 'react';
import { useSelector } from 'react-redux';
import { Outlet } from 'react-router-dom';

import { RootState } from '../../store';
import { canAccessStaff } from '../../utils/adminPermissions';

import LoadingSpinner from '../common/LoadingSpinner';
import ForbiddenPage from '../../pages/error/ForbiddenPage';

/**
 * Protected route component for staff pages
 * - Allows staff / admin / superadmin based on backend user flags
 * - Authorizes based on backend user role only
 * - Acts as a route guard (NOT a layout)
 */
const StaffRoute: React.FC = () => {
  const { user, isAuthenticated, authLoaded } = useSelector(
    (state: RootState) => state.auth
  );

  // Still loading auth state
  if (!authLoaded) {
    return <LoadingSpinner message="Checking authentication..." />;
  }

  // Not logged in
  if (!isAuthenticated) {
    return <ForbiddenPage />;
  }

  // No staff access
  if (!canAccessStaff(user)) {
    return <ForbiddenPage />;
  }

  // Authorized → render nested routes
  return <Outlet />;
};

export default StaffRoute;
