'use client';

import React, { useState, useRef, useEffect } from 'react';
import { ArrowUp, Square } from 'lucide-react';
import { ModelSwitcher } from './ModelSwitcher';
import { EffortLevel } from '@/types';

interface ChatInputProps {
  onSend: (message: string) => void;
  onStop?: () => void;
  isStreaming: boolean;
  selectedModel: string;
  onModelChange: (modelId: string) => void;
  reasoningEffort?: EffortLevel;
  onEffortChange?: (effort: EffortLevel) => void;
}

export function ChatInput({
  onSend,
  onStop,
  isStreaming,
  selectedModel,
  onModelChange,
  reasoningEffort = 'medium',
  onEffortChange,
}: ChatInputProps) {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea as user types
  useEffect(() => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = 'auto';
      el.style.height = `${Math.min(el.scrollHeight, 220)}px`;
    }
  }, [input]);

  const handleSubmit = () => {
    if (!input.trim() || isStreaming) return;
    onSend(input.trim());
    setInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="sticky bottom-0 w-full p-3 sm:p-4 bg-gradient-to-t from-[var(--bg-primary)] via-[var(--bg-primary)] to-transparent pt-6">
      <div className="max-w-4xl mx-auto flex flex-col gap-2">
        {/* Floating Input Container */}
        <div className="flex flex-col bg-[var(--bg-secondary)] border border-[var(--border)] rounded-2xl shadow-[var(--shadow-lg)] focus-within:border-[var(--border-accent)] focus-within:shadow-[var(--shadow-float)] transition-all duration-200 p-2 sm:p-3">
          {/* Textarea */}
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask Aarka anything... (Enter to send, Shift+Enter for new line)"
            disabled={isStreaming}
            rows={1}
            className="w-full max-h-[220px] min-h-[48px] bg-transparent text-[var(--text-primary)] placeholder-[var(--text-tertiary)] resize-none outline-none py-2 px-2 text-sm sm:text-base leading-relaxed disabled:opacity-50"
          />

          {/* Bottom Toolbar */}
          <div className="flex items-center justify-between gap-2 pt-2 border-t border-[var(--border)]/50 mt-1">
            <div className="flex items-center gap-1.5">
              {/* Dual Model & Reasoning Effort Switcher */}
              <ModelSwitcher
                selectedModel={selectedModel}
                onModelChange={onModelChange}
                reasoningEffort={reasoningEffort}
                onEffortChange={onEffortChange}
                direction="up"
              />
            </div>

            <div className="flex items-center gap-2">
              <span className="hidden sm:inline-block text-[11px] font-mono text-[var(--text-tertiary)] mr-1 select-none">
                {input.length > 0 ? `${input.length} chars` : 'Markdown supported'}
              </span>

              {isStreaming ? (
                <button
                  onClick={onStop}
                  type="button"
                  className="w-9 h-9 flex items-center justify-center rounded-xl bg-red-500 hover:bg-red-600 text-white shadow-md transition-all duration-200"
                  title="Stop generation"
                >
                  <Square className="w-4 h-4 fill-current" />
                </button>
              ) : (
                <button
                  onClick={handleSubmit}
                  disabled={!input.trim()}
                  type="button"
                  className={`
                    w-9 h-9 flex items-center justify-center rounded-xl transition-all duration-200
                    ${
                      input.trim()
                        ? 'bg-[var(--accent-primary)] hover:bg-[var(--accent-hover)] text-white shadow-md hover:scale-105'
                        : 'bg-[var(--bg-tertiary)] text-[var(--text-tertiary)] opacity-40 cursor-not-allowed'
                    }
                  `}
                  title="Send message (Enter)"
                >
                  <ArrowUp className="w-4 h-4 stroke-[2.5]" />
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Legal / Accuracy Disclaimer */}
        <div className="text-center text-[11px] text-[var(--text-tertiary)] font-sans">
          Aarka AI can make mistakes. Verify critical facts and financial models.
        </div>
      </div>
    </div>
  );
}
