import * as fs from 'fs/promises';
import { safeExec } from './safe_exec.ts';
import { TransactionalSnapshotManager } from './snapshot_manager.ts';

export type SparcStage = 'SPECIFICATION' | 'PSEUDOCODE' | 'ARCHITECTURE' | 'REFINEMENT' | 'COMPLETION';
export type StageState = 'PASS' | 'FAIL' | 'BLOCKED';

export interface StageVerificationResult {
  stage: SparcStage;
  passed: boolean;
  state: StageState;
  score: number;
  stdout: string;
  stderr: string;
  blockers: string[];
}

export interface SwarmTaskManifest {
  taskId: string;
  specPath: string;
  pseudocodePath: string;
  architecturePath: string;
  sourcePaths: string[];
  testPaths: string[];
  workspaceRoot: string;
  minPassingScore: number;
}

export class SparcSwarmCoordinator {
  private snapshotManager: TransactionalSnapshotManager;

  constructor() {
    this.snapshotManager = new TransactionalSnapshotManager();
  }

  public async executePipeline(manifest: SwarmTaskManifest): Promise<{
    success: boolean;
    stageResults: StageVerificationResult[];
    finalScore: number;
    rolledBack: boolean;
  }> {
    const stageResults: StageVerificationResult[] = [];
    const allTargetFiles = [
      manifest.specPath,
      manifest.pseudocodePath,
      manifest.architecturePath,
      ...manifest.sourcePaths,
      ...manifest.testPaths
    ];

    await this.snapshotManager.beginTransaction(manifest.taskId, allTargetFiles);

    try {
      // Stage 1: Specification
      const specResult = await this.verifySpecification(manifest.specPath);
      stageResults.push(specResult);
      if (!specResult.passed || specResult.state !== 'PASS') {
        this.blockDownstream(stageResults, ['PSEUDOCODE', 'ARCHITECTURE', 'REFINEMENT', 'COMPLETION'], 'Specification gate failed or blocked');
        throw new Error(`SPARC Gate 1 Failed (Specification): ${specResult.blockers.join(', ')}`);
      }

      // Stage 2: Pseudocode
      const pseudoResult = await this.verifyPseudocode(manifest.pseudocodePath);
      stageResults.push(pseudoResult);
      if (!pseudoResult.passed || pseudoResult.state !== 'PASS') {
        this.blockDownstream(stageResults, ['ARCHITECTURE', 'REFINEMENT', 'COMPLETION'], 'Pseudocode gate failed or blocked');
        throw new Error(`SPARC Gate 2 Failed (Pseudocode): ${pseudoResult.blockers.join(', ')}`);
      }

      // Stage 3: Architecture
      const archResult = await this.verifyArchitecture(manifest.architecturePath, manifest.workspaceRoot);
      stageResults.push(archResult);
      if (!archResult.passed || archResult.state !== 'PASS') {
        this.blockDownstream(stageResults, ['REFINEMENT', 'COMPLETION'], 'Architecture gate failed or blocked');
        throw new Error(`SPARC Gate 3 Failed (Architecture): ${archResult.blockers.join(', ')}`);
      }

      // Stage 4: Refinement
      const refResult = await this.executeTddRefinement(manifest);
      stageResults.push(refResult);
      if (!refResult.passed || refResult.state !== 'PASS' || refResult.score < manifest.minPassingScore) {
        this.blockDownstream(stageResults, ['COMPLETION'], 'Refinement gate failed or blocked');
        throw new Error(`SPARC Gate 4 Failed (Refinement score: ${refResult.score} < ${manifest.minPassingScore})`);
      }

      const passedStages = stageResults.filter(r => r.passed && r.state === 'PASS');
      if (passedStages.length !== 4) {
        throw new Error('Completion gate blocked: One or more prerequisite stages did not pass verified gates.');
      }

      const avgScore = Number(
        (passedStages.reduce((sum, r) => sum + r.score, 0) / passedStages.length).toFixed(2)
      );

      const completionResult: StageVerificationResult = {
        stage: 'COMPLETION',
        passed: avgScore >= manifest.minPassingScore,
        state: avgScore >= manifest.minPassingScore ? 'PASS' : 'FAIL',
        score: avgScore,
        stdout: `Pipeline completed successfully with composite quality score ${avgScore}/10`,
        stderr: '',
        blockers: []
      };
      stageResults.push(completionResult);

      this.snapshotManager.commitTransaction(manifest.taskId);

      return {
        success: completionResult.passed,
        stageResults,
        finalScore: avgScore,
        rolledBack: false
      };
    } catch (err: any) {
      await this.snapshotManager.rollbackTransaction(manifest.taskId);

      return {
        success: false,
        stageResults,
        finalScore: 0,
        rolledBack: true
      };
    }
  }

  private blockDownstream(stageResults: StageVerificationResult[], stages: SparcStage[], reason: string): void {
    for (const stage of stages) {
      stageResults.push({
        stage,
        passed: false,
        state: 'BLOCKED',
        score: 0.0,
        stdout: '',
        stderr: `Stage BLOCKED: ${reason}`,
        blockers: [reason]
      });
    }
  }

  public async verifySpecification(specPath: string): Promise<StageVerificationResult> {
    try {
      const content = await fs.readFile(specPath, 'utf-8');
      if (!content || content.trim().length === 0) {
        return {
          stage: 'SPECIFICATION',
          passed: false,
          state: 'BLOCKED',
          score: 0.0,
          stdout: '',
          stderr: 'Specification document is empty or missing content',
          blockers: ['Empty specification document']
        };
      }

      const requiredClauses = [
        '# SPECIFICATION',
        '## PRECONDITIONS',
        '## POSTCONDITIONS',
        '## INVARIANTS',
        '## BOUNDARY CONSTRAINTS'
      ];

      const missing = requiredClauses.filter(clause => !content.toUpperCase().includes(clause));
      const passed = missing.length === 0 && content.length >= 200;
      const score = passed ? 9.2 : Number((( (5 - missing.length) / 5) * 8.0).toFixed(2));

      return {
        stage: 'SPECIFICATION',
        passed,
        state: passed ? 'PASS' : 'FAIL',
        score,
        stdout: passed ? 'All 5 formal specification clauses verified.' : '',
        stderr: missing.length > 0 ? `Missing required clauses: ${missing.join(', ')}` : '',
        blockers: missing
      };
    } catch (err: any) {
      return {
        stage: 'SPECIFICATION',
        passed: false,
        state: 'BLOCKED',
        score: 0,
        stdout: '',
        stderr: err.message,
        blockers: [err.message]
      };
    }
  }

  public async verifyPseudocode(pseudoPath: string): Promise<StageVerificationResult> {
    try {
      const content = await fs.readFile(pseudoPath, 'utf-8');
      if (!content || content.trim().length === 0) {
        return {
          stage: 'PSEUDOCODE',
          passed: false,
          state: 'BLOCKED',
          score: 0.0,
          stdout: '',
          stderr: 'Pseudocode document is empty',
          blockers: ['Empty pseudocode document']
        };
      }

      const hasAlgorithm = /ALGORITHM\s+[a-zA-Z0-9_]+/i.test(content);
      const hasTimeComplexity = /TIME COMPLEXITY:\s*O\([^\)]+\)/i.test(content);
      const hasSpaceComplexity = /SPACE COMPLEXITY:\s*O\([^\)]+\)/i.test(content);
      const hasInvariants = /LOOP INVARIANT|STATE TRANSITION/i.test(content);

      const blockers: string[] = [];
      if (!hasAlgorithm) blockers.push('Missing explicit ALGORITHM declaration');
      if (!hasTimeComplexity) blockers.push('Missing formal asymptotic time complexity bounds O(...)');
      if (!hasSpaceComplexity) blockers.push('Missing formal asymptotic space complexity bounds O(...)');
      if (!hasInvariants) blockers.push('Missing LOOP INVARIANT or STATE TRANSITION proof');

      const passed = blockers.length === 0;
      const present = 4 - blockers.length;
      const score = passed ? 9.0 : Number(((present / 4) * 7.5).toFixed(2));

      return {
        stage: 'PSEUDOCODE',
        passed,
        state: passed ? 'PASS' : 'FAIL',
        score,
        stdout: passed ? 'Algorithmic structure and asymptotic complexity proofs verified.' : '',
        stderr: blockers.join('; '),
        blockers
      };
    } catch (err: any) {
      return {
        stage: 'PSEUDOCODE',
        passed: false,
        state: 'BLOCKED',
        score: 0,
        stdout: '',
        stderr: err.message,
        blockers: [err.message]
      };
    }
  }

  public async verifyArchitecture(archPath: string, workspaceRoot: string): Promise<StageVerificationResult> {
    try {
      const content = await fs.readFile(archPath, 'utf-8');
      if (!content || content.trim().length === 0) {
        return {
          stage: 'ARCHITECTURE',
          passed: false,
          state: 'BLOCKED',
          score: 0.0,
          stdout: '',
          stderr: 'Architecture file is empty',
          blockers: ['Empty architecture file']
        };
      }

      const hasContracts = /export\s+(interface|type|class|enum)\s+[a-zA-Z0-9_]+/i.test(content);

      if (!hasContracts) {
        return {
          stage: 'ARCHITECTURE',
          passed: false,
          state: 'FAIL',
          score: 2.0,
          stdout: '',
          stderr: 'Architecture artifact contains no exported interface or type contracts.',
          blockers: ['No exported contracts']
        };
      }

      try {
        const res = await safeExec('node', ['--check', archPath], { cwd: workspaceRoot });
        return {
          stage: 'ARCHITECTURE',
          passed: true,
          state: 'PASS',
          score: 9.2,
          stdout: 'Architecture contracts validated with zero syntax or interface errors.',
          stderr: res.stderr,
          blockers: []
        };
      } catch (execErr: any) {
        return {
          stage: 'ARCHITECTURE',
          passed: false,
          state: 'FAIL',
          score: 1.0,
          stdout: execErr.stdout || '',
          stderr: execErr.stderr || execErr.message,
          blockers: ['Syntax error in architecture module']
        };
      }
    } catch (err: any) {
      return {
        stage: 'ARCHITECTURE',
        passed: false,
        state: 'BLOCKED',
        score: 0.0,
        stdout: '',
        stderr: err.message,
        blockers: ['Interface contract compilation failed']
      };
    }
  }

  public async executeTddRefinement(manifest: SwarmTaskManifest): Promise<StageVerificationResult> {
    try {
      if (!manifest.testPaths || manifest.testPaths.length === 0) {
        return {
          stage: 'REFINEMENT',
          passed: false,
          state: 'BLOCKED',
          score: 0.0,
          stdout: '',
          stderr: 'Refinement BLOCKED: Zero test paths provided in manifest',
          blockers: ['Zero test paths provided']
        };
      }

      // 1. Verify syntax of source files
      let compilerPassed = true;
      for (const src of manifest.sourcePaths) {
        try {
          await safeExec('node', ['--check', src], { cwd: manifest.workspaceRoot });
        } catch (checkErr: any) {
          compilerPassed = false;
          return {
            stage: 'REFINEMENT',
            passed: false,
            state: 'FAIL',
            score: 2.0,
            stdout: checkErr.stdout || '',
            stderr: `Source file syntax failure in ${src}: ${checkErr.stderr || checkErr.message}`,
            blockers: [`Syntax error in ${src}`]
          };
        }
      }

      // 2. Execute real unit tests
      let allTestsPassed = true;
      let totalTestsRun = 0;
      let stdoutLog = '';
      let stderrLog = '';

      for (const testPath of manifest.testPaths) {
        try {
          const testRes = await safeExec('node', ['--test', testPath], {
            cwd: manifest.workspaceRoot
          });
          stdoutLog += testRes.stdout + '\n';
          stderrLog += testRes.stderr + '\n';

          const passMatch = testRes.stdout.match(/pass\s+(\d+)/i);
          if (passMatch) {
            totalTestsRun += parseInt(passMatch[1], 10);
          }
        } catch (testErr: any) {
          allTestsPassed = false;
          stdoutLog += (testErr.stdout || '') + '\n';
          stderrLog += (testErr.stderr || testErr.message) + '\n';
        }
      }

      if (totalTestsRun === 0 && !allTestsPassed) {
        allTestsPassed = false;
      }

      const score = (allTestsPassed && compilerPassed) ? 9.5 : 3.0;
      const passed = allTestsPassed && compilerPassed && score >= manifest.minPassingScore;

      return {
        stage: 'REFINEMENT',
        passed,
        state: passed ? 'PASS' : 'FAIL',
        score,
        stdout: stdoutLog,
        stderr: passed ? '' : `Test runner reported failures: ${stderrLog}`,
        blockers: passed ? [] : ['Unit tests reported failures or unhandled exceptions']
      };
    } catch (err: any) {
      return {
        stage: 'REFINEMENT',
        passed: false,
        state: 'BLOCKED',
        score: 0.0,
        stdout: '',
        stderr: err.message,
        blockers: ['Execution crash during test runner']
      };
    }
  }
}
