'use client';

import React, { useState, useRef, useEffect } from 'react';
import { ArrowUp, Square, Sparkles, ArrowRight } from 'lucide-react';
import { ModelSwitcher } from './ModelSwitcher';
import { EffortLevel, ToolApprovalRequest } from '@/types';
import { SKILL_CATEGORIES } from '@/components/skills/SkillsModal';
import { isTerminalCommand, detectSubmissionApproval } from '@/lib/commandDetection';
import { FloatingApprovalDrawer } from './FloatingApprovalDrawer';
import { useChatContext } from '@/context/ChatContext';

const ALL_SKILLS = SKILL_CATEGORIES.flatMap((cat) =>
  cat.skills.map((s) => ({
    name: s.name,
    category: cat.category,
    description: s.description,
  }))
);

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
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [dismissedMention, setDismissedMention] = useState(false);
  const [pendingCommand, setPendingCommand] = useState<string | null>(null);
  const [pendingApproval, setPendingApproval] = useState<ToolApprovalRequest | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Consume backend SSE approval requests from context
  const { activeApprovalRequest } = useChatContext();

  // Merge: local intercepted command approval takes priority over backend SSE approval
  const effectiveApproval = pendingApproval || activeApprovalRequest || null;

  // Auto-resize textarea as user types & toggle overflow
  const adjustHeight = () => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = 'auto';
      const maxHeight = 220;
      const targetHeight = Math.min(el.scrollHeight, maxHeight);
      el.style.height = `${Math.max(targetHeight, 48)}px`;
      el.style.overflowY = el.scrollHeight > maxHeight ? 'auto' : 'hidden';
    }
  };

  useEffect(() => {
    adjustHeight();
  }, [input]);

  // Synchronize any browser-restored form values on mount
  useEffect(() => {
    const el = textareaRef.current;
    if (el && el.value && el.value !== input) {
      setInput(el.value);
    }
  }, []);

  // Check if user is typing an @ or / mention
  const lastToken = input.split(/\s+/).pop() || '';
  const isTrigger = !dismissedMention && (lastToken.startsWith('@') || lastToken.startsWith('/'));
  const triggerChar = isTrigger ? lastToken[0] : '';
  const mentionQuery = isTrigger ? lastToken.slice(1).toLowerCase() : '';

  const matchingSkills = isTrigger
    ? ALL_SKILLS.filter(
        (s) =>
          s.name.toLowerCase().includes(mentionQuery) ||
          s.category.toLowerCase().includes(mentionQuery) ||
          s.description.toLowerCase().includes(mentionQuery)
      )
    : [];

  useEffect(() => {
    setSelectedIndex(0);
  }, [mentionQuery]);

  const selectSkill = (skillName: string) => {
    const tokens = input.split(' ');
    if (tokens.length > 0) {
      tokens[tokens.length - 1] = `${triggerChar}${skillName} `;
    } else {
      tokens.push(`${triggerChar}${skillName} `);
    }
    const nextText = tokens.join(' ');
    setInput(nextText);
    setDismissedMention(false);
    textareaRef.current?.focus();
  };

  const effectiveInput = input || (textareaRef.current ? textareaRef.current.value : '');
  const hasContent = Boolean(effectiveInput.trim());

  const handleCancelApproval = () => {
    setPendingApproval(null);
    setPendingCommand(null);
    // Return focus to the same text field and preserve the entered command
    setTimeout(() => {
      textareaRef.current?.focus();
    }, 50);
  };

  const handleResolveCommandApproval = async (
    approvalId: string,
    decision: 'approve' | 'deny',
    reason?: string
  ) => {
    if (decision === 'approve') {
      const cmdToExecute = pendingCommand || effectiveInput.trim();
      setPendingApproval(null);
      setPendingCommand(null);
      setInput('');
      setDismissedMention(false);
      if (textareaRef.current) {
        textareaRef.current.value = '';
        textareaRef.current.style.height = 'auto';
        textareaRef.current.style.overflowY = 'hidden';
      }
      onSend(cmdToExecute);
    } else {
      handleCancelApproval();
    }
  };

  const handleSubmit = () => {
    const textToSend = effectiveInput.trim();
    if (!textToSend || isStreaming) return;

    // Intent detection step: intercept commands, file edits, and finance strategies before execution
    const interceptedApproval = detectSubmissionApproval(textToSend, selectedModel);
    if (interceptedApproval) {
      setPendingCommand(textToSend);
      setPendingApproval(interceptedApproval);
      return;
    }

    // Normal conversational text flow
    onSend(textToSend);
    setInput('');
    setDismissedMention(false);
    if (textareaRef.current) {
      textareaRef.current.value = '';
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.overflowY = 'hidden';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (isTrigger && matchingSkills.length > 0) {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex((prev) => (prev + 1) % matchingSkills.length);
        return;
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex((prev) => (prev - 1 + matchingSkills.length) % matchingSkills.length);
        return;
      }
      if (e.key === 'Enter' || e.key === 'Tab') {
        e.preventDefault();
        selectSkill(matchingSkills[selectedIndex].name);
        return;
      }
      if (e.key === 'Escape') {
        e.preventDefault();
        setDismissedMention(true);
        return;
      }
    }

    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="sticky bottom-0 w-full p-3 sm:p-4 bg-gradient-to-t from-[var(--bg-primary)] via-[var(--bg-primary)] to-transparent pt-6">
      <div className="max-w-4xl mx-auto flex flex-col gap-2">
        {/* Floating Mention Autocomplete Popup */}
        {isTrigger && matchingSkills.length > 0 && (
          <div className="bg-[var(--bg-secondary)] border border-[var(--border-accent)] rounded-2xl shadow-xl overflow-hidden mb-1 max-h-60 overflow-y-auto z-30">
            <div className="px-3.5 py-2 border-b border-[var(--border)] bg-[var(--bg-tertiary)]/50 flex items-center justify-between">
              <span className="text-[11px] font-semibold text-[var(--text-secondary)] flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-[var(--accent-primary)]" />
                Autonomous Skills ({matchingSkills.length})
              </span>
              <span className="text-[10px] text-[var(--text-tertiary)]">
                ↑↓ to navigate, Enter or click to select
              </span>
            </div>
            <div className="p-1.5 flex flex-col gap-1">
              {matchingSkills.map((skill, index) => {
                const isSelected = index === selectedIndex;
                return (
                  <button
                    key={skill.name}
                    type="button"
                    onClick={() => selectSkill(skill.name)}
                    className={`w-full text-left px-3 py-2 rounded-xl transition-all flex items-center justify-between gap-3 ${
                      isSelected
                        ? 'bg-[var(--accent-muted)] border border-[var(--border-accent)]'
                        : 'hover:bg-[var(--bg-tertiary)] text-[var(--text-primary)] border border-transparent'
                    }`}
                  >
                    <div className="flex flex-col min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold text-[var(--accent-primary)]">
                          {triggerChar}{skill.name}
                        </span>
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-[var(--bg-tertiary)] text-[var(--text-secondary)] font-medium">
                          {skill.category}
                        </span>
                      </div>
                      <span className="text-xs text-[var(--text-tertiary)] truncate mt-0.5">
                        {skill.description}
                      </span>
                    </div>
                    <ArrowRight className={`w-3.5 h-3.5 flex-shrink-0 ${isSelected ? 'text-[var(--accent-primary)]' : 'text-transparent'}`} />
                  </button>
                );
              })}
            </div>
          </div>
        )}
        {/* Input-Anchored Approval Drawer (emerges above input, Claude/Gamma style) */}
        {effectiveApproval && (
          <FloatingApprovalDrawer
            request={effectiveApproval}
            onResolve={pendingApproval ? handleResolveCommandApproval : undefined}
            onDismiss={pendingApproval ? handleCancelApproval : undefined}
            anchorMode="inline"
          />
        )}

        {/* Floating Input Container */}
        <div className="flex flex-col bg-[var(--bg-secondary)] border border-[var(--border)] rounded-2xl shadow-[var(--shadow-lg)] focus-within:border-[var(--border-accent)] focus-within:shadow-[var(--shadow-float)] transition-all duration-200 p-2 sm:p-3">
          {/* Textarea */}
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => {
              setInput(e.target.value);
              adjustHeight();
            }}
            onInput={(e) => {
              const val = (e.target as HTMLTextAreaElement).value;
              if (val !== input) setInput(val);
              adjustHeight();
            }}
            onFocus={() => {
              const el = textareaRef.current;
              if (el && el.value && el.value !== input) {
                setInput(el.value);
                adjustHeight();
              }
            }}
            onKeyDown={handleKeyDown}
            placeholder={isStreaming ? "Type your next message or instructions..." : "Ask Aarka anything... (Enter to send, Shift+Enter for new line)"}
            disabled={false}
            rows={1}
            style={{ overflowY: 'hidden' }}
            className="w-full max-h-[220px] min-h-[48px] bg-transparent text-[var(--text-primary)] placeholder-[var(--text-tertiary)] resize-none outline-none py-2 px-2 text-sm sm:text-base leading-relaxed overflow-y-hidden scrollbar-none"
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
                {effectiveInput.length > 0 ? `${effectiveInput.length} chars` : 'Markdown supported'}
              </span>

              {isStreaming ? (
                <button
                  onClick={onStop}
                  type="button"
                  className="w-9 h-9 flex items-center justify-center rounded-full bg-red-500 hover:bg-red-600 text-white shadow-md transition-all duration-200 cursor-pointer"
                  title="Stop generation"
                >
                  <Square className="w-3.5 h-3.5 fill-current" />
                </button>
              ) : (
                <button
                  onClick={handleSubmit}
                  disabled={!hasContent}
                  type="button"
                  className={`
                    w-9 h-9 flex items-center justify-center rounded-full transition-all duration-200
                    ${
                      hasContent
                        ? 'bg-gradient-to-r from-[#E56A47] to-[#B84F2E] hover:from-[#EB7654] hover:to-[#C65734] text-white shadow-md shadow-[#C15F3D]/25 hover:shadow-lg hover:shadow-[#C15F3D]/35 hover:scale-105 active:scale-95 cursor-pointer'
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
