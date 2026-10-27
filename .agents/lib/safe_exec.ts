import { execFile } from 'child_process';
import { promisify } from 'util';

const execFileAsync = promisify(execFile);

export interface SafeExecOptions {
  cwd?: string;
  timeout?: number;
  maxBuffer?: number;
}

export interface SafeExecResult {
  stdout: string;
  stderr: string;
}

/**
 * Executes a binary safely using argument arrays and shell: false.
 * Prevents command injection and subshell escaping.
 */
export async function safeExec(
  binary: string,
  args: string[],
  options: SafeExecOptions = {}
): Promise<SafeExecResult> {
  const { cwd = process.cwd(), timeout = 60000, maxBuffer = 10 * 1024 * 1024 } = options;

  if (!/^[a-zA-Z0-9_\-\.]+$/.test(binary)) {
    throw new Error(`SECURITY ALERT: Invalid binary name: ${binary}`);
  }

  const recursiveFlagRegex = /^(-R|--recursive|\/s)$/i;
  for (const arg of args) {
    if (recursiveFlagRegex.test(arg)) {
      throw new Error(`RULE 8 VIOLATION: Recursive crawling argument rejected: ${arg}`);
    }
  }

  const { stdout, stderr } = await execFileAsync(binary, args, {
    cwd,
    timeout,
    maxBuffer,
    shell: false,
    windowsHide: true
  });

  return { stdout: stdout.toString(), stderr: stderr.toString() };
}
