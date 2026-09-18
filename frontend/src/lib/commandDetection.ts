import { ToolApprovalRequest } from '@/types';

/**
 * Command & Action Intent Detection Utility
 * Detects whether user input in the chat text field is a terminal command,
 * file creation/modification intent, or quantitative finance strategy screening.
 */

const KNOWN_CLI_COMMANDS = new Set([
  'df', 'du', 'ls', 'pwd', 'cd', 'whoami', 'id', 'uname', 'hostname',
  'ps', 'top', 'htop', 'kill', 'pkill', 'free', 'uptime', 'vmstat',
  'iostat', 'netstat', 'ss', 'lsof', 'cat', 'grep', 'egrep', 'fgrep',
  'head', 'tail', 'awk', 'sed', 'find', 'echo', 'touch', 'mkdir',
  'rmdir', 'rm', 'cp', 'mv', 'chmod', 'chown', 'curl', 'wget', 'ping',
  'traceroute', 'dig', 'nslookup', 'git', 'npm', 'npx', 'yarn',
  'pnpm', 'pip', 'pip3', 'python', 'python3', 'node', 'pytest',
  'cargo', 'docker', 'docker-compose', 'podman', 'kubectl', 'helm',
  'systemctl', 'journalctl', 'service', 'sudo', 'bash', 'sh', 'zsh',
  'tar', 'gzip', 'gunzip', 'zip', 'unzip', 'export', 'which', 'whereis',
  'env', 'printenv', 'make', 'cmake', 'gcc', 'g++', 'clang', 'rustc',
  'go', 'mvn', 'gradle', 'terraform', 'ansible', 'ssh', 'scp', 'rsync',
  'date', 'cal', 'wc', 'sort', 'uniq', 'diff', 'clear', 'history',
  'nmap', 'tcpdump', 'ip', 'ifconfig'
]);

const CONVERSATIONAL_STARTERS = [
  'what', 'how', 'why', 'who', 'where', 'when', 'which',
  'can you', 'could you', 'would you', 'should i', 'will you',
  'please', 'tell me', 'explain', 'describe', 'summarize',
  'help', 'write', 'create', 'generate', 'build', 'show me',
  'is there', 'are there', 'do you', 'does it', 'i want',
  'i need', 'give me', 'check if', 'analyze', 'compare'
];

export function isTerminalCommand(raw: string): boolean {
  if (!raw) return false;
  const trimmed = raw.trim();
  if (!trimmed) return false;

  if (trimmed.includes('\n')) {
    const lines = trimmed.split('\n').map((l) => l.trim()).filter(Boolean);
    if (lines.length > 2) return false;
  }

  const clean = trimmed.replace(/^[\$\>#]\s+/, '').trim();
  const lower = clean.toLowerCase();

  for (const starter of CONVERSATIONAL_STARTERS) {
    if (lower.startsWith(starter + ' ') || lower === starter) {
      return false;
    }
  }

  if (clean.endsWith('?')) {
    return false;
  }

  const firstWord = clean.split(/\s+/)[0].toLowerCase();

  if (KNOWN_CLI_COMMANDS.has(firstWord)) {
    const words = clean.split(/\s+/).map((w) => w.toLowerCase());
    const sentenceStopWords = new Set(['the', 'is', 'are', 'was', 'were', 'about', 'because', 'should', 'would', 'could']);
    let stopWordCount = 0;
    for (const w of words) {
      if (sentenceStopWords.has(w)) stopWordCount++;
    }
    if (stopWordCount >= 2) {
      return false;
    }
    return true;
  }

  if (/^(\.|\.\.|\/|[a-zA-Z0-9_\-]+)\/[a-zA-Z0-9_\-\.\/]+/.test(clean)) {
    return true;
  }

  return false;
}

export function detectModelPersona(modelName: string = '') {
  const norm = (modelName || 'aarka').toLowerCase();
  if (norm.includes('claude')) {
    return {
      provider: 'claude' as const,
      name: 'Claude Sonnet',
      badge: 'Claude · Constitutional Safety',
      badge_color: 'border-amber-500/40 bg-amber-500/15 text-amber-700 dark:text-amber-400',
      accent_color: '#C15F3D',
      agent_ref: 'Claude',
    };
  } else if (norm.includes('gemini')) {
    return {
      provider: 'gemini' as const,
      name: 'Gemini Pro',
      badge: 'Gemini · Multimodal Verification',
      badge_color: 'border-blue-500/30 bg-blue-500/10 text-blue-700 dark:text-blue-400',
      accent_color: '#2563EB',
      agent_ref: 'Gemini',
    };
  } else {
    return {
      provider: 'aarka' as const,
      name: 'Aarka AI',
      badge: 'Aarka Engine · Autonomous Execution',
      badge_color: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-400',
      accent_color: '#0D9488',
      agent_ref: 'Aarka',
    };
  }
}

export function detectFileCreationIntent(raw: string): { filename: string; isPython: boolean } | null {
  if (!raw) return null;
  const trimmed = raw.trim();
  const lower = trimmed.toLowerCase();

  const hasActionVerb = /\b(create|write|generate|add|make|save|modify|edit|build)\b/i.test(lower);
  if (!hasActionVerb) return null;

  const fileMatch = trimmed.match(/\b([a-zA-Z0-9_\-\.\/]+\.(?:py|ts|tsx|js|jsx|json|yaml|yml|sh|bash|sql|html|css|env|toml|txt))\b/i);
  if (!fileMatch) return null;

  const filename = fileMatch[1];
  return {
    filename,
    isPython: filename.endsWith('.py'),
  };
}

export function detectFinanceStrategyIntent(raw: string): { symbol: string; signal: 'BULLISH' | 'BEARISH' } | null {
  if (!raw) return null;
  const trimmed = raw.trim();
  const lower = trimmed.toLowerCase();

  const isStrategyKeywords =
    /options?\s+strateg(?:ies|y)|option\s+spread|volatility\s+engine|straddle|strangle|iron\s+condor|screen\s+top\s+(?:bullish|bearish)?\s*options/i.test(lower) ||
    (/\b(screen|scanner|strategies|strategy)\b/i.test(lower) && /\b(nifty|banknifty|finnifty|sensex|options)\b/i.test(lower));

  if (!isStrategyKeywords) return null;

  const tickerMatch = trimmed.match(/\b(NIFTY|BANKNIFTY|FINNIFTY|SENSEX|RELIANCE|TCS|INFY|HDFCBANK|SPY|QQQ|AAPL|MSFT|NVDA|TSLA)\b/i);
  const symbol = tickerMatch ? tickerMatch[1].toUpperCase() : 'NIFTY';
  const signal = lower.includes('bearish') ? 'BEARISH' : 'BULLISH';

  return { symbol, signal };
}

export function detectSubmissionApproval(
  raw: string,
  selectedModel: string = 'aarka'
): ToolApprovalRequest | null {
  if (!raw) return null;
  const trimmed = raw.trim();
  if (!trimmed) return null;

  const persona = detectModelPersona(selectedModel);
  const agentRef = persona.agent_ref;

  // 1. Direct Terminal Command (BashTool)
  if (isTerminalCommand(trimmed)) {
    return {
      approval_id: 'cmd-gate-' + Date.now(),
      tool_name: 'BashTool',
      arguments: { command: trimmed },
      mutation_risk: 'high',
      action_hash: 'cmd-' + Math.random().toString(36).substring(2, 10),
      description: 'Execute terminal command: ' + trimmed,
      human_summary: 'Allow run ' + trimmed + '?',
      command_preview: trimmed,
      timeout_seconds: 120,
      created_at: Date.now(),
      status: 'pending',
      model_persona: persona,
      dynamic_options: [
        {
          id: 1,
          action: 'allow_once',
          label: 'Execute \'' + trimmed + '\' in isolated sandbox',
          detail: 'Run shell command safely within workspace execution constraints.',
          recommended: true,
        },
        {
          id: 2,
          action: 'allow_and_stream',
          label: 'Execute \'' + trimmed + '\' and stream live terminal output',
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
          label: 'Always allow \'' + trimmed + '\' in this session (Always Allow)',
          detail: 'Whitelist this command pattern to prevent redundant authorization gates.',
        },
        {
          id: 5,
          action: 'deny',
          label: 'No (tell ' + agentRef + ' what to do instead)',
          detail: 'Halt command execution and redirect agent workflow.',
        },
      ],
    };
  }

  // 2. Microservice / Script File Creation (FileEditTool)
  const fileIntent = detectFileCreationIntent(trimmed);
  if (fileIntent) {
    const { filename, isPython } = fileIntent;
    const isPy = isPython;
    return {
      approval_id: 'file-gate-' + Date.now(),
      tool_name: 'FileEditTool',
      arguments: { path: filename },
      target_resource: filename,
      mutation_risk: 'high',
      action_hash: 'file-' + Math.random().toString(36).substring(2, 10),
      description: 'Modify file: ' + filename,
      human_summary: 'Allow modify file: ' + filename + '?',
      timeout_seconds: 120,
      created_at: Date.now(),
      status: 'pending',
      model_persona: persona,
      dynamic_options: [
        {
          id: 1,
          action: 'allow_once',
          label: 'Allow & save \'' + filename + '\' to workspace',
          detail: 'Write verified script directly into the workspace root.',
          recommended: true,
        },
        {
          id: 2,
          action: isPy ? 'allow_and_run' : 'allow_in_conversation',
          label: 'Save \'' + filename + '\' and execute immediately (' + (isPy ? 'python ' + filename : 'inspect in workspace') + ')',
          detail: 'Atomic disk write followed by automatic execution in sandbox.',
        },
        {
          id: 3,
          action: 'customize',
          label: 'Inspect & customize \'' + filename + '\' code before committing',
          detail: 'Review diff lines, modify parameters, or adjust imports.',
        },
        {
          id: 4,
          action: 'always_allow',
          label: 'Always allow workspace file modifications in this session (Always Allow)',
          detail: 'Auto-approves future file writes by ' + agentRef + ' for the remainder of this session.',
        },
        {
          id: 5,
          action: 'deny',
          label: 'No (tell ' + agentRef + ' what to do instead)',
          detail: 'Reject this file write and provide alternate requirements or corrections.',
        },
      ],
    };
  }

  // 3. Quantitative Finance Strategy Selection (FinanceStrategyMasterSelection)
  const finIntent = detectFinanceStrategyIntent(trimmed);
  if (finIntent) {
    const { symbol, signal } = finIntent;
    return {
      approval_id: 'fin-gate-' + Date.now(),
      tool_name: 'FinanceStrategyMasterSelection',
      target_resource: symbol + ' · ' + signal + ' Options Strategy',
      human_summary: 'Select Master Strategy for ' + symbol + ' (' + signal + ')',
      mutation_risk: 'medium',
      action_hash: 'fin-' + Math.random().toString(36).substring(2, 10),
      description: 'Screen options strategies for ' + symbol,
      arguments: {
        symbol,
        signal,
        current_price: 25400,
        lot_size: 25,
        expiry: '26-SEP-2026',
        currency: 'INR',
        master_recommended: 'strat-1',
        candidates: [
          {
            candidate_id: 'strat-1',
            category: 'VOLATILITY_ARBITRAGE',
            technology_tag: 'DELTA_NEUTRAL',
            strategy_name: 'Delta-Neutral Volatility Engine',
            strategy_type: 'Options Spread',
            legs: [{ action: 'BUY', type: 'CE', strike: 25500, premium_est: 110 }],
            win_rate_est: '74%',
            risk_reward_actual: '1:2.8',
            max_loss_per_lot: '₹2,200',
            rationale: 'Captures volatility crush while preserving delta-neutral hedging.',
          },
          {
            candidate_id: 'strat-2',
            category: 'DIRECTIONAL_MOMENTUM',
            technology_tag: 'MOMENTUM_BREAKOUT',
            strategy_name: 'Bull Call Algorithmic Ladder',
            strategy_type: 'Bull Spread',
            legs: [{ action: 'BUY', type: 'CE', strike: 25400, premium_est: 140 }],
            win_rate_est: '68%',
            risk_reward_actual: '1:3.2',
            max_loss_per_lot: '₹3,500',
            rationale: 'High momentum breakout tracking system with defined risk.',
          },
        ],
      },
      timeout_seconds: 120,
      created_at: Date.now(),
      status: 'pending',
      model_persona: persona,
      dynamic_options: [
        {
          id: 1,
          action: 'allow_once',
          label: 'Execute Master Strategy (Delta-Neutral Volatility Engine)',
          detail: 'Optimal win rate: 74% • Max loss: ₹2,200.',
          recommended: true,
        },
        {
          id: 2,
          action: 'select_alternative',
          label: 'Execute Alternative Directional Momentum Breakout Ladder',
          detail: 'Higher momentum breakout strategy with dynamic trail stop.',
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
          label: 'No (tell ' + agentRef + ' what to do instead)',
          detail: 'Reject strategy recommendation and scan alternative sectors.',
        },
      ],
    };
  }

  return null;
}
