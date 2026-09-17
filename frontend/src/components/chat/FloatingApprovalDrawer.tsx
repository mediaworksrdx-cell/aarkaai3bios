'use client';

import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  ShieldCheck,
  ShieldX,
  Clock,
  Check,
  Terminal,
  AlertTriangle,
  FileCode,
  TrendingUp,
  Sliders,
  Loader2,
  CheckCircle2,
  Sparkles,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import {
  ToolApprovalRequest,
  RiskLevel,
  ApprovalStatus,
  FinanceStrategyApprovalData,
  CandidateFinanceStrategy,
} from '@/types';
import { useChatContext } from '@/context/ChatContext';

interface FloatingApprovalDrawerProps {
  request: ToolApprovalRequest;
  onResolve?: (approvalId: string, decision: 'approve' | 'deny', reason?: string, selectedMasterStrategy?: string) => Promise<void>;
  onAlwaysAllow?: (toolName: string) => void;
  onDismiss?: () => void;
  className?: string;
}

const RISK_CONFIG: Record<
  RiskLevel,
  { label: string; badgeBg: string; text: string; border: string; icon: React.ComponentType<{ className?: string }> }
> = {
  critical: {
    label: 'Critical Risk',
    badgeBg: 'bg-red-500/15',
    text: 'text-red-400',
    border: 'border-red-500/40',
    icon: AlertTriangle,
  },
  high: {
    label: 'High Risk',
    badgeBg: 'bg-amber-500/15',
    text: 'text-amber-400',
    border: 'border-amber-500/40',
    icon: AlertTriangle,
  },
  medium: {
    label: 'Medium Risk',
    badgeBg: 'bg-yellow-500/15',
    text: 'text-yellow-400',
    border: 'border-yellow-500/40',
    icon: ShieldAlert,
  },
  low: {
    label: 'Low Risk',
    badgeBg: 'bg-blue-500/15',
    text: 'text-blue-400',
    border: 'border-blue-500/40',
    icon: ShieldAlert,
  },
  read_only: {
    label: 'Read Only',
    badgeBg: 'bg-emerald-500/15',
    text: 'text-emerald-400',
    border: 'border-emerald-500/40',
    icon: ShieldCheck,
  },
};

function normalizeStatus(s?: string): ApprovalStatus {
  const norm = (s || 'pending').toLowerCase();
  if (norm === 'approved' || norm === 'approve') return 'approved';
  if (norm === 'rejected' || norm === 'reject' || norm === 'deny' || norm === 'denied') return 'rejected';
  if (norm === 'timeout' || norm === 'expired') return 'timeout';
  return 'pending';
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
  const [showCodePreview, setShowCodePreview] = useState<boolean>(false);
  const [isCustomizeOpen, setIsCustomizeOpen] = useState<boolean>(false);
  const [customArgsText, setCustomArgsText] = useState<string>(() => {
    try {
      if (request.arguments?.command) return String(request.arguments.command);
      return JSON.stringify(request.arguments || {}, null, 2);
    } catch {
      return '';
    }
  });

  // Check if this is a finance strategy approval
  const isFinanceStrategy = request.tool_name === 'FinanceStrategyMasterSelection' ||
    Boolean(request.arguments?.candidates && Array.isArray(request.arguments.candidates));
  const strategyData = (request.arguments || {}) as FinanceStrategyApprovalData;
  const candidates: CandidateFinanceStrategy[] = strategyData.candidates || [];

  const [selectedCandidateId, setSelectedCandidateId] = useState<string>(() => {
    return strategyData.master_recommended || candidates[0]?.candidate_id || '';
  });

  const risk = RISK_CONFIG[request.mutation_risk] || RISK_CONFIG.medium;
  const RiskIcon = risk.icon;

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

    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      const chosenStrategy = isFinanceStrategy ? selectedCandidateId : undefined;
      setStatus(decision === 'approve' ? 'approved' : 'rejected');
      await effectiveResolve(request.approval_id, decision, reason || rejectionReason || undefined, chosenStrategy);
      setTimeout(() => {
        setIsDismissed(true);
        effectiveDismiss();
      }, 350);
    } catch (err: any) {
      setErrorMessage(err?.message || 'Failed to submit approval decision. Please retry.');
      setIsSubmitting(false);
      setStatus('pending');
    }
  };

  const handleSubmitOption = async () => {
    if (status !== 'pending' || isSubmitting) return;

    if (selectedOption === 5) {
      await handleDecision('deny', rejectionReason);
    } else if (selectedOption === 2 || selectedOption === 3 || selectedOption === 4) {
      effectiveAlwaysAllow(request.tool_name);
      await handleDecision('approve');
    } else {
      await handleDecision('approve');
    }
  };

  // Global keyboard shortcuts (1-5 to select, Enter to Submit, Escape to Skip/Deny)
  useEffect(() => {
    if (status !== 'pending' || isSubmitting) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      const targetTag = (e.target as HTMLElement)?.tagName?.toLowerCase();
      if (targetTag === 'input' || targetTag === 'textarea') {
        if (e.key === 'Enter') {
          e.preventDefault();
          handleSubmitOption();
        } else if (e.key === 'Escape') {
          e.preventDefault();
          handleDecision('deny');
        }
        return;
      }

      if (e.key === '1') {
        setSelectedOption(1);
      } else if (e.key === '2') {
        setSelectedOption(2);
      } else if (e.key === '3') {
        setSelectedOption(3);
      } else if (e.key === '4') {
        setSelectedOption(4);
      } else if (e.key === '5') {
        setSelectedOption(5);
      } else if (e.key === 'Enter') {
        e.preventDefault();
        handleSubmitOption();
      } else if (e.key === 'Escape') {
        e.preventDefault();
        handleDecision('deny');
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [status, isSubmitting, selectedOption, rejectionReason, selectedCandidateId]);

  if (isDismissed) {
    return null;
  }

  // Quick feedback confirmation pill upon approval
  if (status === 'approved') {
    return (
      <div
        className={`w-full max-w-4xl mx-auto px-2 sm:px-4 mb-2 z-40 transition-all duration-300 ${className}`}
        data-testid="floating-approval-drawer"
      >
        <div className="flex items-center justify-between px-4 py-2.5 rounded-xl border border-emerald-500/40 bg-emerald-950/80 backdrop-blur-xl shadow-lg shadow-emerald-950/40 text-emerald-400 text-xs font-mono animate-in fade-in">
          <span className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 animate-pulse" />
            <span>Authorized <strong>{request.tool_name}</strong>. Executing in workspace...</span>
          </span>
          <Loader2 className="w-3.5 h-3.5 animate-spin text-emerald-400" />
        </div>
      </div>
    );
  }

  if (status === 'rejected') {
    return (
      <div
        className={`w-full max-w-4xl mx-auto px-2 sm:px-4 mb-2 z-40 transition-all duration-300 ${className}`}
        data-testid="floating-approval-drawer"
      >
        <div className="flex items-center gap-2 px-4 py-2.5 rounded-xl border border-red-500/40 bg-red-950/80 backdrop-blur-xl shadow-lg text-red-400 text-xs font-mono animate-in fade-in">
          <ShieldX className="w-4 h-4 text-red-400" />
          <span>Execution denied by operator.</span>
        </div>
      </div>
    );
  }

  if (status !== 'pending' && !isSubmitting) {
    return null;
  }

  // Human-readable action label for the question and options
  const actionCommand = String(request.arguments?.command || request.command_preview || '');
  const targetResource = String(request.target_resource || request.arguments?.path || '');
  const actionTarget = actionCommand || targetResource || request.tool_name;

  let humanTitle = `Allow ${request.tool_name}?`;
  if (request.tool_name === 'BashTool') {
    humanTitle = `Allow run command?`;
  } else if (request.tool_name === 'FileEditTool') {
    humanTitle = `Allow modify file: ${targetResource || 'script'}?`;
  } else if (request.human_summary) {
    humanTitle = `Allow ${request.human_summary}?`;
  }

  const options = [
    { id: 1, label: 'Yes, allow this time' },
    { id: 2, label: `Yes, and always allow '${actionTarget}' in this conversation` },
    { id: 3, label: `Yes, and always allow '${actionTarget}' in this project` },
    { id: 4, label: `Yes, and always allow '${actionTarget}' (Always Allow)` },
    { id: 5, label: 'No (tell the agent what to do instead)' },
  ];

  return (
    <div
      className={`w-full max-w-4xl mx-auto px-2 sm:px-4 mb-3 z-40 transition-all duration-300 animate-in slide-in-from-bottom-3 ${className}`}
      data-testid="floating-approval-drawer"
    >
      <div className="relative overflow-hidden rounded-2xl border border-[var(--border)]/90 bg-[var(--bg-secondary)]/98 backdrop-blur-2xl shadow-2xl shadow-black/40 ring-1 ring-white/10 p-4 sm:p-5 flex flex-col gap-3.5">
        
        {/* Title Header */}
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-7 h-7 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--border)] flex items-center justify-center flex-shrink-0 text-[var(--text-secondary)]">
              {isFinanceStrategy ? (
                <TrendingUp className="w-4 h-4 text-emerald-400" />
              ) : request.tool_name === 'BashTool' ? (
                <Terminal className="w-4 h-4 text-amber-400" />
              ) : request.tool_name === 'FileEditTool' ? (
                <FileCode className="w-4 h-4 text-blue-400" />
              ) : (
                <RiskIcon className={`w-4 h-4 ${risk.text}`} />
              )}
            </div>
            <h3 className="text-sm sm:text-base font-semibold text-[var(--text-primary)] truncate">
              {humanTitle}
            </h3>
          </div>

          <div className="flex items-center gap-2 flex-shrink-0">
            <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${risk.badgeBg} ${risk.text} ${risk.border}`}>
              {risk.label}
            </span>
            <div className="flex items-center gap-1 text-xs font-mono text-[var(--text-tertiary)]">
              <Clock className="w-3.5 h-3.5" />
              <span>{remainingSeconds}s</span>
            </div>
          </div>
        </div>

        {/* Error Notification */}
        {errorMessage && (
          <div className="p-2.5 rounded-xl bg-red-500/10 border border-red-500/30 text-xs text-red-400 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Command / Resource Box */}
        <div className="rounded-xl bg-[var(--bg-primary)]/90 border border-[var(--border)] p-2.5 sm:p-3 font-mono text-xs text-[var(--text-primary)] break-all select-all flex flex-col gap-1.5 shadow-inner">
          <div className="flex items-center justify-between gap-2 text-[11px] text-[var(--text-tertiary)] select-none">
            <span className="font-semibold text-[var(--text-secondary)]">{request.tool_name}</span>
            {request.diff_preview && (
              <button
                type="button"
                onClick={() => setShowCodePreview(!showCodePreview)}
                className="text-[11px] text-[var(--accent-primary)] hover:underline cursor-pointer flex items-center gap-1"
              >
                <span>{showCodePreview ? 'Hide Preview' : 'View Code Preview'}</span>
                {showCodePreview ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
              </button>
            )}
          </div>
          <div className="text-[var(--text-primary)]">
            {actionTarget}
          </div>
          {showCodePreview && request.diff_preview && (
            <pre className="mt-2 p-2 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] font-mono text-[11px] text-[var(--text-secondary)] max-h-36 overflow-y-auto whitespace-pre-wrap">
              {request.diff_preview}
            </pre>
          )}
        </div>

        {/* FINANCE STRATEGY: Master Candidate Selection (if applicable) */}
        {isFinanceStrategy && candidates.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs text-[var(--text-secondary)]">
              <span className="font-semibold flex items-center gap-1 text-emerald-400">
                <Sparkles className="w-3.5 h-3.5" /> Select Master Strategy:
              </span>
              <span className="text-[11px] font-mono text-[var(--text-tertiary)]">
                {strategyData.symbol} • Spot: ₹{strategyData.current_price?.toLocaleString() || 'N/A'}
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {candidates.map((cand) => {
                const isSelected = cand.candidate_id === selectedCandidateId;
                const isMaster = cand.candidate_id === strategyData.master_recommended;

                return (
                  <div
                    key={cand.candidate_id}
                    onClick={() => status === 'pending' && setSelectedCandidateId(cand.candidate_id)}
                    className={`p-2.5 rounded-xl border transition-all cursor-pointer text-left relative ${
                      isSelected
                        ? 'bg-emerald-500/10 border-emerald-500/50 shadow-md ring-1 ring-emerald-500/30'
                        : 'bg-[var(--bg-primary)]/60 border-[var(--border)] hover:border-[var(--border-hover)]'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-1 mb-1">
                      <span className="text-xs font-bold text-[var(--text-primary)]">
                        {cand.strategy_name}
                      </span>
                      {isMaster && (
                        <span className="text-[9px] font-semibold px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-400 border border-amber-500/40">
                          ★ RECOMMENDED
                        </span>
                      )}
                    </div>
                    <div className="grid grid-cols-3 gap-1 text-[10px] font-mono pt-1 text-[var(--text-secondary)]">
                      <div><span className="text-[var(--text-tertiary)] block">Win Rate</span>{cand.win_rate_est || '70%'}</div>
                      <div><span className="text-[var(--text-tertiary)] block">R:R</span>{cand.risk_reward_actual || '1:2.4'}</div>
                      <div><span className="text-[var(--text-tertiary)] block">Max Loss</span>{cand.max_loss_per_lot || '₹2,500'}</div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* 5 Numbered Claude Options List */}
        <div className="flex flex-col gap-1.5">
          {options.map((opt) => {
            const isSelected = selectedOption === opt.id;
            return (
              <div
                key={opt.id}
                onClick={() => setSelectedOption(opt.id)}
                className={`flex items-center gap-3 px-3 py-2 rounded-xl text-xs sm:text-sm cursor-pointer transition-all ${
                  isSelected
                    ? 'bg-[var(--accent-muted)] border border-[var(--border-accent)] font-medium text-[var(--text-primary)] shadow-sm ring-1 ring-[var(--border-accent)]/40'
                    : 'hover:bg-[var(--bg-tertiary)]/70 text-[var(--text-secondary)] border border-transparent'
                }`}
              >
                <span
                  className={`w-5 h-5 rounded-md flex items-center justify-center text-xs font-mono font-bold flex-shrink-0 transition-colors ${
                    isSelected
                      ? 'bg-[var(--accent-primary)] text-white shadow-sm'
                      : 'bg-[var(--bg-tertiary)] text-[var(--text-tertiary)]'
                  }`}
                >
                  {opt.id}
                </span>
                <span className="flex-1 truncate">{opt.label}</span>
                {isSelected && (
                  <Check className="w-3.5 h-3.5 text-[var(--accent-primary)] flex-shrink-0" />
                )}
              </div>
            );
          })}
        </div>

        {/* Option 5: Expandable Rejection Reason Input */}
        {selectedOption === 5 && (
          <div className="pl-8 -mt-1 animate-in fade-in">
            <input
              type="text"
              value={rejectionReason}
              onChange={(e) => setRejectionReason(e.target.value)}
              placeholder="tell the agent what to do instead..."
              className="w-full px-3 py-2 text-xs bg-[var(--bg-primary)] border border-red-500/40 rounded-xl text-[var(--text-primary)] outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500/30"
              autoFocus
            />
          </div>
        )}

        {/* Inline Argument Customizer (Optional) */}
        {isCustomizeOpen && status === 'pending' && (
          <div className="p-2.5 rounded-xl bg-[var(--bg-primary)] border border-amber-500/30 space-y-2">
            <div className="flex items-center justify-between text-xs text-amber-400 font-semibold">
              <span className="flex items-center gap-1">
                <Sliders className="w-3.5 h-3.5" /> Parameter Customization:
              </span>
              <span className="text-[10px] text-[var(--text-tertiary)]">Read-only preview</span>
            </div>
            <textarea
              value={customArgsText}
              onChange={(e) => setCustomArgsText(e.target.value)}
              className="w-full h-20 p-2 text-xs font-mono bg-[var(--bg-secondary)] border border-[var(--border)] rounded-md text-[var(--text-primary)] outline-none resize-none focus:border-amber-500/50"
              placeholder="Modify arguments..."
            />
          </div>
        )}

        {/* Bottom Actions Bar */}
        <div className="flex items-center justify-between gap-3 pt-2 border-t border-[var(--border)]/60 mt-0.5">
          {/* Left: Customization and Always Allow Quick Button */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsCustomizeOpen(!isCustomizeOpen)}
              type="button"
              className="text-[11px] text-[var(--text-tertiary)] hover:text-[var(--text-secondary)] flex items-center gap-1 cursor-pointer transition-colors"
              title="Customize arguments"
            >
              <Sliders className="w-3 h-3" />
              <span>Customize</span>
            </button>

            <button
              onClick={() => {
                setSelectedOption(4);
                effectiveAlwaysAllow(request.tool_name);
                handleDecision('approve');
              }}
              type="button"
              className="hidden sm:flex text-[11px] text-amber-400/80 hover:text-amber-400 items-center gap-1 cursor-pointer transition-colors"
              title="Always allow this tool"
            >
              <span>Always Allow</span>
            </button>
          </div>

          {/* Right: Skip and Submit Buttons (matching Claude style in screenshot) */}
          <div className="flex items-center gap-2.5">
            <button
              onClick={() => handleDecision('deny')}
              disabled={isSubmitting}
              type="button"
              name="Deny"
              aria-label="Deny"
              className="px-3.5 py-1.5 text-xs font-medium text-[var(--text-tertiary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] rounded-xl transition-all active:scale-95 disabled:opacity-50 cursor-pointer"
            >
              Skip
            </button>

            <button
              onClick={handleSubmitOption}
              disabled={isSubmitting}
              type="button"
              name="Approve"
              aria-label="Approve"
              className="flex items-center gap-1.5 px-4 py-1.5 text-xs font-semibold rounded-xl bg-blue-600 hover:bg-blue-700 active:scale-95 text-white shadow-md shadow-blue-600/25 transition-all disabled:opacity-50 cursor-pointer"
            >
              {isSubmitting ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : null}
              <span>Submit</span>
              <span className="text-[11px] font-mono opacity-80">↵</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
