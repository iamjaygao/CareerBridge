import { UserRole, User } from '../types/index';

/**
 * Get landing path based on user object (checking Django flags first)
 * Priority: is_superuser > is_staff > role field
 */
export const getLandingPathByRole = (
  roleOrUser?: string | UserRole | User | null
): string => {
  // If the input is a user object, check Django flags first
  if (roleOrUser && typeof roleOrUser === 'object' && 'id' in roleOrUser) {
    const user = roleOrUser as User;
    
    // Priority 1: Superuser → kernel control plane
    if (user.is_superuser) {
      console.log(`[AUTH-ROUTE] User is superuser → /superadmin`);
      return '/superadmin';
    }
    
    // Priority 2: Staff (but not superuser) → userland admin
    if (user.is_staff) {
      console.log(`[AUTH-ROUTE] User is staff → /admin`);
      return '/admin';
    }
    
    // Priority 3: Use role field as fallback
    const role = user.role;
    const normalizedRole = role?.toString().trim().toLowerCase() || '';
    console.log(`[AUTH-ROUTE] Using role field: "${role}" → "${normalizedRole}"`);
    
    const roleRouteMap: Record<string, string> = {
      'superadmin': '/superadmin',
      'admin':      '/admin',
      'staff':      '/staff',
      'mentor':     '/mentor',
      'student':    '/student',
    };
    
    const targetPath = roleRouteMap[normalizedRole];
    if (targetPath) {
      return targetPath;
    }
    
    console.error(`[AUTH-ERROR] No route defined for role: "${role}"`);
    return '/';
  }
  
  // Legacy string-based routing (for backward compatibility)
  const normalizedRole = roleOrUser?.toString().trim().toLowerCase() || '';
  const roleRouteMap: Record<string, string> = {
    'superadmin': '/superadmin',
    'admin':      '/admin',
    'staff':      '/staff',
    'mentor':     '/mentor',
    'student':    '/student',
  };
  console.log(`[AUTH-ROUTE] Input: "${roleOrUser}" | Normalized: "${normalizedRole}"`);
  const targetPath = roleRouteMap[normalizedRole];
  if (targetPath) {
    return targetPath;
  }
  if (normalizedRole !== '') {
    console.error(`[AUTH-ERROR] No route defined for role: "${roleOrUser}"`);
  }
  
  return '/login';
};