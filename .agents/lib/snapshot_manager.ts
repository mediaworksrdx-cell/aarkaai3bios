import * as crypto from 'crypto';
import * as fs from 'fs/promises';
import * as path from 'path';

export interface FileSnapshot {
  filePath: string;
  existed: boolean;
  content?: Buffer;
  sha256?: string;
  mode?: number;
}

export interface RollbackEvidence {
  transactionId: string;
  restoredFiles: string[];
  unlinkedOrphans: string[];
  errors: string[];
  phase: string;
  success: boolean;
}

/**
 * Transactional Multi-File Working Tree Snapshot Engine
 * Provides two-phase atomic capture, file modification tracking, SHA-256 byte parity,
 * and zero-leak rollback. Retains snapshots if restoration encounters any error.
 */
export class TransactionalSnapshotManager {
  private activeTransactions: Map<string, FileSnapshot[]> = new Map();
  private failedTransactions: Map<string, { snapshots: FileSnapshot[]; evidence: RollbackEvidence }> = new Map();

  public async beginTransaction(transactionId: string, filePaths: string[]): Promise<void> {
    if (!transactionId || typeof transactionId !== 'string') {
      throw new Error('Transaction ID must be a non-empty string');
    }
    if (this.activeTransactions.has(transactionId)) {
      throw new Error(`Transaction '${transactionId}' is already active.`);
    }

    const snapshots: FileSnapshot[] = [];

    for (const filePath of filePaths) {
      const resolved = path.resolve(filePath);
      try {
        const stat = await fs.stat(resolved);
        const content = await fs.readFile(resolved);
        const sha256 = crypto.createHash('sha256').update(content).digest('hex');
        snapshots.push({ filePath: resolved, existed: true, content, sha256, mode: stat.mode });
      } catch (err: any) {
        if (err.code === 'ENOENT') {
          snapshots.push({ filePath: resolved, existed: false });
        } else {
          throw err;
        }
      }
    }

    this.activeTransactions.set(transactionId, snapshots);
  }

  public async rollbackTransaction(transactionId: string): Promise<RollbackEvidence> {
    const snapshots = this.activeTransactions.get(transactionId);
    if (!snapshots) {
      throw new Error(`Cannot rollback: No active transaction found with ID '${transactionId}'.`);
    }

    const stagingFiles: string[] = [];
    const restoredFiles: string[] = [];
    const unlinkedOrphans: string[] = [];
    const errors: string[] = [];

    // ─── PHASE 1: Staging & Parity Verification ──────────────────────────
    for (const snap of snapshots) {
      if (snap.existed && snap.content) {
        const stagePath = `${snap.filePath}.aarka_rollback_stage`;
        try {
          await fs.mkdir(path.dirname(stagePath), { recursive: true });
          await fs.writeFile(stagePath, snap.content, { mode: snap.mode });

          const stageBytes = await fs.readFile(stagePath);
          const hash = crypto.createHash('sha256').update(stageBytes).digest('hex');
          if (snap.sha256 && hash !== snap.sha256) {
            throw new Error(`Staging byte parity mismatch on ${stagePath}: expected ${snap.sha256}, got ${hash}`);
          }
          stagingFiles.push(stagePath);
        } catch (stageErr: any) {
          errors.push(`Phase 1 staging error on ${snap.filePath}: ${stageErr.message}`);

          // Abort Phase 1: clean staging files without modifying live targets
          for (const sf of stagingFiles) {
            try {
              await fs.unlink(sf);
            } catch {}
          }

          const evidence: RollbackEvidence = {
            transactionId,
            restoredFiles: [],
            unlinkedOrphans: [],
            errors,
            phase: 'PHASE_1_STAGING',
            success: false
          };

          // Preserve snapshots on failure
          this.failedTransactions.set(transactionId, { snapshots, evidence });
          const err = new Error(`Atomic rollback aborted in Phase 1 (no files modified): ${errors.join('; ')}`);
          (err as any).evidence = evidence;
          throw err;
        }
      }
    }

    // ─── PHASE 2: Atomic Swap & Orphan Cleanup ───────────────────────────
    for (let i = snapshots.length - 1; i >= 0; i--) {
      const snap = snapshots[i];
      try {
        if (!snap.existed) {
          try {
            await fs.unlink(snap.filePath);
            unlinkedOrphans.push(snap.filePath);
          } catch (unlinkErr: any) {
            if (unlinkErr.code !== 'ENOENT') {
              errors.push(`Unlink error on ${snap.filePath}: ${unlinkErr.message}`);
            }
          }
        } else if (snap.content) {
          const stagePath = `${snap.filePath}.aarka_rollback_stage`;
          await fs.rename(stagePath, snap.filePath);
          restoredFiles.push(snap.filePath);
        }
      } catch (err: any) {
        errors.push(`Phase 2 replacement error on ${snap.filePath}: ${err.message}`);
      }
    }

    const evidence: RollbackEvidence = {
      transactionId,
      restoredFiles,
      unlinkedOrphans,
      errors,
      phase: 'PHASE_2_EXECUTION',
      success: errors.length === 0
    };

    if (errors.length > 0) {
      // Preserve snapshots in failed map
      this.failedTransactions.set(transactionId, { snapshots, evidence });
      const err = new Error(`Rollback completed with Phase 2 errors: ${errors.join('; ')}. Snapshots preserved.`);
      (err as any).evidence = evidence;
      throw err;
    }

    // Success: clean release
    this.activeTransactions.delete(transactionId);
    return evidence;
  }

  public commitTransaction(transactionId: string): boolean {
    if (!this.activeTransactions.has(transactionId)) {
      throw new Error(`Cannot commit: No active transaction found with ID '${transactionId}'.`);
    }
    return this.activeTransactions.delete(transactionId);
  }

  public hasActiveTransaction(transactionId: string): boolean {
    return this.activeTransactions.has(transactionId);
  }

  public activeTransactionCount(): number {
    return this.activeTransactions.size;
  }

  public getFailedTransaction(transactionId: string): { snapshots: FileSnapshot[]; evidence: RollbackEvidence } | undefined {
    return this.failedTransactions.get(transactionId);
  }
}
