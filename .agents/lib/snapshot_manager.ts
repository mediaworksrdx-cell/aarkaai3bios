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
  success: boolean;
}

/**
 * Transactional Multi-File Working Tree Snapshot Engine
 * Provides atomic capture, file modification tracking, SHA-256 byte parity, and zero-leak rollback.
 */
export class TransactionalSnapshotManager {
  private activeTransactions: Map<string, FileSnapshot[]> = new Map();

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

    const restoredFiles: string[] = [];
    const unlinkedOrphans: string[] = [];
    const errors: string[] = [];

    for (let i = snapshots.length - 1; i >= 0; i--) {
      const snap = snapshots[i];
      try {
        if (!snap.existed) {
          try {
            await fs.unlink(snap.filePath);
            unlinkedOrphans.push(snap.filePath);
          } catch (err: any) {
            if (err.code !== 'ENOENT') {
              errors.push(`Unlink error on ${snap.filePath}: ${err.message}`);
            }
          }
        } else if (snap.content) {
          await fs.mkdir(path.dirname(snap.filePath), { recursive: true });
          await fs.writeFile(snap.filePath, snap.content, { mode: snap.mode });

          // Parity check
          const written = await fs.readFile(snap.filePath);
          const hash = crypto.createHash('sha256').update(written).digest('hex');
          if (hash !== snap.sha256) {
            errors.push(`Byte parity mismatch on ${snap.filePath}: expected ${snap.sha256}, got ${hash}`);
          } else {
            restoredFiles.push(snap.filePath);
          }
        }
      } catch (err: any) {
        errors.push(`Failed to restore ${snap.filePath}: ${err.message}`);
      }
    }

    this.activeTransactions.delete(transactionId);

    const evidence: RollbackEvidence = {
      transactionId,
      restoredFiles,
      unlinkedOrphans,
      errors,
      success: errors.length === 0
    };

    if (errors.length > 0) {
      const err = new Error(`Rollback completed with errors: ${errors.join('; ')}`);
      (err as any).evidence = evidence;
      throw err;
    }

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
}
