import * as fs from 'fs/promises';

export interface FileSnapshot {
  filePath: string;
  existed: boolean;
  content?: Buffer;
  mode?: number;
}

/**
 * Transactional Multi-File Working Tree Snapshot Engine
 * Provides atomic capture, file modification tracking, and zero-leak rollback.
 */
export class TransactionalSnapshotManager {
  private activeTransactions: Map<string, FileSnapshot[]> = new Map();

  public async beginTransaction(transactionId: string, filePaths: string[]): Promise<void> {
    const snapshots: FileSnapshot[] = [];

    for (const filePath of filePaths) {
      try {
        const stat = await fs.stat(filePath);
        const content = await fs.readFile(filePath);
        snapshots.push({ filePath, existed: true, content, mode: stat.mode });
      } catch (err: any) {
        if (err.code === 'ENOENT') {
          snapshots.push({ filePath, existed: false });
        } else {
          throw err;
        }
      }
    }

    this.activeTransactions.set(transactionId, snapshots);
  }

  public async rollbackTransaction(transactionId: string): Promise<boolean> {
    const snapshots = this.activeTransactions.get(transactionId);
    if (!snapshots) return false;

    for (const snap of snapshots) {
      if (!snap.existed) {
        try {
          await fs.unlink(snap.filePath);
        } catch (err: any) {
          if (err.code !== 'ENOENT') {
            console.error(`Rollback unlink error on ${snap.filePath}:`, err);
          }
        }
      } else if (snap.content) {
        const tempPath = `${snap.filePath}.rollback.${Date.now()}`;
        await fs.writeFile(tempPath, snap.content, { mode: snap.mode });
        await fs.rename(tempPath, snap.filePath);
      }
    }

    this.activeTransactions.delete(transactionId);
    return true;
  }

  public commitTransaction(transactionId: string): boolean {
    return this.activeTransactions.delete(transactionId);
  }

  public hasActiveTransaction(transactionId: string): boolean {
    return this.activeTransactions.has(transactionId);
  }
}
