import { describe, it, expect } from 'vitest';
import { isTerminalCommand } from '../commandDetection';

describe('isTerminalCommand', () => {
  it('detects standard terminal commands correctly', () => {
    expect(isTerminalCommand('df -h')).toBe(true);
    expect(isTerminalCommand('ls -la')).toBe(true);
    expect(isTerminalCommand('pytest tests/unit/test_code_mode_unit.py')).toBe(true);
    expect(isTerminalCommand('python3 healthcheck.py')).toBe(true);
    expect(isTerminalCommand('git status')).toBe(true);
    expect(isTerminalCommand('systemctl restart nginx')).toBe(true);
    expect(isTerminalCommand('curl -s https://api.ipify.org')).toBe(true);
    expect(isTerminalCommand('free -m')).toBe(true);
    expect(isTerminalCommand('uptime')).toBe(true);
    expect(isTerminalCommand('./deploy.sh --prod')).toBe(true);
    expect(isTerminalCommand('$ df -h')).toBe(true);
  });

  it('rejects conversational text and natural language queries', () => {
    expect(isTerminalCommand('Explain quantum computing')).toBe(false);
    expect(isTerminalCommand('What does df -h do?')).toBe(false);
    expect(isTerminalCommand('Can you run df -h?')).toBe(false);
    expect(isTerminalCommand('Please check disk space')).toBe(false);
    expect(isTerminalCommand('Hello Aarka!')).toBe(false);
    expect(isTerminalCommand('Write a python function to sort an array')).toBe(false);
    expect(isTerminalCommand('How do I configure nginx?')).toBe(false);
    expect(isTerminalCommand('')).toBe(false);
    expect(isTerminalCommand('   ')).toBe(false);
  });
});
