import { ToolApprovalRequest, CandidateFinanceStrategy } from '@/types';

/**
 * Command & Action Intent Detection Utility
 * Detects whether user input in the chat text field is:
 * 1. A terminal command (BashTool)
 * 2. A microservice/script file creation/modification intent (FileEditTool)
 * 3. A multi-asset quantitative finance strategy selection (Stocks, Index, Commodity, Crypto, Forex)
 *    across market regimes (Bullish, Bearish, Neutral, Reversal)
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

// ── Multi-Asset Financial Knowledge Base ──

export interface AssetInfo {
  symbol: string;
  name: string;
  category: 'Stock' | 'Index' | 'Commodity' | 'Crypto' | 'Forex';
  currency: string;
  lotSize?: number;
  basePrice?: number;
}

export type MarketRegime = 'BULLISH' | 'BEARISH' | 'NEUTRAL' | 'REVERSAL' | 'MULTI_REGIME' | 'ALL_REGIMES';

const KNOWN_FINANCIAL_ASSETS: Record<string, AssetInfo> = {
  // Commodities
  'gold': { symbol: 'GOLD', name: 'Gold', category: 'Commodity', currency: '$', basePrice: 2650 },
  'silver': { symbol: 'SILVER', name: 'Silver', category: 'Commodity', currency: '$', basePrice: 31.5 },
  'crude oil': { symbol: 'CRUDE OIL', name: 'Crude Oil', category: 'Commodity', currency: '$', basePrice: 71.0 },
  'crude': { symbol: 'CRUDE OIL', name: 'Crude Oil', category: 'Commodity', currency: '$', basePrice: 71.0 },
  'oil': { symbol: 'CRUDE OIL', name: 'Crude Oil', category: 'Commodity', currency: '$', basePrice: 71.0 },
  'brent': { symbol: 'BRENT', name: 'Brent Crude', category: 'Commodity', currency: '$', basePrice: 74.5 },
  'natural gas': { symbol: 'NATURAL GAS', name: 'Natural Gas', category: 'Commodity', currency: '$', basePrice: 2.8 },
  'gas': { symbol: 'NATURAL GAS', name: 'Natural Gas', category: 'Commodity', currency: '$', basePrice: 2.8 },
  'copper': { symbol: 'COPPER', name: 'Copper', category: 'Commodity', currency: '$', basePrice: 4.3 },
  'wheat': { symbol: 'WHEAT', name: 'Wheat', category: 'Commodity', currency: '$', basePrice: 580 },
  'corn': { symbol: 'CORN', name: 'Corn', category: 'Commodity', currency: '$', basePrice: 420 },

  // Crypto
  'bitcoin': { symbol: 'BTC', name: 'Bitcoin', category: 'Crypto', currency: '$', basePrice: 63500 },
  'btc': { symbol: 'BTC', name: 'Bitcoin', category: 'Crypto', currency: '$', basePrice: 63500 },
  'ethereum': { symbol: 'ETH', name: 'Ethereum', category: 'Crypto', currency: '$', basePrice: 2650 },
  'eth': { symbol: 'ETH', name: 'Ethereum', category: 'Crypto', currency: '$', basePrice: 2650 },
  'solana': { symbol: 'SOL', name: 'Solana', category: 'Crypto', currency: '$', basePrice: 152 },
  'sol': { symbol: 'SOL', name: 'Solana', category: 'Crypto', currency: '$', basePrice: 152 },
  'ripple': { symbol: 'XRP', name: 'Ripple', category: 'Crypto', currency: '$', basePrice: 0.58 },
  'xrp': { symbol: 'XRP', name: 'Ripple', category: 'Crypto', currency: '$', basePrice: 0.58 },
  'cardano': { symbol: 'ADA', name: 'Cardano', category: 'Crypto', currency: '$', basePrice: 0.38 },
  'ada': { symbol: 'ADA', name: 'Cardano', category: 'Crypto', currency: '$', basePrice: 0.38 },
  'doge': { symbol: 'DOGE', name: 'Dogecoin', category: 'Crypto', currency: '$', basePrice: 0.12 },
  'dogecoin': { symbol: 'DOGE', name: 'Dogecoin', category: 'Crypto', currency: '$', basePrice: 0.12 },
  'crypto': { symbol: 'CRYPTO', name: 'Crypto', category: 'Crypto', currency: '$', basePrice: 60000 },

  // Forex
  'eurusd': { symbol: 'EUR/USD', name: 'EUR/USD', category: 'Forex', currency: '$', basePrice: 1.115 },
  'eur/usd': { symbol: 'EUR/USD', name: 'EUR/USD', category: 'Forex', currency: '$', basePrice: 1.115 },
  'gbpusd': { symbol: 'GBP/USD', name: 'GBP/USD', category: 'Forex', currency: '$', basePrice: 1.325 },
  'gbp/usd': { symbol: 'GBP/USD', name: 'GBP/USD', category: 'Forex', currency: '$', basePrice: 1.325 },
  'usdjpy': { symbol: 'USD/JPY', name: 'USD/JPY', category: 'Forex', currency: '¥', basePrice: 143.5 },
  'usd/jpy': { symbol: 'USD/JPY', name: 'USD/JPY', category: 'Forex', currency: '¥', basePrice: 143.5 },
  'usdinr': { symbol: 'USD/INR', name: 'USD/INR', category: 'Forex', currency: '₹', basePrice: 83.7 },
  'usd/inr': { symbol: 'USD/INR', name: 'USD/INR', category: 'Forex', currency: '₹', basePrice: 83.7 },
  'audusd': { symbol: 'AUD/USD', name: 'AUD/USD', category: 'Forex', currency: '$', basePrice: 0.685 },
  'aud/usd': { symbol: 'AUD/USD', name: 'AUD/USD', category: 'Forex', currency: '$', basePrice: 0.685 },
  'forex': { symbol: 'FOREX', name: 'Forex FX', category: 'Forex', currency: '$', basePrice: 1.0 },

  // Indices
  'nifty': { symbol: 'NIFTY', name: 'NIFTY 50', category: 'Index', currency: '₹', lotSize: 25, basePrice: 25400 },
  'nifty 50': { symbol: 'NIFTY', name: 'NIFTY 50', category: 'Index', currency: '₹', lotSize: 25, basePrice: 25400 },
  'banknifty': { symbol: 'BANKNIFTY', name: 'Bank Nifty', category: 'Index', currency: '₹', lotSize: 15, basePrice: 53200 },
  'bank nifty': { symbol: 'BANKNIFTY', name: 'Bank Nifty', category: 'Index', currency: '₹', lotSize: 15, basePrice: 53200 },
  'sensex': { symbol: 'SENSEX', name: 'BSE Sensex', category: 'Index', currency: '₹', lotSize: 10, basePrice: 83100 },
  'finnifty': { symbol: 'FINNIFTY', name: 'Fin Nifty', category: 'Index', currency: '₹', lotSize: 40, basePrice: 24200 },
  's&p 500': { symbol: 'S&P 500', name: 'S&P 500', category: 'Index', currency: '$', basePrice: 5700 },
  'sp500': { symbol: 'S&P 500', name: 'S&P 500', category: 'Index', currency: '$', basePrice: 5700 },
  's&p': { symbol: 'S&P 500', name: 'S&P 500', category: 'Index', currency: '$', basePrice: 5700 },
  'nasdaq': { symbol: 'NASDAQ', name: 'Nasdaq 100', category: 'Index', currency: '$', basePrice: 19800 },
  'dow': { symbol: 'DOW JONES', name: 'Dow Jones', category: 'Index', currency: '$', basePrice: 42100 },
  'dow jones': { symbol: 'DOW JONES', name: 'Dow Jones', category: 'Index', currency: '$', basePrice: 42100 },

  // Stocks
  'reliance': { symbol: 'RELIANCE', name: 'Reliance Industries', category: 'Stock', currency: '₹', lotSize: 250, basePrice: 2980 },
  'tcs': { symbol: 'TCS', name: 'Tata Consultancy Services', category: 'Stock', currency: '₹', lotSize: 175, basePrice: 4250 },
  'infosys': { symbol: 'INFY', name: 'Infosys', category: 'Stock', currency: '₹', lotSize: 400, basePrice: 1920 },
  'infy': { symbol: 'INFY', name: 'Infosys', category: 'Stock', currency: '₹', lotSize: 400, basePrice: 1920 },
  'hdfc': { symbol: 'HDFCBANK', name: 'HDFC Bank', category: 'Stock', currency: '₹', lotSize: 550, basePrice: 1680 },
  'hdfc bank': { symbol: 'HDFCBANK', name: 'HDFC Bank', category: 'Stock', currency: '₹', lotSize: 550, basePrice: 1680 },
  'icici': { symbol: 'ICICIBANK', name: 'ICICI Bank', category: 'Stock', currency: '₹', lotSize: 700, basePrice: 1240 },
  'icici bank': { symbol: 'ICICIBANK', name: 'ICICI Bank', category: 'Stock', currency: '₹', lotSize: 700, basePrice: 1240 },
  'sbi': { symbol: 'SBIN', name: 'State Bank of India', category: 'Stock', currency: '₹', lotSize: 1500, basePrice: 790 },
  'state bank': { symbol: 'SBIN', name: 'State Bank of India', category: 'Stock', currency: '₹', lotSize: 1500, basePrice: 790 },
  'tata motors': { symbol: 'TATAMOTORS', name: 'Tata Motors', category: 'Stock', currency: '₹', lotSize: 1400, basePrice: 970 },
  'tata steel': { symbol: 'TATASTEEL', name: 'Tata Steel', category: 'Stock', currency: '₹', lotSize: 5500, basePrice: 155 },
  'apple': { symbol: 'AAPL', name: 'Apple', category: 'Stock', currency: '$', basePrice: 228 },
  'aapl': { symbol: 'AAPL', name: 'Apple', category: 'Stock', currency: '$', basePrice: 228 },
  'tesla': { symbol: 'TSLA', name: 'Tesla', category: 'Stock', currency: '$', basePrice: 245 },
  'tsla': { symbol: 'TSLA', name: 'Tesla', category: 'Stock', currency: '$', basePrice: 245 },
  'nvidia': { symbol: 'NVDA', name: 'Nvidia', category: 'Stock', currency: '$', basePrice: 120 },
  'nvda': { symbol: 'NVDA', name: 'Nvidia', category: 'Stock', currency: '$', basePrice: 120 },
  'microsoft': { symbol: 'MSFT', name: 'Microsoft', category: 'Stock', currency: '$', basePrice: 435 },
  'msft': { symbol: 'MSFT', name: 'Microsoft', category: 'Stock', currency: '$', basePrice: 435 },
  'google': { symbol: 'GOOGL', name: 'Alphabet Google', category: 'Stock', currency: '$', basePrice: 165 },
  'amazon': { symbol: 'AMZN', name: 'Amazon', category: 'Stock', currency: '$', basePrice: 188 },
  'meta': { symbol: 'META', name: 'Meta Platforms', category: 'Stock', currency: '$', basePrice: 565 },
};

export function generateCandidateStrategiesForAsset(
  asset: AssetInfo,
  regime: MarketRegime,
  isOptionsIntent: boolean = false
): { master_recommended: string; candidates: CandidateFinanceStrategy[] } {
  const sym = asset.symbol;
  const cur = asset.currency;

  if (regime === 'BULLISH') {
    if (isOptionsIntent) {
      return {
        master_recommended: 'candidate_strat_1',
        candidates: [
          {
            candidate_id: 'candidate_strat_1',
            category: 'BULLISH',
            technology_tag: 'DELTA_NEUTRAL',
            strategy_name: 'Delta-Neutral Volatility Engine',
            strategy_type: 'Options Spread',
            legs: [{ action: 'BUY', type: 'CE', strike: Math.round(asset.basePrice || 25500), premium_est: 110 }],
            win_rate_est: '74%',
            risk_reward_actual: '1:2.8',
            max_loss_per_lot: `${cur}2,200`,
            rationale: 'Captures volatility crush while preserving delta-neutral hedging.',
          },
          {
            candidate_id: 'candidate_strat_2',
            category: 'BULLISH',
            technology_tag: 'MOMENTUM_BREAKOUT',
            strategy_name: 'Bull Call Algorithmic Ladder',
            strategy_type: 'Bull Spread',
            legs: [{ action: 'BUY', type: 'CE', strike: Math.round((asset.basePrice || 25400) - 100), premium_est: 140 }],
            win_rate_est: '68%',
            risk_reward_actual: '1:3.2',
            max_loss_per_lot: `${cur}3,500`,
            rationale: 'High momentum breakout tracking system with defined risk.',
          },
        ],
      };
    }

    return {
      master_recommended: 'candidate_strat_1',
      candidates: [
        {
          candidate_id: 'candidate_strat_1',
          category: 'BULLISH',
          technology_tag: 'Golden Cross Momentum',
          strategy_name: `${sym} Golden Cross Trend Breakout`,
          strategy_type: 'Trend Following',
          legs: [],
          entry_trigger: `Enter on EMA50 > EMA200 alignment with positive MACD histogram`,
          stop_loss: `Trail 2.0x ATR (${cur}${(asset.basePrice || 100) * 0.95})`,
          target: `Target 3.0x ATR expansion (${cur}${(asset.basePrice || 100) * 1.08})`,
          win_rate_est: '78%',
          risk_reward_actual: '1:2.8',
          max_loss_per_lot: `${cur}1,800`,
          rationale: 'Institutional trend breakout confirming EMA50/200 crossover with volume support.',
        },
        {
          candidate_id: 'candidate_strat_2',
          category: 'BULLISH',
          technology_tag: 'Breakout Volume Surge',
          strategy_name: `${sym} Bollinger Upper Band Volume Surge`,
          strategy_type: 'Momentum Breakout',
          legs: [],
          entry_trigger: `Enter on volume surge > 2x SMA(20) breaking upper Bollinger Band`,
          stop_loss: `Stop-loss at EMA20 midline (${cur}${(asset.basePrice || 100) * 0.97})`,
          target: `Target volatility expansion (${cur}${(asset.basePrice || 100) * 1.06})`,
          win_rate_est: '71%',
          risk_reward_actual: '1:3.2',
          max_loss_per_lot: `${cur}1,500`,
          rationale: 'Exploits institutional buying volume expansion breaking consolidation barriers.',
        },
      ],
    };
  }

  if (regime === 'BEARISH') {
    if (isOptionsIntent) {
      const p = Math.round(asset.basePrice || 25400);
      return {
        master_recommended: 'candidate_strat_1',
        candidates: [
          {
            candidate_id: 'candidate_strat_1',
            category: 'BEARISH',
            technology_tag: 'BEAR_PUT_SPREAD',
            strategy_name: 'Bear Put Spread (Moderate Bearish)',
            strategy_type: 'Options Spread',
            legs: [
              { action: 'BUY', type: 'PE', strike: p, premium_est: 130 },
              { action: 'SELL', type: 'PE', strike: p - 200, premium_est: 50 },
            ],
            win_rate_est: '71%',
            risk_reward_actual: '1:2.5',
            max_loss_per_lot: `${cur}2,000`,
            rationale: 'Defined-risk vertical put spread capitalizing on downside continuation.',
          },
          {
            candidate_id: 'candidate_strat_2',
            category: 'BEARISH',
            technology_tag: 'LONG_PUT',
            strategy_name: 'Long Put Breakdown Accelerator',
            strategy_type: 'Long Put',
            legs: [{ action: 'BUY', type: 'PE', strike: p - 100, premium_est: 95 }],
            win_rate_est: '64%',
            risk_reward_actual: '1:3.4',
            max_loss_per_lot: `${cur}2,375`,
            rationale: 'Aggressive directional put purchase targeting high-velocity breakdown.',
          },
        ],
      };
    }

    return {
      master_recommended: 'candidate_strat_1',
      candidates: [
        {
          candidate_id: 'candidate_strat_1',
          category: 'BEARISH',
          technology_tag: 'Death Cross Distribution',
          strategy_name: `${sym} Death Cross Distribution Short`,
          strategy_type: 'Trend Breakdown',
          legs: [],
          entry_trigger: `Enter short on EMA50 < EMA200 divergence with negative MACD`,
          stop_loss: `Stop-loss above EMA50 resistance (${cur}${(asset.basePrice || 100) * 1.05})`,
          target: `Target liquidity pool (${cur}${(asset.basePrice || 100) * 0.92})`,
          win_rate_est: '74%',
          risk_reward_actual: '1:2.9',
          max_loss_per_lot: `${cur}1,700`,
          rationale: 'Short setup riding structural distribution and moving average death cross.',
        },
        {
          candidate_id: 'candidate_strat_2',
          category: 'BEARISH',
          technology_tag: 'Breakdown Volume Surge',
          strategy_name: `${sym} Bollinger Lower Band Breakdown Surge`,
          strategy_type: 'Liquidity Breakdown',
          legs: [],
          entry_trigger: `Enter short on lower Bollinger Band breach with high selling volume`,
          stop_loss: `Stop-loss at EMA20 rebound level (${cur}${(asset.basePrice || 100) * 1.03})`,
          target: `Target support extension (${cur}${(asset.basePrice || 100) * 0.94})`,
          win_rate_est: '69%',
          risk_reward_actual: '1:3.1',
          max_loss_per_lot: `${cur}1,400`,
          rationale: 'Capitalizes on aggressive panic selling and liquidity purge below key support.',
        },
      ],
    };
  }

  if (regime === 'NEUTRAL') {
    if (isOptionsIntent) {
      const p = Math.round(asset.basePrice || 25400);
      return {
        master_recommended: 'candidate_strat_1',
        candidates: [
          {
            candidate_id: 'candidate_strat_1',
            category: 'NEUTRAL',
            technology_tag: 'IRON_CONDOR',
            strategy_name: 'Iron Condor (Neutral / Range-Bound)',
            strategy_type: 'Options Spread',
            legs: [
              { action: 'SELL', type: 'CE', strike: p + 200, premium_est: 60 },
              { action: 'BUY', type: 'CE', strike: p + 300, premium_est: 25 },
              { action: 'SELL', type: 'PE', strike: p - 200, premium_est: 60 },
              { action: 'BUY', type: 'PE', strike: p - 300, premium_est: 25 },
            ],
            win_rate_est: '82%',
            risk_reward_actual: '1:2.0',
            max_loss_per_lot: `${cur}1,750`,
            rationale: 'Double credit spread harvesting theta decay within well-defined volatility boundaries.',
          },
          {
            candidate_id: 'candidate_strat_2',
            category: 'NEUTRAL',
            technology_tag: 'SHORT_STRANGLE',
            strategy_name: 'Short Strangle Premium Harvest',
            strategy_type: 'Options Strangle',
            legs: [
              { action: 'SELL', type: 'CE', strike: p + 350, premium_est: 45 },
              { action: 'SELL', type: 'PE', strike: p - 350, premium_est: 45 },
            ],
            win_rate_est: '86%',
            risk_reward_actual: '1:1.8',
            max_loss_per_lot: `${cur}2,900`,
            rationale: 'High probability OTM premium capture in low-implied-volatility regimes.',
          },
        ],
      };
    }

    return {
      master_recommended: 'candidate_strat_1',
      candidates: [
        {
          candidate_id: 'candidate_strat_1',
          category: 'NEUTRAL',
          technology_tag: 'Range-Bound Mean Reversion',
          strategy_name: `${sym} Range-Bound Channel Oscillation`,
          strategy_type: 'Mean Reversion',
          legs: [],
          entry_trigger: `Buy at channel support and short at channel resistance (ADX < 20)`,
          stop_loss: `Stop-loss on 1.2x ATR breakout outside range`,
          target: `Target range midpoint / opposite boundary`,
          win_rate_est: '82%',
          risk_reward_actual: '1:2.2',
          max_loss_per_lot: `${cur}1,400`,
          rationale: 'Harvests predictable oscillations in range-bound, low-trend market regimes.',
        },
        {
          candidate_id: 'candidate_strat_2',
          category: 'NEUTRAL',
          technology_tag: 'Consolidation Squeeze',
          strategy_name: `${sym} Volatility Squeeze Channel Trading`,
          strategy_type: 'Consolidation Squeeze',
          legs: [],
          entry_trigger: `Grid placement across contracting volatility squeeze bands`,
          stop_loss: `Stop-loss on directional squeeze expansion`,
          target: `Target mean equilibrium price`,
          win_rate_est: '84%',
          risk_reward_actual: '1:2.0',
          max_loss_per_lot: `${cur}1,100`,
          rationale: 'Capitalizes on low volatility compression before explosive directional expansion.',
        },
      ],
    };
  }

  if (regime === 'REVERSAL') {
    if (isOptionsIntent) {
      const p = Math.round(asset.basePrice || 25400);
      return {
        master_recommended: 'candidate_strat_1',
        candidates: [
          {
            candidate_id: 'candidate_strat_1',
            category: 'REVERSAL',
            technology_tag: 'REVERSE_BUTTERFLY',
            strategy_name: 'Reverse Iron Butterfly (Vol Expansion)',
            strategy_type: 'Options Reversal',
            legs: [
              { action: 'BUY', type: 'CE', strike: p, premium_est: 120 },
              { action: 'BUY', type: 'PE', strike: p, premium_est: 120 },
              { action: 'SELL', type: 'CE', strike: p + 250, premium_est: 35 },
              { action: 'SELL', type: 'PE', strike: p - 250, premium_est: 35 },
            ],
            win_rate_est: '68%',
            risk_reward_actual: '1:3.2',
            max_loss_per_lot: `${cur}2,100`,
            rationale: 'Exploits sharp reversal breakout out of consolidation with defined risk.',
          },
          {
            candidate_id: 'candidate_strat_2',
            category: 'REVERSAL',
            technology_tag: 'PIVOT_RATIO_SPREAD',
            strategy_name: 'Contrarian Pivot Ratio Spread',
            strategy_type: 'Options Ratio Spread',
            legs: [
              { action: 'BUY', type: 'CE', strike: p + 50, premium_est: 90 },
              { action: 'SELL', type: 'CE', strike: p + 200, premium_est: 40 },
            ],
            win_rate_est: '72%',
            risk_reward_actual: '1:3.0',
            max_loss_per_lot: `${cur}1,500`,
            rationale: 'Asymmetric risk-reward ratio spread timed at exhaustion pivot support.',
          },
        ],
      };
    }

    return {
      master_recommended: 'candidate_strat_1',
      candidates: [
        {
          candidate_id: 'candidate_strat_1',
          category: 'REVERSAL',
          technology_tag: 'SNIPER_PIVOT',
          strategy_name: `${sym} Climactic Exhaustion & Sniper Pivot`,
          strategy_type: 'Counter-Trend Reversal',
          legs: [],
          win_rate_est: '69%',
          risk_reward_actual: '1:3.7',
          max_loss_per_lot: `${cur}1,500`,
          rationale: 'Identifies volume-climax exhaustion and multi-timeframe divergence for sharp counter-trend pivot.',
        },
        {
          candidate_id: 'candidate_strat_2',
          category: 'REVERSAL',
          technology_tag: 'LIQUIDITY_SWEEP',
          strategy_name: `${sym} False-Breakout Liquidity Sweep Reversal`,
          strategy_type: 'Liquidity Reversal',
          legs: [],
          win_rate_est: '72%',
          risk_reward_actual: '1:3.4',
          max_loss_per_lot: `${cur}1,250`,
          rationale: 'Exploits trapped breakout participants after a false sweep outside the standard deviation band.',
        },
      ],
    };
  }

  // MULTI_REGIME or ALL_REGIMES: 4 interactive cards (Bullish, Bearish, Neutral, Reversal)
  return {
    master_recommended: 'candidate_bull',
    candidates: [
      {
        candidate_id: 'candidate_bull',
        category: 'BULLISH',
        technology_tag: 'TREND_MOMENTUM',
        strategy_name: `${sym} Bullish Momentum Breakout Strategy`,
        strategy_type: 'Trend Following',
        legs: [],
        win_rate_est: '72%',
        risk_reward_actual: '1:3.1',
        max_loss_per_lot: `${cur}1,800`,
        rationale: 'Trend-following long continuation setup tracking institutional inflows.',
      },
      {
        candidate_id: 'candidate_bear',
        category: 'BEARISH',
        technology_tag: 'BREAKDOWN_SHORT',
        strategy_name: `${sym} Bearish Breakdown Short Strategy`,
        strategy_type: 'Directional Short',
        legs: [],
        win_rate_est: '69%',
        risk_reward_actual: '1:3.2',
        max_loss_per_lot: `${cur}1,700`,
        rationale: 'Key support breakdown and liquidity sweep short setup.',
      },
      {
        candidate_id: 'candidate_neutral',
        category: 'NEUTRAL',
        technology_tag: 'RANGE_HARVEST',
        strategy_name: `${sym} Neutral Range Volatility Harvest`,
        strategy_type: 'Mean Reversion',
        legs: [],
        win_rate_est: '80%',
        risk_reward_actual: '1:2.1',
        max_loss_per_lot: `${cur}1,400`,
        rationale: 'Channel oscillation and volatility decay within defined price bands.',
      },
      {
        candidate_id: 'candidate_reversal',
        category: 'REVERSAL',
        technology_tag: 'SNIPER_PIVOT',
        strategy_name: `${sym} Exhaustion Mean-Reversion Reversal`,
        strategy_type: 'Counter-Trend Pivot',
        legs: [],
        win_rate_est: '68%',
        risk_reward_actual: '1:3.7',
        max_loss_per_lot: `${cur}1,500`,
        rationale: 'Counter-trend sniper pivot off multi-timeframe divergence and volume exhaustion.',
      },
    ],
  };
}

export function detectFinanceStrategyIntent(raw: string): {
  asset: AssetInfo;
  regime: MarketRegime;
  isOptionsIntent: boolean;
  symbol: string;
  signal: string;
} | null {
  if (!raw) return null;
  const trimmed = raw.trim();
  const lower = trimmed.toLowerCase();

  // Financial strategy trigger signals
  const hasStrategyKeywords =
    /\b(strategy|strategies|setup|setups|trade|trading|screen|scanner|bullish|bearish|neutral|reversal|options?|call|put|spread|straddle|condor)\b/i.test(lower) ||
    /what\s+strategy\s+to\s+choose|which\s+strategy|choose\s+strategy|trade\s+plan|what\s+strategy/i.test(lower);

  if (!hasStrategyKeywords) return null;

  // 1. Identify financial asset
  let matchedAsset: AssetInfo | null = null;
  const sortedNames = Object.keys(KNOWN_FINANCIAL_ASSETS).sort((a, b) => b.length - a.length);

  for (const name of sortedNames) {
    const regex = new RegExp(`\\b${name.replace('/', '\\/')}\\b`, 'i');
    if (regex.test(lower)) {
      matchedAsset = KNOWN_FINANCIAL_ASSETS[name];
      break;
    }
  }

  // Ticker symbol regex fallback (e.g. BTC, ETH, NIFTY, GOLD, TSLA, AAPL, etc.)
  if (!matchedAsset) {
    const tickerMatch = trimmed.match(/\b(NIFTY|BANKNIFTY|FINNIFTY|SENSEX|GOLD|SILVER|CRUDE|BRENT|BTC|ETH|SOL|XRP|ADA|DOGE|EURUSD|GBPUSD|USDINR|USDJPY|RELIANCE|TCS|INFY|HDFC|AAPL|TSLA|NVDA|MSFT)\b/i);
    if (tickerMatch) {
      const t = tickerMatch[1].toLowerCase();
      matchedAsset = KNOWN_FINANCIAL_ASSETS[t] || {
        symbol: tickerMatch[1].toUpperCase(),
        name: tickerMatch[1].toUpperCase(),
        category: 'Stock',
        currency: '$',
      };
    }
  }

  if (!matchedAsset) {
    // If user asks about strategy, regime, or what strategy to choose without a specific asset
    if (
      /(bullish|bearish|neutral|reversal)/i.test(lower) ||
      /what\s+strategy|which\s+strategy|choose\s+strategy|trade\s+plan|recommend\s+strategy/i.test(lower) ||
      /(strategy|strategies)\b/i.test(lower)
    ) {
      matchedAsset = {
        symbol: 'MARKET',
        name: 'Financial Market',
        category: 'Stock',
        currency: '$',
      };
    } else {
      return null;
    }
  }

  // 2. Identify market regimes mentioned
  const regimes: string[] = [];
  if (/\b(bullish|bull|long|uptrend|buy|buying)\b/i.test(lower)) regimes.push('BULLISH');
  if (/\b(bearish|bear|short|downtrend|sell|selling)\b/i.test(lower)) regimes.push('BEARISH');
  if (/\b(neutral|range-bound|range bound|sideways|consolidation|condor)\b/i.test(lower)) regimes.push('NEUTRAL');
  if (/\b(reversal|mean reversion|mean-reversion|pivot|contrarian|exhaustion|turnaround)\b/i.test(lower)) regimes.push('REVERSAL');

  let regime: MarketRegime = 'ALL_REGIMES';
  if (regimes.length === 1) {
    regime = regimes[0] as MarketRegime;
  } else if (regimes.length > 1) {
    regime = 'MULTI_REGIME';
  } else {
    regime = 'ALL_REGIMES';
  }

  const isOptionsIntent = /\b(option|options|strike|expiry|spread|straddle|condor)\b/i.test(lower);

  return {
    symbol: matchedAsset.symbol,
    signal: regime,
    asset: matchedAsset,
    regime,
    isOptionsIntent,
  };
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
          label: `Execute '${trimmed}' in isolated sandbox`,
          detail: 'Run shell command safely within workspace execution constraints.',
          recommended: true,
        },
        {
          id: 2,
          action: 'allow_and_stream',
          label: `Execute '${trimmed}' and stream live terminal output`,
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
          label: `Always allow '${trimmed}' in this session (Always Allow)`,
          detail: 'Whitelist this command pattern to prevent redundant authorization gates.',
        },
        {
          id: 5,
          action: 'deny',
          label: `No (tell ${agentRef} what to do instead)`,
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
          label: `Allow & save '${filename}' to workspace`,
          detail: 'Write verified script directly into the workspace root.',
          recommended: true,
        },
        {
          id: 2,
          action: isPy ? 'allow_and_run' : 'allow_in_conversation',
          label: `Save '${filename}' and execute immediately (${isPy ? 'python ' + filename : 'inspect in workspace'})`,
          detail: 'Atomic disk write followed by automatic execution in sandbox.',
        },
        {
          id: 3,
          action: 'customize',
          label: `Inspect & customize '${filename}' code before committing`,
          detail: 'Review diff lines, modify parameters, or adjust imports.',
        },
        {
          id: 4,
          action: 'always_allow',
          label: 'Always allow workspace file modifications in this session (Always Allow)',
          detail: `Auto-approves future file writes by ${agentRef} for the remainder of this session.`,
        },
        {
          id: 5,
          action: 'deny',
          label: `No (tell ${agentRef} what to do instead)`,
          detail: 'Reject this file write and provide alternate requirements or corrections.',
        },
      ],
    };
  }

  // 3. Multi-Asset Quantitative Financial Strategy (Stocks, Index, Commodity, Crypto, Forex)
  const finIntent = detectFinanceStrategyIntent(trimmed);
  if (finIntent) {
    const { asset, regime, isOptionsIntent } = finIntent;
    const strategyBundle = generateCandidateStrategiesForAsset(asset, regime, isOptionsIntent);
    const firstCand = strategyBundle.candidates[0];

    const regimeLabel =
      regime === 'ALL_REGIMES' || regime === 'MULTI_REGIME'
        ? 'Strategy Selection'
        : `${regime} Strategy`;

    const summaryText =
      regime === 'ALL_REGIMES' || regime === 'MULTI_REGIME'
        ? `What strategy to choose for ${asset.name} (${asset.category})?`
        : `Select ${regime} Strategy for ${asset.name} (${asset.category})`;

    return {
      approval_id: 'fin-gate-' + Date.now(),
      tool_name: 'FinanceStrategyMasterSelection',
      target_resource: isOptionsIntent
        ? `${asset.symbol} · ${regime === 'ALL_REGIMES' || regime === 'MULTI_REGIME' ? 'Options Strategy' : `${regime} Options Strategy`}`
        : `${asset.symbol} (${asset.category}) · ${regimeLabel}`,
      human_summary: summaryText,
      mutation_risk: 'medium',
      action_hash: 'fin-' + Math.random().toString(36).substring(2, 10),
      description: `Screen ${regimeLabel.toLowerCase()} setups for ${asset.name}`,
      arguments: {
        symbol: asset.symbol,
        category: asset.category,
        signal: regime,
        current_price: asset.basePrice || 25000,
        lot_size: asset.lotSize || 1,
        expiry: '26-SEP-2026',
        currency: asset.currency,
        master_recommended: strategyBundle.master_recommended,
        candidates: strategyBundle.candidates,
      },
      timeout_seconds: 120,
      created_at: Date.now(),
      status: 'pending',
      model_persona: persona,
      dynamic_options: [
        {
          id: 1,
          action: 'allow_once',
          label: `Execute Strategy (${firstCand.strategy_name})`,
          detail: `Optimal win rate: ${firstCand.win_rate_est || '74%'} • Max loss: ${firstCand.max_loss_per_lot || '$1,500'}.`,
          recommended: true,
        },
        {
          id: 2,
          action: 'select_alternative',
          label: strategyBundle.candidates[1]
            ? `Execute Alternative (${strategyBundle.candidates[1].strategy_name})`
            : 'Execute Alternative Tactical Setup',
          detail: 'Alternative strategy setup with dynamic trail stop.',
        },
        {
          id: 3,
          action: 'customize',
          label: isOptionsIntent ? 'Customize strike prices, premium limits & expiry dates' : 'Customize entry price, stop-loss & profit targets',
          detail: isOptionsIntent ? 'Manually tune legs, strikes, and risk allocation.' : 'Manually tune position sizing, risk limits, and take-profit targets.',
        },
        {
          id: 4,
          action: 'always_allow',
          label: 'Always auto-execute strategies matching risk profile (Always Allow)',
          detail: 'Authorize automated position sizing within risk parameters.',
        },
        {
          id: 5,
          action: 'deny',
          label: `No (tell ${agentRef} what to do instead)`,
          detail: 'Reject strategy recommendation and scan alternative assets.',
        },
      ],
    };
  }

  return null;
}
