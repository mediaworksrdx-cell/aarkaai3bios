'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { createPortal } from 'react-dom';
import {
  SquareTerminal,
  FileCode2,
  TrendingUp,
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
  /** 'inline' (default): renders in normal DOM flow above the input field.
   *  'portal': renders as a fixed viewport overlay via createPortal (legacy). */
  anchorMode?: 'inline' | 'portal';
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
    let summary = request.human_summary.trim();
    // Sanitize any legacy "Master of Technology" text
    summary = summary.replace(/Master\s+of\s+Technology\s*/gi, '');
    if (/^allow run /i.test(summary)) {
      return summary.endsWith('?') ? summary : `${summary}?`;
    }
    if (/^allow select /i.test(summary)) {
      const clean = summary.replace(/^allow select\s+/i, 'Select ');
      return clean.endsWith('?') ? clean : `${clean}?`;
    }
    if (/^select /i.test(summary)) {
      return summary.endsWith('?') ? summary : `${summary}?`;
    }
    if (/^what strategy/i.test(summary)) {
      return summary.endsWith('?') ? summary : `${summary}?`;
    }
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
      return `Allow modify file: ${cleanPath}?`;
    }
    if (summary.toLowerCase().startsWith('allow modify ')) {
      if (!summary.toLowerCase().includes('file:')) {
        const clean = summary.replace(/^allow modify\s*/i, '');
        return `Allow modify file: ${clean.endsWith('?') ? clean : clean + '?'}`;
      }
      return summary.endsWith('?') ? summary : `${summary}?`;
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
    return cmd ? `Allow run ${cmd}?` : 'Allow run command?';
  }

  if (request.tool_name === 'FileEditTool') {
    return path ? `Allow modify file: ${path}?` : 'Allow modify file?';
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
  anchorMode = 'inline',
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
  const rawArgs = request.arguments || (request as any).args || {};
  const isFinanceStrategy = request.tool_name === 'FinanceStrategyMasterSelection' ||
    Boolean(rawArgs?.candidates && Array.isArray(rawArgs.candidates));
  const strategyData = rawArgs as FinanceStrategyApprovalData;
  const candidates: CandidateFinanceStrategy[] = strategyData.candidates || [];

  const [selectedCandidateId, setSelectedCandidateId] = useState<string>(() => {
    return strategyData.master_recommended || candidates[0]?.candidate_id || '';
  });

  const actionCommand = String(rawArgs.command || request.command_preview || '');
  const targetResource = String(request.target_resource || rawArgs.path || '');
  const actionTarget = actionCommand || targetResource || (rawArgs ? JSON.stringify(rawArgs) : request.tool_name);

  // Dynamic or synthesized options
  const baseOptions: DynamicApprovalOption[] =
    request.dynamic_options && request.dynamic_options.length > 0
      ? request.dynamic_options
      : synthesizeOptions(request, actionTarget);

  const dynamicOptions = useMemo(() => {
    if (!isFinanceStrategy || !selectedCandidateId) return baseOptions;
    const currentSelected = candidates.find((c) => c.candidate_id === selectedCandidateId) || candidates[0];
    if (!currentSelected) return baseOptions;
    return baseOptions.map((opt) => {
      if (opt.id === 1) {
        return {
          ...opt,
          label: `Execute Strategy (${currentSelected.strategy_name})`,
          detail: `Optimal win rate: ${currentSelected.win_rate_est || '74%'} • Max loss: ${currentSelected.max_loss_per_lot || '$1,500'}.`,
        };
      }
      return opt;
    });
  }, [baseOptions, isFinanceStrategy, selectedCandidateId, candidates]);

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

  // Live countdown timer
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

    if (decision === 'deny') {
      // Immediate clean dismissal on skip/cancel so user is never locked out
      setStatus('rejected');
      setIsDismissed(true);
      if (effectiveDismiss) effectiveDismiss();
      if (effectiveResolve) {
        effectiveResolve(
          request.approval_id,
          'deny',
          reason,
          isFinanceStrategy ? selectedCandidateId : undefined
        ).catch(() => {});
      }
      return;
    }

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
      setStatus('approved');
      setTimeout(() => {
        setIsDismissed(true);
        if (effectiveDismiss) effectiveDismiss();
      }, 400);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to record authorization decision';
      setErrorMessage(msg);
      setIsSubmitting(false);
      // Ensure drawer dismisses anyway so user can continue
      setTimeout(() => {
        setIsDismissed(true);
        if (effectiveDismiss) effectiveDismiss();
      }, 500);
    }
  };

  const handleSubmitOption = async () => {
    const activeOpt = dynamicOptions.find((o) => o.id === selectedOption) || dynamicOptions[0];

    if (selectedOption === 5 || activeOpt?.action === 'deny') {
      await handleDecision('deny', rejectionReason || 'Rejected by user');
      return;
    }

    if (activeOpt?.action === 'customize') {
      // Return to text field to edit parameters
      await handleDecision('deny', 'Edit parameters requested');
      return;
    }

    if (isFinanceStrategy && (selectedOption === 2 || activeOpt?.action === 'select_alternative') && candidates[1]) {
      const cand2 = candidates[1];
      setSelectedCandidateId(cand2.candidate_id);
      if (effectiveResolve) {
        await effectiveResolve(request.approval_id, 'approve', undefined, cand2.candidate_id);
      }
      setStatus('approved');
      setTimeout(() => {
        setIsDismissed(true);
        if (effectiveDismiss) effectiveDismiss();
      }, 400);
      return;
    }

    if (
      activeOpt?.action === 'always_allow' ||
      activeOpt?.action === 'allow_in_conversation' ||
      activeOpt?.action === 'allow_in_project' ||
      (!isFinanceStrategy && (selectedOption === 2 || selectedOption === 3 || selectedOption === 4))
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

  // ── Inline anchor mode: render directly in the DOM flow ──
  const isInline = anchorMode === 'inline';

  // Wrapper for portal vs inline rendering
  const renderWrapper = (children: React.ReactNode) => {
    if (!isInline && typeof document !== 'undefined' && mounted && document.body) {
      return createPortal(children, document.body);
    }
    return children;
  };

  // ── Feedback states ──

  if (status === 'approved') {
    const feedbackContent = (
      <div
        className={
          isInline
            ? `w-full mb-2 animate-emerge ${className}`
            : `fixed inset-0 z-[9999] flex flex-col justify-end items-center pb-24 sm:pb-28 px-4 bg-black/15 dark:bg-black/35 backdrop-blur-[1px] transition-all duration-200 ${className}`
        }
        data-testid="floating-approval-drawer"
      >
        <div
          className={
            isInline
              ? 'flex items-center gap-3 px-5 py-3.5 rounded-2xl border border-emerald-500/25 bg-[var(--bg-secondary)] shadow-[var(--shadow-md)] text-emerald-600 text-sm font-medium w-full'
              : 'flex items-center gap-3 px-6 py-4 rounded-2xl border border-emerald-500/30 bg-white dark:bg-[#18181b] shadow-2xl text-emerald-600 dark:text-emerald-400 text-sm font-medium animate-in fade-in max-w-xl w-full mb-2'
          }
        >
          <CheckCircle2 className="w-5 h-5 text-emerald-500 flex-shrink-0" />
          <span className="truncate">Allowed. Executing in workspace...</span>
        </div>
      </div>
    );
    return renderWrapper(feedbackContent);
  }

  if (status === 'rejected') {
    const feedbackContent = (
      <div
        className={
          isInline
            ? `w-full mb-2 animate-emerge ${className}`
            : `fixed inset-0 z-[9999] flex flex-col justify-end items-center pb-24 sm:pb-28 px-4 bg-black/15 dark:bg-black/35 backdrop-blur-[1px] transition-all duration-200 ${className}`
        }
        data-testid="floating-approval-drawer"
      >
        <div
          className={
            isInline
              ? 'flex items-center gap-3 px-5 py-3.5 rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] shadow-[var(--shadow-md)] text-[var(--text-secondary)] text-sm font-medium w-full'
              : 'flex items-center gap-3 px-6 py-4 rounded-2xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-[#18181b] shadow-2xl text-neutral-700 dark:text-neutral-300 text-sm font-medium animate-in fade-in max-w-xl w-full mb-2'
          }
        >
          <ShieldX className="w-5 h-5 text-[var(--text-tertiary)] flex-shrink-0" />
          <span>Execution skipped. Returning to input...</span>
        </div>
      </div>
    );
    return renderWrapper(feedbackContent);
  }

  if (status !== 'pending' && !isSubmitting) {
    return null;
  }

  // ── Main pending approval card ──

  const cardContent = (
    <div
      className={
        isInline
          ? `w-full mb-2 animate-emerge ${className}`
          : `fixed inset-0 z-[9999] flex flex-col justify-end items-center pb-24 sm:pb-28 px-4 bg-black/15 dark:bg-black/35 backdrop-blur-[1px] transition-all duration-200 animate-in fade-in ${className}`
      }
      data-testid="floating-approval-drawer"
      role="dialog"
      aria-modal={!isInline}
      aria-labelledby="approval-modal-title"
      {...(!isInline && {
        onClick: (e: React.MouseEvent) => {
          if (e.target === e.currentTarget) {
            handleDecision('deny');
          }
        },
      })}
    >
      <div
        className={
          isInline
            ? 'relative w-full rounded-2xl border border-[var(--border)] focus-within:border-[var(--border-accent)] bg-[var(--bg-secondary)] text-[var(--text-primary)] shadow-[var(--shadow-float)] p-5 sm:p-6 flex flex-col gap-3.5 transition-shadow duration-200'
            : 'relative w-full max-w-2xl rounded-2xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-[#18181b] text-neutral-900 dark:text-neutral-100 shadow-2xl shadow-black/10 p-6 sm:p-7 flex flex-col gap-4 animate-in slide-in-from-bottom-4 zoom-in-95 duration-150 mb-2'
        }
      >
        {/* Title Row */}
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2.5 min-w-0">
            {request.tool_name === 'FileEditTool' ? (
              <FileCode2 className="w-4 h-4 text-blue-500 flex-shrink-0 stroke-[2]" />
            ) : request.tool_name === 'FinanceStrategyMasterSelection' ? (
              <TrendingUp className="w-4 h-4 text-emerald-500 flex-shrink-0 stroke-[2]" />
            ) : (
              <SquareTerminal
                className={
                  isInline
                    ? 'w-4 h-4 text-[var(--text-secondary)] flex-shrink-0 stroke-[2]'
                    : 'w-4 h-4 text-neutral-600 dark:text-neutral-400 flex-shrink-0 stroke-[2]'
                }
              />
            )}
            <h3
              id="approval-modal-title"
              className={
                isInline
                  ? 'text-sm sm:text-base font-semibold text-[var(--text-primary)] leading-none truncate'
                  : 'text-sm sm:text-base font-semibold text-neutral-900 dark:text-neutral-100 leading-none truncate'
              }
            >
              {humanTitle}
            </h3>
          </div>

          {/* Badges: Persona Badge & Tool Badge */}
          <div className="flex items-center gap-1.5 flex-shrink-0">
            {request.model_persona?.badge && (
              <span
                className={`text-[10px] font-medium px-2 py-0.5 rounded-full border ${
                  request.model_persona.badge_color ||
                  (request.model_persona.provider === 'claude'
                    ? 'border-amber-500/40 bg-amber-500/15 text-amber-700 dark:text-amber-400'
                    : 'border-emerald-500/40 bg-emerald-500/10 text-emerald-700 dark:text-emerald-400')
                }`}
              >
                {request.model_persona.badge}
              </span>
            )}
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[var(--bg-tertiary)] text-[var(--text-tertiary)] border border-[var(--border)]">
              {request.tool_name}
            </span>
          </div>
        </div>

        {/* Command / Target Box */}
        <div
          className={
            isInline
              ? 'w-full bg-[var(--bg-tertiary)] rounded-xl px-4 py-3 font-mono text-[13px] text-[var(--text-primary)] select-all overflow-x-auto whitespace-pre-wrap break-all'
              : 'w-full bg-[#f4f4f5] dark:bg-neutral-800/80 rounded-xl px-4 py-3 font-mono text-[13px] text-neutral-800 dark:text-neutral-200 select-all overflow-x-auto whitespace-pre-wrap break-all'
          }
        >
          {actionTarget}
        </div>

        {/* Finance Strategy Candidates (if applicable) */}
        {isFinanceStrategy && candidates.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 my-1">
            {candidates.map((cand) => {
              const isSelected = cand.candidate_id === selectedCandidateId;
              const isMaster = cand.candidate_id === strategyData.master_recommended;

              const tag = (cand.technology_tag || cand.strategy_type || '').toUpperCase();
              let regimeBadge = 'border-slate-500/30 bg-slate-500/10 text-slate-400';
              if (tag.includes('BULL')) {
                regimeBadge = 'border-emerald-500/40 bg-emerald-500/15 text-emerald-600 dark:text-emerald-400';
              } else if (tag.includes('BEAR')) {
                regimeBadge = 'border-rose-500/40 bg-rose-500/15 text-rose-600 dark:text-rose-400';
              } else if (tag.includes('NEUTRAL') || tag.includes('VOLATILITY') || tag.includes('DELTA') || tag.includes('GRID')) {
                regimeBadge = 'border-blue-500/40 bg-blue-500/15 text-blue-600 dark:text-blue-400';
              } else if (tag.includes('REVERSAL') || tag.includes('EXHAUSTION') || tag.includes('SWEEP') || tag.includes('PIVOT')) {
                regimeBadge = 'border-purple-500/40 bg-purple-500/15 text-purple-600 dark:text-purple-400';
              }

              return (
                <div
                  key={cand.candidate_id}
                  onClick={() => setSelectedCandidateId(cand.candidate_id)}
                  className={`p-3 rounded-xl border transition-all cursor-pointer text-left ${
                    isSelected
                      ? isInline
                        ? 'bg-[var(--bg-tertiary)] border-[var(--border-accent)] ring-1 ring-[var(--border-accent)] shadow-sm'
                        : 'bg-neutral-100 dark:bg-neutral-800 border-neutral-400 dark:border-neutral-500 ring-1 ring-neutral-400 shadow-sm'
                      : isInline
                        ? 'bg-[var(--bg-secondary)] border-[var(--border)] hover:bg-[var(--bg-hover)]'
                        : 'bg-white dark:bg-neutral-900 border-neutral-200 dark:border-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-800/50'
                  }`}
                >
                  <div className="flex items-center justify-between gap-1 mb-1">
                    <span
                      className={
                        isInline
                          ? 'text-xs font-bold text-[var(--text-primary)]'
                          : 'text-xs font-bold text-neutral-900 dark:text-neutral-100'
                      }
                    >
                      {cand.strategy_name}
                    </span>
                    <div className="flex items-center gap-1">
                      {isMaster && (
                        <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-800 dark:text-amber-400 border border-amber-500/40">
                          ★ RECOMMENDED
                        </span>
                      )}
                      {isSelected && (
                        <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-700 dark:text-emerald-400 border border-emerald-500/40">
                          ✓ SELECTED
                        </span>
                      )}
                    </div>
                  </div>
                  {cand.technology_tag && (
                    <div className="mb-1.5">
                      <span className={`text-[9px] font-semibold font-mono px-1.5 py-0.5 rounded border ${regimeBadge}`}>
                        {cand.technology_tag}
                      </span>
                    </div>
                  )}
                  <div
                    className={
                      isInline
                        ? 'grid grid-cols-3 gap-1 text-[10px] font-mono pt-1 text-[var(--text-tertiary)]'
                        : 'grid grid-cols-3 gap-1 text-[10px] font-mono pt-1 text-neutral-500 dark:text-neutral-400'
                    }
                  >
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
                    ? isInline
                      ? 'bg-[var(--accent-muted)] border border-[var(--border-accent)] text-[var(--text-primary)] font-medium'
                      : 'bg-[#ececed] dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100 font-medium'
                    : isInline
                      ? 'text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] border border-transparent'
                      : 'text-neutral-700 dark:text-neutral-300 hover:bg-[#f4f4f5] dark:hover:bg-neutral-800/50'
                }`}
              >
                <span
                  className={
                    isInline
                      ? 'w-5 h-5 rounded flex items-center justify-center text-xs font-semibold text-[var(--text-secondary)] bg-[var(--bg-tertiary)] flex-shrink-0'
                      : 'w-5 h-5 rounded flex items-center justify-center text-xs font-semibold text-neutral-600 dark:text-neutral-400 bg-[#e4e4e7] dark:bg-neutral-700 flex-shrink-0'
                  }
                >
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
          <div className="pl-8 -mt-0.5">
            <input
              type="text"
              value={rejectionReason}
              onChange={(e) => setRejectionReason(e.target.value)}
              placeholder="tell the agent what to do instead..."
              className={
                isInline
                  ? 'w-full px-3.5 py-2 text-sm bg-[var(--bg-input)] border border-[var(--border)] rounded-xl text-[var(--text-primary)] outline-none focus:border-[var(--border-accent)] focus:ring-1 focus:ring-[var(--accent-primary)] transition-colors'
                  : 'w-full px-3.5 py-2 text-sm bg-neutral-50 dark:bg-neutral-900 border border-neutral-300 dark:border-neutral-700 rounded-xl text-neutral-900 dark:text-neutral-100 outline-none focus:border-[#0070f3] focus:ring-1 focus:ring-[#0070f3]'
              }
              autoFocus
            />
          </div>
        )}

        {/* Error notification if submission fails */}
        {errorMessage && (
          <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-xs text-red-600 dark:text-red-400">
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
            className={
              isInline
                ? 'text-[var(--text-tertiary)] hover:text-[var(--text-primary)] text-sm font-medium px-4 py-2 cursor-pointer transition-colors disabled:opacity-50'
                : 'text-neutral-500 hover:text-neutral-800 dark:text-neutral-400 dark:hover:text-neutral-200 text-sm font-medium px-4 py-2 cursor-pointer transition-colors disabled:opacity-50'
            }
          >
            Skip
          </button>

          <button
            onClick={handleSubmitOption}
            disabled={isSubmitting}
            type="button"
            aria-label="Approve"
            name="Approve"
            className={
              isInline
                ? 'flex items-center gap-1.5 px-5 py-2 text-sm font-medium rounded-xl bg-[var(--accent-primary)] hover:bg-[var(--accent-hover)] text-white shadow-sm transition-all active:scale-[0.98] cursor-pointer disabled:opacity-50'
                : 'flex items-center gap-1.5 px-5 py-2 text-sm font-medium rounded-xl bg-[#0070f3] hover:bg-[#0060df] text-white shadow-sm transition-all active:scale-[0.98] cursor-pointer disabled:opacity-50'
            }
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

  return renderWrapper(cardContent);
}
