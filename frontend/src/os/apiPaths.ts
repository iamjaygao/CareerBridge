/**
 * GateAI OS API Path Constants
 * 
 * Single source of truth for OS endpoint paths.
 * Aligned with GateAI OS Contract v1.0.1
 * 
 * Rules:
 * - Trailing slashes preserved (match backend routing style)
 * - No logic here, constants only
 */

export const OS_API = {
  ATS_SIGNALS: '/ats-signals/',
  HUMAN_LOOP: '/human-loop/',
  DECISION_SLOTS: '/decision-slots/',
  SIGNAL_DELIVERY: '/signal-delivery/',
} as const;

