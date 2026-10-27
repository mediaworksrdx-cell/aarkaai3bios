export interface VectorEntry {
  id: string;
  vector: number[];
  metadata?: Record<string, any>;
}

export interface SearchHit {
  id: string;
  score: number;
  metadata?: Record<string, any>;
}

export interface IRuVectorClient {
  insert(entry: VectorEntry): Promise<boolean>;
  search(queryVector: number[], k: number): Promise<SearchHit[]>;
  size(): number;
}

interface StoredVector {
  id: string;
  normalizedVec: Float32Array;
  metadata?: Record<string, any>;
}

/**
 * PureTypeScriptVectorFallback Engine
 * High-performance, SIMD-friendly in-memory cosine similarity engine.
 * Pre-normalizes vectors to unit length and uses bounded top-k insertion for sub-millisecond execution.
 */
export class PureTypeScriptVectorFallback implements IRuVectorClient {
  private dimension: number;
  private entries: StoredVector[];
  private idIndex: Map<string, number>;
  private queryBuffer: Float32Array;

  constructor(dimension: number = 384) {
    this.dimension = dimension;
    this.entries = [];
    this.idIndex = new Map();
    this.queryBuffer = new Float32Array(dimension);
  }

  public async insert(entry: VectorEntry): Promise<boolean> {
    if (!entry.vector || entry.vector.length !== this.dimension) {
      throw new Error(`Dimension mismatch: expected ${this.dimension}, got ${entry?.vector?.length}`);
    }

    const len = this.dimension;
    let sumSq = 0;
    for (let i = 0; i < len; i++) {
      sumSq += entry.vector[i] * entry.vector[i];
    }
    const invNorm = sumSq > 0 ? 1 / Math.sqrt(sumSq) : 0;

    const normalizedVec = new Float32Array(len);
    for (let i = 0; i < len; i++) {
      normalizedVec[i] = entry.vector[i] * invNorm;
    }

    const stored: StoredVector = {
      id: entry.id,
      normalizedVec,
      metadata: entry.metadata
    };

    if (this.idIndex.has(entry.id)) {
      const idx = this.idIndex.get(entry.id)!;
      this.entries[idx] = stored;
    } else {
      this.idIndex.set(entry.id, this.entries.length);
      this.entries.push(stored);
    }

    return true;
  }

  public async search(queryVector: number[], k: number = 5): Promise<SearchHit[]> {
    if (!queryVector || queryVector.length !== this.dimension) {
      throw new Error(`Query vector dimension mismatch: expected ${this.dimension}, got ${queryVector?.length}`);
    }

    const len = this.dimension;
    let sumSq = 0;
    for (let i = 0; i < len; i++) {
      sumSq += queryVector[i] * queryVector[i];
    }
    const invNorm = sumSq > 0 ? 1 / Math.sqrt(sumSq) : 0;

    const q = this.queryBuffer;
    for (let i = 0; i < len; i++) {
      q[i] = queryVector[i] * invNorm;
    }

    const topHits: SearchHit[] = [];
    const totalEntries = this.entries.length;

    for (let e = 0; e < totalEntries; e++) {
      const record = this.entries[e];
      const v = record.normalizedVec;

      let dot = 0;
      for (let i = 0; i < len; i++) {
        dot += q[i] * v[i];
      }

      if (topHits.length < k) {
        let pos = topHits.length;
        while (pos > 0 && topHits[pos - 1].score < dot) {
          pos--;
        }
        topHits.splice(pos, 0, { id: record.id, score: dot, metadata: record.metadata });
      } else if (dot > topHits[k - 1].score) {
        let pos = k - 1;
        while (pos > 0 && topHits[pos - 1].score < dot) {
          pos--;
        }
        topHits.splice(pos, 0, { id: record.id, score: dot, metadata: record.metadata });
        topHits.pop();
      }
    }

    return topHits;
  }

  public size(): number {
    return this.entries.length;
  }
}

export class RuVectorClientFactory {
  public static async createClient(storagePath?: string, dimension: number = 384): Promise<IRuVectorClient> {
    try {
      const ruvectorModule: any = await import('@ruvector/node');
      const VectorDB = ruvectorModule.VectorDB || ruvectorModule.default?.VectorDB;

      if (VectorDB) {
        const db = new VectorDB({
          dimensions: dimension,
          storagePath: storagePath || './ruvector-memory.db',
          hnsw: { m: 16, efConstruction: 64 }
        });

        return {
          async insert(entry: VectorEntry): Promise<boolean> {
            return await db.insert(entry.id, entry.vector, entry.metadata);
          },
          async search(queryVector: number[], k: number): Promise<SearchHit[]> {
            return await db.search(queryVector, k);
          },
          size(): number {
            return db.size ? db.size() : -1;
          }
        };
      }
    } catch {}

    return new PureTypeScriptVectorFallback(dimension);
  }
}
