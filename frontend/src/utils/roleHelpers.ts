/**
 * Role helper utilities for permission checking
 * These helpers check the actual role string, not user objects
 */

export type UserRole = 'admin' | 'staff' | 'mentor' | 'student' | 'superadmin';

/**
 * Check if role has admin access (admin or superadmin)
 */
export const hasAdminAccess = (role: string | null | undefined): boolean => {
  if (!role) return false;
  const normalizedRole = typeof role === 'string' ? role.toLowerCase() : role;
  return normalizedRole === 'admin' || normalizedRole === 'superadmin';
};

/**
 * Check if role has financial access (admin or superadmin)
 * This determines if a user can view financial data like revenue, earnings, payouts
 */
export const hasFinancialAccess = (role: string | null | undefined): boolean => {
  if (!role) return false;
  const normalizedRole = typeof role === 'string' ? role.toLowerCase() : role;
  return normalizedRole === 'admin' || normalizedRole === 'superadmin';
};

/**
 * Check if role is superadmin
 */
export const isSuperAdmin = (role: string | null | undefined): boolean => {
  if (!role) return false;
  const normalizedRole = typeof role === 'string' ? role.toLowerCase() : role;
  return normalizedRole === 'superadmin';
};

/**
 * Check if role is admin
 */
export const isAdmin = (role: string | null | undefined): boolean => {
  if (!role) return false;
  const normalizedRole = typeof role === 'string' ? role.toLowerCase() : role;
  return normalizedRole === 'admin';
};

