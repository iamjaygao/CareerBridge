/**
 * Workload Runtime Console Page Tests
 * 
 * Critical Phase-A.2 requirement:
 * - Page MUST NOT make API calls to frozen endpoints
 * - Page MUST only fetch static registry file
 */

import React from 'react';
import { render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import WorkloadRuntimeConsolePage from '../WorkloadRuntimeConsolePage';

// Mock fetch
global.fetch = jest.fn();

// The page also loads live bus states from the kernel API.
jest.mock('../../../services/api/client', () => ({
  __esModule: true,
  default: {
    get: jest.fn(() => Promise.resolve({ data: [{ bus_name: 'AI_BUS', state: 'OFF' }] })),
    patch: jest.fn(),
  },
}));

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

    render(
      <MemoryRouter>
        <WorkloadRuntimeConsolePage />
      </MemoryRouter>
    );

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

    render(
      <MemoryRouter>
        <WorkloadRuntimeConsolePage />
      </MemoryRouter>
    );

    // Wait for data to load: the Power Buses table has exactly one data row,
    // and that row shows the bus by its display name ("AI" for AI_BUS; the
    // component shortens names via getBusDisplayName on purpose).
    await waitFor(() => {
      expect(within(screen.getByRole('table')).getAllByRole('row')).toHaveLength(2); // header + 1 bus
    });
    const [, busRow] = within(screen.getByRole('table')).getAllByRole('row');
    expect(within(busRow).getByText('AI')).toBeInTheDocument();

    // Verify summary is displayed: the Total Buses card shows 1.
    // The summary cards have no accessible role, so scope to the MUI Card.
    // eslint-disable-next-line testing-library/no-node-access
    const totalBusesCard = screen.getByText('Total Buses').closest('.MuiCard-root') as HTMLElement;
    expect(totalBusesCard).not.toBeNull();
    expect(within(totalBusesCard).getByText('1')).toBeInTheDocument();
    expect(screen.getByText('OFF')).toBeInTheDocument(); // Bus state
  });

  it('should handle registry load error gracefully', async () => {
    (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

    render(
      <MemoryRouter>
        <WorkloadRuntimeConsolePage />
      </MemoryRouter>
    );

    // Wait for error to display
    await waitFor(() => {
      expect(screen.getByText(/Failed to Load Registry/i)).toBeInTheDocument();
    });

    // Verify still no calls to frozen endpoints
    expect(global.fetch).toHaveBeenCalledTimes(1);
    expect(global.fetch).toHaveBeenCalledWith('/registry/WORKLOAD_FROZEN_BUS_REGISTRY.json');
  });
});
