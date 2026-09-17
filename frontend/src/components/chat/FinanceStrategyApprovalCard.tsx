'use client';

import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  ShieldCheck,
  ShieldAlert,
  Clock,
  Check,
  X,
  Copy,
  AlertTriangle,
  Award,
  Zap,
  ArrowRight,
  ChevronDown,
  ChevronUp,
  Loader2,
} from 'lucide-react';
import {
  ToolApprovalRequest,
  CandidateFinanceStrategy,
  FinanceStrategyApprovalData,
  ApprovalStatus,
} from '@/types';
import { submitToolApproval } from '@/lib/api';

interface FinanceStrategyApprovalCardProps {
  request: ToolApprovalRequest;
  onResolve?: (approvalId: string, decision: 'approve' | 'deny', reason?: string) => Promise<void>;
  className?: string;
}

export function FinanceStrategyApprovalCard({
  request,
  onResolve,
  className = '',
}: FinanceStrategyApprovalCardProps) {
  const strategyData = (request.arguments || {}) as FinanceStrategyApprovalData;
  const candidates = strategyData.candidates || [];
  
  const [selectedCandidateId, setSelectedCandidateId] = useState<string>(() => {
    return strategyData.master_recommended || candidates[0]?.candidate_id || '';
  });

  const [status, setStatus] = useState<ApprovalStatus>(request.status || 'pending');
  const [remainingSeconds, setRemainingSeconds] = useState<number>(() => {
    const rawCreatedAt = request.created_at || Date.now();
    const createdAtMs = rawCreatedAt < 1e11 ? rawCreatedAt * 1000 : rawCreatedAt;
    const elapsed = Math.floor((Date.now() - createdAtMs) / 1000);
    return Math.max(0, (request.timeout_seconds || 120) - elapsed);
  });
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [copiedHash, setCopiedHash] = useState<boolean>(false);
  const [showDetails, setShowDetails] = useState<boolean>(true);

  // 120s countdown timer
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

  const selectedCandidate = candidates.find((c) => c.candidate_id === selectedCandidateId) || candidates[0];

  const handleDecision = async (decision: 'approve' | 'deny') => {
    if (status !== 'pending' || isSubmitting) return;

    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      if (onResolve) {
        await onResolve(request.approval_id, decision, selectedCandidate?.strategy_name);
      } else {
        await submitToolApproval(
          request.approval_id,
          decision,
          selectedCandidate?.strategy_name,
          selectedCandidateId
        );
      }
      setStatus(decision === 'approve' ? 'approved' : 'rejected');
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to submit strategy decision');
    } finally {
      setIsSubmitting(false);
    }
  };

  const copyActionHash = () => {
    navigator.clipboard.writeText(request.action_hash);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2000);
  };

  const isSignalBullish = (strategyData.signal || '').toUpperCase() === 'BULLISH';
  const isSignalBearish = (strategyData.signal || '').toUpperCase() === 'BEARISH';

  return (
    <div
      data-testid="finance-strategy-approval-card"
      className={`my-3 rounded-xl border border-amber-500/30 bg-card p-4 sm:p-5 shadow-lg dark:bg-card/80 backdrop-blur transition-all ${className}`}
    >
      {/* Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/60 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-amber-500/10 text-amber-500">
            <Award className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold tracking-tight text-foreground sm:text-base">
                Master Strategy Approval Gate
              </span>
              <span
                className={`rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${
                  isSignalBullish
                    ? 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/20'
                    : isSignalBearish
                    ? 'bg-rose-500/10 text-rose-500 border border-rose-500/20'
                    : 'bg-yellow-500/10 text-yellow-600 border border-yellow-500/20'
                }`}
              >
                {strategyData.signal || 'ANALYSIS'}
              </span>
            </div>
            <p className="text-xs text-muted-foreground">
              {strategyData.symbol || 'ASSET'} • Spot: {strategyData.currency || '₹'}
              {strategyData.current_price?.toLocaleString() || '—'} • Expiry: {strategyData.expiry || 'Monthly'}
            </p>
          </div>
        </div>

        {/* Timer / Status Pill */}
        <div className="flex items-center gap-2">
          {status === 'pending' && (
            <div
              className={`flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold ${
                remainingSeconds <= 20
                  ? 'bg-red-500/10 text-red-500 animate-pulse'
                  : 'bg-muted text-muted-foreground'
              }`}
            >
              <Clock className="h-3.5 w-3.5" />
              <span>{remainingSeconds}s remaining</span>
            </div>
          )}
          {status === 'approved' && (
            <div className="flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-500 border border-emerald-500/30">
              <ShieldCheck className="h-3.5 w-3.5" />
              <span>Resolved: APPROVED</span>
            </div>
          )}
          {status === 'rejected' && (
            <div className="flex items-center gap-1.5 rounded-full bg-rose-500/10 px-3 py-1 text-xs font-semibold text-rose-500 border border-rose-500/30">
              <ShieldAlert className="h-3.5 w-3.5" />
              <span>Resolved: REJECTED</span>
            </div>
          )}
          {(status === 'timeout' || status === 'expired') && (
            <div className="flex items-center gap-1.5 rounded-full bg-muted px-3 py-1 text-xs font-semibold text-muted-foreground">
              <Clock className="h-3.5 w-3.5" />
              <span>Timed Out (Fail-Closed)</span>
            </div>
          )}
        </div>
      </div>

      {/* Master of Technology Selection Header */}
      <div className="mt-4 mb-2">
        <div className="flex items-center justify-between">
          <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
            <Zap className="h-3.5 w-3.5 text-amber-500" />
            Select Master of Technology Strategy
          </label>
          <span className="text-[11px] text-muted-foreground">
            Compare candidate algorithmic models
          </span>
        </div>

        {/* Candidates Radio Cards */}
        <div className="mt-2 grid grid-cols-1 gap-2.5 sm:grid-cols-2">
          {candidates.map((cand) => {
            const isSelected = cand.candidate_id === selectedCandidateId;
            const isRec = cand.candidate_id === strategyData.master_recommended;
            return (
              <div
                key={cand.candidate_id}
                onClick={() => status === 'pending' && setSelectedCandidateId(cand.candidate_id)}
                className={`relative flex flex-col justify-between rounded-lg border p-3 cursor-pointer transition-all ${
                  isSelected
                    ? 'border-amber-500 bg-amber-500/5 shadow-sm'
                    : 'border-border/70 hover:border-border hover:bg-muted/30'
                } ${status !== 'pending' ? 'cursor-default pointer-events-none' : ''}`}
              >
                <div>
                  <div className="flex items-center justify-between gap-1.5">
                    <span className="text-xs font-bold text-foreground">
                      {cand.strategy_name}
                    </span>
                    {isRec && (
                      <span className="rounded bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/30 px-1.5 py-0.5 text-[9px] font-semibold uppercase">
                        Recommended
                      </span>
                    )}
                  </div>
                  <p className="mt-0.5 text-[11px] text-muted-foreground">
                    {cand.technology_tag}
                  </p>
                </div>

                <div className="mt-2 flex items-center justify-between pt-2 border-t border-border/40 text-[11px]">
                  <span className="text-muted-foreground">
                    R:R: <strong className="text-foreground">{cand.risk_reward_actual || '1:5'}</strong>
                  </span>
                  <span className="text-muted-foreground">
                    Win Rate: <strong className="text-emerald-500">{cand.win_rate_est || '—'}</strong>
                  </span>
                  <span className={`inline-flex items-center text-xs ${isSelected ? 'text-amber-500 font-bold' : 'text-muted-foreground'}`}>
                    {isSelected ? '✓ Selected' : 'Select'}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Selected Strategy Deep Metrics */}
      {selectedCandidate && (
        <div className="mt-3 rounded-lg border border-border/60 bg-muted/20 p-3">
          <div className="flex items-center justify-between text-xs text-muted-foreground mb-2">
            <span className="font-semibold text-foreground">
              Master Plan: {selectedCandidate.strategy_name}
            </span>
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="flex items-center gap-1 hover:text-foreground text-[11px]"
            >
              {showDetails ? 'Hide Details' : 'Show Details'}
              {showDetails ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
            </button>
          </div>

          {showDetails && (
            <div className="space-y-3">
              {/* Legs Table */}
              {selectedCandidate.legs && selectedCandidate.legs.length > 0 && (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-[11px]">
                    <thead>
                      <tr className="border-b border-border/60 text-muted-foreground">
                        <th className="pb-1 font-semibold">Leg Action</th>
                        <th className="pb-1 font-semibold">Type</th>
                        <th className="pb-1 font-semibold">Strike</th>
                        <th className="pb-1 font-semibold text-right">Est. Premium</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border/30">
                      {selectedCandidate.legs.map((leg, idx) => (
                        <tr key={idx} className="hover:bg-muted/40">
                          <td className="py-1">
                            <span
                              className={`font-bold ${
                                leg.action === 'BUY' ? 'text-emerald-500' : 'text-rose-500'
                              }`}
                            >
                              {leg.action}
                            </span>
                          </td>
                          <td className="py-1 font-mono">{leg.type}</td>
                          <td className="py-1 font-mono font-semibold text-foreground">
                            {strategyData.currency || '₹'}
                            {leg.strike}
                          </td>
                          <td className="py-1 text-right font-mono text-muted-foreground">
                            {strategyData.currency || '₹'}
                            {leg.premium_est}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Quantitative Metrics Grid */}
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 pt-1 text-[11px]">
                <div className="rounded bg-card/60 p-2 border border-border/40">
                  <span className="text-muted-foreground block text-[10px] uppercase">Max Loss/Lot</span>
                  <span className="font-semibold text-rose-500">
                    {selectedCandidate.max_loss_per_lot || 'Defined'}
                  </span>
                </div>
                <div className="rounded bg-card/60 p-2 border border-border/40">
                  <span className="text-muted-foreground block text-[10px] uppercase">Max Gain/Lot</span>
                  <span className="font-semibold text-emerald-500">
                    {selectedCandidate.max_gain_per_lot || 'Target'}
                  </span>
                </div>
                <div className="rounded bg-card/60 p-2 border border-border/40">
                  <span className="text-muted-foreground block text-[10px] uppercase">Target Price</span>
                  <span className="font-semibold text-foreground">
                    {selectedCandidate.target || 'N/A'}
                  </span>
                </div>
                <div className="rounded bg-card/60 p-2 border border-border/40">
                  <span className="text-muted-foreground block text-[10px] uppercase">Stop Loss</span>
                  <span className="font-semibold text-amber-500">
                    {selectedCandidate.stop_loss || 'Defined'}
                  </span>
                </div>
              </div>

              {selectedCandidate.rationale && (
                <p className="text-[11px] text-muted-foreground italic">
                  "{selectedCandidate.rationale}"
                </p>
              )}
            </div>
          )}
        </div>
      )}

      {/* Action Hash & Security Footer */}
      <div className="mt-3 flex flex-wrap items-center justify-between gap-2 text-[10px] text-muted-foreground border-t border-border/40 pt-2">
        <div className="flex items-center gap-1 font-mono">
          <span>SHA-256:</span>
          <span className="truncate max-w-[140px] sm:max-w-[220px]">
            {request.action_hash || 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'}
          </span>
          <button
            onClick={copyActionHash}
            className="hover:text-foreground inline-flex items-center p-0.5"
            title="Copy Action Hash"
          >
            {copiedHash ? <Check className="h-2.5 w-2.5 text-emerald-500" /> : <Copy className="h-2.5 w-2.5" />}
          </button>
        </div>
        <span>Fail-closed policy active (120s TTL)</span>
      </div>

      {/* Error Message */}
      {errorMessage && (
        <div className="mt-2 rounded bg-rose-500/10 p-2 text-xs text-rose-500 border border-rose-500/30">
          {errorMessage}
        </div>
      )}

      {/* Interactive Action Buttons */}
      {status === 'pending' && (
        <div className="mt-4 flex flex-wrap items-center justify-end gap-2.5 pt-1">
          <button
            onClick={() => handleDecision('deny')}
            disabled={isSubmitting}
            className="rounded-lg border border-border px-3.5 py-1.5 text-xs font-semibold text-muted-foreground hover:bg-muted/80 hover:text-foreground transition disabled:opacity-50"
          >
            Reject Strategy
          </button>
          <button
            onClick={() => handleDecision('approve')}
            disabled={isSubmitting}
            className="flex items-center gap-1.5 rounded-lg bg-emerald-600 px-4 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-emerald-500 transition disabled:opacity-50"
          >
            {isSubmitting ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Check className="h-3.5 w-3.5" />
            )}
            <span>Approve Master of Technology ({selectedCandidate?.strategy_name || 'Strategy'})</span>
          </button>
        </div>
      )}
    </div>
  );
}