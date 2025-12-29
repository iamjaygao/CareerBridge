/**
 * Get the home dashboard path based on user role
 * @param role - User role (superadmin, admin, staff, mentor, student)
 * @returns Dashboard path for the role
 */
export const getHomePath = (role?: string | null): string => {
  const roleMap: Record<string, string> = {
    superadmin: '/superadmin',
    admin: '/admin',
    staff: '/staff',
    mentor: '/mentor',
    student: '/student',
  };

  return roleMap[role || ''] || '/dashboard';
};
