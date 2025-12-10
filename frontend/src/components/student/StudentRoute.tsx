import React from 'react';
import { useSelector } from 'react-redux';
import { RootState } from '../../store';
import { canAccessStudent } from '../../utils/adminPermissions';
import { useRole } from '../../contexts/RoleContext';
import LoadingSpinner from '../common/LoadingSpinner';
import ForbiddenPage from '../../pages/error/ForbiddenPage';

interface StudentRouteProps {
  children: React.ReactNode;
}

/**
 * Protected route component for student pages
 * Shows 403 Forbidden page if user is not a student
 * Supports role impersonation for superadmin
 * Uses activeRole (impersonate_role from localStorage || user.role)
 */
const StudentRoute: React.FC<StudentRouteProps> = ({ children }) => {
  const { user, isAuthenticated } = useSelector((state: RootState) => state.auth);
  const { activeRole } = useRole();

  // Show loading while checking auth
  if (!isAuthenticated) {
    return <LoadingSpinner message="Checking authentication..." />;
  }

  // Check if user has student access (using activeRole for impersonation support)
  if (!canAccessStudent(user, activeRole)) {
    return <ForbiddenPage />;
  }

  return <>{children}</>;
};

export default StudentRoute;

