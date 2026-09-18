import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { FloatingApprovalDrawer } from '../FloatingApprovalDrawer';
import { ToolApprovalRequest } from '@/types';

// Mock useChatContext
vi.mock('@/context/ChatContext', () => ({
  useChatContext: () => ({
    resolveApproval: vi.fn(),
    alwaysAllowTool: vi.fn(),
    dismissActiveApproval: vi.fn(),
  }),
}));

const mockBashRequest: ToolApprovalRequest = {
  approval_id: 'gate-abc-78901',
  tool_name: 'BashTool',
  arguments: {
    command: 'python3 healthcheck.py',
  },
  mutation_risk: 'high',
  action_hash: '3a1f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a',
  human_summary: 'Execute shell command: python3 healthcheck.py',
  timeout_seconds: 120,
  created_at: Date.now(),
  status: 'pending',
};

const mockClaudeFileRequest: ToolApprovalRequest = {
  approval_id: 'gate-claude-4455',
  tool_name: 'FileEditTool',
  arguments: {
    path: 'healthcheck.py',
    content: 'import os\nprint("Disk check")',
  },
  mutation_risk: 'high',
  action_hash: '99bf86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a',
  human_summary: 'Modify file: healthcheck.py',
  timeout_seconds: 120,
  created_at: Date.now(),
  status: 'pending',
  model_persona: {
    provider: 'claude',
    name: 'Claude Sonnet',
    badge: 'Claude · Constitutional Safety',
    badge_color: 'border-[#D97706]/40 bg-[#D97706]/15 text-[#F59E0B]',
    accent_color: '#D97706',
    agent_ref: 'Claude',
  },
  dynamic_options: [
    {
      id: 1,
      action: 'allow_once',
      label: "Allow & save 'healthcheck.py' to workspace",
      recommended: true,
    },
    {
      id: 2,
      action: 'allow_and_run',
      label: "Save 'healthcheck.py' and execute immediately (python healthcheck.py)",
    },
    {
      id: 3,
      action: 'customize',
      label: "Inspect & customize 'healthcheck.py' code before committing",
    },
    {
      id: 4,
      action: 'always_allow',
      label: 'Always allow workspace file modifications in this session',
    },
    {
      id: 5,
      action: 'deny',
      label: 'No (tell Claude what to do instead)',
    },
  ],
};

const mockGeminiRequest: ToolApprovalRequest = {
  approval_id: 'gate-gemini-7788',
  tool_name: 'BashTool',
  arguments: {
    command: 'pytest tests/unit',
  },
  mutation_risk: 'medium',
  action_hash: '77bf86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a',
  human_summary: 'Execute shell command: pytest tests/unit',
  timeout_seconds: 120,
  created_at: Date.now(),
  status: 'pending',
  model_persona: {
    provider: 'gemini',
    name: 'Gemini Pro',
    badge: 'Gemini · Multimodal Verification',
    badge_color: 'border-indigo-500/40 bg-indigo-500/15 text-indigo-400',
    accent_color: '#6366F1',
    agent_ref: 'Gemini',
  },
};

const mockFinanceRequest: ToolApprovalRequest = {
  approval_id: 'gate-fin-99881',
  tool_name: 'FinanceStrategyMasterSelection',
  arguments: {
    symbol: 'NIFTY',
    current_price: 25400,
    lot_size: 25,
    expiry: '26-SEP-2026',
    signal: 'BULLISH',
    currency: 'INR',
    master_recommended: 'strat-1',
    candidates: [
      {
        candidate_id: 'strat-1',
        category: 'VOLATILITY_ARBITRAGE',
        technology_tag: 'DELTA_NEUTRAL',
        strategy_name: 'Delta-Neutral Volatility Engine',
        strategy_type: 'Options Spread',
        legs: [{ action: 'BUY', type: 'CE', strike: 25500, premium_est: 110 }],
        win_rate_est: '74%',
        risk_reward_actual: '1:2.8',
        max_loss_per_lot: '₹2,200',
        rationale: 'Captures volatility crush while preserving delta-neutral hedging.',
      },
      {
        candidate_id: 'strat-2',
        category: 'DIRECTIONAL_MOMENTUM',
        technology_tag: 'MOMENTUM_BREAKOUT',
        strategy_name: 'Bull Call Algorithmic Ladder',
        strategy_type: 'Bull Spread',
        legs: [{ action: 'BUY', type: 'CE', strike: 25400, premium_est: 140 }],
        win_rate_est: '68%',
        risk_reward_actual: '1:3.2',
        max_loss_per_lot: '₹3,500',
        rationale: 'High momentum breakout tracking system with defined risk.',
      },
    ],
  },
  mutation_risk: 'medium',
  action_hash: '5e86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
  human_summary: 'Execute Master Options Strategy Selection for NIFTY',
  timeout_seconds: 120,
  created_at: Date.now(),
  status: 'pending',
};

describe('FloatingApprovalDrawer Component', () => {
  it('renders minimalist card matching reference with title, command box, options, and actions', () => {
    render(<FloatingApprovalDrawer request={mockBashRequest} />);

    expect(screen.getByTestId('floating-approval-drawer')).toBeInTheDocument();
    expect(screen.getByText('Allow run python3 healthcheck.py?')).toBeInTheDocument();
    expect(screen.getByText('python3 healthcheck.py')).toBeInTheDocument();
    expect(screen.getByText('Yes, allow this time')).toBeInTheDocument();
    expect(screen.getByText("Yes, and always allow 'python3 healthcheck.py' in this conversation")).toBeInTheDocument();
    expect(screen.getByText("Yes, and always allow 'python3 healthcheck.py' in this project")).toBeInTheDocument();
    expect(screen.getByText("Yes, and always allow 'python3 healthcheck.py'")).toBeInTheDocument();
    expect(screen.getByText('No (tell the agent what to do instead)')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Approve/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Deny/i })).toBeInTheDocument();
  });

  it('calls onResolve with approve decision when Submit button is clicked', async () => {
    const mockResolve = vi.fn().mockResolvedValue(undefined);
    render(<FloatingApprovalDrawer request={mockBashRequest} onResolve={mockResolve} />);

    const approveBtn = screen.getByRole('button', { name: /Approve/i });
    fireEvent.click(approveBtn);

    await waitFor(() => {
      expect(mockResolve).toHaveBeenCalledWith('gate-abc-78901', 'approve', undefined, undefined);
    });
  });

  it('handles selecting option 4 (always allow) and submitting', async () => {
    const mockResolve = vi.fn().mockResolvedValue(undefined);
    const mockAlwaysAllow = vi.fn();
    render(
      <FloatingApprovalDrawer
        request={mockBashRequest}
        onResolve={mockResolve}
        onAlwaysAllow={mockAlwaysAllow}
      />
    );

    const alwaysOption = screen.getByText("Yes, and always allow 'python3 healthcheck.py'");
    fireEvent.click(alwaysOption);

    const submitBtn = screen.getByRole('button', { name: /Approve/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(mockAlwaysAllow).toHaveBeenCalledWith('BashTool');
      expect(mockResolve).toHaveBeenCalledWith('gate-abc-78901', 'approve', undefined, undefined);
    });
  });

  it('renders Master Finance Strategy candidate cards and passes selected strategy to onResolve', async () => {
    const mockResolve = vi.fn().mockResolvedValue(undefined);
    render(<FloatingApprovalDrawer request={mockFinanceRequest} onResolve={mockResolve} />);

    expect(screen.getByText('Delta-Neutral Volatility Engine')).toBeInTheDocument();
    expect(screen.getByText('Bull Call Algorithmic Ladder')).toBeInTheDocument();
    expect(screen.getByText('★ RECOMMENDED')).toBeInTheDocument();

    // Select the second strategy
    const secondStratCard = screen.getByText('Bull Call Algorithmic Ladder');
    fireEvent.click(secondStratCard);

    // Click Submit
    const approveBtn = screen.getByRole('button', { name: /Approve/i });
    fireEvent.click(approveBtn);

    await waitFor(() => {
      expect(mockResolve).toHaveBeenCalledWith('gate-fin-99881', 'approve', undefined, 'strat-2');
    });
  });

  it('toggles option 5 to input rejection reason and submits deny', async () => {
    const mockResolve = vi.fn().mockResolvedValue(undefined);
    render(<FloatingApprovalDrawer request={mockBashRequest} onResolve={mockResolve} />);

    const option5 = screen.getByText('No (tell the agent what to do instead)');
    fireEvent.click(option5);

    const reasonInput = screen.getByPlaceholderText('tell the agent what to do instead...');
    expect(reasonInput).toBeInTheDocument();

    fireEvent.change(reasonInput, { target: { value: 'run unit tests instead' } });

    const submitBtn = screen.getByRole('button', { name: /Approve/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(mockResolve).toHaveBeenCalledWith('gate-abc-78901', 'deny', 'run unit tests instead', undefined);
    });
  });

  it('renders dynamic contextual options when provided by model persona', () => {
    render(<FloatingApprovalDrawer request={mockClaudeFileRequest} />);

    expect(screen.getByText("Allow & save 'healthcheck.py' to workspace")).toBeInTheDocument();
    expect(screen.getByText("Save 'healthcheck.py' and execute immediately (python healthcheck.py)")).toBeInTheDocument();
    expect(screen.getByText("No (tell Claude what to do instead)")).toBeInTheDocument();
  });

  it('renders synthesized options tailored to Gemini model persona', () => {
    render(<FloatingApprovalDrawer request={mockGeminiRequest} />);

    expect(screen.getByText('Allow run backend unit tests?')).toBeInTheDocument();
    expect(screen.getByText('pytest tests/unit')).toBeInTheDocument();
    expect(screen.getByText('No (tell Gemini what to do instead)')).toBeInTheDocument();
  });
});
