'use client';

import React, { useState, useEffect, useRef } from 'react';
import {
  ShieldAlert,
  ShieldCheck,
  ShieldX,
  Clock,
  Check,
  X,
  Copy,
  Terminal,
  AlertTriangle,
  FileCode,
  TrendingUp,
  Zap,
  Sliders,
  ChevronDown,
  ChevronUp,
  Loader2,
  CheckCircle2,
  Sparkles,
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
  { label: string; badgeBg: string; text: string; border: string; glow: string; icon: React.ComponentType<{ className?: string }> }
> = {
  critical: {
    label: 'Critical Risk',
    badgeBg: 'bg-red-500/15',
    text: 'text-red-400',
    border: 'border-red-500/40',
    glow: 'shadow-red-500/10',
    icon: AlertTriangle,
  },
  high: {
    label: 'High Risk',
    badgeBg: 'bg-amber-500/15',
    text: 'text-amber-400',
    border: 'border-amber-500/40',
    glow: 'shadow-amber-500/10',
    icon: AlertTriangle,
  },
  medium: {
    label: 'Medium Risk',
    badgeBg: 'bg-yellow-500/15',
    text: 'text-yellow-400',
    border: 'border-yellow-500/40',
    glow: 'shadow-yellow-500/10',
    icon: ShieldAlert,
  },
  low: {
    label: 'Low Risk',
    badgeBg: 'bg-blue-500/15',
    text: 'text-blue-400',
    border: 'border-blue-500/40',
    glow: 'shadow-blue-500/10',
    icon: ShieldAlert,
  },
  read_only: {
    label: 'Read Only',
    badgeBg: 'bg-emerald-500/15',
    text: 'text-emerald-400',
    border: 'border-emerald-500/40',
    glow: 'shadow-emerald-500/10',
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
  const [copiedHash, setCopiedHash] = useState<boolean>(false);
  const [isDismissed, setIsDismissed] = useState<boolean>(false);
  const [isCollapsed, setIsCollapsed] = useState<boolean>(false);
  const [isCustomizeOpen, setIsCustomizeOpen] = useState<boolean>(false);
  const [customArgsText, setCustomArgsText] = useState<string>(() => {
    try {
      if (request.arguments?.command) return String(request.arguments.command);
      return JSON.stringify(request.arguments || {}, null, 2);
    } catch {
      return '';
    }
  });
  const [rejectionReason, setRejectionReason] = useState<string>('');
  const [showRejectInput, setShowRejectInput] = useState<boolean>(false);

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

  // Global keyboard shortcuts (Enter to Approve, Escape to Deny)
  useEffect(() => {
    if (status !== 'pending' || isSubmitting) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      const targetTag = (e.target as HTMLElement)?.tagName?.toLowerCase();
      if (targetTag === 'input' || targetTag === 'textarea') {
        return;
      }

      if (e.key === 'Enter') {
        e.preventDefault();
        handleDecision('approve');
      } else if (e.key === 'Escape') {
        e.preventDefault();
        if (showRejectInput) {
          handleDecision('deny');
        } else {
          setShowRejectInput(true);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [status, isSubmitting, showRejectInput, selectedCandidateId]);

  const handleDecision = async (decision: 'approve' | 'deny') => {
    if (status !== 'pending' || isSubmitting) return;

    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      const chosenStrategy = isFinanceStrategy ? selectedCandidateId : undefined;
      setStatus(decision === 'approve' ? 'approved' : 'rejected');
      await effectiveResolve(request.approval_id, decision, rejectionReason || undefined, chosenStrategy);
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

  const handleAlwaysAllow = async () => {
    if (status !== 'pending' || isSubmitting) return;
    effectiveAlwaysAllow(request.tool_name);
    await handleDecision('approve');
  };

  const handleCopyHash = () => {
    if (!request.action_hash) return;
    navigator.clipboard.writeText(request.action_hash).then(() => {
      setCopiedHash(true);
      setTimeout(() => setCopiedHash(false), 2000);
    });
  };

  const timerPercent = Math.max(0, Math.min(100, (remainingSeconds / totalTimeout) * 100));
  const isUrgent = remainingSeconds <= 20 && remainingSeconds > 0;
  const gateShortId = (request.approval_id || '').slice(-6).toUpperCase();

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

  return (
    <div
      className={`w-full max-w-4xl mx-auto px-2 sm:px-4 mb-2 z-40 transition-all duration-300 animate-in slide-in-from-bottom-3 ${className}`}
      data-testid="floating-approval-drawer"
    >
      <div className="relative overflow-hidden rounded-2xl border border-[var(--border)]/80 bg-[var(--bg-secondary)]/95 backdrop-blur-xl shadow-2xl shadow-black/40 ring-1 ring-white/10">
        {/* Animated Countdown Progress Bar */}
        <div className="w-full h-1 bg-[var(--bg-tertiary)] overflow-hidden relative">
          <div
            className={`h-full transition-all duration-1000 ease-linear ${
              isUrgent ? 'bg-red-500 animate-pulse' : 'bg-gradient-to-r from-amber-500 via-emerald-500 to-teal-400'
            }`}
            style={{ width: `${timerPercent}%` }}
          />
        </div>

        {/* Header HUD Bar */}
        <div className="px-4 py-3 sm:px-5 flex items-center justify-between gap-3 border-b border-[var(--border)]/50 bg-[var(--bg-tertiary)]/40">
          <div className="flex items-center gap-2.5 min-w-0">
            {/* Tool Icon */}
            <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-[var(--bg-primary)] border border-[var(--border)] flex items-center justify-center shadow-inner">
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

            {/* Tool Name & Gate ID */}
            <div className="flex flex-col min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-xs sm:text-sm font-semibold text-[var(--text-primary)] truncate font-mono">
                  {request.tool_name}
                </span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[var(--bg-primary)] border border-[var(--border)] text-[var(--text-tertiary)]">
                  GATE-{gateShortId}
                </span>
                {/* Risk Badge */}
                <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full border ${risk.badgeBg} ${risk.text} ${risk.border} flex items-center gap-1`}>
                  <RiskIcon className="w-2.5 h-2.5" />
                  <span>{risk.label}</span>
                </span>
              </div>
              <p className="text-[11px] text-[var(--text-secondary)] truncate">
                {request.human_summary || request.description || 'Operator approval required to proceed.'}
              </p>
            </div>
          </div>

          {/* Right Header: Timer & Collapse */}
          <div className="flex items-center gap-2 flex-shrink-0">
            <div
              className={`flex items-center gap-1 text-xs font-mono px-2 py-1 rounded-md border ${
                isUrgent
                  ? 'bg-red-500/10 border-red-500/40 text-red-400 animate-pulse'
                  : 'bg-[var(--bg-primary)] border-[var(--border)] text-[var(--text-secondary)]'
              }`}
              title="Auto-timeout countdown"
            >
              <Clock className="w-3.5 h-3.5" />
              <span>{remainingSeconds}s</span>
            </div>

            {/* Collapse/Expand Toggle */}
            <button
              onClick={() => setIsCollapsed(!isCollapsed)}
              type="button"
              className="p-1 rounded-md hover:bg-[var(--bg-hover)] text-[var(--text-tertiary)] hover:text-[var(--text-primary)] transition-colors"
              title={isCollapsed ? 'Expand details' : 'Collapse drawer'}
            >
              {isCollapsed ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
            </button>
          </div>
        </div>

        {/* Collapsible Body */}
        {!isCollapsed && (
          <div className="px-4 py-3 sm:px-5 space-y-3 max-h-[320px] overflow-y-auto scrollbar-thin">
            {/* Error Message */}
            {errorMessage && (
              <div className="p-2.5 rounded-lg bg-red-500/10 border border-red-500/30 text-xs text-red-400 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                <span>{errorMessage}</span>
              </div>
            )}

            {/* FINANCE STRATEGY: Master of Technology Candidate Cards */}
            {isFinanceStrategy && candidates.length > 0 && (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs text-[var(--text-secondary)]">
                  <span className="font-semibold flex items-center gap-1 text-emerald-400">
                    <Sparkles className="w-3.5 h-3.5" /> Select Master Technology Strategy:
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
                            ? 'bg-emerald-500/10 border-emerald-500/50 shadow-md shadow-emerald-500/10 ring-1 ring-emerald-500/30'
                            : 'bg-[var(--bg-primary)]/60 border-[var(--border)] hover:border-[var(--border-hover)] hover:bg-[var(--bg-primary)]'
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

                        <p className="text-[11px] text-[var(--text-tertiary)] mb-2 line-clamp-2">
                          {cand.rationale || `${cand.strategy_type} with optimized risk-to-reward ratio.`}
                        </p>

                        <div className="grid grid-cols-3 gap-1 text-[10px] font-mono pt-1 border-t border-[var(--border)]/40 text-[var(--text-secondary)]">
                          <div>
                            <span className="text-[var(--text-tertiary)] block">Win Rate</span>
                            <span className="font-semibold text-emerald-400">{cand.win_rate_est || '70%'}</span>
                          </div>
                          <div>
                            <span className="text-[var(--text-tertiary)] block">R:R</span>
                            <span className="font-semibold text-blue-400">{cand.risk_reward_actual || '1:2.4'}</span>
                          </div>
                          <div>
                            <span className="text-[var(--text-tertiary)] block">Max Loss</span>
                            <span className="font-semibold text-red-400">{cand.max_loss_per_lot || '₹2,500'}</span>
                          </div>
                        </div>

                        {isSelected && (
                          <div className="absolute top-2 right-2 text-emerald-400">
                            <CheckCircle2 className="w-4 h-4" />
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* BASH TOOL: Command Preview */}
            {!isFinanceStrategy && request.tool_name === 'BashTool' && (
              <div className="space-y-1">
                <div className="flex items-center justify-between text-[11px] text-[var(--text-tertiary)]">
                  <span>Command to execute in workspace:</span>
                  <span className="text-[10px] font-mono text-emerald-400/80">AST Sandboxed</span>
                </div>
                <div className="p-2.5 rounded-lg bg-[var(--bg-primary)] border border-[var(--border)] font-mono text-xs text-amber-300 break-all select-all flex items-center justify-between gap-2">
                  <span className="font-semibold text-[var(--text-secondary)] select-none">$</span>
                  <code className="flex-1 overflow-x-auto">{request.arguments?.command || request.command_preview}</code>
                  <button
                    onClick={() => {
                      const cmd = String(request.arguments?.command || request.command_preview || '');
                      navigator.clipboard.writeText(cmd);
                    }}
                    type="button"
                    className="p-1 hover:bg-[var(--bg-tertiary)] rounded text-[var(--text-tertiary)] hover:text-[var(--text-primary)]"
                    title="Copy command"
                  >
                    <Copy className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            )}

            {/* FILE EDIT TOOL: Path & Diff Preview */}
            {!isFinanceStrategy && request.tool_name === 'FileEditTool' && (
              <div className="space-y-1">
                <div className="flex items-center justify-between text-[11px] text-[var(--text-tertiary)]">
                  <span>Target File:</span>
                  <span className="font-mono text-blue-400 text-[10px] truncate max-w-[200px]">
                    {request.target_resource || request.arguments?.path}
                  </span>
                </div>
                {request.diff_preview && (
                  <pre className="p-2 rounded-lg bg-[var(--bg-primary)] border border-[var(--border)] font-mono text-[11px] text-[var(--text-secondary)] max-h-28 overflow-y-auto whitespace-pre-wrap">
                    {request.diff_preview}
                  </pre>
                )}
              </div>
            )}

            {/* Inline Argument Customizer */}
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

            {/* Rejection Reason Input Drawer */}
            {showRejectInput && status === 'pending' && (
              <div className="p-2.5 rounded-xl bg-red-500/10 border border-red-500/30 space-y-2">
                <span className="text-xs text-red-400 font-semibold flex items-center gap-1">
                  <ShieldX className="w-3.5 h-3.5" /> Reason for denial (optional):
                </span>
                <input
                  type="text"
                  value={rejectionReason}
                  onChange={(e) => setRejectionReason(e.target.value)}
                  placeholder="e.g. Command modifies protected file or invalid parameters"
                  className="w-full p-2 text-xs bg-[var(--bg-primary)] border border-[var(--border)] rounded-md text-[var(--text-primary)] outline-none focus:border-red-500/50"
                />
                <div className="flex items-center justify-end gap-2 pt-1">
                  <button
                    onClick={() => setShowRejectInput(false)}
                    type="button"
                    className="px-2.5 py-1 text-xs rounded bg-[var(--bg-tertiary)] text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => handleDecision('deny')}
                    disabled={isSubmitting}
                    type="button"
                    className="px-3 py-1 text-xs font-medium rounded bg-red-500 hover:bg-red-600 text-white"
                  >
                    Confirm Denial (Esc)
                  </button>
                </div>
              </div>
            )}

            {/* Cryptographic SHA-256 Hash Preview */}
            <div className="flex items-center justify-between text-[10px] font-mono text-[var(--text-tertiary)] pt-1">
              <span className="truncate max-w-[280px]">
                Hash: {request.action_hash || 'SHA-256 Verified'}
              </span>
              <button
                onClick={handleCopyHash}
                type="button"
                className="hover:text-[var(--text-secondary)] flex items-center gap-1 cursor-pointer transition-colors"
                title="Copy SHA-256 action hash"
              >
                <Copy className="w-3 h-3" />
                <span>{copiedHash ? 'Copied!' : 'Copy Hash'}</span>
              </button>
            </div>
          </div>
        )}

        {/* Action Controls Bar */}
        {status === 'pending' && (
          <div className="px-4 py-2.5 sm:px-5 border-t border-[var(--border)]/60 bg-[var(--bg-primary)]/70 flex flex-wrap items-center justify-between gap-2">
            {/* Left Controls: Always Allow & Customize */}
            <div className="flex items-center gap-1.5 flex-wrap">
              <button
                onClick={handleAlwaysAllow}
                disabled={isSubmitting}
                type="button"
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-xl bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 border border-amber-500/30 transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 cursor-pointer"
                title="Auto-approve this tool for the rest of this session"
              >
                <Zap className="w-3.5 h-3.5 text-amber-400" />
                <span>Always Allow</span>
                <span className="hidden sm:inline text-[10px] font-mono text-amber-400/60">(Session)</span>
              </button>

              <button
                onClick={() => setIsCustomizeOpen(!isCustomizeOpen)}
                type="button"
                className={`flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium rounded-xl border transition-all ${
                  isCustomizeOpen
                    ? 'bg-[var(--bg-tertiary)] border-amber-500/40 text-amber-400'
                    : 'bg-[var(--bg-secondary)] hover:bg-[var(--bg-tertiary)] border-[var(--border)] text-[var(--text-secondary)]'
                }`}
                title="Customize parameters"
              >
                <Sliders className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Customize</span>
              </button>
            </div>

            {/* Right Controls: Deny & Approve */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => {
                  if (!showRejectInput) setShowRejectInput(true);
                  else handleDecision('deny');
                }}
                disabled={isSubmitting}
                type="button"
                className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded-xl bg-[var(--bg-secondary)] hover:bg-red-500/15 border border-[var(--border)] hover:border-red-500/30 text-[var(--text-secondary)] hover:text-red-400 transition-all active:scale-95 disabled:opacity-50 cursor-pointer"
                title="Deny execution (Esc)"
              >
                <X className="w-3.5 h-3.5" />
                <span>Deny</span>
                <span className="hidden sm:inline text-[10px] font-mono text-[var(--text-tertiary)]">(Esc)</span>
              </button>

              <button
                onClick={() => handleDecision('approve')}
                disabled={isSubmitting}
                type="button"
                className="flex items-center gap-1.5 px-4 py-1.5 text-xs font-semibold rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white shadow-md shadow-emerald-500/25 hover:shadow-lg hover:shadow-emerald-500/35 transition-all hover:scale-[1.03] active:scale-[0.98] disabled:opacity-50 cursor-pointer"
                title="Approve and proceed execution (Enter)"
              >
                {isSubmitting ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Check className="w-3.5 h-3.5 stroke-[2.5]" />
                )}
                <span>Approve</span>
                <span className="text-[10px] font-mono opacity-80">(Enter)</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
