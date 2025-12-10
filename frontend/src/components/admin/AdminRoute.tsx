import React from 'react';
import { Navigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { RootState } from '../../store';
import { canAccessAdmin } from '../../utils/adminPermissions';
import { useRole } from '../../contexts/RoleContext';
import LoadingSpinner from '../common/LoadingSpinner';
import ForbiddenPage from '../../pages/error/ForbiddenPage';

interface AdminRouteProps {
  children: React.ReactNode;
}

/**
 * Protected route component for admin pages
 * Shows 403 Forbidden page if user is not an admin
 * Supports role impersonation for superadmin
 */
const AdminRoute: React.FC<AdminRouteProps> = ({ children }) => {
  const { user, isAuthenticated } = useSelector((state: RootState) => state.auth);
  const { activeRole } = useRole();

  // Show loading while checking auth
  if (!isAuthenticated) {
    return <LoadingSpinner message="Checking authentication..." />;
  }

  // Check if user has admin access (using activeRole for impersonation support)
  if (!canAccessAdmin(user, activeRole)) {
    return <ForbiddenPage />;
  }

  return <>{children}</>;
};

export default AdminRoute;

