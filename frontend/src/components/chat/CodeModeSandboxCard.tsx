'use client';

import React, { useState } from 'react';
import {
  Code,
  Terminal,
  Activity,
  ShieldCheck,
  ShieldAlert,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  XCircle,
  Clock,
  Loader2,
  Copy,
  Check,
  AlertOctagon,
  Maximize2,
  Minimize2,
} from 'lucide-react';
import { CodeModeExecution, CodeModeExecutionStep } from '@/types';

interface CodeModeSandboxCardProps {
  execution: CodeModeExecution;
  className?: string;
}

type TabType = 'script' | 'timeline' | 'console';

export function CodeModeSandboxCard({ execution, className = '' }: CodeModeSandboxCardProps) {
  const [isExpanded, setIsExpanded] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<TabType>('timeline');
  const [copiedScript, setCopiedScript] = useState<boolean>(false);
  const [expandedStepId, setExpandedStepId] = useState<string | null>(null);

  const status = execution.status || 'completed';
  const steps = execution.steps || [];
  const consoleOutput = execution.console_output || [];
  const boundaries = execution.security_boundaries || {
    network_access: false,
    file_system_scope: 'workspace_isolated',
    max_execution_time_sec: 30,
    mutation_allowed: false,
  };

  const handleCopyScript = () => {
    if (execution.script && typeof navigator !== 'undefined') {
      navigator.clipboard.writeText(execution.script);
      setCopiedScript(true);
      setTimeout(() => setCopiedScript(false), 2000);
    }
  };

  const toggleStep = (stepId: string) => {
    setExpandedStepId((prev) => (prev === stepId ? null : stepId));
  };

  return (
    <div
      className={`my-3.5 rounded-xl border bg-[var(--bg-secondary)] border-[var(--border-strong)] shadow-[var(--shadow-sm)] overflow-hidden transition-all duration-200 ${className}`}
      data-testid="codemode-sandbox-card"
    >
      {/* Top Header Bar */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-[var(--bg-tertiary)]/70 border-b border-[var(--border)]">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-[var(--accent-muted)] border border-[var(--border-accent)] flex items-center justify-center text-[var(--accent-primary)] shadow-xs">
            <Terminal className="w-3.5 h-3.5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-bold text-[var(--text-primary)]">
                CodeMode Sandbox
              </span>
              <span className="font-mono text-[10px] text-[var(--text-tertiary)]">
                #{execution.execution_id.substring(0, 8)}
              </span>
            </div>
          </div>
        </div>

        {/* Status Badge & Collapsible Toggle */}
        <div className="flex items-center gap-2">
          {status === 'running' && (
            <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-blue-500/10 border border-blue-500/30 text-blue-600 dark:text-blue-400 animate-pulse">
              <Loader2 className="w-3 h-3 animate-spin" />
              <span>Executing</span>
            </div>
          )}
          {status === 'completed' && (
            <div className="flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-500/10 border border-emerald-500/30 text-emerald-600 dark:text-emerald-400">
              <CheckCircle2 className="w-3 h-3" />
              <span>Sandbox Clean</span>
            </div>
          )}
          {status === 'failed' && (
            <div className="flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-rose-500/10 border border-rose-500/30 text-rose-600 dark:text-rose-400">
              <XCircle className="w-3 h-3" />
              <span>Execution Failed</span>
            </div>
          )}
          {status === 'paused' && (
            <div className="flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-amber-500/10 border border-amber-500/30 text-amber-600 dark:text-amber-400">
              <Clock className="w-3 h-3" />
              <span>Gate Paused</span>
            </div>
          )}

          <button
            onClick={() => setIsExpanded(!isExpanded)}
            type="button"
            className="p-1 rounded-md text-[var(--text-tertiary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] transition-colors cursor-pointer"
            title={isExpanded ? 'Collapse tray' : 'Expand tray'}
          >
            {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {isExpanded && (
        <>
          {/* Security Boundaries strip */}
          <div className="flex flex-wrap items-center justify-between gap-2 px-4 py-1.5 bg-[var(--bg-tertiary)]/40 border-b border-[var(--border)] text-[10px] text-[var(--text-secondary)]">
            <div className="flex items-center gap-3">
              <span className="flex items-center gap-1">
                {boundaries.network_access ? (
                  <ShieldAlert className="w-3 h-3 text-amber-500" />
                ) : (
                  <ShieldCheck className="w-3 h-3 text-emerald-500" />
                )}
                <span>Network: {boundaries.network_access ? 'Enabled' : 'Airgapped'}</span>
              </span>
              <span className="flex items-center gap-1">
                <ShieldCheck className="w-3 h-3 text-emerald-500" />
                <span>Scope: {boundaries.file_system_scope}</span>
              </span>
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3 text-blue-500" />
                <span>Limit: {boundaries.max_execution_time_sec}s</span>
              </span>
            </div>
            <div>
              <span className="font-mono text-[9.5px] uppercase tracking-wider text-[var(--text-tertiary)]">
                {steps.length} steps · {consoleOutput.length} logs
              </span>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex items-center gap-1 px-3 pt-2 bg-[var(--bg-secondary)] border-b border-[var(--border)]">
            <button
              onClick={() => setActiveTab('timeline')}
              type="button"
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-t-lg text-xs font-semibold transition-colors cursor-pointer ${
                activeTab === 'timeline'
                  ? 'border-b-2 border-[var(--accent-primary)] text-[var(--accent-primary)] bg-[var(--bg-tertiary)]/40'
                  : 'text-[var(--text-tertiary)] hover:text-[var(--text-primary)]'
              }`}
            >
              <Activity className="w-3.5 h-3.5" />
              <span>Tool Timeline ({steps.length})</span>
            </button>

            <button
              onClick={() => setActiveTab('script')}
              type="button"
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-t-lg text-xs font-semibold transition-colors cursor-pointer ${
                activeTab === 'script'
                  ? 'border-b-2 border-[var(--accent-primary)] text-[var(--accent-primary)] bg-[var(--bg-tertiary)]/40'
                  : 'text-[var(--text-tertiary)] hover:text-[var(--text-primary)]'
              }`}
            >
              <Code className="w-3.5 h-3.5" />
              <span>Generated Script</span>
            </button>

            <button
              onClick={() => setActiveTab('console')}
              type="button"
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-t-lg text-xs font-semibold transition-colors cursor-pointer ${
                activeTab === 'console'
                  ? 'border-b-2 border-[var(--accent-primary)] text-[var(--accent-primary)] bg-[var(--bg-tertiary)]/40'
                  : 'text-[var(--text-tertiary)] hover:text-[var(--text-primary)]'
              }`}
            >
              <Terminal className="w-3.5 h-3.5" />
              <span>Console Output ({consoleOutput.length})</span>
            </button>
          </div>

          {/* Tab Content Areas */}
          <div className="p-3 bg-[var(--bg-primary)] min-h-[140px] max-h-[360px] overflow-y-auto">
            {/* 1. TIMELINE TAB */}
            {activeTab === 'timeline' && (
              <div className="space-y-2">
                {steps.length === 0 ? (
                  <div className="p-4 text-center text-xs text-[var(--text-tertiary)] italic">
                    No tools invoked in this execution.
                  </div>
                ) : (
                  steps.map((step, idx) => {
                    const isStepExpanded = expandedStepId === step.step_id;
                    return (
                      <div
                        key={step.step_id || idx}
                        className="rounded-lg border border-[var(--border)] bg-[var(--bg-secondary)] overflow-hidden"
                      >
                        <button
                          onClick={() => toggleStep(step.step_id)}
                          type="button"
                          className="w-full flex items-center justify-between p-2.5 hover:bg-[var(--bg-tertiary)]/40 text-left transition-colors cursor-pointer"
                        >
                          <div className="flex items-center gap-2">
                            <span className="w-5 h-5 rounded-full bg-[var(--bg-tertiary)] flex items-center justify-center text-[10px] font-mono font-bold text-[var(--text-secondary)]">
                              {idx + 1}
                            </span>
                            <span className="font-mono text-xs font-bold text-[var(--text-primary)]">
                              {step.tool_name}
                            </span>
                            {step.duration_ms !== undefined && (
                              <span className="text-[10px] text-[var(--text-tertiary)]">
                                {step.duration_ms}ms
                              </span>
                            )}
                          </div>

                          <div className="flex items-center gap-2">
                            {step.status === 'completed' && (
                              <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-emerald-600 dark:text-emerald-400">
                                <CheckCircle2 className="w-3 h-3" />
                                <span>Passed</span>
                              </span>
                            )}
                            {step.status === 'running' && (
                              <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-blue-600 dark:text-blue-400 animate-pulse">
                                <Loader2 className="w-3 h-3 animate-spin" />
                                <span>Running</span>
                              </span>
                            )}
                            {step.status === 'failed' && (
                              <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-rose-600 dark:text-rose-400">
                                <XCircle className="w-3 h-3" />
                                <span>Failed</span>
                              </span>
                            )}
                            {step.status === 'blocked' && (
                              <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-amber-600 dark:text-amber-400">
                                <AlertOctagon className="w-3 h-3" />
                                <span>Blocked</span>
                              </span>
                            )}

                            {isStepExpanded ? (
                              <ChevronUp className="w-3.5 h-3.5 text-[var(--text-tertiary)]" />
                            ) : (
                              <ChevronDown className="w-3.5 h-3.5 text-[var(--text-tertiary)]" />
                            )}
                          </div>
                        </button>

                        {isStepExpanded && (
                          <div className="p-3 border-t border-[var(--border)] bg-[var(--code-bg)] text-[11px] font-mono space-y-2">
                            {step.arguments && (
                              <div>
                                <span className="text-[10px] text-[var(--text-tertiary)] uppercase font-semibold block mb-0.5">
                                  Arguments:
                                </span>
                                <pre className="m-0 whitespace-pre-wrap text-[var(--text-primary)]">
                                  {JSON.stringify(step.arguments, null, 2)}
                                </pre>
                              </div>
                            )}

                            {step.output && (
                              <div>
                                <span className="text-[10px] text-emerald-600 uppercase font-semibold block mb-0.5">
                                  Step Output:
                                </span>
                                <pre className="m-0 whitespace-pre-wrap text-emerald-700 dark:text-emerald-300">
                                  {step.output}
                                </pre>
                              </div>
                            )}

                            {step.error && (
                              <div>
                                <span className="text-[10px] text-rose-600 uppercase font-semibold block mb-0.5">
                                  Error:
                                </span>
                                <pre className="m-0 whitespace-pre-wrap text-rose-600 dark:text-rose-400">
                                  {step.error}
                                </pre>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })
                )}
              </div>
            )}

            {/* 2. SCRIPT TAB */}
            {activeTab === 'script' && (
              <div className="relative rounded-lg bg-[var(--code-bg)] border border-[var(--code-border)] p-3">
                <div className="flex items-center justify-between pb-2 mb-2 border-b border-[var(--border)]">
                  <span className="text-[10px] font-mono uppercase text-[var(--text-tertiary)] font-bold">
                    Sandbox Code (Isolated Execution)
                  </span>
                  <button
                    onClick={handleCopyScript}
                    type="button"
                    className="flex items-center gap-1 text-[11px] text-[var(--text-secondary)] hover:text-[var(--text-primary)] cursor-pointer"
                  >
                    {copiedScript ? (
                      <>
                        <Check className="w-3 h-3 text-emerald-500" />
                        <span className="text-emerald-500">Copied</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-3 h-3" />
                        <span>Copy Code</span>
                      </>
                    )}
                  </button>
                </div>
                <pre className="text-xs font-mono text-[var(--text-primary)] whitespace-pre-wrap leading-relaxed overflow-x-auto m-0">
                  <code>{execution.script || '# No script captured.'}</code>
                </pre>
              </div>
            )}

            {/* 3. CONSOLE OUTPUT TAB */}
            {activeTab === 'console' && (
              <div className="rounded-lg bg-zinc-950 p-3 font-mono text-xs text-zinc-100 min-h-[120px] overflow-x-auto">
                <div className="text-[10px] text-zinc-500 pb-1 mb-2 border-b border-zinc-800 flex items-center justify-between">
                  <span>SANDBOX STDOUT / STDERR STREAM</span>
                  <span>LINES: {consoleOutput.length}</span>
                </div>
                {consoleOutput.length === 0 ? (
                  <span className="text-zinc-600 italic">No console logs emitted.</span>
                ) : (
                  consoleOutput.map((line, idx) => (
                    <div key={idx} className="leading-5 whitespace-pre-wrap text-zinc-300">
                      <span className="text-zinc-600 mr-2 select-none">{idx + 1}</span>
                      {line}
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
