/**
 * GateAI OS Legacy API Detection
 * 
 * Safety net to warn about legacy API path usage in development.
 * Does not block requests, only warns.
 */

export function assertNoLegacyApi(url: string): void {
  const forbidden = [
    '/api/v1/resumes/',
    '/api/v1/mentors/',
    '/api/v1/appointments/',
    '/api/v1/notifications/',
  ];
  
  if (process.env.NODE_ENV !== 'production') {
    if (forbidden.some((p) => url.includes(p))) {
      // eslint-disable-next-line no-console
      console.warn('[GateAI OS] Legacy API path detected:', url);
    }
  }
}

