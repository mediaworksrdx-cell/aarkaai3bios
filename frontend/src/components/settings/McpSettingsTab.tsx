'use client';

import React, { useState, useEffect } from 'react';
import {
  Server,
  RefreshCw,
  Power,
  ShieldAlert,
  ShieldCheck,
  Terminal,
  Folder,
  Globe,
  Edit3,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Clock,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { McpServerInfo, McpTool, RiskLevel } from '@/types';
import { fetchMcpServers, toggleMcpServer } from '@/lib/api';

export function McpSettingsTab() {
  const [servers, setServers] = useState<McpServerInfo[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [togglingServerId, setTogglingServerId] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [expandedServerId, setExpandedServerId] = useState<string | null>(null);

  const loadServers = async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const res = await fetchMcpServers();
      if (res && res.servers) {
        setServers(res.servers);
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to load MCP servers');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadServers();
  }, []);

  const handleToggle = async (server: McpServerInfo) => {
    const newEnabled = !server.enabled;
    setTogglingServerId(server.id);
    setErrorMessage(null);

    try {
      const res = await toggleMcpServer(server.id, newEnabled);
      if (res && res.server) {
        setServers((prev) =>
          prev.map((s) => (s.id === server.id ? { ...s, ...res.server } : s))
        );
      } else {
        setServers((prev) =>
          prev.map((s) => (s.id === server.id ? { ...s, enabled: newEnabled } : s))
        );
      }
    } catch (err: any) {
      setErrorMessage(err.message || `Failed to toggle server ${server.id}`);
    } finally {
      setTogglingServerId(null);
    }
  };

  const toggleServerExpand = (serverId: string) => {
    setExpandedServerId((prev) => (prev === serverId ? null : serverId));
  };

  const getRiskBadge = (risk: RiskLevel) => {
    switch (risk) {
      case 'critical':
        return (
          <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/30">
            CRITICAL
          </span>
        );
      case 'high':
        return (
          <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/30">
            HIGH
          </span>
        );
      case 'medium':
        return (
          <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-yellow-500/10 text-yellow-700 dark:text-yellow-400 border border-yellow-500/30">
            MEDIUM
          </span>
        );
      case 'low':
        return (
          <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/30">
            LOW
          </span>
        );
      default:
        return (
          <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30">
            READ ONLY
          </span>
        );
    }
  };

  return (
    <div className="space-y-4" data-testid="mcp-settings-tab">
      {/* Top Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-xs font-bold text-[var(--text-primary)]">
            Model Context Protocol (MCP) Servers
          </h3>
          <p className="text-[11px] text-[var(--text-tertiary)]">
            Inspect, toggle, and audit external tool servers connected to the AARKAAI neural mesh.
          </p>
        </div>
        <button
          onClick={loadServers}
          disabled={isLoading}
          type="button"
          className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] border border-[var(--border)] transition-colors cursor-pointer disabled:opacity-50"
          title="Refresh server status"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Error alert */}
      {errorMessage && (
        <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-600 dark:text-red-400 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Loading Skeleton */}
      {isLoading && servers.length === 0 && (
        <div className="p-8 text-center text-xs text-[var(--text-tertiary)] space-y-2">
          <RefreshCw className="w-5 h-5 animate-spin mx-auto text-[var(--accent-primary)]" />
          <p>Scanning connected Model Context Protocol servers...</p>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && servers.length === 0 && (
        <div className="p-8 rounded-xl border border-dashed border-[var(--border)] text-center space-y-2">
          <Server className="w-8 h-8 text-[var(--text-tertiary)] mx-auto" />
          <h4 className="text-xs font-bold text-[var(--text-primary)]">No MCP Servers Configured</h4>
          <p className="text-[11px] text-[var(--text-tertiary)] max-w-sm mx-auto">
            Configure local or remote MCP servers in <code className="font-mono">mcp_config.yaml</code> to empower Aarka AI with safe tool integration.
          </p>
        </div>
      )}

      {/* Server List */}
      <div className="space-y-3">
        {servers.map((server) => {
          const isToggling = togglingServerId === server.id;
          const isExpanded = expandedServerId === server.id;
          const tools = server.tools || [];

          return (
            <div
              key={server.id}
              className={`rounded-xl border transition-all duration-200 bg-[var(--bg-secondary)] ${
                server.enabled
                  ? 'border-[var(--border-strong)] shadow-[var(--shadow-sm)]'
                  : 'border-[var(--border)] opacity-75'
              }`}
            >
              {/* Server Row */}
              <div className="p-3.5 flex items-center justify-between gap-3">
                <div className="flex items-center gap-3 min-w-0">
                  <div
                    className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 border ${
                      server.enabled
                        ? 'bg-[var(--accent-muted)] border-[var(--border-accent)] text-[var(--accent-primary)]'
                        : 'bg-[var(--bg-tertiary)] border-[var(--border)] text-[var(--text-tertiary)]'
                    }`}
                  >
                    <Server className="w-4 h-4" />
                  </div>

                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-xs text-[var(--text-primary)] truncate">
                        {server.name || server.id}
                      </span>
                      <span className="font-mono text-[9px] uppercase px-1.5 py-0.2 rounded bg-[var(--bg-tertiary)] text-[var(--text-tertiary)]">
                        {server.transport || 'stdio'}
                      </span>
                    </div>

                    <div className="flex items-center gap-2 mt-0.5 text-[11px] text-[var(--text-tertiary)]">
                      {server.enabled ? (
                        <span className="inline-flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-medium">
                          <CheckCircle2 className="w-3 h-3" />
                          <span>Connected</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-zinc-500 font-medium">
                          <XCircle className="w-3 h-3" />
                          <span>Disabled</span>
                        </span>
                      )}

                      {server.ping_ms !== undefined && server.enabled && (
                        <>
                          <span>·</span>
                          <span className="font-mono text-[10px]">{server.ping_ms}ms ping</span>
                        </>
                      )}

                      <span>·</span>
                      <span>{tools.length} tools registered</span>
                    </div>
                  </div>
                </div>

                {/* Controls */}
                <div className="flex items-center gap-2.5 flex-shrink-0">
                  {/* Tool List Toggle Button */}
                  <button
                    onClick={() => toggleServerExpand(server.id)}
                    type="button"
                    className="p-1.5 rounded-lg text-[var(--text-tertiary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] transition-colors cursor-pointer"
                    title={isExpanded ? 'Collapse tools' : 'View tools & permissions'}
                  >
                    {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </button>

                  {/* Enable / Disable Switch */}
                  <button
                    onClick={() => handleToggle(server)}
                    disabled={isToggling}
                    type="button"
                    role="switch"
                    aria-checked={server.enabled}
                    className={`relative inline-flex h-5 w-9 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none disabled:opacity-50 ${
                      server.enabled ? 'bg-[var(--accent-primary)]' : 'bg-zinc-300 dark:bg-zinc-700'
                    }`}
                  >
                    <span
                      aria-hidden="true"
                      className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow-sm ring-0 transition duration-200 ease-in-out ${
                        server.enabled ? 'translate-x-4' : 'translate-x-0'
                      }`}
                    />
                  </button>
                </div>
              </div>

              {/* Tools list dropdown */}
              {isExpanded && (
                <div className="px-3.5 pb-3.5 pt-1 border-t border-[var(--border)] bg-[var(--bg-primary)]/50 rounded-b-xl space-y-2">
                  <div className="text-[10px] uppercase font-bold text-[var(--text-tertiary)] tracking-wider">
                    Registered Server Capabilities & Permissions
                  </div>

                  {tools.length === 0 ? (
                    <div className="text-xs text-[var(--text-tertiary)] italic py-1">
                      No tools exposed by this server.
                    </div>
                  ) : (
                    <div className="space-y-1.5">
                      {tools.map((tool) => {
                        const perms = tool.permissions || {
                          network: false,
                          filesystem: false,
                          shell: false,
                          mutating: false,
                        };

                        return (
                          <div
                            key={tool.name}
                            className="p-2 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] flex flex-col sm:flex-row sm:items-center justify-between gap-2"
                          >
                            <div className="min-w-0">
                              <div className="flex items-center gap-1.5">
                                <span className="font-mono text-xs font-bold text-[var(--text-primary)]">
                                  {tool.name}
                                </span>
                                {getRiskBadge(tool.mutation_risk)}
                              </div>
                              <p className="text-[11px] text-[var(--text-secondary)] mt-0.5 line-clamp-1">
                                {tool.description || 'No description provided.'}
                              </p>
                            </div>

                            {/* Permission chips */}
                            <div className="flex items-center gap-1.5 flex-wrap">
                              {perms.network && (
                                <span
                                  className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] bg-blue-500/10 text-blue-600 dark:text-blue-400 font-medium"
                                  title="Network Access Permitted"
                                >
                                  <Globe className="w-3 h-3" />
                                  <span>Net</span>
                                </span>
                              )}
                              {perms.filesystem && (
                                <span
                                  className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] bg-amber-500/10 text-amber-600 dark:text-amber-400 font-medium"
                                  title="Filesystem Read/Write Permitted"
                                >
                                  <Folder className="w-3 h-3" />
                                  <span>FS</span>
                                </span>
                              )}
                              {perms.shell && (
                                <span
                                  className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] bg-purple-500/10 text-purple-600 dark:text-purple-400 font-medium"
                                  title="Shell Execution Permitted"
                                >
                                  <Terminal className="w-3 h-3" />
                                  <span>Shell</span>
                                </span>
                              )}
                              {perms.mutating && (
                                <span
                                  className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] bg-rose-500/10 text-rose-600 dark:text-rose-400 font-medium"
                                  title="State Mutating Tool — Triggers Approval Gate"
                                >
                                  <Edit3 className="w-3 h-3" />
                                  <span>Mutating</span>
                                </span>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
