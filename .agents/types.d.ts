/// <reference types="node" />

declare module '@ruvector/node' {
  export interface VectorDBOptions {
    dimensions?: number;
    storagePath?: string;
    hnsw?: { m?: number; efConstruction?: number };
  }
  export class VectorDB {
    constructor(options?: VectorDBOptions);
    insert(id: string, vector: number[], metadata?: Record<string, any>): Promise<boolean>;
    search(queryVector: number[], k: number): Promise<Array<{ id: string; score: number; metadata?: Record<string, any> }>>;
    size?(): number;
  }
}
