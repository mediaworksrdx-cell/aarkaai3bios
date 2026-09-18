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

describe('ChatInput Command Permission Flow', () => {
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

  it('intercepts terminal command df -h on Enter, displays permission popup, and does not execute immediately', () => {
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
  });

  it('preserves entered command in text field when popup is skipped/cancelled', async () => {
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

    // After skipping, onSend should not have been called
    expect(onSend).not.toHaveBeenCalled();

    // The text in the input should still be preserved
    expect(textarea.value).toBe('df -h');
  });

  it('executes pendingCommand only after user approves in the popup', async () => {
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

    expect(onSend).not.toHaveBeenCalled();

    const drawer = screen.getByTestId('floating-approval-drawer');
    // Click Submit in the popup (Option 1 selected by default)
    const approveBtn = within(drawer).getByRole('button', { name: /Approve/i });
    fireEvent.click(approveBtn);

    await waitFor(() => {
      expect(onSend).toHaveBeenCalledWith('df -h');
    });

    // Input should be cleared upon approved execution
    expect(textarea.value).toBe('');
  });
});
