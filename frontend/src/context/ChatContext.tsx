'use client';

import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { Conversation, Message, EffortLevel, ToolApprovalRequest, CodeModeExecution, CodeModeExecutionStep } from '@/types';
import { streamChat, submitFeedbackApi, submitToolApproval } from '@/lib/api';

const STORAGE_KEY = 'aarka-conversations-v3';
const SESSION_ACTIVE_KEY = 'aarka-active-conv-id';

function isPageReload(): boolean {
  if (typeof window === 'undefined' || typeof performance === 'undefined') return false;
  try {
    const navEntries = performance.getEntriesByType('navigation');
    if (navEntries.length > 0) {
      return (navEntries[0] as PerformanceNavigationTiming).type === 'reload';
    }
    // Fallback for older browsers
    return (performance as any).navigation?.type === 1;
  } catch {
    return false;
  }
}

export function generateId(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    try {
      return crypto.randomUUID();
    } catch {}
  }
  return 'id-' + Math.random().toString(36).substring(2, 11) + '-' + Date.now().toString(36);
}

interface ChatContextType {
  conversations: Conversation[];
  activeConversationId: string | null;
  activeConversation: Conversation | undefined;
  messages: Message[];
  isStreaming: boolean;
  error: string | null;
  selectedModel: string;
  setSelectedModel: (model: string) => void;
  reasoningEffort: EffortLevel;
  setReasoningEffort: (effort: EffortLevel) => void;
  createConversation: (model?: string, effort?: EffortLevel) => string;
  deleteConversation: (id: string) => void;
  renameConversation: (id: string, title: string) => void;
  setActiveConversationId: (id: string | null) => void;
  sendMessage: (content: string, model?: string, effort?: EffortLevel) => Promise<void>;
  regenerateResponse: (assistantMessageId: string) => Promise<void>;
  submitFeedback: (messageId: string, rating: 1 | -1, correction?: string) => Promise<void>;
  resolveApproval: (approvalId: string, decision: 'approve' | 'deny', reason?: string, selectedMasterStrategy?: string) => Promise<void>;
  activeApprovalRequest: ToolApprovalRequest | null;
  alwaysAllowedTools: string[];
  alwaysAllowTool: (toolName: string) => void;
  dismissActiveApproval: () => void;
  stopGeneration: () => void;
  clearError: () => void;
  clearAllHistory: () => void;
  isMounted: boolean;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export function ChatProvider({ children, user }: { children: React.ReactNode; user?: any }) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedModel, setSelectedModelState] = useState<string>('aarka-2.0');
  const [reasoningEffort, setReasoningEffortState] = useState<EffortLevel>('high');
  const [isMounted, setIsMounted] = useState<boolean>(false);
  const [activeApprovalRequest, setActiveApprovalRequest] = useState<ToolApprovalRequest | null>(null);
  const [alwaysAllowedTools, setAlwaysAllowedTools] = useState<string[]>([]);
  const alwaysAllowedToolsRef = useRef<string[]>([]);

  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    alwaysAllowedToolsRef.current = alwaysAllowedTools;
  }, [alwaysAllowedTools]);

  const currentStorageKey = user && user.email
    ? `aarka-conv-v3-${user.email.toLowerCase()}`
    : 'aarka-conv-v3-guest';

  // Load preferences
  useEffect(() => {
    setIsMounted(true);
    try {
      const savedModel = localStorage.getItem('aarka-model') || localStorage.getItem('aarkaa-model');
      if (savedModel) {
        if (savedModel === 'aarkaa-7b' || savedModel === 'aarkaa-3b' || savedModel === 'aarkaa-2.0' || savedModel === 'aarka-2.0') {
          setSelectedModelState('aarka-2.0');
        } else if (savedModel.startsWith('gemini')) {
          setSelectedModelState('gemini-3.7');
        } else if (savedModel.startsWith('claude') || savedModel.includes('sonnet')) {
          setSelectedModelState('claude-sonnet-5');
        } else {
          setSelectedModelState(savedModel);
        }
      }

      const savedEffort = (localStorage.getItem('aarka-effort') || localStorage.getItem('aarkaa-effort')) as EffortLevel;
      if (savedEffort && ['low', 'medium', 'high'].includes(savedEffort)) {
        setReasoningEffortState(savedEffort);
      }
    } catch {}
  }, []);

  // Sync activeConversationId into sessionStorage so page refreshes in the same tab preserve it
  useEffect(() => {
    if (activeConversationId) {
      try {
        sessionStorage.setItem(SESSION_ACTIVE_KEY, activeConversationId);
      } catch {}
    }
  }, [activeConversationId]);

  // Load conversations whenever user account changes or app mounts
  useEffect(() => {
    try {
      const isReload = isPageReload();
      const saved = localStorage.getItem(currentStorageKey);
      let sanitized: Conversation[] = [];

      if (saved && saved !== 'undefined' && saved !== 'null') {
        try {
          const parsed = JSON.parse(saved);
          if (Array.isArray(parsed) && parsed.length > 0) {
            sanitized = parsed
              .filter(c => c && typeof c === 'object')
              .map(c => ({
                id: c.id || generateId(),
                title: c.title || 'New Chat',
                messages: Array.isArray(c.messages)
                  ? c.messages.filter((m: any) => m && typeof m === 'object').map((m: any) => ({
                      id: m.id || generateId(),
                      role: m.role || 'user',
                      content: typeof m.content === 'string' ? m.content : '',
                      timestamp: typeof m.timestamp === 'number' ? m.timestamp : Date.now(),
                      modelUsed: m.modelUsed || 'Aarka AI',
                      effort: m.effort || 'medium',
                      error: m.error,
                      isStreaming: false,
                    }))
                  : [],
                createdAt: typeof c.createdAt === 'number' ? c.createdAt : Date.now(),
                updatedAt: typeof c.updatedAt === 'number' ? c.updatedAt : Date.now(),
                model: c.model || 'aarka-2.0',
                effort: c.effort || 'high',
              }));
          }
        } catch (e) {
          console.warn('Corrupted storage reset', e);
        }
      }

      // If user is authenticated and has no conversations, check for guest conversations to migrate
      if (user && user.email && sanitized.length === 0) {
        try {
          const guestSaved = localStorage.getItem('aarka-conv-v3-guest');
          if (guestSaved) {
            const guestParsed = JSON.parse(guestSaved);
            if (Array.isArray(guestParsed) && guestParsed.length > 0) {
              sanitized = guestParsed;
              try {
                localStorage.setItem(currentStorageKey, JSON.stringify(sanitized));
              } catch {}
            }
          }
        } catch {}
      }

      let sessionActiveId: string | null = null;
      let isTabInitialized = false;
      try {
        sessionActiveId = sessionStorage.getItem(SESSION_ACTIVE_KEY);
        isTabInitialized = sessionStorage.getItem('aarka_tab_initialized') === 'true';
      } catch {}

      // Preserve active conversation ONLY on an in-tab reload within an already-initialized tab
      const sessionConv = (isReload && isTabInitialized && sessionActiveId)
        ? sanitized.find(c => c.id === sessionActiveId)
        : null;

      if (sessionConv) {
        setConversations(sanitized);
        setActiveConversationId(sessionConv.id);
        return;
      }

      // Fresh visit / new tab / new window:
      // Always start on a clean "New Chat" (WelcomeScreen), while preserving all past conversations in the sidebar
      const freshId = generateId();
      const freshConv: Conversation = {
        id: freshId,
        title: 'New Chat',
        messages: [],
        createdAt: Date.now(),
        updatedAt: Date.now(),
        model: selectedModel || 'aarka-2.0',
        effort: reasoningEffort || 'high',
      };

      setConversations([freshConv, ...sanitized]);
      setActiveConversationId(freshId);
      try {
        sessionStorage.setItem(SESSION_ACTIVE_KEY, freshId);
        sessionStorage.setItem('aarka_tab_initialized', 'true');
      } catch {}
    } catch (e) {
      console.warn('Failed to load user conversations', e);
    }
  }, [currentStorageKey, user]);

  // Save conversations to currentStorageKey on change (only persist conversations that have messages)
  useEffect(() => {
    if (isMounted) {
      try {
        const toPersist = conversations.filter(c => Array.isArray(c.messages) && c.messages.length > 0);
        localStorage.setItem(currentStorageKey, JSON.stringify(toPersist));
      } catch (e) {
        console.warn('Failed to persist user conversations', e);
      }
    }
  }, [conversations, currentStorageKey, isMounted]);

  const setSelectedModel = useCallback((model: string) => {
    const normalized = model === 'aarkaa-7b' || model === 'aarkaa-3b' || model === 'aarkaa-2.0' || model === 'aarka-2.0'
      ? 'aarka-2.0'
      : model.startsWith('gemini')
      ? 'gemini-3.7'
      : (model.startsWith('claude') || model.includes('sonnet'))
      ? 'claude-sonnet-5'
      : model;
    setSelectedModelState(normalized);
    try {
      localStorage.setItem('aarka-model', normalized);
    } catch {}
  }, []);

  const setReasoningEffort = useCallback((effort: EffortLevel) => {
    setReasoningEffortState(effort);
    try {
      localStorage.setItem('aarka-effort', effort);
    } catch {}
  }, []);

  const activeConversation = conversations.find(c => c && c.id === activeConversationId);
  const messages = (activeConversation && Array.isArray(activeConversation.messages)) ? activeConversation.messages : [];

  const createConversation = useCallback((model: string = 'aarka-2.0', effort: EffortLevel = 'high'): string => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsStreaming(false);

    const newId = generateId();
    const newConv: Conversation = {
      id: newId,
      title: 'New Chat',
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now(),
      model,
      effort,
    };
    setConversations(prev => [newConv, ...prev.filter(c => Array.isArray(c.messages) && c.messages.length > 0)]);
    setActiveConversationId(newId);
    try {
      sessionStorage.setItem(SESSION_ACTIVE_KEY, newId);
    } catch {}
    setError(null);
    return newId;
  }, []);

  const deleteConversation = useCallback((id: string) => {
    setConversations(prev => {
      const remaining = prev.filter(c => c.id !== id);
      if (activeConversationId === id) {
        const nextActive = remaining.find(c => Array.isArray(c.messages) && c.messages.length > 0);
        if (nextActive) {
          setActiveConversationId(nextActive.id);
          try {
            sessionStorage.setItem(SESSION_ACTIVE_KEY, nextActive.id);
          } catch {}
        } else {
          const newId = generateId();
          const fallback: Conversation = {
            id: newId,
            title: 'New Chat',
            messages: [],
            createdAt: Date.now(),
            updatedAt: Date.now(),
            model: selectedModel,
            effort: reasoningEffort,
          };
          setActiveConversationId(newId);
          try {
            sessionStorage.setItem(SESSION_ACTIVE_KEY, newId);
          } catch {}
          return [fallback];
        }
      }
      return remaining;
    });
  }, [activeConversationId, selectedModel, reasoningEffort]);

  const renameConversation = useCallback((id: string, title: string) => {
    setConversations(prev =>
      prev.map(c => (c.id === id ? { ...c, title, updatedAt: Date.now() } : c))
    );
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const stopGeneration = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setIsStreaming(false);
      if (activeConversationId) {
        setConversations(prev =>
          prev.map(c => {
            if (c.id === activeConversationId) {
              const updated = [...c.messages];
              const last = updated[updated.length - 1];
              if (last && last.role === 'assistant') {
                updated[updated.length - 1] = { ...last, isStreaming: false };
              }
              return { ...c, messages: updated, updatedAt: Date.now() };
            }
            return c;
          })
        );
      }
    }
  }, [activeConversationId]);

  const sendMessage = useCallback(
    async (content: string, modelOverride?: string, effortOverride?: EffortLevel) => {
      const text = content.trim();
      if (!text || isStreaming) return;

      const model = modelOverride || selectedModel;
      const effort = effortOverride || reasoningEffort;
      let convId = activeConversationId;

      if (!convId) {
        convId = createConversation(model, effort);
      }

      const userMsg: Message = {
        id: generateId(),
        role: 'user',
        content: text,
        timestamp: Date.now(),
      };

      const assistantMsgId = generateId();
      const assistantPlaceholder: Message = {
        id: assistantMsgId,
        role: 'assistant',
        content: '',
        timestamp: Date.now(),
        modelUsed: model === 'gemini-3.7' ? 'Google Gemini 3.7' : (model.startsWith('claude') || model.includes('sonnet')) ? 'Claude Sonnet 5' : 'Aarka AI',
        effort: effort,
        isStreaming: true,
      };

      setConversations(prev =>
        prev.map(c => {
          if (c.id === convId) {
            let title = c.title;
            if (title === 'New Chat') {
              title = text.length > 38 ? text.substring(0, 38) + '...' : text;
            }
            return {
              ...c,
              title,
              messages: [...c.messages, userMsg, assistantPlaceholder],
              updatedAt: Date.now(),
            };
          }
          return c;
        })
      );

      setIsStreaming(true);
      setError(null);
      abortControllerRef.current = new AbortController();

      let accumulated = '';
      let finalModel = model === 'gemini-3.7' ? 'Google Gemini 3.7' : (model.startsWith('claude') || model.includes('sonnet')) ? 'Claude Sonnet 5' : 'Aarka AI';

      try {
        const stream = streamChat(text, convId, model, effort, undefined, abortControllerRef.current.signal);

        for await (const chunk of stream) {
          const delta = chunk.token ?? chunk.content ?? chunk.text;
          if (delta && typeof delta === 'string') {
            accumulated += delta;
            setConversations(prev =>
              prev.map(c => {
                if (c.id === convId) {
                  const msgs = c.messages.map(m =>
                    m.id === assistantMsgId ? { ...m, content: accumulated } : m
                  );
                  return { ...c, messages: msgs };
                }
                return c;
              })
            );
          } else if (chunk.type === 'approval_request') {
            const approvalReq: ToolApprovalRequest = chunk.payload || chunk;
            setConversations(prev =>
              prev.map(c => {
                if (c.id === convId) {
                  const msgs = c.messages.map(m =>
                    m.id === assistantMsgId ? { ...m, approvalRequest: approvalReq } : m
                  );
                  return { ...c, messages: msgs };
                }
                return c;
              })
            );

            // If user previously allowed this tool for this session, auto-approve immediately
            if (alwaysAllowedToolsRef.current.includes(approvalReq.tool_name)) {
              submitToolApproval(approvalReq.approval_id, 'approve').catch(err => {
                console.error('Auto-approval submission error:', err);
              });
            } else {
              setActiveApprovalRequest(approvalReq);
            }
          } else if (chunk.type === 'approval_resolved') {
            const resolved = chunk.payload || chunk;
            setActiveApprovalRequest(prev => (prev?.approval_id === resolved.approval_id ? null : prev));
            setConversations(prev =>
              prev.map(c => {
                if (c.id === convId) {
                  const msgs = c.messages.map(m => {
                    if (m.id === assistantMsgId && m.approvalRequest) {
                      return {
                        ...m,
                        approvalRequest: {
                          ...m.approvalRequest,
                          status: resolved.status || (resolved.decision === 'approve' ? 'approved' : 'rejected'),
                          resolved_at: resolved.resolved_at || Date.now(),
                          resolved_by: resolved.resolved_by,
                        },
                      };
                    }
                    return m;
                  });
                  return { ...c, messages: msgs };
                }
                return c;
              })
            );
          } else if (chunk.type === 'tool_result') {
            const toolRes = chunk.payload || chunk;
            const obs = typeof toolRes.observation === 'string' ? toolRes.observation.trim() : '';
            if (obs) {
              accumulated += `\n\n\`\`\`bash\n# [${toolRes.tool_name || 'Tool'} Output]\n${obs}\n\`\`\`\n\n`;
              setConversations(prev =>
                prev.map(c => {
                  if (c.id === convId) {
                    const msgs = c.messages.map(m =>
                      m.id === assistantMsgId ? { ...m, content: accumulated } : m
                    );
                    return { ...c, messages: msgs };
                  }
                  return c;
                })
              );
            }
          } else if (chunk.type === 'codemode_execution') {
            const execution: CodeModeExecution = chunk.payload || chunk;
            setConversations(prev =>
              prev.map(c => {
                if (c.id === convId) {
                  const msgs = c.messages.map(m =>
                    m.id === assistantMsgId ? { ...m, codeModeExecution: execution } : m
                  );
                  return { ...c, messages: msgs };
                }
                return c;
              })
            );
          } else if (chunk.type === 'codemode_step') {
            const step: CodeModeExecutionStep = chunk.payload || chunk;
            setConversations(prev =>
              prev.map(c => {
                if (c.id === convId) {
                  const msgs = c.messages.map(m => {
                    if (m.id === assistantMsgId && m.codeModeExecution) {
                      const existingSteps = m.codeModeExecution.steps || [];
                      const stepIdx = existingSteps.findIndex(s => s.step_id === step.step_id);
                      let newSteps;
                      if (stepIdx >= 0) {
                        newSteps = [...existingSteps];
                        newSteps[stepIdx] = { ...newSteps[stepIdx], ...step };
                      } else {
                        newSteps = [...existingSteps, step];
                      }
                      return {
                        ...m,
                        codeModeExecution: { ...m.codeModeExecution, steps: newSteps },
                      };
                    }
                    return m;
                  });
                  return { ...c, messages: msgs };
                }
                return c;
              })
            );
          } else if (chunk.type === 'final' || chunk.type === 'final_response') {
            if (chunk.content) accumulated = chunk.content;
            if (chunk.response) accumulated = chunk.response;
            if (chunk.model_used) finalModel = chunk.model_used;
          } else if (chunk.type === 'error' && chunk.detail) {
            throw new Error(chunk.detail);
          }
        }

        const cleanContent = accumulated
          .replace(/(?:\r?\n|\s)*(?:\*{1,2}|[\(\[])?\s*end of (?:answer|response|text|explanation)\s*(?:\*{1,2}|[\)\]])?\.?[\s`]*$/gi, '')
          .replace(/(?:\r?\n|\s)*---+\s*end\s+(?:of\s+)?(?:answer|response|disclaimer|text)\s*---+[\s`]*$/gi, '')
          .replace(/(?:\r?\n|\s)*(?:#Aarkaa(?:AI)?|#Aarka(?:AI)?)\b.*$/gi, '')
          .replace(/(?:\r?\n|\s)*(?:#[A-Za-z0-9_\-\/]+)+\s*$/gi, '')
          .trimEnd();

        setConversations(prev =>
          prev.map(c => {
            if (c.id === convId) {
              const msgs = c.messages.map(m =>
                m.id === assistantMsgId
                  ? {
                      ...m,
                      content: cleanContent || 'No response received from engine.',
                      isStreaming: false,
                      modelUsed: finalModel,
                    }
                  : m
              );
              return { ...c, messages: msgs, updatedAt: Date.now() };
            }
            return c;
          })
        );
      } catch (err: any) {
        if (err.name === 'AbortError') {
          console.log('[Chat] Stream canceled by user');
        } else {
          console.error('[Chat] Stream error:', err);
          const errorMsg = err.message || 'Unable to connect to AI server. Please try again.';
          setError(errorMsg);
          setConversations(prev =>
            prev.map(c => {
              if (c.id === convId) {
                const msgs = c.messages.map(m =>
                  m.id === assistantMsgId
                    ? {
                        ...m,
                        content: accumulated ? accumulated + `\n\n*(Error: ${errorMsg})*` : `Error: ${errorMsg}`,
                        isStreaming: false,
                        error: errorMsg,
                      }
                    : m
                );
                return { ...c, messages: msgs, updatedAt: Date.now() };
              }
              return c;
            })
          );
        }
      } finally {
        setIsStreaming(false);
        abortControllerRef.current = null;
      }
    },
    [activeConversationId, isStreaming, selectedModel, reasoningEffort, createConversation]
  );

  const submitFeedback = useCallback(
    async (messageId: string, rating: 1 | -1, correction?: string) => {
      if (!activeConversationId) return;

      setConversations(prev =>
        prev.map(c => {
          if (c.id === activeConversationId) {
            const msgs = c.messages.map(m =>
              m.id === messageId ? { ...m, feedback: rating === 1 ? ('up' as const) : ('down' as const) } : m
            );
            return { ...c, messages: msgs };
          }
          return c;
        })
      );

      await submitFeedbackApi(rating, activeConversationId, correction);
    },
    [activeConversationId]
  );

  const resolveApproval = useCallback(
    async (approvalId: string, decision: 'approve' | 'deny', reason?: string, selectedMasterStrategy?: string) => {
      setActiveApprovalRequest(prev => (prev?.approval_id === approvalId ? null : prev));
      await submitToolApproval(approvalId, decision, reason, selectedMasterStrategy);
      setConversations(prev =>
        prev.map(c => {
          const msgs = c.messages.map(m => {
            if (m.approvalRequest && m.approvalRequest.approval_id === approvalId) {
              return {
                ...m,
                approvalRequest: {
                  ...m.approvalRequest,
                  status: decision === 'approve' ? ('approved' as const) : ('rejected' as const),
                  resolved_at: Date.now(),
                  rejection_reason: reason,
                  selected_master_strategy: selectedMasterStrategy,
                },
              };
            }
            return m;
          });
          return { ...c, messages: msgs };
        })
      );
    },
    []
  );

  const alwaysAllowTool = useCallback((toolName: string) => {
    setAlwaysAllowedTools(prev => {
      if (prev.includes(toolName)) return prev;
      const updated = [...prev, toolName];
      alwaysAllowedToolsRef.current = updated;
      return updated;
    });
  }, []);

  const dismissActiveApproval = useCallback(() => {
    setActiveApprovalRequest(null);
  }, []);

  const regenerateResponse = useCallback(
    async (assistantMessageId: string) => {
      if (isStreaming || !activeConversationId) return;

      const activeConv = conversations.find(c => c.id === activeConversationId);
      if (!activeConv) return;

      const msgIndex = activeConv.messages.findIndex(m => m.id === assistantMessageId);
      if (msgIndex === -1) return;

      let userQuery = '';
      for (let i = msgIndex - 1; i >= 0; i--) {
        if (activeConv.messages[i].role === 'user') {
          userQuery = activeConv.messages[i].content;
          break;
        }
      }

      if (!userQuery) return;

      // Remove the assistant message
      setConversations(prev =>
        prev.map(c => {
          if (c.id === activeConversationId) {
            const truncated = c.messages.slice(0, msgIndex);
            return { ...c, messages: truncated };
          }
          return c;
        })
      );

      // Re-trigger sendMessage with the user query
      await sendMessage(userQuery, activeConv.model || selectedModel, activeConv.effort || reasoningEffort);
    },
    [activeConversationId, conversations, isStreaming, selectedModel, reasoningEffort, sendMessage]
  );

  const clearAllHistory = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsStreaming(false);
    setError(null);

    const freshId = generateId();
    const freshConv: Conversation = {
      id: freshId,
      title: 'New Chat',
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now(),
      model: selectedModel || 'aarka-2.0',
      effort: reasoningEffort || 'high',
    };

    setConversations([freshConv]);
    setActiveConversationId(freshId);

    try {
      sessionStorage.setItem(SESSION_ACTIVE_KEY, freshId);
      localStorage.setItem(currentStorageKey, JSON.stringify([freshConv]));
      localStorage.removeItem('aarka-conv-v3-guest');
      localStorage.removeItem('aarka-conversations-v3');
      localStorage.removeItem('aarkaa-conversations-v3');
      localStorage.removeItem('aarkaa-conversations');
    } catch (e) {
      console.warn('Failed to clear storage keys on history reset', e);
    }
  }, [currentStorageKey, selectedModel, reasoningEffort]);

  return (
    <ChatContext.Provider
      value={{
        conversations,
        activeConversationId,
        activeConversation,
        messages,
        isStreaming,
        error,
        selectedModel,
        setSelectedModel,
        reasoningEffort,
        setReasoningEffort,
        createConversation,
        deleteConversation,
        renameConversation,
        setActiveConversationId,
        sendMessage,
        regenerateResponse,
        submitFeedback,
        resolveApproval,
        activeApprovalRequest,
        alwaysAllowedTools,
        alwaysAllowTool,
        dismissActiveApproval,
        stopGeneration,
        clearError,
        clearAllHistory,
        isMounted,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}

export function useChatContext(): ChatContextType {
  const context = useContext(ChatContext);
  if (!context) {
    return {
      conversations: [],
      activeConversationId: null,
      activeConversation: undefined,
      messages: [],
      isStreaming: false,
      error: null,
      selectedModel: 'aarka-2.0',
      setSelectedModel: () => {},
      reasoningEffort: 'medium',
      setReasoningEffort: () => {},
      createConversation: () => '',
      deleteConversation: () => {},
      renameConversation: () => {},
      setActiveConversationId: () => {},
      sendMessage: async () => {},
      regenerateResponse: async () => {},
      submitFeedback: async () => {},
      resolveApproval: async () => {},
      activeApprovalRequest: null,
      alwaysAllowedTools: [],
      alwaysAllowTool: () => {},
      dismissActiveApproval: () => {},
      stopGeneration: () => {},
      clearError: () => {},
      clearAllHistory: () => {},
      isMounted: true,
    };
  }
  return context;
}
