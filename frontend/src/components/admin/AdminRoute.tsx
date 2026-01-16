import React from 'react';
import { Outlet, Navigate, useLocation } from 'react-router-dom';
import { useSelector } from 'react-redux';

import { RootState } from '../../store';
import { canAccessAdmin } from '../../utils/adminPermissions';

import LoadingSpinner from '../common/LoadingSpinner';
import ForbiddenPage from '../../pages/error/ForbiddenPage';

/**
 * Protected route component for admin pages
 * - Authorizes based on backend user role only
 * - Acts as a route guard (NOT a layout)
 */
const AdminRoute: React.FC = () => {
  const { user, isAuthenticated, authLoaded } = useSelector(
    (state: RootState) => state.auth
  );
  const location = useLocation();

  // Still loading auth state
  if (!authLoaded) {
    return <LoadingSpinner message="Checking authentication..." />;
  }

  // Not logged in
  if (!isAuthenticated) {
    return <ForbiddenPage />;
  }

  if (user?.role === 'superadmin') {
    if (location.pathname.startsWith('/analytics')) {
      return (
        <Navigate
          to={`/superadmin/analytics${location.search}`}
          replace
        />
      );
    }
    return <ForbiddenPage />;
  }

  // No admin access
  if (!canAccessAdmin(user)) {
    return <ForbiddenPage />;
  }

  // Authorized → render nested routes
  return <Outlet />;
};

export default AdminRoute;
