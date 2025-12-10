/**
 * Permission utilities for role-based access control
 */

export type UserRole = 'visitor' | 'student' | 'mentor' | 'admin' | 'staff';

/**
 * Get user role from auth state
 */
export const getUserRole = (isAuthenticated: boolean, userRole?: string): UserRole => {
  if (!isAuthenticated) {
    return 'visitor';
  }
  return (userRole as UserRole) || 'student';
};

/**
 * Check if user has permission to view full mentor list
 */
export const canViewFullMentorList = (role: UserRole): boolean => {
  return role !== 'visitor';
};

/**
 * Check if user can view mentor details
 */
export const canViewMentorDetails = (role: UserRole): boolean => {
  return role !== 'visitor';
};

/**
 * Check if user can view mentor pricing
 */
export const canViewMentorPricing = (role: UserRole): boolean => {
  return role !== 'visitor';
};

/**
 * Check if user can book appointments
 */
export const canBookAppointment = (role: UserRole): boolean => {
  return role !== 'visitor';
};

/**
 * Check if user can view full resume analysis
 */
export const canViewFullResumeAnalysis = (role: UserRole): boolean => {
  return role !== 'visitor';
};

/**
 * Check if user can upload resume (visitors can upload but won't see results)
 */
export const canUploadResume = (role: UserRole): boolean => {
  return true; // Everyone can upload
};

/**
 * Get number of featured mentors to show for visitors
 */
export const getFeaturedMentorsCount = (role: UserRole): number => {
  return role === 'visitor' ? 4 : Infinity;
};

