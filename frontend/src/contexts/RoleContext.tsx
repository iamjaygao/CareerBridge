import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useSelector } from 'react-redux';
import { RootState } from '../store';

const OVERRIDE_ROLE_KEY = 'override_role'; // Key for role switching (superadmin only)

interface RoleContextType {
  currentRole: string | null;
  activeRole: string | null; // effectiveRole = override_role || user.role
  effectiveRole: string | null; // Alias for activeRole
  isImpersonating: boolean;
  setOverrideRole: (role: string | null) => void;
  resetOverrideRole: () => void;
  isSuperAdmin: boolean;
  // Backward compatibility
  setImpersonatedRole: (role: string | null) => void;
  resetImpersonation: () => void;
}

const RoleContext = createContext<RoleContextType | undefined>(undefined);

export const RoleProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useSelector((state: RootState) => state.auth);
  const [overrideRole, setOverrideRoleState] = useState<string | null>(null);

  // Load override role from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(OVERRIDE_ROLE_KEY);
    if (stored) {
      setOverrideRoleState(stored);
    }
  }, []);

  // Determine effective role: override_role OR real user role
  // effectiveRole = override_role ?? user.role
  const effectiveRole = overrideRole || user?.role || null;
  const isImpersonating = !!overrideRole;
  const isSuperAdmin = user?.role === 'superadmin';

  // Expose effectiveRole as activeRole and currentRole for backward compatibility
  const activeRole = effectiveRole;
  const currentRole = effectiveRole;

  const setOverrideRole = (role: string | null) => {
    if (role) {
      localStorage.setItem(OVERRIDE_ROLE_KEY, role);
      setOverrideRoleState(role);
    } else {
      localStorage.removeItem(OVERRIDE_ROLE_KEY);
      setOverrideRoleState(null);
    }
  };

  const resetOverrideRole = () => {
    localStorage.removeItem(OVERRIDE_ROLE_KEY);
    setOverrideRoleState(null);
  };

  // Backward compatibility aliases
  const setImpersonatedRole = setOverrideRole;
  const resetImpersonation = resetOverrideRole;

  return (
    <RoleContext.Provider
      value={{
        currentRole,
        activeRole,
        effectiveRole,
        isImpersonating,
        setOverrideRole,
        resetOverrideRole,
        isSuperAdmin,
        // Backward compatibility
        setImpersonatedRole,
        resetImpersonation,
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

