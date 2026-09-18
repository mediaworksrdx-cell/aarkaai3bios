/**
 * Command Detection Utility
 * Detects whether user input in the chat text field is a terminal/system command.
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

  // Single-line only check: if input has many newlines, it's not a single command
  if (trimmed.includes('\n')) {
    const lines = trimmed.split('\n').map((l) => l.trim()).filter(Boolean);
    if (lines.length > 2) return false;
  }

  // Strip leading prompt characters ($ or > or #)
  const clean = trimmed.replace(/^[\$\>#]\s+/, '').trim();
  const lower = clean.toLowerCase();

  // Natural language conversational indicators
  for (const starter of CONVERSATIONAL_STARTERS) {
    if (lower.startsWith(starter + ' ') || lower === starter) {
      return false;
    }
  }

  // Questions ending with a question mark are conversational
  if (clean.endsWith('?')) {
    return false;
  }

  // Primary command token
  const firstWord = clean.split(/\s+/)[0].toLowerCase();

  if (KNOWN_CLI_COMMANDS.has(firstWord)) {
    // Avoid false positives on sentences that happen to start with a verb like 'echo' or 'find'
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

  // Executable paths (e.g. ./test.sh, ../script.py, /usr/bin/tool)
  if (/^(\.|\.\.|\/|[a-zA-Z0-9_\-]+)\/[a-zA-Z0-9_\-\.\/]+/.test(clean)) {
    return true;
  }

  return false;
}
