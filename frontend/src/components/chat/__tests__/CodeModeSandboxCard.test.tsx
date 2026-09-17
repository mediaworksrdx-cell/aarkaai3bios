import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { CodeModeSandboxCard } from '../CodeModeSandboxCard';
import { CodeModeExecution } from '@/types';

const mockExecution: CodeModeExecution = {
  execution_id: 'exec-8888-abcd',
  script: 'def run():\n    print("Hello from sandbox")\n    return True',
  status: 'completed',
  steps: [
    {
      step_id: 'step-1',
      tool_name: 'git.status',
      arguments: { repo: 'current' },
      status: 'completed',
      duration_ms: 12,
      output: 'On branch main, working tree clean',
    },
    {
      step_id: 'step-2',
      tool_name: 'sandbox.eval',
      arguments: { expr: '2 + 2' },
      status: 'completed',
      duration_ms: 4,
      output: '4',
    },
  ],
  console_output: [
    '[sandbox] Initializing microVM',
    '[sandbox] Execution completed successfully',
  ],
  security_boundaries: {
    network_access: false,
    file_system_scope: 'workspace_isolated',
    max_execution_time_sec: 30,
    mutation_allowed: false,
  },
  created_at: Date.now() - 5000,
  completed_at: Date.now(),
};

describe('CodeModeSandboxCard Component', () => {
  it('renders execution header, status pill, and security boundaries', () => {
    render(<CodeModeSandboxCard execution={mockExecution} />);

    expect(screen.getByText('CodeMode Sandbox')).toBeInTheDocument();
    expect(screen.getByText('#exec-888')).toBeInTheDocument();
    expect(screen.getByText('Sandbox Clean')).toBeInTheDocument();
    expect(screen.getByText(/Network: Airgapped/i)).toBeInTheDocument();
    expect(screen.getByText(/Scope: workspace_isolated/i)).toBeInTheDocument();
    expect(screen.getByText(/Limit: 30s/i)).toBeInTheDocument();
  });

  it('renders tool steps on Timeline tab and allows expanding step details', () => {
    render(<CodeModeSandboxCard execution={mockExecution} />);

    expect(screen.getByText('git.status')).toBeInTheDocument();
    expect(screen.getByText('sandbox.eval')).toBeInTheDocument();
    expect(screen.getAllByText('Passed').length).toBe(2);

    // Expand step 1
    const step1Btn = screen.getByText('git.status').closest('button');
    expect(step1Btn).toBeInTheDocument();
    if (step1Btn) {
      fireEvent.click(step1Btn);
      expect(screen.getByText(/On branch main, working tree clean/i)).toBeInTheDocument();
    }
  });

  it('switches to Script tab and displays generated code', () => {
    render(<CodeModeSandboxCard execution={mockExecution} />);

    const scriptTab = screen.getByRole('button', { name: /Generated Script/i });
    fireEvent.click(scriptTab);

    expect(screen.getByText(/def run\(\):/i)).toBeInTheDocument();
    expect(screen.getByText(/print\("Hello from sandbox"\)/i)).toBeInTheDocument();
  });

  it('switches to Console tab and displays stdout/stderr lines', () => {
    render(<CodeModeSandboxCard execution={mockExecution} />);

    const consoleTab = screen.getByRole('button', { name: /Console Output/i });
    fireEvent.click(consoleTab);

    expect(screen.getByText(/SANDBOX STDOUT \/ STDERR STREAM/i)).toBeInTheDocument();
    expect(screen.getByText(/\[sandbox\] Initializing microVM/i)).toBeInTheDocument();
    expect(screen.getByText(/\[sandbox\] Execution completed successfully/i)).toBeInTheDocument();
  });
});
