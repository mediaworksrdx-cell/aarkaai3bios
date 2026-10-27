import * as crypto from 'crypto';
import * as fs from 'fs/promises';
import * as path from 'path';

export type CapabilityAction = 'READ' | 'WRITE' | 'EXECUTE';

export interface CapabilityToken {
  tokenId: string;
  fileId: string;
  allowedActions: CapabilityAction[];
  expiresAt: number;
  signature: string;
}

export class HardenedCapabilityGateway {
  private canonicalWorkspaceRoot: string;
  private readonly secretKey: Buffer;

  constructor(workspaceRoot: string, secretKeyHex?: string) {
    this.canonicalWorkspaceRoot = path.resolve(workspaceRoot);
    this.secretKey = secretKeyHex
      ? Buffer.from(secretKeyHex, 'hex')
      : crypto.randomBytes(32);
  }

  public async initialize(): Promise<void> {
    try {
      this.canonicalWorkspaceRoot = await fs.realpath(this.canonicalWorkspaceRoot);
    } catch {
      await fs.mkdir(this.canonicalWorkspaceRoot, { recursive: true });
      this.canonicalWorkspaceRoot = await fs.realpath(this.canonicalWorkspaceRoot);
    }
  }

  public issueCapability(
    fileId: string,
    actions: CapabilityAction[],
    ttlMs: number = 300000
  ): CapabilityToken {
    if (!fileId || typeof fileId !== 'string') {
      throw new Error('CAPABILITY ERROR: fileId must be a valid non-empty string');
    }

    const cleanPath = path.normalize(fileId).replace(/^[\\\/]+/, '');
    const expiresAt = Date.now() + ttlMs;
    const tokenId = `cap_${crypto.randomBytes(8).toString('hex')}`;
    const sortedActions = [...actions].sort();

    const payload = `${tokenId}:${cleanPath}:${sortedActions.join(',')}:${expiresAt}`;
    const signature = crypto
      .createHmac('sha256', this.secretKey)
      .update(payload)
      .digest('hex');

    return {
      tokenId,
      fileId: cleanPath,
      allowedActions: sortedActions,
      expiresAt,
      signature
    };
  }

  public async readFileWithCapability(token: CapabilityToken): Promise<string> {
    this.validateToken(token, 'READ');
    const physicalPath = await this.getValidatedPhysicalPath(token.fileId);
    return await fs.readFile(physicalPath, 'utf-8');
  }

  public async writeFileWithCapability(token: CapabilityToken, content: string): Promise<void> {
    this.validateToken(token, 'WRITE');
    const physicalPath = await this.getValidatedPhysicalPath(token.fileId);
    const parentDir = path.dirname(physicalPath);
    await fs.mkdir(parentDir, { recursive: true });
    await fs.writeFile(physicalPath, content, 'utf-8');
  }

  public validateToken(token: CapabilityToken, requestedAction: CapabilityAction): void {
    if (!token || !token.tokenId || !token.fileId || !token.signature) {
      throw new Error('CAPABILITY ERROR: Malformed or missing capability token');
    }

    if (Date.now() > token.expiresAt) {
      throw new Error(`CAPABILITY ERROR: Token ${token.tokenId} has expired.`);
    }

    if (!token.allowedActions.includes(requestedAction)) {
      throw new Error(
        `CAPABILITY ERROR: Action '${requestedAction}' not authorized for token ${token.tokenId}. Authorized: [${token.allowedActions.join(', ')}]`
      );
    }

    const sortedActions = [...token.allowedActions].sort();
    const payload = `${token.tokenId}:${token.fileId}:${sortedActions.join(',')}:${token.expiresAt}`;
    const expectedSig = crypto
      .createHmac('sha256', this.secretKey)
      .update(payload)
      .digest('hex');

    if (!crypto.timingSafeEqual(Buffer.from(token.signature, 'hex'), Buffer.from(expectedSig, 'hex'))) {
      throw new Error(`CAPABILITY ERROR: Cryptographic signature mismatch on token ${token.tokenId}.`);
    }
  }

  public async getValidatedPhysicalPath(fileId: string): Promise<string> {
    if (fileId.includes('\0') || fileId.includes('..')) {
      throw new Error(`SECURITY ALERT: Path traversal or null-byte attempted: ${fileId}`);
    }

    const rawPath = path.resolve(this.canonicalWorkspaceRoot, fileId);

    let realTarget: string;
    try {
      realTarget = await fs.realpath(rawPath);
    } catch (err: any) {
      if (err.code === 'ENOENT') {
        let checkDir = path.dirname(rawPath);
        while (checkDir !== this.canonicalWorkspaceRoot && checkDir.length > this.canonicalWorkspaceRoot.length) {
          try {
            const parentReal = await fs.realpath(checkDir);
            if (!parentReal.startsWith(this.canonicalWorkspaceRoot + path.sep) && parentReal !== this.canonicalWorkspaceRoot) {
              throw new Error(`SECURITY ALERT: Directory breakout attempted: ${fileId}`);
            }
            break;
          } catch (e: any) {
            if (e.code === 'ENOENT') {
              checkDir = path.dirname(checkDir);
            } else {
              throw e;
            }
          }
        }
        return rawPath;
      }
      throw err;
    }

    if (!realTarget.startsWith(this.canonicalWorkspaceRoot + path.sep) && realTarget !== this.canonicalWorkspaceRoot) {
      throw new Error(`SECURITY ALERT: Symlink breakout attempted to external path: ${realTarget}`);
    }

    return realTarget;
  }
}
