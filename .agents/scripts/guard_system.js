#!/usr/bin/env node
/**
 * Zero-Discovery & Host Confinement Guard Hook (PreToolUse)
 * 
 * Intercepts tool calls before execution to enforce:
 * 1. Zero Server-Filesystem Discovery (no list_dir, find_by_name, recursive grep).
 * 2. Strict Host OS & Server Filesystem Isolation (no access to server roots /home, /var, /tmp, C:\Windows).
 * 3. Prevention of shell crawling utilities (no os.walk, glob, dir /s, find, tree).
 */

const path = require('path');

// Prohibited server root paths and system directories
const PROHIBITED_ROOTS = [
  // Unix/Linux server roots
  '/etc', '/var', '/opt', '/tmp', '/usr', '/bin', '/sbin', '/root', '/home',
  // Windows system paths
  'c:/windows', 'c:/program files', 'c:/program files (x86)',
  'c:/users/daarv/appdata'
];

// Patterns for filesystem discovery and crawling in commands
const DISCOVERY_COMMAND_PATTERNS = [
  /os\.walk/i,
  /os\.scandir/i,
  /os\.listdir/i,
  /glob\.glob/i,
  /Path\.rglob/i,
  /fs\.readdir/i,
  /Get-ChildItem.*(-Recurse|-r)/i,
  /dir\s+.*\/[sS]/i,
  /(^|\s)tree(\s+|$|\.)/i,
  /(^|\s)find\s+[\/\.~]/i,
  /(^|\s)locate\s+/i,
  /(^|\s)ls\s+.*-[a-zA-Z]*[R]/i,
  /(^|\s)du\s+-[a-zA-Z]*[sh]/i,
  // System introspection commands
  /(^|\s)tasklist(\s+|$)/i,
  /(^|\s)net\s+user/i,
  /(^|\s)whoami\s+\/all/i,
  /(^|\s)systeminfo(\s+|$)/i,
  /(^|\s)reg\s+query/i,
  /(^|\s)diskpart/i,
  /(^|\s)shutdown\s+/i
];

function isPathProhibited(targetPath) {
  if (!targetPath || typeof targetPath !== 'string') return false;
  
  // Convert all path separators to '/' and lowercase for uniform cross-platform matching
  const normalized = targetPath.replace(/\\/g, '/').toLowerCase();

  // Block parent path directory traversal attempts
  if (normalized.includes('..')) {
    return true;
  }

  // Block drive roots (e.g. "c:/", "c:", "/")
  if (/^[a-z]:\/?$/i.test(normalized) || normalized === '/' || normalized === '') {
    return true;
  }

  // Check prohibited system paths
  for (const root of PROHIBITED_ROOTS) {
    if (normalized === root || normalized.startsWith(root + '/') || (root.startsWith('/') && normalized.startsWith(root))) {
      return true;
    }
  }

  return false;
}

function evaluateToolCall(toolCall) {
  if (!toolCall || !toolCall.name) {
    return { decision: 'allow' };
  }

  const name = toolCall.name.toLowerCase();
  const args = toolCall.args || {};

  // 1. Hard-Block Server Discovery Tools
  if (name === 'list_dir') {
    return {
      decision: 'deny',
      reason: 'Zero-Discovery Policy: Directory listing and server filesystem discovery are strictly forbidden. Use explicit user-provided file handles (file_id) instead.'
    };
  }

  if (name === 'find_by_name') {
    return {
      decision: 'deny',
      reason: 'Zero-Discovery Policy: Server file searching and discovery are disabled. Operate exclusively on explicit user-provided file handles.'
    };
  }

  if (name === 'grep_search') {
    // Prohibit grep across directory trees
    const searchPath = args.SearchPath || '';
    if (!searchPath || !path.extname(searchPath)) {
      return {
        decision: 'deny',
        reason: 'Zero-Discovery Policy: Directory-wide grep search is disabled to prevent server filesystem crawling.'
      };
    }
  }

  // 2. Protect Server Filesystem from Arbitrary Path Reads & Writes
  const candidatePath = args.AbsolutePath || args.TargetFile || args.SearchPath || args.DirectoryPath;
  if (candidatePath && isPathProhibited(candidatePath)) {
    return {
      decision: 'deny',
      reason: `Access Denied: Path '${candidatePath}' targets a protected server or host system directory. Server scanning is strictly prohibited.`
    };
  }

  // 3. Block Shell Commands Executing Crawlers or Host Discovery
  if (name === 'run_command') {
    const cmd = args.CommandLine || '';
    for (const pattern of DISCOVERY_COMMAND_PATTERNS) {
      if (pattern.test(cmd)) {
        return {
          decision: 'deny',
          reason: `Execution Denied: Command matches prohibited filesystem discovery or system reconnaissance pattern (${pattern}). Aarka has no server-filesystem discovery capability.`
        };
      }
    }
  }

  // Allow safe execution
  return { decision: 'allow' };
}

// Read stdin hook payload
let inputData = '';
process.stdin.setEncoding('utf-8');

process.stdin.on('data', (chunk) => {
  inputData += chunk;
});

process.stdin.on('end', () => {
  try {
    if (!inputData.trim()) {
      process.stdout.write(JSON.stringify({ decision: 'allow' }));
      process.exit(0);
    }

    const payload = JSON.parse(inputData);
    const result = evaluateToolCall(payload.toolCall);
    process.stdout.write(JSON.stringify(result));
  } catch (err) {
    // Fail-secure: On unexpected JSON or parse error, log and reject
    process.stdout.write(JSON.stringify({
      decision: 'deny',
      reason: 'Security Guard Error: Invalid hook payload encountered: ' + err.message
    }));
  }
  process.exit(0);
});
