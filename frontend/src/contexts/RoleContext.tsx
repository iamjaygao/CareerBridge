/**
 * RoleContext - 4-World OS Hardened
 * 
 * SECURITY PATCH: PATCH-S0-CLEAN (Ghost World Purge)
 * 
 * REMOVED:
 * - All role override/impersonation logic
 * - localStorage role switching
 * - setOverrideRole / resetOverrideRole
 * - isImpersonating flag
 * 
 * RETAINED:
 * - isSuperAdmin check (reads from backend user.is_superuser)
 * - currentRole (reads from backend user.role)
 * 
 * PRINCIPLE:
 * The ONLY source of truth for user role/permissions is the backend
 * authenticated user profile. No frontend override is allowed.
 */

import React, { createContext, useContext, ReactNode } from 'react';
import { useSelector } from 'react-redux';
import { RootState } from '../store';

interface RoleContextType {
  currentRole: string | null;
  isSuperAdmin: boolean;
  isStaff: boolean;
}

const RoleContext = createContext<RoleContextType | undefined>(undefined);

export const RoleProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { user } = useSelector((state: RootState) => state.auth);

  // ════════════════════════════════════════════════════════════════════════
  // SECURITY: Role determined ONLY by backend authentication
  // ════════════════════════════════════════════════════════════════════════
  const currentRole = user?.role || null;
  const isSuperAdmin = Boolean(user?.is_superuser);
  const isStaff = Boolean(user?.is_staff);

  return (
    <RoleContext.Provider
      value={{
        currentRole,
        isSuperAdmin,
        isStaff,
      }}
    >
      {children}
    </RoleContext.Provider>
  );
};

export const useRole = (): RoleContextType => {
  const context = useContext(RoleContext);
  if (!context) {
    throw new Error('useRole must be used within a RoleProvider');
  }
  return context;
};
