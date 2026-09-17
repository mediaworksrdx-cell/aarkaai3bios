import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ToolApprovalCard } from '../ToolApprovalCard';
import { ToolApprovalRequest } from '@/types';

const mockPendingRequest: ToolApprovalRequest = {
  approval_id: 'appr-uuid-12345',
  tool_name: 'filesystem.write_file',
  arguments: {
    path: 'modules/critical.py',
    content: 'print("mutated")',
  },
  mutation_risk: 'critical',
  action_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
  description: 'Write updated code to modules/critical.py',
  timeout_seconds: 120,
  created_at: Date.now(),
  status: 'pending',
};

describe('ToolApprovalCard Component', () => {
  it('renders tool name, critical risk badge, and action description', () => {
    render(<ToolApprovalCard request={mockPendingRequest} />);

    expect(screen.getByText('filesystem.write_file')).toBeInTheDocument();
    expect(screen.getByText('Critical Risk')).toBeInTheDocument();
    expect(screen.getByText(/Write updated code to modules\/critical\.py/i)).toBeInTheDocument();
    expect(screen.getByText('Approve Action')).toBeInTheDocument();
    expect(screen.getByText('Deny...')).toBeInTheDocument();
  });

  it('calls onResolve with approve decision when Approve Action button is clicked', async () => {
    const mockOnResolve = vi.fn().mockResolvedValue(undefined);
    render(<ToolApprovalCard request={mockPendingRequest} onResolve={mockOnResolve} />);

    const approveBtn = screen.getByRole('button', { name: /Approve Action/i });
    fireEvent.click(approveBtn);

    await waitFor(() => {
      expect(mockOnResolve).toHaveBeenCalledWith('appr-uuid-12345', 'approve', undefined);
    });

    expect(screen.getByText('Approved')).toBeInTheDocument();
    expect(screen.getByText(/Mutation authorized and executed/i)).toBeInTheDocument();
  });

  it('reveals denial reason input and allows confirming denial', async () => {
    const mockOnResolve = vi.fn().mockResolvedValue(undefined);
    render(<ToolApprovalCard request={mockPendingRequest} onResolve={mockOnResolve} />);

    const denyBtn = screen.getByRole('button', { name: /Deny\.\.\./i });
    fireEvent.click(denyBtn);

    const reasonInput = screen.getByPlaceholderText(/Path is out of scope/i);
    expect(reasonInput).toBeInTheDocument();

    fireEvent.change(reasonInput, { target: { value: 'Disallowed file mutation' } });

    const confirmDenyBtn = screen.getByRole('button', { name: /Confirm Deny/i });
    fireEvent.click(confirmDenyBtn);

    await waitFor(() => {
      expect(mockOnResolve).toHaveBeenCalledWith('appr-uuid-12345', 'deny', 'Disallowed file mutation');
    });

    expect(screen.getByText('Rejected')).toBeInTheDocument();
    expect(screen.getByText(/Mutation blocked by operator/i)).toBeInTheDocument();
  });

  it('renders resolved status cleanly for pre-approved requests', () => {
    const approvedRequest: ToolApprovalRequest = {
      ...mockPendingRequest,
      status: 'approved',
      resolved_at: Date.now() - 1000,
      resolved_by: 'operator@aarkaa.ai',
    };

    render(<ToolApprovalCard request={approvedRequest} />);

    expect(screen.getByText('Approved')).toBeInTheDocument();
    expect(screen.queryByText('Approve Action')).not.toBeInTheDocument();
    expect(screen.getByText(/Mutation authorized and executed/i)).toBeInTheDocument();
  });
});
