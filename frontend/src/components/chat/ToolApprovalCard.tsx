'use client';

import React, { useState, useEffect } from 'react';
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
  ChevronDown,
  ChevronUp,
  Loader2,
  FileCode,
} from 'lucide-react';
import { ToolApprovalRequest, RiskLevel, ApprovalStatus } from '@/types';
import { submitToolApproval } from '@/lib/api';

interface ToolApprovalCardProps {
  request: ToolApprovalRequest;
  onResolve?: (approvalId: string, decision: 'approve' | 'deny', reason?: string) => Promise<void>;
  className?: string;
}

const RISK_CONFIG: Record<
  RiskLevel,
  { label: string; bg: string; text: string; border: string; icon: React.ComponentType<{ className?: string }> }
> = {
  critical: {
    label: 'Critical Risk',
    bg: 'bg-red-500/10',
    text: 'text-red-500 dark:text-red-400',
    border: 'border-red-500/30',
    icon: AlertTriangle,
  },
  high: {
    label: 'High Risk',
    bg: 'bg-amber-500/10',
    text: 'text-amber-500 dark:text-amber-400',
    border: 'border-amber-500/30',
    icon: AlertTriangle,
  },
  medium: {
    label: 'Medium Risk',
    bg: 'bg-yellow-500/10',
    text: 'text-yellow-600 dark:text-yellow-400',
    border: 'border-yellow-500/30',
    icon: ShieldAlert,
  },
  low: {
    label: 'Low Risk',
    bg: 'bg-blue-500/10',
    text: 'text-blue-500 dark:text-blue-400',
    border: 'border-blue-500/30',
    icon: ShieldAlert,
  },
  read_only: {
    label: 'Read Only',
    bg: 'bg-emerald-500/10',
    text: 'text-emerald-500 dark:text-emerald-400',
    border: 'border-emerald-500/30',
    icon: ShieldCheck,
  },
};

export function ToolApprovalCard({ request, onResolve, className = '' }: ToolApprovalCardProps) {
  const [status, setStatus] = useState<ApprovalStatus>(request.status || 'pending');
  const [remainingSeconds, setRemainingSeconds] = useState<number>(() => {
    const rawCreatedAt = request.created_at || Date.now();
    const createdAtMs = rawCreatedAt < 1e11 ? rawCreatedAt * 1000 : rawCreatedAt;
    const elapsed = Math.floor((Date.now() - createdAtMs) / 1000);
    return Math.max(0, (request.timeout_seconds || 120) - elapsed);
  });
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [showArgs, setShowArgs] = useState<boolean>(true);
  const [copiedHash, setCopiedHash] = useState<boolean>(false);
  const [rejectionReason, setRejectionReason] = useState<string>('');
  const [showRejectInput, setShowRejectInput] = useState<boolean>(false);

  const risk = RISK_CONFIG[request.mutation_risk] || RISK_CONFIG.medium;
  const RiskIcon = risk.icon;

  // Synchronize when parent updates request.status (e.g. via approval_resolved SSE event)
  useEffect(() => {
    if (request.status && request.status !== status) {
      setStatus(request.status);
    }
  }, [request.status]);

  // Countdown timer for pending approvals
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

  const handleCopyHash = () => {
    if (request.action_hash && typeof navigator !== 'undefined') {
      navigator.clipboard.writeText(request.action_hash);
      setCopiedHash(true);
      setTimeout(() => setCopiedHash(false), 2000);
    }
  };

  const handleDecision = async (decision: 'approve' | 'deny') => {
    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      if (onResolve) {
        await onResolve(request.approval_id, decision, decision === 'deny' ? rejectionReason : undefined);
      } else {
        await submitToolApproval(
          request.approval_id,
          decision,
          decision === 'deny' ? rejectionReason : undefined
        );
      }
      setStatus(decision === 'approve' ? 'approved' : 'rejected');
      setShowRejectInput(false);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to submit approval decision');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      className={`my-3.5 rounded-xl border bg-[var(--bg-secondary)] border-[var(--border-strong)] shadow-[var(--shadow-sm)] overflow-hidden transition-all duration-200 ${className}`}
      data-testid="tool-approval-card"
    >
      {/* Header bar */}
      <div className="flex items-center justify-between px-4 py-3 bg-[var(--bg-tertiary)]/70 border-b border-[var(--border)]">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] flex items-center justify-center text-[var(--accent-primary)] shadow-xs">
            <Terminal className="w-3.5 h-3.5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-bold text-[var(--text-primary)]">
                {request.tool_name}
              </span>
              <span
                className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold border ${risk.bg} ${risk.text} ${risk.border}`}
              >
                <RiskIcon className="w-2.5 h-2.5" />
                {risk.label}
              </span>
            </div>
          </div>
        </div>

        {/* Status Pill */}
        <div className="flex items-center gap-2">
          {status === 'pending' && (
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-amber-500/10 border border-amber-500/30 text-amber-600 dark:text-amber-400 animate-pulse">
              <Clock className="w-3 h-3" />
              <span>{remainingSeconds}s remaining</span>
            </div>
          )}
          {status === 'approved' && (
            <div className="flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-500/10 border border-emerald-500/30 text-emerald-600 dark:text-emerald-400">
              <Check className="w-3 h-3" />
              <span>Approved</span>
            </div>
          )}
          {status === 'rejected' && (
            <div className="flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-rose-500/10 border border-rose-500/30 text-rose-600 dark:text-rose-400">
              <X className="w-3 h-3" />
              <span>Rejected</span>
            </div>
          )}
          {(status === 'timeout' || status === 'expired') && (
            <div className="flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-zinc-500/10 border border-zinc-500/30 text-zinc-500">
              <Clock className="w-3 h-3" />
              <span>Expired</span>
            </div>
          )}
        </div>
      </div>

      {/* Card Body */}
      <div className="p-4 space-y-3">
        {/* Operation Description */}
        <div className="text-xs text-[var(--text-secondary)] leading-relaxed">
          <span className="font-semibold text-[var(--text-primary)]">Action: </span>
          {request.description || `Execute mutation via ${request.tool_name}`}
        </div>

        {/* Action Hash */}
        {request.action_hash && (
          <div className="flex items-center justify-between px-2.5 py-1.5 rounded-lg bg-[var(--bg-tertiary)]/50 border border-[var(--border)] text-[11px] font-mono">
            <div className="flex items-center gap-1.5 text-[var(--text-tertiary)] truncate">
              <span className="font-semibold">Action Hash:</span>
              <span className="truncate max-w-[220px] sm:max-w-[320px] text-[var(--text-secondary)]">
                {request.action_hash}
              </span>
            </div>
            <button
              onClick={handleCopyHash}
              type="button"
              className="ml-2 flex items-center gap-1 text-[10px] text-[var(--text-tertiary)] hover:text-[var(--text-primary)] transition-colors cursor-pointer"
              title="Copy action hash"
            >
              {copiedHash ? (
                <>
                  <Check className="w-3 h-3 text-emerald-500" />
                  <span className="text-emerald-500 font-medium">Copied</span>
                </>
              ) : (
                <>
                  <Copy className="w-3 h-3" />
                  <span>Copy</span>
                </>
              )}
            </button>
          </div>
        )}

        {/* Arguments Accordion */}
        {request.arguments && Object.keys(request.arguments).length > 0 && (
          <div className="rounded-lg border border-[var(--border)] overflow-hidden">
            <button
              onClick={() => setShowArgs(!showArgs)}
              type="button"
              className="w-full flex items-center justify-between px-3 py-2 bg-[var(--bg-tertiary)]/40 hover:bg-[var(--bg-tertiary)] text-[11px] font-semibold text-[var(--text-secondary)] transition-colors text-left cursor-pointer"
            >
              <div className="flex items-center gap-1.5">
                <FileCode className="w-3.5 h-3.5 text-[var(--accent-primary)]" />
                <span>Call Arguments ({Object.keys(request.arguments).length} fields)</span>
              </div>
              {showArgs ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>
            {showArgs && (
              <div className="p-3 bg-[var(--code-bg)] overflow-x-auto text-[11px] font-mono text-[var(--text-primary)]">
                <pre className="m-0 leading-relaxed whitespace-pre-wrap">
                  {JSON.stringify(request.arguments, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}

        {/* Rejection input box if opened */}
        {showRejectInput && status === 'pending' && (
          <div className="p-3 rounded-lg bg-rose-500/5 border border-rose-500/20 space-y-2">
            <div className="text-[11px] font-medium text-rose-600 dark:text-rose-400">
              Reason for denial (optional, fed back to agent):
            </div>
            <input
              type="text"
              value={rejectionReason}
              onChange={(e) => setRejectionReason(e.target.value)}
              placeholder="E.g., Path is out of scope, command syntax needs correction..."
              className="w-full px-2.5 py-1.5 rounded-md bg-[var(--bg-primary)] border border-[var(--border)] text-xs text-[var(--text-primary)] placeholder-[var(--text-tertiary)] focus:outline-none focus:border-rose-500"
            />
          </div>
        )}

        {/* Error message */}
        {errorMessage && (
          <div className="text-[11px] text-red-500 flex items-center gap-1">
            <AlertTriangle className="w-3 h-3" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Action Controls */}
        {status === 'pending' && (
          <div className="flex items-center justify-end gap-2 pt-1 border-t border-[var(--border)]">
            {!showRejectInput ? (
              <button
                onClick={() => setShowRejectInput(true)}
                disabled={isSubmitting}
                type="button"
                className="px-3 py-1.5 rounded-lg text-xs font-medium text-rose-600 dark:text-rose-400 hover:bg-rose-500/10 border border-rose-500/30 transition-colors cursor-pointer disabled:opacity-50"
              >
                Deny...
              </button>
            ) : (
              <button
                onClick={() => handleDecision('deny')}
                disabled={isSubmitting}
                type="button"
                className="px-3 py-1.5 rounded-lg text-xs font-semibold text-white bg-rose-600 hover:bg-rose-500 transition-colors cursor-pointer disabled:opacity-50 flex items-center gap-1"
              >
                {isSubmitting ? <Loader2 className="w-3 h-3 animate-spin" /> : <X className="w-3.5 h-3.5" />}
                <span>Confirm Deny</span>
              </button>
            )}

            <button
              onClick={() => handleDecision('approve')}
              disabled={isSubmitting}
              type="button"
              className="px-4 py-1.5 rounded-lg text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-500 shadow-sm transition-colors cursor-pointer disabled:opacity-50 flex items-center gap-1.5"
            >
              {isSubmitting ? <Loader2 className="w-3 h-3 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
              <span>Approve Action</span>
            </button>
          </div>
        )}

        {/* Resolved state footer */}
        {status !== 'pending' && (
          <div className="text-[11px] text-[var(--text-tertiary)] pt-1 border-t border-[var(--border)] flex items-center justify-between">
            <span>
              {status === 'approved' && 'Mutation authorized and executed.'}
              {status === 'rejected' && 'Mutation blocked by operator.'}
              {(status === 'timeout' || status === 'expired') && 'Request timed out without operator signature.'}
            </span>
            <span className="font-mono text-[10px]">Gate ID: {request.approval_id.substring(0, 8)}</span>
          </div>
        )}
      </div>
    </div>
  );
}
