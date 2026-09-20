'use client';

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { ArrowUp, Square, Sparkles, ArrowRight, Plus, Mic, MicOff, X, FileText } from 'lucide-react';
import { ModelSwitcher } from './ModelSwitcher';
import { EffortLevel, ToolApprovalRequest, CandidateFinanceStrategy } from '@/types';
import { SKILL_CATEGORIES } from '@/components/skills/SkillsModal';
import { isTerminalCommand, detectSubmissionApproval } from '@/lib/commandDetection';
import { FloatingApprovalDrawer } from './FloatingApprovalDrawer';
import { useChatContext } from '@/context/ChatContext';

export interface AttachedFile {
  id: string;
  file: File;
  name: string;
  size: number;
  type: string;
  previewUrl?: string;
  textContent?: string;
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function isTextLikeFile(file: File): boolean {
  if (file.type.startsWith('text/')) return true;
  const name = file.name.toLowerCase();
  const textExtensions = [
    '.txt', '.md', '.json', '.csv', '.py', '.ts', '.tsx', '.js', '.jsx',
    '.html', '.css', '.scss', '.yaml', '.yml', '.xml', '.sql', '.sh',
    '.bash', '.env', '.log', '.rs', '.go', '.java', '.c', '.cpp', '.h'
  ];
  return textExtensions.some((ext) => name.endsWith(ext));
}

const readTextFileContent = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    if (file.size > 500 * 1024) {
      resolve(`[File content omitted: ${file.name} is larger than 500KB]`);
      return;
    }
    const reader = new FileReader();
    reader.onload = () => resolve((reader.result as string) || '');
    reader.onerror = () => reject(reader.error);
    reader.readAsText(file);
  });
};

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
  const [attachedFiles, setAttachedFiles] = useState<AttachedFile[]>([]);
  const [isListening, setIsListening] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const recognitionRef = useRef<any>(null);

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
  const hasContent = Boolean(effectiveInput.trim()) || attachedFiles.length > 0;

  // Cleanup object URLs and speech recognition on unmount
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch {
          // ignore
        }
      }
      attachedFiles.forEach((af) => {
        if (af.previewUrl) {
          URL.revokeObjectURL(af.previewUrl);
        }
      });
    };
  }, []);

  const toggleListening = () => {
    if (typeof window === 'undefined') return;

    if (isListening) {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch (e) {
          console.warn('Error stopping speech recognition:', e);
        }
      }
      setIsListening(false);
      return;
    }

    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert('Speech recognition is not supported in this browser. Please use Google Chrome, Edge, or a Chromium-based browser.');
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      let lastFinalTranscript = '';

      recognition.onstart = () => {
        setIsListening(true);
      };

      recognition.onresult = (event: any) => {
        let interimTranscript = '';
        let currentFinal = '';

        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            currentFinal += event.results[i][0].transcript;
          } else {
            interimTranscript += event.results[i][0].transcript;
          }
        }

        const newText = (currentFinal || interimTranscript).trim();
        if (newText && newText !== lastFinalTranscript) {
          setInput((prev) => {
            const separator = prev && !prev.endsWith(' ') ? ' ' : '';
            return `${prev}${separator}${newText}`;
          });
          lastFinalTranscript = newText;
          adjustHeight();
        }
      };

      recognition.onerror = (event: any) => {
        console.warn('Speech recognition error:', event.error);
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch (err) {
      console.error('Failed to initialize speech recognition:', err);
      setIsListening(false);
    }
  };

  const handleFileClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const newAttachments: AttachedFile[] = [];

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const isImg = file.type.startsWith('image/');
      let previewUrl: string | undefined;

      if (isImg && typeof window !== 'undefined') {
        try {
          previewUrl = URL.createObjectURL(file);
        } catch {
          // ignore
        }
      }

      let textContent: string | undefined;
      if (isTextLikeFile(file)) {
        try {
          textContent = await readTextFileContent(file);
        } catch (err) {
          console.warn('Failed to read file content:', err);
        }
      }

      newAttachments.push({
        id: `file-${Date.now()}-${i}-${Math.random().toString(36).slice(2, 7)}`,
        file,
        name: file.name,
        size: file.size,
        type: file.type || 'application/octet-stream',
        previewUrl,
        textContent,
      });
    }

    setAttachedFiles((prev) => [...prev, ...newAttachments]);

    // Reset input element value so the same file can be re-attached if removed
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const removeAttachedFile = (id: string) => {
    setAttachedFiles((prev) => {
      const target = prev.find((f) => f.id === id);
      if (target?.previewUrl) {
        URL.revokeObjectURL(target.previewUrl);
      }
      return prev.filter((f) => f.id !== id);
    });
  };

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
    reason?: string,
    selectedMasterStrategy?: string
  ) => {
    if (decision === 'approve') {
      let cmdToExecute = pendingCommand || effectiveInput.trim();

      // If user approved a finance strategy and selected a candidate, format explicit execution prompt
      if (pendingApproval && (pendingApproval.tool_name === 'FinanceStrategyMasterSelection' || pendingApproval.arguments?.candidates)) {
        const candidates = pendingApproval.arguments?.candidates as CandidateFinanceStrategy[] | undefined;
        const symbol = pendingApproval.arguments?.symbol || '';
        const category = pendingApproval.arguments?.category || '';
        if (candidates && candidates.length > 0) {
          const chosen = (selectedMasterStrategy && candidates.find((c) => c.candidate_id === selectedMasterStrategy)) || candidates[0];
          if (chosen) {
            cmdToExecute = `Execute ${chosen.strategy_name} for ${symbol || 'asset'}${category ? ` (${category})` : ''}: ${chosen.rationale || `Follow disciplined risk parameters with ${chosen.win_rate_est || 'high'} win rate and ${chosen.risk_reward_actual || '1:2+'} R:R`}`;
          }
        }
      }

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
    if ((!textToSend && attachedFiles.length === 0) || isStreaming) return;

    // Intent detection step: intercept commands, file edits, and finance strategies before execution
    // Interception applies only if user submitted pure text without attachments
    if (textToSend && attachedFiles.length === 0) {
      try {
        const interceptedApproval = detectSubmissionApproval(textToSend, selectedModel);
        if (interceptedApproval) {
          console.log('[Aarka Intent Intercepted]', interceptedApproval);
          setPendingCommand(textToSend);
          setPendingApproval(interceptedApproval);
          return;
        }
      } catch (err) {
        console.warn('[Aarka Intent Interception Warning]', err);
      }
    }

    // Format message with any attached files
    let finalMessage = textToSend;
    if (attachedFiles.length > 0) {
      const fileHeaders: string[] = [];
      attachedFiles.forEach((af) => {
        if (af.textContent !== undefined) {
          fileHeaders.push(`[Attached File: ${af.name} (${formatFileSize(af.size)})]\n\`\`\`\n${af.textContent}\n\`\`\``);
        } else {
          fileHeaders.push(`[Attached ${af.type.startsWith('image/') ? 'Photo' : 'File'}: ${af.name} (${formatFileSize(af.size)})]`);
        }
      });

      const attachmentsBlock = fileHeaders.join('\n\n');
      finalMessage = textToSend ? `${attachmentsBlock}\n\n${textToSend}` : attachmentsBlock;

      // Clean up object URLs
      attachedFiles.forEach((af) => {
        if (af.previewUrl) {
          URL.revokeObjectURL(af.previewUrl);
        }
      });
      setAttachedFiles([]);
    }

    // Normal conversational text flow
    onSend(finalMessage);
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
          {/* Attached Files Preview Strip */}
          {attachedFiles.length > 0 && (
            <div
              className="flex flex-wrap gap-2 mb-2 pb-2 border-b border-[var(--border)]/40 max-h-36 overflow-y-auto px-1"
              data-testid="attached-files-container"
            >
              {attachedFiles.map((af) => {
                const isImg = Boolean(af.previewUrl);
                return (
                  <div
                    key={af.id}
                    className="flex items-center gap-2 px-2.5 py-1.5 rounded-xl bg-[var(--bg-tertiary)] border border-[var(--border)] text-xs text-[var(--text-primary)] group shadow-sm transition-all"
                    data-testid={`attachment-chip-${af.id}`}
                  >
                    {isImg ? (
                      <img
                        src={af.previewUrl}
                        alt={af.name}
                        className="w-6 h-6 object-cover rounded-md border border-[var(--border)]"
                      />
                    ) : (
                      <FileText className="w-4 h-4 text-[var(--accent-primary)] flex-shrink-0" />
                    )}
                    <span className="font-medium max-w-[140px] truncate" title={af.name}>
                      {af.name}
                    </span>
                    <span className="text-[10px] text-[var(--text-tertiary)] font-mono">
                      {formatFileSize(af.size)}
                    </span>
                    <button
                      type="button"
                      onClick={() => removeAttachedFile(af.id)}
                      className="text-[var(--text-tertiary)] hover:text-red-400 p-0.5 rounded-full hover:bg-[var(--bg-primary)] transition-colors cursor-pointer"
                      title="Remove attachment"
                      data-testid={`remove-attachment-${af.id}`}
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                );
              })}
            </div>
          )}

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
            placeholder={isListening ? "Listening... speak now..." : isStreaming ? "Type your next message or instructions..." : "Ask Aarka anything... (Enter to send, Shift+Enter for new line)"}
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

              {/* Hidden File Input for Attachments */}
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept="image/*,.pdf,.doc,.docx,.txt,.csv,.json,.py,.ts,.tsx,.js,.jsx,.html,.css,.md,.log,.xml,.yaml,.yml"
                onChange={handleFileChange}
                className="hidden"
                data-testid="chat-file-input"
              />

              {/* Attach '+' Button */}
              <button
                type="button"
                onClick={handleFileClick}
                className="h-8 px-2.5 flex items-center gap-1.5 text-xs font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] bg-[var(--bg-primary)]/50 border border-[var(--border)] rounded-lg transition-colors cursor-pointer shadow-xs"
                title="Attach photos or files (+)"
                data-testid="attach-files-button"
              >
                <Plus className="w-4 h-4 text-[var(--text-secondary)] hover:text-[var(--text-primary)]" />
                <span className="hidden sm:inline text-[11px] font-medium">Attach</span>
              </button>

              {/* Microphone Voice-to-Text Button */}
              <button
                type="button"
                onClick={toggleListening}
                className={`
                  h-8 px-2.5 flex items-center gap-1.5 text-xs font-medium border rounded-lg transition-all cursor-pointer shadow-xs
                  ${
                    isListening
                      ? 'bg-red-500/15 border-red-500/50 text-red-400 animate-pulse shadow-sm shadow-red-500/20'
                      : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] bg-[var(--bg-primary)]/50 border-[var(--border)]'
                  }
                `}
                title={isListening ? 'Stop voice recording' : 'Voice input (Microphone)'}
                data-testid="microphone-button"
              >
                {isListening ? (
                  <>
                    <MicOff className="w-4 h-4 text-red-400" />
                    <span className="hidden sm:inline text-[11px] text-red-400 font-medium">Listening...</span>
                    <span className="w-2 h-2 rounded-full bg-red-500 animate-ping ml-0.5 hidden sm:inline-block" />
                  </>
                ) : (
                  <>
                    <Mic className="w-4 h-4" />
                    <span className="hidden sm:inline text-[11px] font-medium">Voice</span>
                  </>
                )}
              </button>
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
