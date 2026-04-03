/**
 * SuperAdmin Kernel Root
 * 
 * Phase-A: Clean Kernel Control Plane
 * - No legacy dashboard runtime
 * - No frozen module auto-requests
 * - Pure kernel world root
 */

import React from 'react';

export default function SuperAdminRoot() {
  return (
    <div style={{ padding: 32 }}>
      <h1>GateAI Kernel Control Plane</h1>
      <p>SuperAdmin World Root</p>
      <p>All legacy dashboard runtimes are disconnected.</p>
      <p style={{ marginTop: 24, color: '#666' }}>
        Phase-A: Kernel world is isolated from frozen modules.
      </p>
    </div>
  );
}
