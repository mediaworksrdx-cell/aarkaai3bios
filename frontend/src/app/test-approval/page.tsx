'use client';

import React, { useState } from 'react';
import { ToolApprovalCard } from '@/components/chat/ToolApprovalCard';
import { CodeModeSandboxCard } from '@/components/chat/CodeModeSandboxCard';
import { ToolApprovalRequest, CodeModeExecution } from '@/types';
import { ArrowLeft, RefreshCw, CheckCircle2 } from 'lucide-react';
import Link from 'next/link';

export default function TestApprovalPage() {
  const [activeTab, setActiveTab] = useState<'approvals' | 'sandbox'>('approvals');
  const [resolvedLog, setResolvedLog] = useState<string[]>([]);

  // Demo interactive pending request
  const [pendingReq, setPendingReq] = useState<ToolApprovalRequest>({
    approval_id: 'appr-demo-849204',
    tool_name: 'filesystem.write_file',
    arguments: {
      path: 'modules/critical_engine.py',
      mode: 'w',
      content: 'def run():\n    return "Approved Mutation"',
      backup: true,
    },
    mutation_risk: 'critical',
    action_hash: '8f4e2b8109d736a49c6d482937be415f9bce664727227bea3801c24294a4c479',
    description: 'Write updated engine parameters to modules/critical_engine.py',
    timeout_seconds: 120,
    created_at: Date.now(),
    status: 'pending',
  });

  const highRiskReq: ToolApprovalRequest = {
    approval_id: 'appr-demo-high-7721',
    tool_name: 'bash.execute',
    arguments: {
      command: 'systemctl restart nginx',
      timeout_sec: 15,
    },
    mutation_risk: 'high',
    action_hash: '3a92f5c415b58a10ad629bce664775fd381d812c8b17743392b5fb78f8488f247',
    description: 'Execute system command to reload Nginx reverse proxy configuration',
    timeout_seconds: 90,
    created_at: Date.now() - 30000,
    status: 'pending',
  };

  const preApprovedReq: ToolApprovalRequest = {
    approval_id: 'appr-demo-approved-1102',
    tool_name: 'git.checkout',
    arguments: {
      branch: 'main',
      force: false,
    },
    mutation_risk: 'medium',
    action_hash: '2b5fb78f8488f2476eb9a1774339d812c8b75fd381bce664727227beb09e42175',
    description: 'Switch repository HEAD to branch main',
    timeout_seconds: 120,
    created_at: Date.now() - 60000,
    status: 'approved',
    resolved_by: 'operator@aarkaa.ai',
    resolved_at: Date.now() - 10000,
  };

  const rejectedReq: ToolApprovalRequest = {
    approval_id: 'appr-demo-rejected-9934',
    tool_name: 'postgres.drop_table',
    arguments: {
      table_name: 'temp_audit_cache',
    },
    mutation_risk: 'critical',
    action_hash: 'f9d2b8d32cde4c764d81dbbec3f5bc53d8e2a9f354aa1aa77e8fc2a0080b06c55',
    description: 'Drop PostgreSQL table temp_audit_cache',
    timeout_seconds: 120,
    created_at: Date.now() - 90000,
    status: 'rejected',
    rejection_reason: 'Table drop not authorized in production scope',
    resolved_by: 'security_auditor',
    resolved_at: Date.now() - 45000,
  };

  const demoExecution: CodeModeExecution = {
    execution_id: 'exec-demo-4482',
    script: `def execute_pipeline():\n    # Phase 1: Check git status\n    status = run_tool("git.status")\n    # Phase 2: Compute delta metrics\n    result = evaluate_delta(status)\n    return {"success": True, "delta": result}`,
    status: 'completed',
    steps: [
      {
        step_id: 'step-1',
        tool_name: 'git.status',
        arguments: { repo: 'current' },
        status: 'completed',
        duration_ms: 18,
        output: 'On branch main\nYour branch is up to date with origin/main.\nnothing to commit, working tree clean',
      },
      {
        step_id: 'step-2',
        tool_name: 'filesystem.read_file',
        arguments: { path: 'config.py' },
        status: 'completed',
        duration_ms: 6,
        output: 'MODEL_PATH = "models/f16"\nMAX_TOKENS = 4096',
      },
      {
        step_id: 'step-3',
        tool_name: 'filesystem.write_file',
        arguments: { path: 'var/approvals.db' },
        status: 'completed',
        duration_ms: 12,
        output: 'Write operation committed via CAS gate.',
      },
    ],
    console_output: [
      '[00:00.012] [sandbox:init] Spawning gVisor microVM container...',
      '[00:00.084] [sandbox:net] Network namespace: airgapped (loopback only).',
      '[00:00.120] [step:1] Executing git.status...',
      '[00:00.138] [step:1] Exit code 0 (18ms).',
      '[00:00.145] [step:2] Executing filesystem.read_file...',
      '[00:00.151] [step:2] Exit code 0 (6ms).',
      '[00:00.160] [step:3] Approval gate signature verified for filesystem.write_file.',
      '[00:00.172] [sandbox:done] Execution completed safely in 172ms.',
    ],
    security_boundaries: {
      network_access: false,
      file_system_scope: 'workspace_isolated',
      max_execution_time_sec: 30,
      mutation_allowed: true,
    },
    created_at: Date.now() - 4000,
    completed_at: Date.now(),
  };

  const handleResolve = async (approvalId: string, decision: 'approve' | 'deny', reason?: string) => {
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = `[${timestamp}] Gate ${approvalId.substring(0, 12)} -> ${decision.toUpperCase()}${reason ? ` (Reason: ${reason})` : ''}`;
    setResolvedLog((prev) => [logEntry, ...prev]);

    if (approvalId === pendingReq.approval_id) {
      setPendingReq((prev) => ({
        ...prev,
        status: decision === 'approve' ? 'approved' : 'rejected',
        resolved_at: Date.now(),
        resolved_by: 'local_operator',
        rejection_reason: reason,
      }));
    }
  };

  const handleResetPending = () => {
    setPendingReq({
      approval_id: `appr-demo-${Math.floor(100000 + Math.random() * 900000)}`,
      tool_name: 'filesystem.write_file',
      arguments: {
        path: 'modules/critical_engine.py',
        mode: 'w',
        content: 'def run():\n    return "Approved Mutation"',
        backup: true,
      },
      mutation_risk: 'critical',
      action_hash: '8f4e2b8109d736a49c6d482937be415f9bce664727227bea3801c24294a4c479',
      description: 'Write updated engine parameters to modules/critical_engine.py',
      timeout_seconds: 120,
      created_at: Date.now(),
      status: 'pending',
    });
  };

  return (
    <div className="min-h-screen bg-[var(--bg-primary)] p-4 sm:p-8 overflow-y-auto font-sans">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Top bar */}
        <div className="flex items-center justify-between border-b border-[var(--border)] pb-4">
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] border border-[var(--border)] transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to Chat</span>
            </Link>
            <h1 className="text-base font-bold text-[var(--text-primary)]">
              Antigravity Approval Card & Sandbox Verification Suite
            </h1>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setActiveTab('approvals')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                activeTab === 'approvals'
                  ? 'bg-[var(--accent-primary)] text-white shadow-sm'
                  : 'text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)]'
              }`}
            >
              Approval Cards
            </button>
            <button
              onClick={() => setActiveTab('sandbox')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                activeTab === 'sandbox'
                  ? 'bg-[var(--accent-primary)] text-white shadow-sm'
                  : 'text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)]'
              }`}
            >
              CodeMode Sandbox
            </button>
          </div>
        </div>

        {/* Tab 1: Approval Cards Verification */}
        {activeTab === 'approvals' && (
          <div className="space-y-6">
            {/* Live Interactive Card */}
            <div className="p-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-strong)] space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wider">
                    1. Live Interactive Pending Card (Click Approve or Deny)
                  </h2>
                  <p className="text-[11px] text-[var(--text-tertiary)]">
                    Features real-time 120s countdown, parameter accordion, copyable action hash, and denial reason feedback.
                  </p>
                </div>
                <button
                  onClick={handleResetPending}
                  className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] border border-[var(--border)] transition-colors"
                  title="Reset card to pending state"
                >
                  <RefreshCw className="w-3 h-3" />
                  <span>Reset Demo</span>
                </button>
              </div>

              <ToolApprovalCard request={pendingReq} onResolve={handleResolve} />

              {resolvedLog.length > 0 && (
                <div className="mt-3 p-2.5 rounded-lg bg-[var(--code-bg)] border border-[var(--border)] text-[11px] font-mono text-[var(--text-secondary)] space-y-1">
                  <span className="text-[10px] uppercase font-bold text-[var(--text-tertiary)] block">
                    Local Resolution Event Log:
                  </span>
                  {resolvedLog.map((log, idx) => (
                    <div key={idx} className="text-emerald-600 dark:text-emerald-400">
                      ✓ {log}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Static State Variants */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)] space-y-2">
                <h3 className="text-xs font-bold text-[var(--text-primary)]">
                  2. Pre-Approved State (Immutable)
                </h3>
                <p className="text-[11px] text-[var(--text-tertiary)]">
                  Displays verified checkmark, resolution metadata, and disabled CAS gate.
                </p>
                <ToolApprovalCard request={preApprovedReq} />
              </div>

              <div className="p-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)] space-y-2">
                <h3 className="text-xs font-bold text-[var(--text-primary)]">
                  3. Rejected State (Operator Denial)
                </h3>
                <p className="text-[11px] text-[var(--text-tertiary)]">
                  Displays red rejection badge and recorded rejection rationale.
                </p>
                <ToolApprovalCard request={rejectedReq} />
              </div>
            </div>

            {/* High Risk Command Card */}
            <div className="p-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)] space-y-2">
              <h3 className="text-xs font-bold text-[var(--text-primary)]">
                4. High Risk Bash Command Gate
              </h3>
              <p className="text-[11px] text-[var(--text-tertiary)]">
                Intercepts mutating host commands with amber risk badge.
              </p>
              <ToolApprovalCard request={highRiskReq} onResolve={handleResolve} />
            </div>
          </div>
        )}

        {/* Tab 2: CodeMode Sandbox Tray */}
        {activeTab === 'sandbox' && (
          <div className="p-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-strong)] space-y-3">
            <div>
              <h2 className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wider">
                CodeMode Sandbox Execution Tray
              </h2>
              <p className="text-[11px] text-[var(--text-tertiary)]">
                Includes Tool Timeline with execution durations, Generated Script with copy button, and raw Console Output stream.
              </p>
            </div>

            <CodeModeSandboxCard execution={demoExecution} />
          </div>
        )}
      </div>
    </div>
  );
}
