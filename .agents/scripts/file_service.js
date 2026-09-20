/**
 * FileService: Capability-Based, Zero-Discovery File Interface
 * 
 * Enforces strict handle-based access to files. Aarka interacts solely with
 * cryptographically generated `file_id` references rather than raw server filesystem paths.
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

class FileService {
  constructor(baseStorageDir = null) {
    this.baseStorageDir = baseStorageDir || path.resolve(__dirname, '..', '..', '.storage', 'sessions');
    this.registry = new Map(); // sessionId -> Map(file_id -> FileMetadata)
    this._ensureBaseDirectory();
  }

  _ensureBaseDirectory() {
    if (!fs.existsSync(this.baseStorageDir)) {
      fs.mkdirSync(this.baseStorageDir, { recursive: true, mode: 0o700 });
    }
  }

  _getSessionDir(sessionId) {
    // Sanitize sessionId to prevent directory traversal
    const safeSessionId = sessionId.replace(/[^a-zA-Z0-9_-]/g, '');
    if (!safeSessionId) {
      throw new Error('Invalid or unsafe sessionId');
    }
    const sessionDir = path.join(this.baseStorageDir, safeSessionId);
    if (!fs.existsSync(sessionDir)) {
      fs.mkdirSync(sessionDir, { recursive: true, mode: 0o700 });
    }
    return sessionDir;
  }

  /**
   * Registers an uploaded user file into isolated session storage.
   * Generates an opaque handle (file_id).
   */
  registerFile(sessionId, fileContent, originalName, mimeType = 'application/octet-stream') {
    const sessionDir = this._getSessionDir(sessionId);
    const sanitizedFileName = path.basename(originalName).replace(/[^a-zA-Z0-9._-]/g, '_');
    const fileId = 'fid_' + crypto.randomBytes(16).toString('hex');
    const storagePath = path.join(sessionDir, fileId + '_' + sanitizedFileName);

    fs.writeFileSync(storagePath, fileContent, { mode: 0o600 });

    const stats = fs.statSync(storagePath);
    const metadata = {
      fileId,
      originalName: sanitizedFileName,
      mimeType,
      sizeBytes: stats.size,
      createdAt: new Date().toISOString(),
      storagePath: path.resolve(storagePath)
    };

    if (!this.registry.has(sessionId)) {
      this.registry.set(sessionId, new Map());
    }
    this.registry.get(sessionId).set(fileId, metadata);

    // Return opaque reference only (storagePath is strictly internal)
    return {
      fileId: metadata.fileId,
      fileName: metadata.originalName,
      mimeType: metadata.mimeType,
      sizeBytes: metadata.sizeBytes,
      createdAt: metadata.createdAt
    };
  }

  /**
   * Reads a file using only its explicit opaque handle (file_id).
   * Verifies canonical path strictly resides within the session isolation sandbox.
   */
  readFile(sessionId, fileId, encoding = 'utf-8') {
    const sessionRegistry = this.registry.get(sessionId);
    if (!sessionRegistry || !sessionRegistry.has(fileId)) {
      throw new Error(`Permission Denied: File handle '${fileId}' does not exist or has not been authorized in this session.`);
    }

    const metadata = sessionRegistry.get(fileId);
    const sessionDir = this._getSessionDir(sessionId);

    // Canonical path verification to protect against symlink escapes
    const realFilePath = fs.realpathSync(metadata.storagePath);
    const realSessionDir = fs.realpathSync(sessionDir);

    if (!realFilePath.startsWith(realSessionDir + path.sep)) {
      throw new Error(`Security Violation: File path escape detected for handle '${fileId}'.`);
    }

    const content = encoding ? fs.readFileSync(realFilePath, encoding) : fs.readFileSync(realFilePath);
    return {
      metadata: {
        fileId: metadata.fileId,
        fileName: metadata.originalName,
        mimeType: metadata.mimeType,
        sizeBytes: metadata.sizeBytes
      },
      content
    };
  }

  /**
   * Lists explicit authorized file handles for the current session.
   * Does NOT scan the filesystem; reads solely from the authorized in-memory registry.
   */
  listAuthorizedFiles(sessionId) {
    const sessionRegistry = this.registry.get(sessionId);
    if (!sessionRegistry) {
      return [];
    }

    const fileList = [];
    for (const [fileId, meta] of sessionRegistry.entries()) {
      fileList.push({
        fileId,
        fileName: meta.originalName,
        mimeType: meta.mimeType,
        sizeBytes: meta.sizeBytes,
        createdAt: meta.createdAt
      });
    }
    return fileList;
  }

  /**
   * Revokes and securely purges an explicit file handle.
   */
  revokeFile(sessionId, fileId) {
    const sessionRegistry = this.registry.get(sessionId);
    if (!sessionRegistry || !sessionRegistry.has(fileId)) {
      return false;
    }

    const metadata = sessionRegistry.get(fileId);
    try {
      if (fs.existsSync(metadata.storagePath)) {
        fs.unlinkSync(metadata.storagePath);
      }
    } catch (_) {
      // Ignore unlink errors during cleanup
    }

    sessionRegistry.delete(fileId);
    return true;
  }
}

module.exports = { FileService };
