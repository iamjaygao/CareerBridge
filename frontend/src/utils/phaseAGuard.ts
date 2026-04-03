/**
 * Phase-A Feature Guard
 * 
 * Purpose: Stop 404 spam from frozen modules
 * 
 * Phase-A freeze list (hard-coded止血):
 * - SEARCH
 * - SIGNAL_DELIVERY  
 * - ATS_SIGNALS
 * - APPOINTMENTS
 * - PAYMENTS
 * - CHAT
 * - DASHBOARD (legacy metrics)
 * 
 * Phase-A active modules:
 * - USERS
 * - PEER_MOCK
 * - KERNEL_ADMIN
 * - DECISION_SLOTS
 * - HUMAN_LOOP
 */

const FROZEN_MODULES = new Set([
  'SEARCH',
  'SIGNAL_DELIVERY',
  'ATS_SIGNALS',
  'APPOINTMENTS',
  'PAYMENTS',
  'CHAT',
  'DASHBOARD',
  'JOB_CRAWLER',
  'RESUME_MATCHER',
  'ADMINPANEL', // Phase-A: SuperAdmin world doesn't use legacy admin settings
]);

/**
 * Check if a module is frozen in Phase-A
 */
export const isModuleFrozen = (moduleName: string): boolean => {
  return FROZEN_MODULES.has(moduleName.toUpperCase());
};

/**
 * Check if a module is active in Phase-A
 */
export const isModuleActive = (moduleName: string): boolean => {
  return !isModuleFrozen(moduleName);
};

/**
 * Guard function: only execute if module is active
 * Returns null if module is frozen (prevents request)
 */
export const guardModuleCall = <T>(
  moduleName: string,
  callback: () => Promise<T>
): Promise<T | null> => {
  if (isModuleFrozen(moduleName)) {
    console.debug(`[PHASE-A] Module ${moduleName} is frozen, skipping request`);
    return Promise.resolve(null);
  }
  return callback();
};

/**
 * Synchronous guard: returns boolean
 */
export const canCallModule = (moduleName: string): boolean => {
  const canCall = !isModuleFrozen(moduleName);
  if (!canCall) {
    console.debug(`[PHASE-A] Module ${moduleName} is frozen, request blocked`);
  }
  return canCall;
};
