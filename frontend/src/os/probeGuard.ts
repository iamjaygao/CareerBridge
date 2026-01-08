/**
 * GateAI OS Probe Guard
 * 
 * Prevents automatic probing/prefetching of write-sensitive endpoints.
 * 
 * RATIONALE:
 * - HUMAN_LOOP domain contains write-only mutation endpoints
 * - These must NEVER be auto-probed, prefetched, or speculatively called
 * - Only explicit user actions should trigger write operations
 * 
 * CONTRACT:
 * - Read endpoints: Can be probed/prefetched safely
 * - Write endpoints: Require explicit user intent
 * 
 * ENFORCEMENT:
 * - Throw error if write endpoint is accessed without user action
 * - Warn in development for potential misuse
 */

/**
 * Write-sensitive URL patterns that must NEVER be auto-probed
 */
const WRITE_ENDPOINT_PATTERNS = [
  '/update',
  '/create',
  '/delete',
  '/cancel',
  '/remove',
  '/apply',
];

/**
 * Check if URL is a write endpoint
 */
export function isWriteEndpoint(url: string): boolean {
  return WRITE_ENDPOINT_PATTERNS.some(pattern => url.includes(pattern));
}

/**
 * Assert that URL is safe for automatic probing
 * 
 * @param url - The URL to check
 * @param context - Context for debugging (e.g., 'bootstrap', 'preload')
 * @throws Error if URL is a write endpoint
 */
export function assertSafeForProbe(url: string, context: string = 'unknown'): void {
  if (isWriteEndpoint(url)) {
    const error = `[GateAI OS] Probe Guard: Write endpoint detected in ${context}: ${url}`;
    
    if (process.env.NODE_ENV !== 'production') {
      console.error(error);
      console.trace('Call stack:');
    }
    
    throw new Error(
      `${error}\n\n` +
      `Write endpoints must NEVER be auto-probed. This violates the GateAI OS contract.\n` +
      `Solution: Use explicit user actions for write operations.`
    );
  }
}

/**
 * Domains that require strict write protection
 * 
 * HUMAN_LOOP:
 * - Contains mentor profile mutations (/profile/update/)
 * - Must never be auto-probed on page load
 * - Requires explicit mentor authentication
 */
export const WRITE_PROTECTED_DOMAINS = [
  'HUMAN_LOOP',
] as const;

/**
 * Check if a domain requires write protection
 */
export function isWriteProtectedDomain(domain: string): boolean {
  return WRITE_PROTECTED_DOMAINS.includes(domain as any);
}

/**
 * Validate that an API call is safe
 * 
 * Used in request interceptors to catch misuse early
 */
export function validateApiCall(url: string, method: string, context?: string): void {
  // Only check GET requests (these should never target write endpoints)
  if (method.toUpperCase() === 'GET') {
    if (isWriteEndpoint(url)) {
      assertSafeForProbe(url, context || 'API call');
    }
  }
}

