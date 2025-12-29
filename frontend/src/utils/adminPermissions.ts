/**
 * Admin permission utilities for role-based access control
 */

export type UserRole = 'admin' | 'staff' | 'mentor' | 'student' | 'superadmin';

/**
 * Generic user interface for permission checking
 */
interface UserForPermissions {
  role?: string | UserRole;
}

/**
 * Get active role for permission checking
 * This supports role impersonation for superadmin
 * Uses localStorage.getItem("impersonate_role") || user.role
 */
export const getActiveRole = (user: UserForPermissions | null | undefined, impersonatedRole?: string | null): string | null => {
  // If impersonating, use impersonated role
  if (impersonatedRole) {
    return impersonatedRole;
  }
  // Check localStorage directly as fallback
  const storedRole = localStorage.getItem('impersonate_role');
  if (storedRole) {
    return storedRole;
  }
  // Otherwise use actual user role
  if (!user || !user.role) return null;
  return typeof user.role === 'string' ? user.role.toLowerCase() : user.role;
};

/**
 * Get current role for permission checking (alias for getActiveRole for backward compatibility)
 */
export const getCurrentRole = getActiveRole;

/**
 * Check if user is a superadmin (real role, not impersonated)
 */
export const isSuperAdmin = (user: UserForPermissions | null | undefined): boolean => {
  if (!user || !user.role) return false;
  const role = typeof user.role === 'string' ? user.role.toLowerCase() : user.role;
  return role === 'superadmin';
};

/**
 * Check if user is an admin
 * Supports role impersonation for superadmin
 */
export const isAdmin = (user: UserForPermissions | null | undefined, impersonatedRole?: string | null): boolean => {
  if (!user || !user.role) return false;
  const role = typeof user.role === 'string' ? user.role.toLowerCase() : user.role;
  return role === 'admin';
};

/**
 * Check if user is staff
 * Supports role impersonation for superadmin
 */
export const isStaff = (user: UserForPermissions | null | undefined, impersonatedRole?: string | null): boolean => {
  // Superadmin can impersonate any role
  if (isSuperAdmin(user)) {
    const currentRole = getCurrentRole(user, impersonatedRole);
    return currentRole === 'staff';
  }
  if (!user || !user.role) return false;
  const role = typeof user.role === 'string' ? user.role.toLowerCase() : user.role;
  return role === 'staff';
};

/**
 * Check if user has admin access (admin or superadmin)
 * This is the main helper for determining if a user can see/administer admin content
 * Superadmin always has admin access
 */
export const hasAdminAccess = (user: UserForPermissions | null | undefined, impersonatedRole?: string | null): boolean => {
  if (!user || !user.role) return false;
  const role = typeof user.role === 'string' ? user.role.toLowerCase() : user.role;
  
  // Admin has admin access
  if (role === 'admin') {
    return true;
  }
  
  return false;
};

/**
 * Check if user has staff access (staff or admin)
 * Supports role impersonation for superadmin
 * Superadmin can access staff routes even without impersonation
 */
export const hasStaffAccess = (user: UserForPermissions | null | undefined, impersonatedRole?: string | null): boolean => {
  // Superadmin can access everything, or impersonate staff/admin
  if (isSuperAdmin(user)) {
    // If impersonating, check if impersonated role is staff or admin
    if (impersonatedRole) {
      return impersonatedRole === 'staff' || impersonatedRole === 'admin';
    }
    // If not impersonating, superadmin can access staff routes
    return true;
  }
  if (!user || !user.role) return false;
  const role = typeof user.role === 'string' ? user.role.toLowerCase() : user.role;
  return role === 'staff' || role === 'admin';
};

/**
 * Get user role
 */
export const getUserRole = (user: UserForPermissions | null | undefined): UserRole | null => {
  if (!user || !user.role) return null;
  const role = typeof user.role === 'string' ? user.role.toLowerCase() : user.role;
  return role as UserRole;
};

/**
 * Check if user can access admin routes (admin only)
 * Supports role impersonation for superadmin
 */
export const canAccessAdmin = (user: UserForPermissions | null | undefined, impersonatedRole?: string | null): boolean => {
  return hasAdminAccess(user, impersonatedRole);
};

/**
 * Check if user can access staff routes (staff or admin)
 * Supports role impersonation for superadmin
 */
export const canAccessStaff = (user: UserForPermissions | null | undefined, impersonatedRole?: string | null): boolean => {
  return hasStaffAccess(user, impersonatedRole);
};

/**
 * Check if user is a student
 * Supports role impersonation for superadmin
 * Superadmin can access student routes even without impersonation
 */
export const isStudent = (user: UserForPermissions | null | undefined, impersonatedRole?: string | null): boolean => {
  // Superadmin can access everything, or impersonate student
  if (isSuperAdmin(user)) {
    // If impersonating, check if impersonated role is student
    if (impersonatedRole) {
      return impersonatedRole === 'student';
    }
    // If not impersonating, superadmin can access student routes
    return true;
  }
  if (!user || !user.role) return false;
  const role = typeof user.role === 'string' ? user.role.toLowerCase() : user.role;
  return role === 'student';
};

/**
 * Check if user can access student routes
 * Supports role impersonation for superadmin
 */
export const canAccessStudent = (user: UserForPermissions | null | undefined, impersonatedRole?: string | null): boolean => {
  return isStudent(user, impersonatedRole);
};

/**
 * Check if user is a mentor
 * Supports role impersonation for superadmin
 * Superadmin can access mentor routes even without impersonation
 */
export const isMentor = (user: UserForPermissions | null | undefined, impersonatedRole?: string | null): boolean => {
  // Superadmin can access everything, or impersonate mentor
  if (isSuperAdmin(user)) {
    // If impersonating, check if impersonated role is mentor
    if (impersonatedRole) {
      return impersonatedRole === 'mentor';
    }
    // If not impersonating, superadmin can access mentor routes
    return true;
  }
  if (!user || !user.role) return false;
  const role = typeof user.role === 'string' ? user.role.toLowerCase() : user.role;
  return role === 'mentor';
};

/**
 * Check if user can access mentor routes
 * Supports role impersonation for superadmin
 */
export const canAccessMentor = (user: UserForPermissions | null | undefined, impersonatedRole?: string | null): boolean => {
  return isMentor(user, impersonatedRole);
};

/**
 * Check if user has financial access (admin or superadmin)
 * This determines if a user can view financial data like revenue, earnings, payouts
 * Superadmin ALWAYS has financial access, even when impersonating
 * Admin has financial access
 */
export const hasFinancialAccess = (user: UserForPermissions | null | undefined, impersonatedRole?: string | null): boolean => {
  if (!user || !user.role) return false;
  const role = typeof user.role === 'string' ? user.role.toLowerCase() : user.role;
  
  // Superadmin ALWAYS has financial access (even when impersonating)
  // This ensures financial widgets always show for real superadmin
  if (role === 'superadmin') {
    return true;
  }
  
  // Admin has financial access
  if (role === 'admin') {
    return true;
  }
  
  // If impersonating as admin or superadmin, grant access
  if (impersonatedRole) {
    const impersonated = typeof impersonatedRole === 'string' ? impersonatedRole.toLowerCase() : impersonatedRole;
    return impersonated === 'admin' || impersonated === 'superadmin';
  }
  
  return false;
};
