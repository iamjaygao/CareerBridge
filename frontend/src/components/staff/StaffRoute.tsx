import React from 'react';
import { useSelector } from 'react-redux';
import { RootState } from '../../store';
import { canAccessStaff } from '../../utils/adminPermissions';
import { useRole } from '../../contexts/RoleContext';
import LoadingSpinner from '../common/LoadingSpinner';
import ForbiddenPage from '../../pages/error/ForbiddenPage';

interface StaffRouteProps {
  children: React.ReactNode;
}

/**
 * Protected route component for staff pages
 * Shows 403 Forbidden page if user is not staff or admin
 * Supports role impersonation for superadmin
 * Uses activeRole (impersonate_role from localStorage || user.role)
 */
const StaffRoute: React.FC<StaffRouteProps> = ({ children }) => {
  const { user, isAuthenticated } = useSelector((state: RootState) => state.auth);
  const { activeRole } = useRole();

  // Show loading while checking auth
  if (!isAuthenticated) {
    return <LoadingSpinner message="Checking authentication..." />;
  }

  // Check if user has staff access (using activeRole for impersonation support)
  if (!canAccessStaff(user, activeRole)) {
    return <ForbiddenPage />;
  }

  return <>{children}</>;
};

export default StaffRoute;

