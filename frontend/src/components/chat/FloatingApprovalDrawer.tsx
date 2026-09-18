'use client';

import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
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
  Cpu,
  X,
} from 'lucide-react';
import {
  ToolApprovalRequest,
  RiskLevel,
  ApprovalStatus,
  FinanceStrategyApprovalData,
  CandidateFinanceStrategy,
  DynamicApprovalOption,
  ModelPersona,
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
    badgeBg: 'bg-red-500/10',
    text: 'text-red-600 dark:text-red-400',
    border: 'border-red-500/30',
    icon: AlertTriangle,
  },
  high: {
    label: 'High Risk',
    badgeBg: 'bg-amber-500/10',
    text: 'text-amber-700 dark:text-amber-400',
    border: 'border-amber-500/30',
    icon: AlertTriangle,
  },
  medium: {
    label: 'Medium Risk',
    badgeBg: 'bg-yellow-500/10',
    text: 'text-yellow-700 dark:text-yellow-400',
    border: 'border-yellow-500/30',
    icon: ShieldAlert,
  },
  low: {
    label: 'Low Risk',
    badgeBg: 'bg-blue-500/10',
    text: 'text-blue-700 dark:text-blue-400',
    border: 'border-blue-500/30',
    icon: ShieldAlert,
  },
  read_only: {
    label: 'Read Only',
    badgeBg: 'bg-emerald-500/10',
    text: 'text-emerald-700 dark:text-emerald-400',
    border: 'border-emerald-500/30',
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

function synthesizeClientDynamicOptions(
  request: ToolApprovalRequest
): DynamicApprovalOption[] {
  const toolName = request.tool_name;
  const targetResource = String(request.target_resource || request.arguments?.path || '');
  const cmd = String(request.arguments?.command || request.command_preview || '');
  const agent = request.model_persona?.agent_ref || 'Aarka';

  if (toolName === 'FileEditTool') {
    const isPy = targetResource.endsWith('.py');
    return [
      {
        id: 1,
        action: 'allow_once',
        label: `Allow & save '${targetResource || 'file'}' to workspace`,
        detail: 'Write verified code directly into the workspace root.',
        recommended: true,
      },
      {
        id: 2,
        action: 'allow_and_run',
        label: `Save '${targetResource || 'file'}' and execute immediately (${isPy ? `python ${targetResource}` : 'inspect in workspace'})`,
        detail: 'Atomic disk write followed by automatic sandbox execution.',
      },
      {
        id: 3,
        action: 'customize',
        label: `Inspect & customize '${targetResource || 'file'}' code before committing`,
        detail: 'Review diff lines, modify parameters, or adjust imports.',
      },
      {
        id: 4,
        action: 'always_allow',
        label: `Always allow workspace file modifications in this session (Always Allow)`,
        detail: `Auto-approves future file writes by ${agent} for this session.`,
      },
      {
        id: 5,
        action: 'deny',
        label: `No (tell ${agent} what to do instead)`,
        detail: 'Reject this file write and provide alternate requirements.',
      },
    ];
  }

  if (toolName === 'BashTool') {
    const cmdShort = cmd.length > 45 ? `${cmd.slice(0, 45)}...` : cmd || 'command';
    return [
      {
        id: 1,
        action: 'allow_once',
        label: `Execute '${cmdShort}' in isolated sandbox`,
        detail: 'Run command safely within workspace execution constraints.',
        recommended: true,
      },
      {
        id: 2,
        action: 'allow_and_stream',
        label: `Execute '${cmdShort}' and stream live terminal output`,
        detail: 'Stream stdout & stderr chunks directly to chat console.',
      },
      {
        id: 3,
        action: 'customize',
        label: 'Edit command parameters before execution',
        detail: 'Modify flags, arguments, or environment variables.',
      },
      {
        id: 4,
        action: 'always_allow',
        label: `Always allow '${cmdShort}' in this session (Always Allow)`,
        detail: 'Whitelist this command pattern to prevent redundant authorization gates.',
      },
      {
        id: 5,
        action: 'deny',
        label: `No (tell ${agent} what to do instead)`,
        detail: 'Halt command execution and redirect agent workflow.',
      },
    ];
  }

  if (toolName === 'FinanceStrategyMasterSelection') {
    return [
      {
        id: 1,
        action: 'allow_once',
        label: 'Execute Master Strategy (Recommended)',
        detail: 'Optimal risk-adjusted strategy selected by quantitative engine.',
        recommended: true,
      },
      {
        id: 2,
        action: 'select_alternative',
        label: 'Execute Alternative Momentum Breakout Ladder',
        detail: 'Directional momentum strategy with dynamic trail stop.',
      },
      {
        id: 3,
        action: 'customize',
        label: 'Customize strike prices, premium limits & expiry dates',
        detail: 'Manually tune legs, lots, and risk allocation.',
      },
      {
        id: 4,
        action: 'always_allow',
        label: 'Always auto-execute strategies matching risk profile (Always Allow)',
        detail: 'Authorize automated multi-leg position sizing within risk limit.',
      },
      {
        id: 5,
        action: 'deny',
        label: `No (tell ${agent} what to do instead)`,
        detail: 'Reject strategy recommendation and scan alternative sectors.',
      },
    ];
  }

  return [
    {
      id: 1,
      action: 'allow_once',
      label: `Allow execution of ${toolName}`,
      detail: `Authorize single execution of ${toolName} with specified parameters.`,
      recommended: true,
    },
    {
      id: 2,
      action: 'allow_in_conversation',
      label: `Allow ${toolName} for this task in conversation`,
      detail: 'Permits sequential steps without prompt interruption.',
    },
    {
      id: 3,
      action: 'customize',
      label: `Inspect & modify ${toolName} arguments`,
      detail: 'Review and edit payload parameters before execution.',
    },
    {
      id: 4,
      action: 'always_allow',
      label: `Always allow ${toolName} in this session (Always Allow)`,
      detail: `Auto-approves ${toolName} calls for remainder of session.`,
    },
    {
      id: 5,
      action: 'deny',
      label: `No (tell ${agent} what to do instead)`,
      detail: 'Cancel action and request an alternative solution.',
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

  useEffect(() => {
    setMounted(true);
  }, []);

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

  // Model persona branding
  const persona: ModelPersona = request.model_persona || {
    provider: 'aarka',
    name: 'Aarka AI',
    badge: 'Aarka Engine · Autonomous Execution',
    badge_color: 'border-teal-500/30 bg-teal-500/10 text-teal-700 dark:text-teal-400',
    accent_color: '#0D9488',
    agent_ref: 'Aarka',
  };

  // Dynamic context-aware options (backend or synthesized fallback)
  const dynamicOptions: DynamicApprovalOption[] =
    request.dynamic_options && request.dynamic_options.length > 0
      ? request.dynamic_options
      : synthesizeClientDynamicOptions(request);

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

    const activeOpt = dynamicOptions.find((o) => o.id === selectedOption);
    if (selectedOption === 5 || activeOpt?.action === 'deny') {
      await handleDecision('deny', rejectionReason);
    } else if (
      selectedOption === 4 ||
      activeOpt?.action === 'always_allow' ||
      activeOpt?.action === 'allow_in_conversation'
    ) {
      effectiveAlwaysAllow(request.tool_name);
      await handleDecision('approve');
    } else if (activeOpt?.action === 'customize') {
      setIsCustomizeOpen(true);
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

  // Helper renderer that wraps content in createPortal when mounted
  const renderPortalOrContent = (children: React.ReactNode) => {
    if (typeof document !== 'undefined' && mounted && document.body) {
      return createPortal(children, document.body);
    }
    return children;
  };

  // Quick feedback confirmation modal upon approval
  if (status === 'approved') {
    return renderPortalOrContent(
      <div
        className={`fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black/25 dark:bg-black/50 backdrop-blur-[3px] transition-all duration-300 ${className}`}
        data-testid="floating-approval-drawer"
      >
        <div className="flex items-center justify-between gap-4 px-6 py-4 rounded-2xl border border-emerald-500/40 bg-[var(--bg-secondary)] shadow-2xl shadow-black/10 text-emerald-600 dark:text-emerald-400 text-sm font-mono animate-in fade-in max-w-md w-full">
          <span className="flex items-center gap-3 min-w-0">
            <CheckCircle2 className="w-5 h-5 text-emerald-500 animate-pulse flex-shrink-0" />
            <span className="truncate">Authorized <strong>{request.tool_name}</strong>. Executing in workspace...</span>
          </span>
          <Loader2 className="w-4 h-4 animate-spin text-emerald-500 flex-shrink-0" />
        </div>
      </div>
    );
  }

  if (status === 'rejected') {
    return renderPortalOrContent(
      <div
        className={`fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black/25 dark:bg-black/50 backdrop-blur-[3px] transition-all duration-300 ${className}`}
        data-testid="floating-approval-drawer"
      >
        <div className="flex items-center gap-3 px-6 py-4 rounded-2xl border border-red-500/40 bg-[var(--bg-secondary)] shadow-2xl shadow-black/10 text-red-600 dark:text-red-400 text-sm font-mono animate-in fade-in max-w-md w-full">
          <ShieldX className="w-5 h-5 text-red-500 flex-shrink-0" />
          <span>Execution denied by operator. Workspace unchanged.</span>
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

  return renderPortalOrContent(
    <div
      className={`fixed inset-0 z-[9999] flex items-center justify-center p-4 sm:p-6 bg-black/30 dark:bg-black/60 backdrop-blur-[3px] transition-all duration-200 animate-in fade-in ${className}`}
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
      <div className="relative w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-2xl border border-[var(--border-strong)] bg-[var(--bg-secondary)] text-[var(--text-primary)] shadow-2xl shadow-black/15 ring-1 ring-black/[0.04] dark:ring-white/10 p-5 sm:p-6 flex flex-col gap-4 animate-in zoom-in-95 duration-150">
        
        {/* Top Header: Model Persona & Risk & Countdown */}
        <div className="flex items-center justify-between gap-3 border-b border-[var(--border)] pb-3.5">
          <div className="flex items-center gap-2 flex-wrap">
            <span
              className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border shadow-sm ${persona.badge_color}`}
              title={`Active Engine: ${persona.name}`}
            >
              <Cpu className="w-3.5 h-3.5 flex-shrink-0" />
              <span>{persona.badge}</span>
            </span>

            <span className={`text-[11px] font-mono px-2.5 py-1 rounded-full border ${risk.badgeBg} ${risk.text} ${risk.border}`}>
              {risk.label}
            </span>
          </div>

          <div className="flex items-center gap-3 flex-shrink-0">
            <div className="flex items-center gap-1.5 text-xs font-mono text-[var(--text-secondary)] bg-[var(--bg-tertiary)] px-3 py-1 rounded-lg border border-[var(--border)]">
              <Clock className="w-3.5 h-3.5 text-[var(--text-tertiary)]" />
              <span>{remainingSeconds}s</span>
            </div>

            <button
              onClick={() => handleDecision('deny')}
              type="button"
              className="p-1.5 text-[var(--text-tertiary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] rounded-lg transition-colors cursor-pointer"
              title="Dismiss dialog (Esc)"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Title & Tool Name */}
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-xl bg-[var(--bg-tertiary)] border border-[var(--border)] flex items-center justify-center flex-shrink-0 text-[var(--text-secondary)] mt-0.5 shadow-sm">
            {isFinanceStrategy ? (
              <TrendingUp className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
            ) : request.tool_name === 'BashTool' ? (
              <Terminal className="w-5 h-5 text-amber-600 dark:text-amber-400" />
            ) : request.tool_name === 'FileEditTool' ? (
              <FileCode className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            ) : (
              <RiskIcon className={`w-5 h-5 ${risk.text}`} />
            )}
          </div>
          <div className="min-w-0 flex-1">
            <div className="text-[11px] font-mono text-[var(--text-tertiary)] uppercase tracking-wider mb-0.5">
              Authorization Required · Protected Workspace Operation
            </div>
            <h3 id="approval-modal-title" className="text-base sm:text-lg font-bold text-[var(--text-primary)] leading-tight tracking-tight">
              {humanTitle}
            </h3>
          </div>
        </div>

        {/* Error Notification */}
        {errorMessage && (
          <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-xs text-red-600 dark:text-red-400 flex items-center gap-2 animate-in fade-in">
            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Command / Resource Box */}
        <div className="rounded-xl bg-[var(--code-bg)] border border-[var(--code-border)] p-3.5 font-mono text-xs text-[var(--text-primary)] break-all select-all flex flex-col gap-2">
          <div className="flex items-center justify-between gap-2 text-[11px] text-[var(--text-secondary)] select-none">
            <span className="font-bold">{request.tool_name}</span>
            {request.diff_preview && (
              <button
                type="button"
                onClick={() => setShowCodePreview(!showCodePreview)}
                className="text-[11px] text-[var(--accent-primary)] hover:underline cursor-pointer flex items-center gap-1 font-medium"
              >
                <span>{showCodePreview ? 'Hide Preview' : 'View Code Preview'}</span>
                {showCodePreview ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
              </button>
            )}
          </div>
          <div className="bg-[var(--bg-secondary)] p-2.5 rounded-lg border border-[var(--border)] font-mono text-xs text-[var(--text-primary)] leading-relaxed shadow-sm">
            {actionTarget}
          </div>
          {showCodePreview && request.diff_preview && (
            <pre className="mt-1 p-3 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] font-mono text-[11px] text-[var(--text-secondary)] max-h-48 overflow-y-auto whitespace-pre-wrap shadow-inner">
              {request.diff_preview}
            </pre>
          )}
        </div>

        {/* FINANCE STRATEGY: Master Candidate Selection (if applicable) */}
        {isFinanceStrategy && candidates.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs text-[var(--text-secondary)]">
              <span className="font-bold flex items-center gap-1 text-emerald-700 dark:text-emerald-400">
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
                    className={`p-3 rounded-xl border transition-all cursor-pointer text-left relative ${
                      isSelected
                        ? 'bg-[var(--accent-muted)] border-[var(--accent-primary)] shadow-sm ring-1 ring-[var(--accent-primary)]/30'
                        : 'bg-[var(--bg-primary)] border-[var(--border)] hover:bg-[var(--bg-hover)]'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-1 mb-1">
                      <span className="text-xs font-bold text-[var(--text-primary)]">
                        {cand.strategy_name}
                      </span>
                      {isMaster && (
                        <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-800 dark:text-amber-400 border border-amber-500/40">
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

        {/* Dynamic Contextual Options List */}
        <div className="space-y-2">
          <div className="text-xs font-medium text-[var(--text-secondary)] px-1 flex items-center justify-between">
            <span>Select Action (press 1–5 or click):</span>
            <span className="text-[11px] font-mono opacity-70">Enter to confirm</span>
          </div>

          <div className="flex flex-col gap-2">
            {dynamicOptions.map((opt) => {
              const isSelected = selectedOption === opt.id;
              return (
                <div
                  key={opt.id}
                  onClick={() => setSelectedOption(opt.id)}
                  className={`flex items-start gap-3 p-3 rounded-xl cursor-pointer transition-all ${
                    isSelected
                      ? 'bg-[var(--accent-muted)] border-2 border-[var(--accent-primary)] shadow-sm'
                      : 'bg-[var(--bg-primary)] hover:bg-[var(--bg-hover)] border border-[var(--border)]'
                  }`}
                >
                  <span
                    className={`w-6 h-6 rounded-md flex items-center justify-center text-xs font-mono font-bold flex-shrink-0 mt-0.5 transition-colors ${
                      isSelected
                        ? 'bg-[var(--accent-primary)] text-white shadow-sm'
                        : 'bg-[var(--bg-tertiary)] text-[var(--text-secondary)] border border-[var(--border)]'
                    }`}
                  >
                    {opt.id}
                  </span>

                  <div className="flex-1 min-w-0 flex flex-col gap-0.5">
                    <div className="flex items-center gap-2">
                      <span className="text-xs sm:text-sm font-semibold text-[var(--text-primary)]">
                        {opt.label}
                      </span>
                      {opt.recommended && (
                        <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-emerald-500/15 text-emerald-800 dark:text-emerald-400 border border-emerald-500/30 flex-shrink-0">
                          RECOMMENDED
                        </span>
                      )}
                    </div>
                    {opt.detail && (
                      <span className="text-xs text-[var(--text-secondary)] leading-snug">
                        {opt.detail}
                      </span>
                    )}
                  </div>

                  {isSelected && (
                    <Check className="w-4 h-4 text-[var(--accent-primary)] flex-shrink-0 mt-1 stroke-[2.5]" />
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Option 5: Expandable Rejection Reason Input */}
        {selectedOption === 5 && (
          <div className="pl-9 -mt-1 animate-in fade-in">
            <input
              type="text"
              value={rejectionReason}
              onChange={(e) => setRejectionReason(e.target.value)}
              placeholder="tell the agent what to do instead..."
              className="w-full px-3.5 py-2.5 text-xs bg-[var(--bg-primary)] border border-red-500/40 rounded-xl text-[var(--text-primary)] outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500/30 shadow-inner"
              autoFocus
            />
          </div>
        )}

        {/* Inline Argument Customizer */}
        {isCustomizeOpen && status === 'pending' && (
          <div className="p-3.5 rounded-xl bg-[var(--bg-primary)] border border-amber-500/30 space-y-2 animate-in fade-in">
            <div className="flex items-center justify-between text-xs text-amber-700 dark:text-amber-400 font-bold">
              <span className="flex items-center gap-1.5">
                <Sliders className="w-3.5 h-3.5" /> Parameter Customization:
              </span>
              <span className="text-[10px] text-[var(--text-tertiary)] font-normal">Editable preview</span>
            </div>
            <textarea
              value={customArgsText}
              onChange={(e) => setCustomArgsText(e.target.value)}
              className="w-full h-24 p-2.5 text-xs font-mono bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg text-[var(--text-primary)] outline-none resize-none focus:border-[var(--accent-primary)]"
              placeholder="Modify arguments..."
            />
          </div>
        )}

        {/* Bottom Actions Bar */}
        <div className="flex items-center justify-between gap-3 pt-3 border-t border-[var(--border)] mt-0.5">
          {/* Left: Customization and Always Allow Quick Button */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsCustomizeOpen(!isCustomizeOpen)}
              type="button"
              name="Customize"
              aria-label="Customize"
              className="text-xs text-[var(--text-secondary)] hover:text-[var(--text-primary)] flex items-center gap-1.5 px-3 py-1.5 rounded-lg hover:bg-[var(--bg-tertiary)] cursor-pointer transition-colors"
              title="Customize arguments"
            >
              <Sliders className="w-3.5 h-3.5" />
              <span>Customize</span>
            </button>

            <button
              onClick={() => {
                setSelectedOption(4);
                effectiveAlwaysAllow(request.tool_name);
                handleDecision('approve');
              }}
              type="button"
              name="Always Allow"
              aria-label="Always Allow"
              className="text-xs text-amber-800 dark:text-amber-400 hover:text-amber-900 flex items-center gap-1 px-3 py-1.5 rounded-lg hover:bg-amber-500/10 cursor-pointer transition-colors font-medium"
              title="Always allow this tool"
            >
              <span>Always Allow</span>
            </button>
          </div>

          {/* Right: Skip and Submit Buttons */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => handleDecision('deny')}
              disabled={isSubmitting}
              type="button"
              name="Deny"
              aria-label="Deny"
              className="px-4 py-2 text-xs font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] border border-[var(--border)] rounded-xl transition-all active:scale-95 disabled:opacity-50 cursor-pointer"
            >
              Skip
            </button>

            <button
              onClick={handleSubmitOption}
              disabled={isSubmitting}
              type="button"
              name="Approve"
              aria-label="Approve"
              className="flex items-center gap-2 px-6 py-2.5 text-xs font-semibold rounded-xl bg-[var(--accent-primary)] hover:bg-[var(--accent-hover)] active:scale-95 text-white shadow-md shadow-[var(--accent-primary)]/20 transition-all disabled:opacity-50 cursor-pointer"
            >
              {isSubmitting ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : null}
              <span>Submit</span>
              <span className="text-[11px] font-mono opacity-90">↵</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
