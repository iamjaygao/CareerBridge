import React from 'react';
import { useSelector } from 'react-redux';
import { RootState } from '../../store';
import { canAccessMentor } from '../../utils/adminPermissions';
import { useRole } from '../../contexts/RoleContext';
import LoadingSpinner from '../common/LoadingSpinner';
import ForbiddenPage from '../../pages/error/ForbiddenPage';

interface MentorRouteProps {
  children: React.ReactNode;
}

/**
 * Protected route component for mentor pages
 * Shows 403 Forbidden page if user is not a mentor
 * Supports role impersonation for superadmin
 * Uses activeRole (impersonate_role from localStorage || user.role)
 */
const MentorRoute: React.FC<MentorRouteProps> = ({ children }) => {
  const { user, isAuthenticated } = useSelector((state: RootState) => state.auth);
  const { activeRole } = useRole();

  // Show loading while checking auth
  if (!isAuthenticated) {
    return <LoadingSpinner message="Checking authentication..." />;
  }

  // Check if user has mentor access (using activeRole for impersonation support)
  if (!canAccessMentor(user, activeRole)) {
    return <ForbiddenPage />;
  }

  return <>{children}</>;
};

export default MentorRoute;

