import { UserRole } from '../types/index';

export const getLandingPathByRole = (role?: string | UserRole | null): string => {
  const normalizedRole = role?.toString().trim().toLowerCase() || '';
  const roleRouteMap: Record<string, string> = {
    'superadmin': '/superadmin',
    'admin':      '/admin',
    'staff':      '/staff',
    'mentor':     '/mentor',
    'student':    '/student',
  };
  console.log(`[AUTH-ROUTE] Input: "${role}" | Normalized: "${normalizedRole}"`);
  const targetPath = roleRouteMap[normalizedRole];
  if (targetPath) {
    return targetPath;
  }
  if (normalizedRole !== '') {
    console.error(`[AUTH-ERROR] No route defined for role: "${role}"`);
  }
  
  return '/login';
};