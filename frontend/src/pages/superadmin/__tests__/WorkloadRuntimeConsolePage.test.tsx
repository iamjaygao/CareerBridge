/**
 * Workload Runtime Console Page Tests
 * 
 * Critical Phase-A.2 requirement:
 * - Page MUST NOT make API calls to frozen endpoints
 * - Page MUST only fetch static registry file
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import WorkloadRuntimeConsolePage from '../WorkloadRuntimeConsolePage';

// Mock fetch
global.fetch = jest.fn();

describe('WorkloadRuntimeConsolePage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should only fetch static registry file on mount', async () => {
    const mockRegistry = {
      version: '0.2',
      generated_at: '2026-01-14T00:00:00.000Z',
      scan_summary: {
        total_workloads: 2,
        total_buses: 1,
        by_bus: { AI_BUS: 2 },
      },
      buses: {
        AI_BUS: {
          state: 'OFF',
          workloads: [
            {
              name: 'test-workload',
              kind: 'backend',
              world: 'app',
              status: 'FROZEN',
              reason: 'Test freeze',
              entrypoints: {
                frontend_routes: [],
                backend_prefixes: [],
              },
              signals: {
                code_refs: ['test.py:1'],
                keywords: ['frozen'],
              },
            },
          ],
        },
      },
    };

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockRegistry,
    });

    render(<WorkloadRuntimeConsolePage />);

    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
    });

    // Verify ONLY ONE fetch call to static registry
    expect(global.fetch).toHaveBeenCalledTimes(1);
    expect(global.fetch).toHaveBeenCalledWith('/registry/WORKLOAD_FROZEN_BUS_REGISTRY.json');

    // Verify no calls to backend API endpoints
    const calls = (global.fetch as jest.Mock).mock.calls;
    calls.forEach(([url]) => {
      expect(url).not.toMatch(/\/api\/v1\//);
      expect(url).not.toMatch(/\/api\/admin\//);
      expect(url).not.toMatch(/\/api\/engines\//);
    });
  });

  it('should display registry data when loaded', async () => {
    const mockRegistry = {
      version: '0.2',
      generated_at: '2026-01-14T00:00:00.000Z',
      scan_summary: {
        total_workloads: 1,
        total_buses: 1,
        by_bus: { AI_BUS: 1 },
      },
      buses: {
        AI_BUS: {
          state: 'OFF',
          workloads: [
            {
              name: 'test-workload',
              kind: 'backend',
              world: 'app',
              status: 'FROZEN',
              reason: 'Phase-A freeze',
              entrypoints: {
                frontend_routes: [],
                backend_prefixes: [],
              },
              signals: {
                code_refs: ['test.py:1'],
                keywords: ['frozen'],
              },
            },
          ],
        },
      },
    };

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockRegistry,
    });

    render(<WorkloadRuntimeConsolePage />);

    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText(/AI_BUS/i)).toBeInTheDocument();
    });

    // Verify summary is displayed
    expect(screen.getByText('1')).toBeInTheDocument(); // Total buses or workloads
    expect(screen.getByText('OFF')).toBeInTheDocument(); // Bus state
  });

  it('should handle registry load error gracefully', async () => {
    (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

    render(<WorkloadRuntimeConsolePage />);

    // Wait for error to display
    await waitFor(() => {
      expect(screen.getByText(/Failed to Load Registry/i)).toBeInTheDocument();
    });

    // Verify still no calls to frozen endpoints
    expect(global.fetch).toHaveBeenCalledTimes(1);
    expect(global.fetch).toHaveBeenCalledWith('/registry/WORKLOAD_FROZEN_BUS_REGISTRY.json');
  });
});
