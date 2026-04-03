import React from 'react';
import { useSelector } from 'react-redux';
import { Outlet } from 'react-router-dom';

import { RootState } from '../../store';
import { canAccessMentor } from '../../utils/adminPermissions';

import LoadingSpinner from '../common/LoadingSpinner';
import ForbiddenPage from '../../pages/error/ForbiddenPage';

/**
 * Protected route component for mentor pages
 * - Authorizes based on backend user role only
 * - Acts as a route guard (NOT a layout)
 */
const MentorRoute: React.FC = () => {
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

  // No mentor access
  if (!canAccessMentor(user)) {
    return <ForbiddenPage />;
  }

  // Authorized → render nested routes
  return <Outlet />;
};

export default MentorRoute;
