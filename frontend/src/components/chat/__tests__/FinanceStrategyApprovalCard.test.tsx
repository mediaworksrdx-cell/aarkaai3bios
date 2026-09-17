import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { FinanceStrategyApprovalCard } from '../FinanceStrategyApprovalCard';
import { ToolApprovalRequest } from '@/types';

const mockFinanceRequest: ToolApprovalRequest = {
  approval_id: 'appr-strat-test-101',
  tool_name: 'FinanceStrategyMasterSelection',
  arguments: {
    symbol: 'SBIN.NS',
    current_price: 814.5,
    lot_size: 1500,
    expiry: '28-MAY-2026',
    signal: 'BULLISH',
    currency: '₹',
    master_recommended: 'candidate_defined_risk',
    candidates: [
      {
        candidate_id: 'candidate_defined_risk',
        category: 'Defined Risk (Spread)',
        technology_tag: 'Institutional Hedged Spread',
        strategy_name: 'Bull Call Spread (Defined Risk)',
        strategy_type: 'bull_call_spread',
        legs: [
          { action: 'BUY', type: 'CE', strike: 815, premium_est: 18.5 },
          { action: 'SELL', type: 'CE', strike: 835, premium_est: 7.2 },
        ],
        entry_trigger: 'Enter when price holds above EMA 20',
        stop_loss: 'Exit both legs if spot drops below ₹800.00',
        target: 'Hold till expiry if spot closes above ₹835.00',
        max_loss_per_lot: '₹16,950',
        max_gain_per_lot: '₹13,050',
        risk_reward_actual: '1:1.3',
        win_rate_est: '68%',
        rationale: 'Defined risk limits downside against volatility drops.',
      },
      {
        candidate_id: 'candidate_alpha_momentum',
        category: 'High-Alpha Momentum',
        technology_tag: 'Algorithmic Directional Outright',
        strategy_name: 'Naked Long Call (Aggressive Momentum)',
        strategy_type: 'long_call',
        legs: [
          { action: 'BUY', type: 'CE', strike: 820, premium_est: 15.0 },
        ],
        entry_trigger: 'Enter on 15m volume breakout',
        stop_loss: 'Exit if premium drops below ₹7.50',
        target: 'Target ₹845.00',
        max_loss_per_lot: '₹22,500',
        max_gain_per_lot: '₹45,000',
        risk_reward_actual: '1:2.0',
        win_rate_est: '52%',
        rationale: 'Breakout above monthly pivot.',
      },
    ],
  },
  mutation_risk: 'high',
  action_hash: '9a8d4f1837c35a10ad629bce664775fd381d812c8b17743392b5fb78f8488e14',
  description: 'Authorize Master of Technology Strategy for SBIN.NS',
  timeout_seconds: 120,
  created_at: Date.now(),
  status: 'pending',
};

describe('FinanceStrategyApprovalCard Component', () => {
  it('renders candidate strategies and Master of Technology selection UI', () => {
    render(<FinanceStrategyApprovalCard request={mockFinanceRequest} />);

    expect(screen.getByText('Master Strategy Approval Gate')).toBeInTheDocument();
    expect(screen.getByText('BULLISH')).toBeInTheDocument();
    expect(screen.getByText('Bull Call Spread (Defined Risk)')).toBeInTheDocument();
    expect(screen.getByText('Naked Long Call (Aggressive Momentum)')).toBeInTheDocument();
    expect(screen.getByText(/Select Master of Technology Strategy/i)).toBeInTheDocument();
  });

  it('allows switching the selected master candidate strategy', () => {
    render(<FinanceStrategyApprovalCard request={mockFinanceRequest} />);

    // Click the aggressive momentum candidate card
    const alphaOption = screen.getByText('Naked Long Call (Aggressive Momentum)');
    fireEvent.click(alphaOption);

    // Verify master plan title updates
    expect(screen.getByText(/Master Plan: Naked Long Call/i)).toBeInTheDocument();
  });

  it('submits approval with chosen master candidate strategy name', async () => {
    const mockOnResolve = vi.fn().mockResolvedValue(undefined);
    render(<FinanceStrategyApprovalCard request={mockFinanceRequest} onResolve={mockOnResolve} />);

    const approveBtn = screen.getByRole('button', { name: /Approve Master of Technology/i });
    fireEvent.click(approveBtn);

    await waitFor(() => {
      expect(mockOnResolve).toHaveBeenCalledWith(
        'appr-strat-test-101',
        'approve',
        'Bull Call Spread (Defined Risk)'
      );
    });

    expect(screen.getByText('Resolved: APPROVED')).toBeInTheDocument();
  });

  it('submits rejection when Reject Strategy is clicked', async () => {
    const mockOnResolve = vi.fn().mockResolvedValue(undefined);
    render(<FinanceStrategyApprovalCard request={mockFinanceRequest} onResolve={mockOnResolve} />);

    const rejectBtn = screen.getByRole('button', { name: /Reject Strategy/i });
    fireEvent.click(rejectBtn);

    await waitFor(() => {
      expect(mockOnResolve).toHaveBeenCalledWith(
        'appr-strat-test-101',
        'deny',
        'Bull Call Spread (Defined Risk)'
      );
    });

    expect(screen.getByText('Resolved: REJECTED')).toBeInTheDocument();
  });
});