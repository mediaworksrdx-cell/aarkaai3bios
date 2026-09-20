/**
 * Verification Test Suite: Zero-Discovery & Host Confinement Architecture
 */

const assert = require('assert');
const { spawnSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const { FileService } = require('../scripts/file_service.js');

const GUARD_SCRIPT = path.resolve(__dirname, '..', 'scripts', 'guard_system.js');

function runGuardHook(payload) {
  const result = spawnSync('node', [GUARD_SCRIPT], {
    input: JSON.stringify(payload),
    encoding: 'utf-8'
  });

  if (result.error) {
    throw result.error;
  }
  return JSON.parse(result.stdout);
}

let totalTests = 0;
let passedTests = 0;

function test(name, fn) {
  totalTests++;
  try {
    fn();
    console.log(`  ✓ [PASS] ${name}`);
    passedTests++;
  } catch (err) {
    console.error(`  ✕ [FAIL] ${name}: ${err.message}`);
    throw err;
  }
}

console.log('\n--- Running Zero-Discovery & Host Confinement Test Suite ---\n');

// 1. FileService Capability Handle Tests
console.log('1. Testing FileService Capability Handle Interface:');

const testStorageDir = path.resolve(__dirname, '..', '..', '.storage_test');
const fileService = new FileService(testStorageDir);
const sessionId = 'session_test_abc123';

test('FileService registers file and returns opaque handle', () => {
  const registration = fileService.registerFile(
    sessionId,
    'Financial Q3 Report Summary Contents',
    'report.pdf',
    'application/pdf'
  );
  assert(registration.fileId.startsWith('fid_'), 'Handle must start with fid_');
  assert.strictEqual(registration.fileName, 'report.pdf');
  assert.strictEqual(registration.storagePath, undefined, 'Internal storage path must not be leaked');
});

test('FileService reads file successfully with valid file_id', () => {
  const reg = fileService.registerFile(sessionId, 'Secret content', 'data.txt', 'text/plain');
  const readRes = fileService.readFile(sessionId, reg.fileId);
  assert.strictEqual(readRes.content, 'Secret content');
  assert.strictEqual(readRes.metadata.fileName, 'data.txt');
});

test('FileService rejects arbitrary or unauthorized file_id', () => {
  assert.throws(() => {
    fileService.readFile(sessionId, 'fid_unauthorized_fake');
  }, /Permission Denied/);
});

test('FileService listAuthorizedFiles returns only session-registered handles without filesystem scanning', () => {
  const files = fileService.listAuthorizedFiles(sessionId);
  assert(files.length >= 2, 'Should list registered files');
  files.forEach(f => {
    assert(f.fileId, 'Must have fileId');
    assert.strictEqual(f.storagePath, undefined, 'Must not leak disk path');
  });
});

test('FileService revokes and purges handle', () => {
  const reg = fileService.registerFile(sessionId, 'To be deleted', 'temp.txt');
  const revoked = fileService.revokeFile(sessionId, reg.fileId);
  assert.strictEqual(revoked, true);
  assert.throws(() => {
    fileService.readFile(sessionId, reg.fileId);
  }, /Permission Denied/);
});

// Cleanup test storage
try {
  fs.rmSync(testStorageDir, { recursive: true, force: true });
} catch (_) {}

// 2. PreToolUse Guard Hook Tests
console.log('\n2. Testing PreToolUse Hook Enforcement:');

test('PreToolUse denies list_dir (server discovery)', () => {
  const res = runGuardHook({
    toolCall: {
      name: 'list_dir',
      args: { DirectoryPath: 'c:\\server\\app' }
    }
  });
  assert.strictEqual(res.decision, 'deny');
  assert(res.reason.includes('Zero-Discovery Policy'));
});

test('PreToolUse denies find_by_name (server scanning)', () => {
  const res = runGuardHook({
    toolCall: {
      name: 'find_by_name',
      args: { SearchDirectory: 'c:\\server', Pattern: '*.pdf' }
    }
  });
  assert.strictEqual(res.decision, 'deny');
  assert(res.reason.includes('Zero-Discovery Policy'));
});

test('PreToolUse denies directory-wide grep_search', () => {
  const res = runGuardHook({
    toolCall: {
      name: 'grep_search',
      args: { SearchPath: 'c:\\server\\project', Query: 'password' }
    }
  });
  assert.strictEqual(res.decision, 'deny');
  assert(res.reason.includes('grep search is disabled'));
});

test('PreToolUse denies reading Linux server root paths (/etc/passwd)', () => {
  const res = runGuardHook({
    toolCall: {
      name: 'view_file',
      args: { AbsolutePath: '/etc/passwd' }
    }
  });
  assert.strictEqual(res.decision, 'deny');
  assert(res.reason.includes('Access Denied'));
});

test('PreToolUse denies reading Windows system root paths (C:\\Windows)', () => {
  const res = runGuardHook({
    toolCall: {
      name: 'view_file',
      args: { AbsolutePath: 'C:\\Windows\\System32\\config' }
    }
  });
  assert.strictEqual(res.decision, 'deny');
  assert(res.reason.includes('Access Denied'));
});

test('PreToolUse denies path traversal attempts (..)', () => {
  const res = runGuardHook({
    toolCall: {
      name: 'view_file',
      args: { AbsolutePath: 'c:\\app\\..\\..\\secret.env' }
    }
  });
  assert.strictEqual(res.decision, 'deny');
});

test('PreToolUse denies shell command with os.walk', () => {
  const res = runGuardHook({
    toolCall: {
      name: 'run_command',
      args: { CommandLine: 'python -c "import os; [print(x) for x in os.walk(\'/\')]"' }
    }
  });
  assert.strictEqual(res.decision, 'deny');
  assert(res.reason.includes('Execution Denied'));
});

test('PreToolUse denies shell command with Get-ChildItem -Recurse', () => {
  const res = runGuardHook({
    toolCall: {
      name: 'run_command',
      args: { CommandLine: 'Get-ChildItem -Recurse C:\\' }
    }
  });
  assert.strictEqual(res.decision, 'deny');
});

test('PreToolUse denies shell command with dir /s', () => {
  const res = runGuardHook({
    toolCall: {
      name: 'run_command',
      args: { CommandLine: 'dir /s /b *.secret' }
    }
  });
  assert.strictEqual(res.decision, 'deny');
});

test('PreToolUse denies system reconnaissance (tasklist / net user)', () => {
  const res = runGuardHook({
    toolCall: {
      name: 'run_command',
      args: { CommandLine: 'tasklist' }
    }
  });
  assert.strictEqual(res.decision, 'deny');
});

test('PreToolUse allows legitimate safe actions', () => {
  const res = runGuardHook({
    toolCall: {
      name: 'view_file',
      args: { AbsolutePath: 'c:\\Users\\daarv\\.gemini\\antigravity\\scratch\\aarkaai3b\\src\\index.ts' }
    }
  });
  assert.strictEqual(res.decision, 'allow');
});

console.log(`\nResults: ${passedTests}/${totalTests} tests passed successfully (100%).\n`);
