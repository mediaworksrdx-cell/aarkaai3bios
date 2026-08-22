'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Sparkles, ChevronDown, Check } from 'lucide-react';
import { MODEL_OPTIONS, EFFORT_OPTIONS, EffortLevel } from '@/styles/theme';

interface ModelSwitcherProps {
  selectedModel: string;
  onModelChange: (modelId: string) => void;
  reasoningEffort?: EffortLevel;
  onEffortChange?: (effort: EffortLevel) => void;
  direction?: 'up' | 'down';
}

export function ModelSwitcher({
  selectedModel,
  onModelChange,
  reasoningEffort = 'medium',
  onEffortChange,
  direction = 'up',
}: ModelSwitcherProps) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Normalize model ID
  const activeModelId = selectedModel === 'aarkaa-2.0' || selectedModel === 'aarkaa-7b' || selectedModel === 'aarkaa-3b' || selectedModel === 'aarka-2.0'
    ? 'aarka-2.0'
    : selectedModel.startsWith('gemini')
    ? 'gemini-2.5'
    : selectedModel;

  const currentModel = MODEL_OPTIONS.find(m => m.id === activeModelId) || MODEL_OPTIONS[0];
  const currentEffort = EFFORT_OPTIONS.find(e => e.id === reasoningEffort) || EFFORT_OPTIONS[1];

  // Close on outside click
  useEffect(() => {
    const handleOutsideClick = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleOutsideClick);
    return () => document.removeEventListener('mousedown', handleOutsideClick);
  }, []);

  return (
    <div className="relative inline-block" ref={dropdownRef}>
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        type="button"
        className="
          flex items-center gap-2 px-3 py-1.5 rounded-full
          bg-[var(--bg-secondary)] hover:bg-[var(--bg-hover)]
          border border-[var(--border)] hover:border-[var(--border-accent)]
          text-xs font-medium text-[var(--text-primary)]
          shadow-[var(--shadow-sm)] transition-all duration-200
          focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent-primary)]
        "
      >
        <span className="text-sm">{currentModel.icon}</span>
        <span className="font-medium text-[var(--text-primary)]">{currentModel.label}</span>
        <span className="text-[10px] font-mono uppercase bg-[var(--accent-muted)] text-[var(--accent-primary)] border border-[var(--border-accent)] px-1.5 py-0.5 rounded-md font-semibold">
          {currentEffort.label}
        </span>
        <ChevronDown className={`w-3.5 h-3.5 text-[var(--text-tertiary)] transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {/* Popover Card */}
      {isOpen && (
        <div
          className={`
            absolute left-0 ${direction === 'up' ? 'bottom-full mb-2.5' : 'top-full mt-2.5'}
            w-72 sm:w-80 max-w-[calc(100vw-32px)] bg-[var(--bg-secondary)] border border-[var(--border)]
            rounded-2xl shadow-[var(--shadow-float)] p-2.5 z-50 overflow-hidden
            animate-slide-up backdrop-blur-md space-y-2.5
          `}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-1 pb-1.5 border-b border-[var(--border)]">
            <span className="text-[10px] font-semibold text-[var(--text-tertiary)] uppercase tracking-wider font-mono">
              Model & Effort
            </span>
            <Sparkles className="w-3.5 h-3.5 text-[var(--accent-primary)]" />
          </div>

          {/* Model Selection */}
          <div className="space-y-1">
            {MODEL_OPTIONS.map((model) => {
              const isSelected = currentModel.id === model.id;
              return (
                <button
                  key={model.id}
                  onClick={() => {
                    onModelChange(model.id);
                  }}
                  type="button"
                  className={`
                    w-full text-left px-2.5 py-2 rounded-xl transition-all duration-150
                    flex items-center justify-between gap-2.5 cursor-pointer
                    ${
                      isSelected
                        ? 'bg-[var(--bg-tertiary)] border border-[var(--border-accent)] shadow-[var(--shadow-sm)]'
                        : 'hover:bg-[var(--bg-hover)] border border-transparent'
                    }
                  `}
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <span className="text-sm flex-shrink-0">{model.icon}</span>
                    <span className={`text-xs font-semibold truncate ${isSelected ? 'text-[var(--accent-primary)]' : 'text-[var(--text-primary)]'}`}>
                      {model.label}
                    </span>
                  </div>
                  {isSelected && <Check className="w-3.5 h-3.5 text-[var(--accent-primary)] flex-shrink-0" />}
                </button>
              );
            })}
          </div>

          {/* Reasoning Effort Selector */}
          <div className="pt-2 border-t border-[var(--border)] space-y-1.5">
            <div className="flex items-center justify-between px-1">
              <span className="text-[10px] font-mono text-[var(--text-tertiary)] uppercase tracking-wider">
                Reasoning Effort
              </span>
              <span className="text-[10px] text-[var(--accent-primary)] font-semibold">
                {currentEffort.label}
              </span>
            </div>

            <div className="grid grid-cols-3 gap-1 p-1 bg-[var(--bg-primary)] rounded-xl border border-[var(--border)]">
              {EFFORT_OPTIONS.map((opt) => {
                const isEffortSelected = opt.id === reasoningEffort;
                return (
                  <button
                    key={opt.id}
                    onClick={() => {
                      if (onEffortChange) onEffortChange(opt.id);
                    }}
                    type="button"
                    className={`
                      flex items-center justify-center gap-1 py-1.5 px-2 rounded-lg text-center transition-all duration-150 cursor-pointer
                      ${
                        isEffortSelected
                          ? 'bg-[var(--bg-secondary)] text-[var(--accent-primary)] font-semibold shadow-sm border border-[var(--border-accent)]'
                          : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)]'
                      }
                    `}
                  >
                    <span className="text-xs">{opt.icon}</span>
                    <span className="text-xs font-medium">{opt.label}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
