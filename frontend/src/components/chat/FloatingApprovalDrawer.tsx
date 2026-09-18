'use client';

import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import {
  SquareTerminal,
  CheckCircle2,
  ShieldX,
  Loader2,
} from 'lucide-react';
import {
  ToolApprovalRequest,
  ApprovalStatus,
  FinanceStrategyApprovalData,
  CandidateFinanceStrategy,
  DynamicApprovalOption,
} from '@/types';
import { useChatContext } from '@/context/ChatContext';

interface FloatingApprovalDrawerProps {
  request: ToolApprovalRequest;
  onResolve?: (approvalId: string, decision: 'approve' | 'deny', reason?: string, selectedMasterStrategy?: string) => Promise<void>;
  onAlwaysAllow?: (toolName: string) => void;
  onDismiss?: () => void;
  className?: string;
}

function normalizeStatus(s?: string): ApprovalStatus {
  const norm = (s || 'pending').toLowerCase();
  if (norm === 'approved' || norm === 'approve') return 'approved';
  if (norm === 'rejected' || norm === 'reject' || norm === 'deny' || norm === 'denied') return 'rejected';
  if (norm === 'timeout' || norm === 'expired') return 'timeout';
  return 'pending';
}

function getHumanTitle(request: ToolApprovalRequest): string {
  const cmd = String(request.arguments?.command || request.command_preview || '').trim();
  const path = String(request.arguments?.path || request.target_resource || '').trim();

  if (request.human_summary) {
    const summary = request.human_summary.trim();
    if (/^execute shell command:\s*pytest/i.test(summary) || /^pytest/i.test(cmd)) {
      if (cmd.includes('unit')) {
        return 'Allow run backend unit tests?';
      }
      return 'Allow run unit tests?';
    }
    if (summary.toLowerCase().startsWith('execute shell command:')) {
      const cleanCmd = summary.replace(/^execute shell command:\s*/i, '');
      return `Allow run ${cleanCmd}?`;
    }
    if (summary.toLowerCase().startsWith('modify file:')) {
      const cleanPath = summary.replace(/^modify file:\s*/i, '');
      return `Allow modify ${cleanPath}?`;
    }
    if (summary.toLowerCase().startsWith('allow ')) {
      return summary.endsWith('?') ? summary : `${summary}?`;
    }
    return `Allow ${summary}?`;
  }

  if (request.tool_name === 'BashTool') {
    if (/pytest/i.test(cmd)) {
      if (cmd.includes('unit')) {
        return 'Allow run backend unit tests?';
      }
      return 'Allow run unit tests?';
    }
    return cmd ? `Allow run ${cmd.length > 35 ? cmd.slice(0, 35) + '...' : cmd}?` : 'Allow run command?';
  }

  if (request.tool_name === 'FileEditTool') {
    return path ? `Allow modify ${path}?` : 'Allow modify file?';
  }

  return `Allow ${request.tool_name}?`;
}

function synthesizeOptions(
  request: ToolApprovalRequest,
  actionTarget: string
): DynamicApprovalOption[] {
  const agent = request.model_persona?.agent_ref || 'the agent';
  const targetLabel = actionTarget || 'this operation';

  return [
    {
      id: 1,
      action: 'allow_once',
      label: 'Yes, allow this time',
      recommended: true,
    },
    {
      id: 2,
      action: 'allow_in_conversation',
      label: `Yes, and always allow '${targetLabel}' in this conversation`,
    },
    {
      id: 3,
      action: 'allow_in_project',
      label: `Yes, and always allow '${targetLabel}' in this project`,
    },
    {
      id: 4,
      action: 'always_allow',
      label: `Yes, and always allow '${targetLabel}'`,
    },
    {
      id: 5,
      action: 'deny',
      label: `No (tell ${agent} what to do instead)`,
    },
  ];
}

export function FloatingApprovalDrawer({
  request,
  onResolve,
  onAlwaysAllow,
  onDismiss,
  className = '',
}: FloatingApprovalDrawerProps) {
  const { resolveApproval: contextResolve, alwaysAllowTool: contextAlwaysAllow, dismissActiveApproval } = useChatContext();
  const effectiveResolve = onResolve || contextResolve;
  const effectiveAlwaysAllow = onAlwaysAllow || contextAlwaysAllow;
  const effectiveDismiss = onDismiss || dismissActiveApproval;

  const [mounted, setMounted] = useState<boolean>(false);
  const [status, setStatus] = useState<ApprovalStatus>(() => normalizeStatus(request.status));
  const totalTimeout = request.timeout_seconds || 120;
  const [remainingSeconds, setRemainingSeconds] = useState<number>(() => {
    const rawCreatedAt = request.created_at || Date.now();
    const createdAtMs = rawCreatedAt < 1e11 ? rawCreatedAt * 1000 : rawCreatedAt;
    const elapsed = Math.floor((Date.now() - createdAtMs) / 1000);
    return Math.max(0, totalTimeout - elapsed);
  });

  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isDismissed, setIsDismissed] = useState<boolean>(false);
  const [selectedOption, setSelectedOption] = useState<number>(1);
  const [rejectionReason, setRejectionReason] = useState<string>('');

  useEffect(() => {
    setMounted(true);
  }, []);

  // Finance strategy selection support
  const isFinanceStrategy = request.tool_name === 'FinanceStrategyMasterSelection' ||
    Boolean(request.arguments?.candidates && Array.isArray(request.arguments.candidates));
  const strategyData = (request.arguments || {}) as FinanceStrategyApprovalData;
  const candidates: CandidateFinanceStrategy[] = strategyData.candidates || [];

  const [selectedCandidateId, setSelectedCandidateId] = useState<string>(() => {
    return strategyData.master_recommended || candidates[0]?.candidate_id || '';
  });

  const actionCommand = String(request.arguments?.command || request.command_preview || '');
  const targetResource = String(request.target_resource || request.arguments?.path || '');
  const actionTarget = actionCommand || targetResource || (request.arguments ? JSON.stringify(request.arguments) : request.tool_name);

  // Dynamic or synthesized options
  const dynamicOptions: DynamicApprovalOption[] =
    request.dynamic_options && request.dynamic_options.length > 0
      ? request.dynamic_options
      : synthesizeOptions(request, actionTarget);

  const humanTitle = getHumanTitle(request);

  // Synchronize when request.status updates
  useEffect(() => {
    if (request.status) {
      const nextStatus = normalizeStatus(request.status);
      if (nextStatus !== status) {
        setStatus(nextStatus);
      }
    }
  }, [request.status, status]);

  // Live countdown timer (runs in background for automatic timeout expiry)
  useEffect(() => {
    if (status !== 'pending' || remainingSeconds <= 0) return;

    const timer = setInterval(() => {
      setRemainingSeconds((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          setStatus('timeout');
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [status, remainingSeconds]);

  const handleDecision = async (decision: 'approve' | 'deny', reason?: string) => {
    if (status !== 'pending' || isSubmitting) return;

    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      if (effectiveResolve) {
        await effectiveResolve(
          request.approval_id,
          decision,
          reason,
          isFinanceStrategy ? selectedCandidateId : undefined
        );
      }
      setStatus(decision === 'approve' ? 'approved' : 'rejected');
      setTimeout(() => {
        setIsDismissed(true);
        if (effectiveDismiss) effectiveDismiss();
      }, 700);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to record authorization decision';
      setErrorMessage(msg);
      setIsSubmitting(false);
    }
  };

  const handleSubmitOption = async () => {
    const activeOpt = dynamicOptions.find((o) => o.id === selectedOption) || dynamicOptions[0];

    if (selectedOption === 5 || activeOpt?.action === 'deny') {
      await handleDecision('deny', rejectionReason || 'Rejected by user');
      return;
    }

    if (
      selectedOption === 2 ||
      selectedOption === 3 ||
      selectedOption === 4 ||
      activeOpt?.action === 'always_allow' ||
      activeOpt?.action === 'allow_in_conversation' ||
      activeOpt?.action === 'allow_in_project'
    ) {
      if (effectiveAlwaysAllow) effectiveAlwaysAllow(request.tool_name);
    }

    await handleDecision('approve');
  };

  // Keyboard shortcut listener: 1-5 to select, Enter to submit, Esc to skip
  useEffect(() => {
    if (status !== 'pending' || isSubmitting) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        if (e.key === 'Enter') {
          e.preventDefault();
          handleSubmitOption();
        }
        return;
      }

      if (e.key === '1') setSelectedOption(1);
      else if (e.key === '2') setSelectedOption(2);
      else if (e.key === '3') setSelectedOption(3);
      else if (e.key === '4') setSelectedOption(4);
      else if (e.key === '5') setSelectedOption(5);
      else if (e.key === 'Enter') {
        e.preventDefault();
        handleSubmitOption();
      } else if (e.key === 'Escape') {
        e.preventDefault();
        handleDecision('deny');
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [status, isSubmitting, selectedOption, rejectionReason, selectedCandidateId, dynamicOptions]);

  if (isDismissed) {
    return null;
  }

  const renderPortalOrContent = (children: React.ReactNode) => {
    if (typeof document !== 'undefined' && mounted && document.body) {
      return createPortal(children, document.body);
    }
    return children;
  };

  // Feedback states
  if (status === 'approved') {
    return renderPortalOrContent(
      <div
        className={`fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black/20 dark:bg-black/40 backdrop-blur-[2px] transition-all duration-200 ${className}`}
        data-testid="floating-approval-drawer"
      >
        <div className="flex items-center gap-3 px-6 py-4 rounded-2xl border border-emerald-500/30 bg-white dark:bg-[#18181b] shadow-xl text-emerald-600 dark:text-emerald-400 text-sm font-medium animate-in fade-in max-w-md w-full">
          <CheckCircle2 className="w-5 h-5 text-emerald-500 flex-shrink-0" />
          <span className="truncate">Allowed. Executing in workspace...</span>
        </div>
      </div>
    );
  }

  if (status === 'rejected') {
    return renderPortalOrContent(
      <div
        className={`fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black/20 dark:bg-black/40 backdrop-blur-[2px] transition-all duration-200 ${className}`}
        data-testid="floating-approval-drawer"
      >
        <div className="flex items-center gap-3 px-6 py-4 rounded-2xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-[#18181b] shadow-xl text-neutral-700 dark:text-neutral-300 text-sm font-medium animate-in fade-in max-w-md w-full">
          <ShieldX className="w-5 h-5 text-neutral-500 flex-shrink-0" />
          <span>Execution skipped. Workspace unchanged.</span>
        </div>
      </div>
    );
  }

  if (status !== 'pending' && !isSubmitting) {
    return null;
  }

  return renderPortalOrContent(
    <div
      className={`fixed inset-0 z-[9999] flex items-center justify-center p-4 sm:p-6 bg-black/20 dark:bg-black/40 backdrop-blur-[2px] transition-all duration-200 animate-in fade-in ${className}`}
      data-testid="floating-approval-drawer"
      role="dialog"
      aria-modal="true"
      aria-labelledby="approval-modal-title"
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          handleDecision('deny');
        }
      }}
    >
      <div className="relative w-full max-w-2xl rounded-2xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-[#18181b] text-neutral-900 dark:text-neutral-100 shadow-xl shadow-black/5 p-6 sm:p-7 flex flex-col gap-4 animate-in zoom-in-95 duration-150">
        
        {/* Title Row */}
        <div className="flex items-center gap-2.5">
          <SquareTerminal className="w-4 h-4 text-neutral-600 dark:text-neutral-400 flex-shrink-0 stroke-[2]" />
          <h3 id="approval-modal-title" className="text-sm sm:text-base font-semibold text-neutral-900 dark:text-neutral-100 leading-none">
            {humanTitle}
          </h3>
        </div>

        {/* Command / Target Box */}
        <div className="w-full bg-[#f4f4f5] dark:bg-neutral-800/80 rounded-xl px-4 py-3 font-mono text-[13px] text-neutral-800 dark:text-neutral-200 select-all overflow-x-auto whitespace-pre-wrap break-all">
          {actionTarget}
        </div>

        {/* Finance Strategy Candidates (if applicable) */}
        {isFinanceStrategy && candidates.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 my-1">
            {candidates.map((cand) => {
              const isSelected = cand.candidate_id === selectedCandidateId;
              const isMaster = cand.candidate_id === strategyData.master_recommended;

              return (
                <div
                  key={cand.candidate_id}
                  onClick={() => setSelectedCandidateId(cand.candidate_id)}
                  className={`p-3 rounded-xl border transition-all cursor-pointer text-left ${
                    isSelected
                      ? 'bg-neutral-100 dark:bg-neutral-800 border-neutral-400 dark:border-neutral-600 shadow-sm'
                      : 'bg-white dark:bg-neutral-900 border-neutral-200 dark:border-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-800/50'
                  }`}
                >
                  <div className="flex items-center justify-between gap-1 mb-1">
                    <span className="text-xs font-bold text-neutral-900 dark:text-neutral-100">
                      {cand.strategy_name}
                    </span>
                    {isMaster && (
                      <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-800 dark:text-amber-400 border border-amber-500/40">
                        ★ RECOMMENDED
                      </span>
                    )}
                  </div>
                  <div className="grid grid-cols-3 gap-1 text-[10px] font-mono pt-1 text-neutral-500 dark:text-neutral-400">
                    <div>Win: {cand.win_rate_est || '70%'}</div>
                    <div>R:R: {cand.risk_reward_actual || '1:2.4'}</div>
                    <div>Risk: {cand.max_loss_per_lot || '₹2,500'}</div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* 5 Options List */}
        <div className="flex flex-col gap-1.5" role="radiogroup">
          {dynamicOptions.map((opt) => {
            const isSelected = selectedOption === opt.id;
            return (
              <div
                key={opt.id}
                role="radio"
                aria-checked={isSelected}
                tabIndex={0}
                onClick={() => setSelectedOption(opt.id)}
                className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl cursor-pointer select-none transition-colors text-sm ${
                  isSelected
                    ? 'bg-[#ececed] dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100 font-medium'
                    : 'text-neutral-700 dark:text-neutral-300 hover:bg-[#f4f4f5] dark:hover:bg-neutral-800/50'
                }`}
              >
                <span className="w-5 h-5 rounded flex items-center justify-center text-xs font-semibold text-neutral-600 dark:text-neutral-400 bg-[#e4e4e7] dark:bg-neutral-700 flex-shrink-0">
                  {opt.id}
                </span>
                <span className="truncate flex-1">
                  {opt.label}
                </span>
              </div>
            );
          })}
        </div>

        {/* Option 5: Rejection Reason Input */}
        {selectedOption === 5 && (
          <div className="pl-8 -mt-0.5 animate-in fade-in duration-150">
            <input
              type="text"
              value={rejectionReason}
              onChange={(e) => setRejectionReason(e.target.value)}
              placeholder="tell the agent what to do instead..."
              className="w-full px-3.5 py-2 text-sm bg-neutral-50 dark:bg-neutral-900 border border-neutral-300 dark:border-neutral-700 rounded-xl text-neutral-900 dark:text-neutral-100 outline-none focus:border-[#0070f3] focus:ring-1 focus:ring-[#0070f3]"
              autoFocus
            />
          </div>
        )}

        {/* Error notification if submission fails */}
        {errorMessage && (
          <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-xs text-red-600 dark:text-red-400 animate-in fade-in">
            {errorMessage}
          </div>
        )}

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 pt-2 mt-1">
          <button
            onClick={() => handleDecision('deny')}
            disabled={isSubmitting}
            type="button"
            aria-label="Deny"
            name="Deny"
            className="text-neutral-500 hover:text-neutral-800 dark:text-neutral-400 dark:hover:text-neutral-200 text-sm font-medium px-4 py-2 cursor-pointer transition-colors disabled:opacity-50"
          >
            Skip
          </button>

          <button
            onClick={handleSubmitOption}
            disabled={isSubmitting}
            type="button"
            aria-label="Approve"
            name="Approve"
            className="flex items-center gap-1.5 px-5 py-2 text-sm font-medium rounded-xl bg-[#0070f3] hover:bg-[#0060df] text-white shadow-sm transition-all active:scale-[0.98] cursor-pointer disabled:opacity-50"
          >
            {isSubmitting ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : null}
            <span>Submit</span>
            <span className="text-xs font-mono">↵</span>
          </button>
        </div>

      </div>
    </div>
  );
}
