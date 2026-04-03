import { User } from '../types/index';

/**
 * Get the home dashboard path based on user role or user object
 * Priority: is_superuser > is_staff > role field
 * @param roleOrUser - User role string or User object
 * @returns Dashboard path for the role
 */
export const getHomePath = (roleOrUser?: string | User | null): string => {
  // If the input is a user object, check Django flags first
  if (roleOrUser && typeof roleOrUser === 'object' && 'id' in roleOrUser) {
    const user = roleOrUser as User;
    
    // Priority 1: Superuser → kernel control plane
    if (user.is_superuser) {
      return '/superadmin';
    }
    
    // Priority 2: Staff (but not superuser) → userland admin
    if (user.is_staff) {
      return '/admin';
    }
    
    // Priority 3: Use role field as fallback
    const role = user.role;
    const roleMap: Record<string, string> = {
      superadmin: '/superadmin',
      admin: '/admin',
      staff: '/staff',
      mentor: '/mentor',
      student: '/student',
    };
    return roleMap[role] || '/dashboard';
  }
  
  // Legacy string-based routing (for backward compatibility)
  const roleMap: Record<string, string> = {
    superadmin: '/superadmin',
    admin: '/admin',
    staff: '/staff',
    mentor: '/mentor',
    student: '/student',
  };

  const role = roleOrUser as string;
  return roleMap[role || ''] || '/dashboard';
};
