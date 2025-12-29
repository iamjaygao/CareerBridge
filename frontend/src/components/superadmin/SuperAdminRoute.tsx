import React from 'react';
import { Outlet } from 'react-router-dom';
import { useSelector } from 'react-redux';

import { RootState } from '../../store';
import { isSuperAdmin } from '../../utils/adminPermissions';

import LoadingSpinner from '../common/LoadingSpinner';
import ForbiddenPage from '../../pages/error/ForbiddenPage';

/**
 * Protected route component for superadmin pages.
 * Only allows real superadmin role (no impersonation).
 */
const SuperAdminRoute: React.FC = () => {
  const { user, isAuthenticated, authLoaded } = useSelector(
    (state: RootState) => state.auth
  );

  if (!authLoaded) {
    return <LoadingSpinner message="Checking authentication..." />;
  }

  if (!isAuthenticated) {
    return <ForbiddenPage />;
  }

  if (!isSuperAdmin(user)) {
    return <ForbiddenPage />;
  }

  return <Outlet />;
};

export default SuperAdminRoute;
