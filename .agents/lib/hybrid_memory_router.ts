import type { IRuVectorClient, SearchHit } from './ruvector_client.ts';
import { performance } from 'perf_hooks';

export interface MemoryEntity {
  name: string;
  entityType: string;
  observations: string[];
}

export interface IMcpMemoryAdapter {
  searchNodes(query: string): Promise<MemoryEntity[]>;
  openNodes(names: string[]): Promise<MemoryEntity[]>;
}

export interface HybridContextResult {
  query: string;
  hardConstraints: string[];
  semanticAssociates: SearchHit[];
  fusedScoreMap: Record<string, number>;
  synthesizedContextPrompt: string;
  latencyMs: number;
}

export class HybridMemoryRouter {
  private mcpAdapter: IMcpMemoryAdapter;
  private ruVectorClient: IRuVectorClient;
  private rrfConstant: number;

  constructor(
    mcpAdapter: IMcpMemoryAdapter,
    ruVectorClient: IRuVectorClient,
    rrfConstant: number = 60
  ) {
    this.mcpAdapter = mcpAdapter;
    this.ruVectorClient = ruVectorClient;
    this.rrfConstant = rrfConstant;
  }

  public async retrieveHybridContext(
    query: string,
    queryVector: number[],
    topK: number = 5
  ): Promise<HybridContextResult> {
    const t0 = performance.now();

    const [entities, vectorHits] = await Promise.all([
      this.mcpAdapter.searchNodes(query),
      this.ruVectorClient.search(queryVector, topK)
    ]);

    const hardConstraints: string[] = [];
    const fusedScoreMap: Record<string, number> = {};

    const entityCount = entities.length;
    for (let i = 0; i < entityCount; i++) {
      const entity = entities[i];
      const rank = i + 1;
      const rrf = 1 / (this.rrfConstant + rank);
      fusedScoreMap[entity.name] = (fusedScoreMap[entity.name] || 0) + (rrf * 1.5);

      const obsCount = entity.observations.length;
      for (let j = 0; j < obsCount; j++) {
        hardConstraints.push(`[RULE:${entity.entityType.toUpperCase()}] ${entity.name}: ${entity.observations[j]}`);
      }
    }

    const vectorCount = vectorHits.length;
    for (let i = 0; i < vectorCount; i++) {
      const hit = vectorHits[i];
      const rank = i + 1;
      const rrf = 1 / (this.rrfConstant + rank);
      fusedScoreMap[hit.id] = (fusedScoreMap[hit.id] || 0) + rrf;
    }

    const promptSections: string[] = [];

    if (hardConstraints.length > 0) {
      promptSections.push('### DETERMINISTIC ARCHITECTURAL CONSTRAINTS (MCP GRAPH):');
      promptSections.push(...hardConstraints);
    }

    if (vectorHits.length > 0) {
      promptSections.push('\n### ASSOCIATIVE CODE PATTERNS (RUVECTOR):');
      vectorHits.forEach((hit, idx) => {
        const score = hit.score.toFixed(4);
        const metaStr = hit.metadata ? JSON.stringify(hit.metadata) : '';
        promptSections.push(`- Match #${idx + 1} [Score: ${score}] ID: ${hit.id} ${metaStr}`);
      });
    }

    const latencyMs = Number((performance.now() - t0).toFixed(3));

    return {
      query,
      hardConstraints,
      semanticAssociates: vectorHits,
      fusedScoreMap,
      synthesizedContextPrompt: promptSections.join('\n'),
      latencyMs
    };
  }
}
