import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ChatInput } from '../ChatInput';

// Mock useChatContext
vi.mock('@/context/ChatContext', () => ({
  useChatContext: () => ({
    resolveApproval: vi.fn(),
    alwaysAllowTool: vi.fn(),
    dismissActiveApproval: vi.fn(),
  }),
}));

describe('ChatInput Command & Intent Permission Flow - Multi-Asset & Regimes', () => {
  it('submits normal conversational text directly without showing permission popup', () => {
    const onSend = vi.fn();
    render(
      <ChatInput
        onSend={onSend}
        isStreaming={false}
        selectedModel="aarka-2.0"
        onModelChange={vi.fn()}
      />
    );

    const textarea = screen.getByPlaceholderText(/Ask Aarka anything/i);
    fireEvent.change(textarea, { target: { value: 'Explain quantum computing in simple terms' } });
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: false });

    expect(onSend).toHaveBeenCalledWith('Explain quantum computing in simple terms');
    expect(screen.queryByTestId('floating-approval-drawer')).not.toBeInTheDocument();
  });

  it('Case 1: Intercepts terminal command df -h on Enter, displays popup with BashTool, and executes upon approval', async () => {
    const onSend = vi.fn();
    render(
      <ChatInput
        onSend={onSend}
        isStreaming={false}
        selectedModel="aarka-2.0"
        onModelChange={vi.fn()}
      />
    );

    const textarea = screen.getByPlaceholderText(/Ask Aarka anything/i);
    fireEvent.change(textarea, { target: { value: 'df -h' } });
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: false });

    // onSend should NOT have been called yet!
    expect(onSend).not.toHaveBeenCalled();

    // Popup should be visible with exact command and options matching reference
    const drawer = screen.getByTestId('floating-approval-drawer');
    expect(drawer).toBeInTheDocument();
    expect(within(drawer).getByText('Allow run df -h?')).toBeInTheDocument();
    expect(within(drawer).getByText('df -h')).toBeInTheDocument();
    expect(within(drawer).getByText("Execute 'df -h' in isolated sandbox")).toBeInTheDocument();
    expect(within(drawer).getByText("Execute 'df -h' and stream live terminal output")).toBeInTheDocument();
    expect(within(drawer).getByText('Edit command parameters before execution')).toBeInTheDocument();
    expect(within(drawer).getByText("Always allow 'df -h' in this session (Always Allow)")).toBeInTheDocument();
    expect(within(drawer).getByText('No (tell Aarka what to do instead)')).toBeInTheDocument();

    // Approve
    const approveBtn = within(drawer).getByRole('button', { name: /Approve/i });
    fireEvent.click(approveBtn);

    await waitFor(() => {
      expect(onSend).toHaveBeenCalledWith('df -h');
    });
  });

  it('Case 2: Intercepts microservice file creation (FileEditTool) for api_service.py and displays dynamic options', async () => {
    const onSend = vi.fn();
    render(
      <ChatInput
        onSend={onSend}
        isStreaming={false}
        selectedModel="aarka-2.0"
        onModelChange={vi.fn()}
      />
    );

    const textarea = screen.getByPlaceholderText(/Ask Aarka anything/i);
    const prompt = 'Create a Python script api_service.py with a FastAPI health check and status endpoint';
    fireEvent.change(textarea, { target: { value: prompt } });
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: false });

    expect(onSend).not.toHaveBeenCalled();

    const drawer = screen.getByTestId('floating-approval-drawer');
    expect(drawer).toBeInTheDocument();
    expect(within(drawer).getByText('Allow modify file: api_service.py?')).toBeInTheDocument();
    expect(within(drawer).getByText('api_service.py')).toBeInTheDocument();
    expect(within(drawer).getByText('FileEditTool')).toBeInTheDocument();
    expect(within(drawer).getByText("Allow & save 'api_service.py' to workspace")).toBeInTheDocument();
    expect(within(drawer).getByText("Save 'api_service.py' and execute immediately (python api_service.py)")).toBeInTheDocument();
    expect(within(drawer).getByText("Inspect & customize 'api_service.py' code before committing")).toBeInTheDocument();
    expect(within(drawer).getByText('No (tell Aarka what to do instead)')).toBeInTheDocument();

    const approveBtn = within(drawer).getByRole('button', { name: /Approve/i });
    fireEvent.click(approveBtn);

    await waitFor(() => {
      expect(onSend).toHaveBeenCalledWith(prompt);
    });
  });

  it('Case 3: Intercepts quantitative finance strategy selection for NIFTY, displays strategy cards, and triggers chosen strategy on approve', async () => {
    const onSend = vi.fn();
    render(
      <ChatInput
        onSend={onSend}
        isStreaming={false}
        selectedModel="aarka-2.0"
        onModelChange={vi.fn()}
      />
    );

    const textarea = screen.getByPlaceholderText(/Ask Aarka anything/i);
    const prompt = 'Screen top bullish options strategies for NIFTY';
    fireEvent.change(textarea, { target: { value: prompt } });
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: false });

    expect(onSend).not.toHaveBeenCalled();

    const drawer = screen.getByTestId('floating-approval-drawer');
    expect(drawer).toBeInTheDocument();
    expect(within(drawer).getByText('Aarka Engine · Autonomous Execution')).toBeInTheDocument();
    expect(within(drawer).getByText('Delta-Neutral Volatility Engine')).toBeInTheDocument();
    expect(within(drawer).getByText('Bull Call Algorithmic Ladder')).toBeInTheDocument();
    expect(within(drawer).getByText('★ RECOMMENDED')).toBeInTheDocument();

    const approveBtn = within(drawer).getByRole('button', { name: /Approve/i });
    fireEvent.click(approveBtn);

    await waitFor(() => {
      expect(onSend).toHaveBeenCalledWith(
        expect.stringContaining('Execute Delta-Neutral Volatility Engine for NIFTY')
      );
    });
  });

  it('Case 4: Selecting a different candidate card triggers that specific strategy execution', async () => {
    const onSend = vi.fn();
    render(
      <ChatInput
        onSend={onSend}
        isStreaming={false}
        selectedModel="aarka-2.0"
        onModelChange={vi.fn()}
      />
    );

    const textarea = screen.getByPlaceholderText(/Ask Aarka anything/i);
    fireEvent.change(textarea, { target: { value: 'Screen top bullish options strategies for NIFTY' } });
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: false });

    const drawer = screen.getByTestId('floating-approval-drawer');
    expect(drawer).toBeInTheDocument();

    // Click the second candidate card
    const card2 = within(drawer).getByText('Bull Call Algorithmic Ladder');
    fireEvent.click(card2);

    // Option 1 dynamically reflects the selected strategy
    expect(within(drawer).getByText(/Execute Strategy \(Bull Call Algorithmic Ladder\)/i)).toBeInTheDocument();

    const approveBtn = within(drawer).getByRole('button', { name: /Approve/i });
    fireEvent.click(approveBtn);

    await waitFor(() => {
      expect(onSend).toHaveBeenCalledWith(
        expect.stringContaining('Execute Bull Call Algorithmic Ladder for NIFTY')
      );
    });
  });

  it('Case 5: Multi-Asset Commodity Interception -> Gold Reversal popup and execution', async () => {
    const onSend = vi.fn();
    render(
      <ChatInput
        onSend={onSend}
        isStreaming={false}
        selectedModel="aarka-2.0"
        onModelChange={vi.fn()}
      />
    );

    const textarea = screen.getByPlaceholderText(/Ask Aarka anything/i);
    fireEvent.change(textarea, { target: { value: 'Suggest a reversal trading strategy for Gold' } });
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: false });

    const drawer = screen.getByTestId('floating-approval-drawer');
    expect(drawer).toBeInTheDocument();
    expect(within(drawer).getByText(/Select REVERSAL Strategy for Gold \(Commodity\)/i)).toBeInTheDocument();

    const approveBtn = within(drawer).getByRole('button', { name: /Approve/i });
    fireEvent.click(approveBtn);

    await waitFor(() => {
      expect(onSend).toHaveBeenCalledWith(
        expect.stringContaining('for GOLD (Commodity)')
      );
    });
  });

  it('Case 6: Multi-Asset Crypto Interception -> Bitcoin Neutral Grid popup and execution', async () => {
    const onSend = vi.fn();
    render(
      <ChatInput
        onSend={onSend}
        isStreaming={false}
        selectedModel="aarka-2.0"
        onModelChange={vi.fn()}
      />
    );

    const textarea = screen.getByPlaceholderText(/Ask Aarka anything/i);
    fireEvent.change(textarea, { target: { value: 'What neutral strategy should I use for Bitcoin?' } });
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: false });

    const drawer = screen.getByTestId('floating-approval-drawer');
    expect(drawer).toBeInTheDocument();
    expect(within(drawer).getByText(/Select NEUTRAL Strategy for Bitcoin \(Crypto\)/i)).toBeInTheDocument();
    expect(within(drawer).getByText('BTC Range-Bound Volatility Harvest')).toBeInTheDocument();

    const approveBtn = within(drawer).getByRole('button', { name: /Approve/i });
    fireEvent.click(approveBtn);

    await waitFor(() => {
      expect(onSend).toHaveBeenCalledWith(
        expect.stringContaining('Execute BTC Range-Bound Volatility Harvest for BTC (Crypto)')
      );
    });
  });

  it('Case 7: Claude engine persona test for db_backup.py with amber badge and Claude tailored options', async () => {
    const onSend = vi.fn();
    render(
      <ChatInput
        onSend={onSend}
        isStreaming={false}
        selectedModel="claude-3-7-sonnet"
        onModelChange={vi.fn()}
      />
    );

    const textarea = screen.getByPlaceholderText(/Ask Aarka anything/i);
    const prompt = 'Write a backup script db_backup.py to compress and archive the database';
    fireEvent.change(textarea, { target: { value: prompt } });
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: false });

    expect(onSend).not.toHaveBeenCalled();

    const drawer = screen.getByTestId('floating-approval-drawer');
    expect(drawer).toBeInTheDocument();
    expect(within(drawer).getByText('Allow modify file: db_backup.py?')).toBeInTheDocument();
    expect(within(drawer).getByText('Claude · Constitutional Safety')).toBeInTheDocument();
    expect(within(drawer).getByText("Allow & save 'db_backup.py' to workspace")).toBeInTheDocument();
    expect(within(drawer).getByText('No (tell Claude what to do instead)')).toBeInTheDocument();

    const approveBtn = within(drawer).getByRole('button', { name: /Approve/i });
    fireEvent.click(approveBtn);

    await waitFor(() => {
      expect(onSend).toHaveBeenCalledWith(prompt);
    });
  });

  it('preserves entered text in field when popup is skipped/cancelled', async () => {
    const onSend = vi.fn();
    render(
      <ChatInput
        onSend={onSend}
        isStreaming={false}
        selectedModel="aarka-2.0"
        onModelChange={vi.fn()}
      />
    );

    const textarea = screen.getByPlaceholderText(/Ask Aarka anything/i) as HTMLTextAreaElement;
    fireEvent.change(textarea, { target: { value: 'df -h' } });
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: false });

    const drawer = screen.getByTestId('floating-approval-drawer');
    expect(drawer).toBeInTheDocument();

    const skipBtn = within(drawer).getByRole('button', { name: /Deny/i });
    fireEvent.click(skipBtn);

    expect(onSend).not.toHaveBeenCalled();
    expect(textarea.value).toBe('df -h');
  });
});
