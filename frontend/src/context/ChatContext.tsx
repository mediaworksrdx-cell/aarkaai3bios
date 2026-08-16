'use client';

import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { Conversation, Message, EffortLevel } from '@/types';
import { streamChat, submitFeedbackApi } from '@/lib/api';

const STORAGE_KEY = 'aarka-conversations-v3';

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

  const abortControllerRef = useRef<AbortController | null>(null);

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
          setSelectedModelState('gemini-2.5');
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

  // Load conversations whenever user account changes
  useEffect(() => {
    try {
      const saved = localStorage.getItem(currentStorageKey);
      if (saved && saved !== 'undefined' && saved !== 'null') {
        try {
          const parsed = JSON.parse(saved);
          if (Array.isArray(parsed) && parsed.length > 0) {
            const sanitized: Conversation[] = parsed
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

            if (sanitized.length > 0) {
              setConversations(sanitized);
              setActiveConversationId(sanitized[0].id);
              return;
            }
          }
        } catch (e) {
          console.warn('Corrupted storage reset', e);
        }
      }

      // Initial clean conversation for this user
      const initialId = generateId();
      const initialConv: Conversation = {
        id: initialId,
        title: 'New Chat',
        messages: [],
        createdAt: Date.now(),
        updatedAt: Date.now(),
        model: 'aarka-2.0',
        effort: 'high',
      };
      setConversations([initialConv]);
      setActiveConversationId(initialId);
      localStorage.setItem(currentStorageKey, JSON.stringify([initialConv]));
    } catch (e) {
      console.warn('Failed to load user conversations', e);
    }
  }, [currentStorageKey]);

  // Save conversations to currentStorageKey on change
  useEffect(() => {
    if (isMounted && conversations.length > 0) {
      try {
        localStorage.setItem(currentStorageKey, JSON.stringify(conversations));
      } catch (e) {
        console.warn('Failed to persist user conversations', e);
      }
    }
  }, [conversations, currentStorageKey, isMounted]);

  const setSelectedModel = useCallback((model: string) => {
    const normalized = model === 'aarkaa-7b' || model === 'aarkaa-3b' || model === 'aarkaa-2.0' || model === 'aarka-2.0'
      ? 'aarka-2.0'
      : model.startsWith('gemini')
      ? 'gemini-2.5'
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
    setConversations(prev => [newConv, ...prev]);
    setActiveConversationId(newId);
    setError(null);
    return newId;
  }, []);

  const deleteConversation = useCallback((id: string) => {
    setConversations(prev => {
      const remaining = prev.filter(c => c.id !== id);
      if (activeConversationId === id) {
        if (remaining.length > 0) {
          setActiveConversationId(remaining[0].id);
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
        modelUsed: model === 'gemini-2.5' ? 'Google Gemini 2.5' : 'Aarka AI',
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
      let finalModel = model === 'gemini-2.5' ? 'Google Gemini 2.5' : 'Aarka AI';

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
          } else if (chunk.type === 'final' || chunk.type === 'final_response') {
            if (chunk.content) accumulated = chunk.content;
            if (chunk.response) accumulated = chunk.response;
            if (chunk.model_used) finalModel = chunk.model_used;
          } else if (chunk.type === 'error' && chunk.detail) {
            throw new Error(chunk.detail);
          }
        }

        setConversations(prev =>
          prev.map(c => {
            if (c.id === convId) {
              const msgs = c.messages.map(m =>
                m.id === assistantMsgId
                  ? {
                      ...m,
                      content: accumulated || 'No response received from engine.',
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
      stopGeneration: () => {},
      clearError: () => {},
      clearAllHistory: () => {},
      isMounted: true,
    };
  }
  return context;
}
