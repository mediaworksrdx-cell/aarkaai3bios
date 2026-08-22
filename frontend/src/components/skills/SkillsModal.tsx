'use client';

import React, { useState } from 'react';
import { X, Sparkles, Cpu, BookOpen, Layers, ShieldCheck, Search, Code, TrendingUp, FileText } from 'lucide-react';

interface SkillsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const SKILL_CATEGORIES = [
  {
    category: 'Finance & Quantitative Math',
    icon: TrendingUp,
    skills: [
      { name: 'finance', description: 'Quantitative portfolio construction, Sharpe/Sortino ratios, risk models, and Black-Scholes pricing' },
      { name: 'dcf-valuation', description: 'Institutional 3-statement Discounted Cash Flow models with WACC & terminal sensitivity tables' },
      { name: 'market-microstructure', description: 'Order book dynamics, limit orders, spread analysis, and execution slippage modeling' },
    ],
  },
  {
    category: 'System Architecture & Engineering',
    icon: Layers,
    skills: [
      { name: 'architecture', description: 'Distributed systems design, CAP theorem trade-offs, consensus (Raft/Paxos), and microservices' },
      { name: 'codebase-design', description: 'Deep module interfaces, information hiding, seam placement, and AI-navigable architectures' },
      { name: 'domain-modeling', description: 'Ubiquitous language construction, DDD entity boundaries, and architectural decision records' },
      { name: 'design-an-interface', description: 'Parallel multi-agent interface exploration and radical API design comparisons' },
    ],
  },
  {
    category: 'Code Quality, Refactoring & QA',
    icon: Code,
    skills: [
      { name: 'tdd', description: 'Test-driven development, red-green-refactor cycles, and comprehensive integration testing' },
      { name: 'request-refactor-plan', description: 'Safe incremental refactoring plans broken down into tiny, verifiable commits' },
      { name: 'diagnosing-bugs', description: 'Root-cause hypothesis generation and regression testing for complex runtime defects' },
      { name: 'qa', description: 'Interactive QA sessions and conversational GitHub issue filing with domain context' },
      { name: 'review', description: 'Parallel standards and PRD spec reviews across branch diffs' },
      { name: 'resolving-merge-conflicts', description: 'Semantic git merge conflict resolution preserving codebase invariants' },
    ],
  },
  {
    category: 'Document Generation & Publishing',
    icon: FileText,
    skills: [
      { name: 'pdf', description: 'Strict 6-page high-density executive report generator with embedded Base64 matplotlib charts' },
      { name: 'obsidian-vault', description: 'Bidirectional markdown knowledge bases, wikilinks, and structured index notes' },
    ],
  },
  {
    category: 'Autonomous Subagents & Orchestration',
    icon: Cpu,
    skills: [
      { name: 'skill-router', description: 'Vector FAISS semantic skill discovery and automatic priority execution pipeline' },
      { name: 'ai-ml', description: 'Dataset pipeline review, training methodologies, evaluation benchmarks, and inference profiling' },
      { name: 'git-guardrails', description: 'Pre-execution git command interception blocking destructive pushes or resets' },
      { name: 'setup-pre-commit', description: 'Husky pre-commit hooks with lint-staged, Prettier, and type-checking enforcement' },
    ],
  },
];

export function SkillsModal({ isOpen, onClose }: SkillsModalProps) {
  const [search, setSearch] = useState('');

  if (!isOpen) return null;

  const filteredCategories = SKILL_CATEGORIES.map((cat) => {
    const filteredSkills = cat.skills.filter(
      (s) =>
        s.name.toLowerCase().includes(search.toLowerCase()) ||
        s.description.toLowerCase().includes(search.toLowerCase()) ||
        cat.category.toLowerCase().includes(search.toLowerCase())
    );
    return { ...cat, skills: filteredSkills };
  }).filter((cat) => cat.skills.length > 0);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-md transition-opacity"
        onClick={onClose}
      />

      {/* Modal Container */}
      <div className="relative bg-[var(--bg-secondary)] rounded-3xl w-full max-w-2xl border border-[var(--border)] shadow-[var(--shadow-float)] p-6 sm:p-8 flex flex-col max-h-[85vh] animate-slide-up z-10">
        
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-[var(--border)] mb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-[var(--accent-muted)] border border-[var(--border-accent)] flex items-center justify-center text-[var(--accent-primary)] shadow-sm">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xl sm:text-2xl font-serif text-[var(--text-primary)] font-medium">
                Integrated Skills & Subagents
              </h2>
              <p className="text-xs text-[var(--text-secondary)]">
                Autonomous specialized skills active in Aarka AI
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            type="button"
            className="p-2 rounded-xl text-[var(--text-tertiary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] transition-colors"
            title="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Search Bar */}
        <div className="relative mb-4">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-tertiary)]" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search skills (e.g., finance, tdd, pdf, architecture)..."
            className="w-full bg-[var(--bg-primary)] text-[var(--text-primary)] placeholder-[var(--text-tertiary)] text-xs sm:text-sm pl-10 pr-4 py-2.5 rounded-xl border border-[var(--border)] focus:border-[var(--border-accent)] outline-none transition-all"
          />
        </div>

        {/* Skills List */}
        <div className="flex-1 overflow-y-auto space-y-6 pr-1">
          {filteredCategories.map((cat) => {
            const Icon = cat.icon;
            return (
              <div key={cat.category} className="space-y-2.5">
                <div className="flex items-center gap-2 text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider">
                  <Icon className="w-4 h-4 text-[var(--accent-primary)]" />
                  <span>{cat.category}</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                  {cat.skills.map((skill) => (
                    <div
                      key={skill.name}
                      className="p-3 rounded-2xl bg-[var(--bg-primary)] border border-[var(--border)] hover:border-[var(--border-accent)] transition-all flex flex-col justify-between group"
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-mono font-bold text-[var(--text-primary)] group-hover:text-[var(--accent-primary)] transition-colors">
                          /{skill.name}
                        </span>
                        <span className="text-[9px] uppercase font-mono px-1.5 py-0.5 rounded bg-[var(--bg-tertiary)] text-[var(--text-tertiary)] border border-[var(--border)]">
                          Autonomous
                        </span>
                      </div>
                      <p className="text-[11px] text-[var(--text-secondary)] leading-relaxed line-clamp-2">
                        {skill.description}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer */}
        <div className="pt-4 border-t border-[var(--border)] mt-4 flex items-center justify-between text-xs text-[var(--text-tertiary)]">
          <span>Orchestration: Skill Router → Research → Architecture → Code → Verification</span>
          <span className="font-mono text-[10px] text-[var(--accent-primary)]">v2.0 Active</span>
        </div>
      </div>
    </div>
  );
}
