import { describe, it, expect } from 'vitest';
import {
  isTerminalCommand,
  detectFileCreationIntent,
  detectFinanceStrategyIntent,
  detectSubmissionApproval,
  detectModelPersona,
} from '../commandDetection';

describe('commandDetection Module', () => {
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

  describe('detectFileCreationIntent', () => {
    it('detects file creation intents with filenames', () => {
      const res1 = detectFileCreationIntent(
        'Create a Python script api_service.py with a FastAPI health check and status endpoint'
      );
      expect(res1).not.toBeNull();
      expect(res1?.filename).toBe('api_service.py');
      expect(res1?.isPython).toBe(true);

      const res2 = detectFileCreationIntent(
        'Write a backup script db_backup.py to compress and archive the database'
      );
      expect(res2).not.toBeNull();
      expect(res2?.filename).toBe('db_backup.py');
      expect(res2?.isPython).toBe(true);
    });

    it('returns null for queries without file creation actions', () => {
      expect(detectFileCreationIntent('Explain what api_service.py does')).toBeNull();
      expect(detectFileCreationIntent('How is the weather today?')).toBeNull();
    });
  });

  describe('detectFinanceStrategyIntent', () => {
    it('detects options strategy screening intents', () => {
      const res = detectFinanceStrategyIntent('Screen top bullish options strategies for NIFTY');
      expect(res).not.toBeNull();
      expect(res?.symbol).toBe('NIFTY');
      expect(res?.signal).toBe('BULLISH');
    });
  });

  describe('detectSubmissionApproval - 4 Test Cases', () => {
    it('Case 1: Direct Terminal Command (BashTool) -> df -h', () => {
      const req = detectSubmissionApproval('df -h', 'aarka-2.0');
      expect(req).not.toBeNull();
      expect(req?.tool_name).toBe('BashTool');
      expect(req?.human_summary).toBe('Allow run df -h?');
      expect(req?.command_preview).toBe('df -h');
      expect(req?.dynamic_options?.[0]?.label).toContain("Execute 'df -h' in isolated sandbox");
    });

    it('Case 2: Microservice File Creation (FileEditTool) -> api_service.py', () => {
      const req = detectSubmissionApproval(
        'Create a Python script api_service.py with a FastAPI health check and status endpoint',
        'aarka-2.0'
      );
      expect(req).not.toBeNull();
      expect(req?.tool_name).toBe('FileEditTool');
      expect(req?.target_resource).toBe('api_service.py');
      expect(req?.human_summary).toBe('Allow modify file: api_service.py?');
      expect(req?.dynamic_options?.[0]?.label).toBe("Allow & save 'api_service.py' to workspace");
      expect(req?.dynamic_options?.[1]?.label).toBe("Save 'api_service.py' and execute immediately (python api_service.py)");
      expect(req?.dynamic_options?.[4]?.label).toBe('No (tell Aarka what to do instead)');
    });

    it('Case 3: Quantitative Finance Strategy Selection (FinanceStrategy) -> NIFTY', () => {
      const req = detectSubmissionApproval('Screen top bullish options strategies for NIFTY', 'aarka-2.0');
      expect(req).not.toBeNull();
      expect(req?.tool_name).toBe('FinanceStrategyMasterSelection');
      expect(req?.target_resource).toBe('NIFTY · BULLISH Options Strategy');
      expect(req?.model_persona?.badge).toBe('Aarka Engine · Autonomous Execution');
      expect(req?.arguments?.candidates).toHaveLength(2);
      expect(req?.arguments?.candidates[0].strategy_name).toBe('Delta-Neutral Volatility Engine');
      expect(req?.dynamic_options?.[0]?.label).toContain('Execute Master Strategy (Delta-Neutral Volatility Engine)');
    });

    it('Case 4: Claude Engine Persona Test -> db_backup.py with Claude', () => {
      const req = detectSubmissionApproval(
        'Write a backup script db_backup.py to compress and archive the database',
        'claude-3-7-sonnet'
      );
      expect(req).not.toBeNull();
      expect(req?.tool_name).toBe('FileEditTool');
      expect(req?.target_resource).toBe('db_backup.py');
      expect(req?.human_summary).toBe('Allow modify file: db_backup.py?');
      expect(req?.model_persona?.badge).toBe('Claude · Constitutional Safety');
      expect(req?.model_persona?.provider).toBe('claude');
      expect(req?.dynamic_options?.[4]?.label).toBe('No (tell Claude what to do instead)');
    });
  });
});
