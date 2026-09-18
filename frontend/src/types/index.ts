export type EffortLevel = 'low' | 'medium' | 'high';

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: number;
  modelUsed?: string;
  effort?: EffortLevel;
  isStreaming?: boolean;
  error?: string;
  feedback?: 'up' | 'down';
  approvalRequest?: ToolApprovalRequest;
  codeModeExecution?: CodeModeExecution;
  mcpEvents?: McpEvent[];
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  createdAt: number;
  updatedAt: number;
  model: string;
  effort?: EffortLevel;
}

export interface StreamChunk {
  type?: 'content' | 'token' | 'status' | 'metadata' | 'final' | 'final_response' | 'error' | string;
  token?: string;
  content?: string;
  text?: string;
  status?: string;
  detail?: string;
  response?: string;
  model_used?: string;
  processing_time?: number;
  sources?: string[];
  [key: string]: any;
}

export interface ModelOption {
  id: string;
  label: string;
  name?: string;
  description: string;
  icon?: string;
  badge?: string;
  provider?: string;
  tier?: 'standard' | 'premium' | 'flagship';
}

export interface User {
  id: string;
  email: string;
  name: string;
  picture?: string;
}

// ==========================================
// AARKAAI Approval Gates & Risk Levels
// ==========================================

export type RiskLevel = 'read_only' | 'low' | 'medium' | 'high' | 'critical';

export type ApprovalStatus = 'pending' | 'approved' | 'rejected' | 'timeout' | 'expired';

export interface ModelPersona {
  provider: 'aarka' | 'gemini' | 'claude' | string;
  name: string;
  badge: string;
  badge_color: string;
  accent_color: string;
  agent_ref: string;
}

export interface DynamicApprovalOption {
  id: number;
  action: 'allow_once' | 'allow_and_run' | 'allow_and_stream' | 'allow_in_conversation' | 'customize' | 'always_allow' | 'dry_run' | 'select_alternative' | 'deny' | string;
  label: string;
  detail?: string;
  recommended?: boolean;
}

export interface ToolApprovalRequest {
  approval_id: string;
  tool_name: string;
  arguments: Record<string, any>;
  mutation_risk: RiskLevel;
  action_hash: string;
  description: string;
  timeout_seconds: number;
  created_at: number;
  status: ApprovalStatus;
  resolved_by?: string;
  resolved_at?: number;
  rejection_reason?: string;
  human_summary?: string;
  target_resource?: string;
  diff_preview?: string;
  command_preview?: string;
  model_persona?: ModelPersona;
  dynamic_options?: DynamicApprovalOption[];
}

export interface ToolApprovalDecision {
  decision: 'approve' | 'deny';
  reason?: string;
  selected_master_strategy?: string;
}

export interface CandidateFinanceStrategy {
  candidate_id: string;
  category: string;
  technology_tag: string;
  strategy_name: string;
  strategy_type: string;
  legs: Array<{ action: string; type: string; strike: number; premium_est: number }>;
  entry_trigger?: string;
  stop_loss?: string;
  target?: string;
  max_loss_per_lot?: string;
  max_gain_per_lot?: string;
  risk_reward_actual?: string;
  win_rate_est?: string;
  rationale?: string;
}

export interface FinanceStrategyApprovalData {
  symbol: string;
  current_price: number;
  lot_size: number;
  expiry: string;
  signal: string;
  currency: string;
  master_recommended: string;
  candidates: CandidateFinanceStrategy[];
  disclaimer?: string;
}

// ==========================================
// CodeMode Sandbox Execution
// ==========================================

export interface CodeModeExecutionStep {
  step_id: string;
  tool_name: string;
  arguments?: Record<string, any>;
  status: 'running' | 'completed' | 'failed' | 'blocked';
  duration_ms?: number;
  output?: string;
  error?: string;
}

export interface CodeModeSecurityBoundaries {
  network_access: boolean;
  file_system_scope: string;
  max_execution_time_sec: number;
  mutation_allowed: boolean;
}

export interface CodeModeExecution {
  execution_id: string;
  script: string;
  status: 'initializing' | 'running' | 'completed' | 'failed' | 'paused';
  steps: CodeModeExecutionStep[];
  console_output: string[];
  security_boundaries: CodeModeSecurityBoundaries;
  created_at: number;
  completed_at?: number;
}

// ==========================================
// Model Context Protocol (MCP) Management
// ==========================================

export interface McpToolPermissions {
  network: boolean;
  filesystem: boolean;
  shell: boolean;
  mutating: boolean;
}

export interface McpTool {
  name: string;
  description: string;
  input_schema?: Record<string, any>;
  mutation_risk: RiskLevel;
  permissions: McpToolPermissions;
  enabled: boolean;
}

export interface McpServerInfo {
  id: string;
  name: string;
  description?: string;
  transport: 'stdio' | 'sse' | 'websocket' | 'http';
  status: 'connected' | 'disconnected' | 'error' | 'disabled';
  enabled: boolean;
  ping_ms?: number;
  error_message?: string;
  tools: McpTool[];
  total_calls?: number;
}

export interface McpEvent {
  event_type: 'call_start' | 'call_success' | 'call_error';
  server_id: string;
  tool_name: string;
  timestamp: number;
  duration_ms?: number;
  arguments?: Record<string, any>;
  error?: string;
}

// ==========================================
// SSE Typed Stream Envelope
// ==========================================

export interface StreamEvent {
  event_id: string;
  sequence: number;
  event_type:
    | 'text_chunk'
    | 'approval_request'
    | 'approval_resolved'
    | 'codemode_execution'
    | 'codemode_step'
    | 'mcp_event'
    | 'final_response'
    | 'error';
  timestamp: number;
  payload: any;
}

