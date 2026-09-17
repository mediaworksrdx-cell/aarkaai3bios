import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { McpSettingsTab } from '../McpSettingsTab';
import * as api from '@/lib/api';
import { McpServerInfo } from '@/types';

const mockServers: McpServerInfo[] = [
  {
    id: 'filesystem',
    name: 'Local Filesystem Engine',
    description: 'Safe sandboxed access to workspace directory',
    transport: 'stdio',
    status: 'connected',
    enabled: true,
    ping_ms: 8,
    tools: [
      {
        name: 'filesystem.read_file',
        description: 'Read file contents from workspace',
        mutation_risk: 'read_only',
        permissions: {
          network: false,
          filesystem: true,
          shell: false,
          mutating: false,
        },
        enabled: true,
      },
      {
        name: 'filesystem.write_file',
        description: 'Write file contents to workspace',
        mutation_risk: 'critical',
        permissions: {
          network: false,
          filesystem: true,
          shell: false,
          mutating: true,
        },
        enabled: true,
      },
    ],
  },
  {
    id: 'postgres',
    name: 'PostgreSQL Vector & Relational Store',
    description: 'Direct SQL query interface',
    transport: 'stdio',
    status: 'disabled',
    enabled: false,
    tools: [],
  },
];

describe('McpSettingsTab Component', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('fetches and renders connected MCP servers and their statuses', async () => {
    vi.spyOn(api, 'fetchMcpServers').mockResolvedValue({
      status: 'ok',
      servers: mockServers,
    });

    render(<McpSettingsTab />);

    await waitFor(() => {
      expect(screen.getByText('Local Filesystem Engine')).toBeInTheDocument();
      expect(screen.getByText('PostgreSQL Vector & Relational Store')).toBeInTheDocument();
    });

    expect(screen.getByText('Connected')).toBeInTheDocument();
    expect(screen.getByText('Disabled')).toBeInTheDocument();
    expect(screen.getByText('8ms ping')).toBeInTheDocument();
  });

  it('allows toggling server state between enabled and disabled', async () => {
    vi.spyOn(api, 'fetchMcpServers').mockResolvedValue({
      status: 'ok',
      servers: mockServers,
    });

    const toggleSpy = vi.spyOn(api, 'toggleMcpServer').mockResolvedValue({
      status: 'ok',
      server: {
        ...mockServers[0],
        enabled: false,
        status: 'disabled',
      },
    });

    render(<McpSettingsTab />);

    await waitFor(() => {
      expect(screen.getByText('Local Filesystem Engine')).toBeInTheDocument();
    });

    const switches = screen.getAllByRole('switch');
    expect(switches.length).toBe(2);

    // Toggle the first enabled server
    fireEvent.click(switches[0]);

    await waitFor(() => {
      expect(toggleSpy).toHaveBeenCalledWith('filesystem', false);
    });
  });

  it('expands tools list and renders permission chips and mutation badges', async () => {
    vi.spyOn(api, 'fetchMcpServers').mockResolvedValue({
      status: 'ok',
      servers: mockServers,
    });

    render(<McpSettingsTab />);

    await waitFor(() => {
      expect(screen.getByText('Local Filesystem Engine')).toBeInTheDocument();
    });

    // Expand tools list by clicking the chevron button
    const expandButtons = screen.getAllByTitle(/View tools & permissions/i);
    expect(expandButtons.length).toBeGreaterThanOrEqual(1);
    fireEvent.click(expandButtons[0]);

    await waitFor(() => {
      expect(screen.getByText('filesystem.read_file')).toBeInTheDocument();
      expect(screen.getByText('filesystem.write_file')).toBeInTheDocument();
    });

    expect(screen.getByText('READ ONLY')).toBeInTheDocument();
    expect(screen.getByText('CRITICAL')).toBeInTheDocument();
    expect(screen.getByText('Mutating')).toBeInTheDocument();
    expect(screen.getAllByText('FS').length).toBe(2);
  });
});
