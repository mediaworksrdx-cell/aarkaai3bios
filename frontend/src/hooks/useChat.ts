'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import { Message, EffortLevel } from '@/types';
import { streamChat } from '@/lib/api';

export function useChat(conversationId: string) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const clearError = useCallback(() => setError(null), []);

  const stopGeneration = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setIsStreaming(false);
    }
  }, []);

  const sendMessage = useCallback(async (content: string, model: string = 'aarkaa-2.0', effort: EffortLevel = 'high') => {
    if (!content.trim()) return;

    const userMessage: Message = {
      id: crypto.randomUUID ? crypto.randomUUID() : 'id-' + Date.now(),
      role: 'user',
      content,
      timestamp: Date.now(),
    };

    const assistantMessageId = crypto.randomUUID ? crypto.randomUUID() : 'id-' + Date.now();
    const initialAssistantMessage: Message = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
      modelUsed: model,
      effort,
      isStreaming: true,
    };

    setMessages(prev => [...prev, userMessage, initialAssistantMessage]);
    setIsStreaming(true);
    setError(null);

    abortControllerRef.current = new AbortController();

    try {
      const generator = streamChat(
        content,
        conversationId,
        model,
        effort,
        null,
        abortControllerRef.current.signal
      );

      let accumulatedText = '';
      for await (const chunk of generator) {
        const token = chunk.token ?? chunk.content ?? chunk.text;
        if (token) {
          accumulatedText += token;
          setMessages(prev => {
            const msgs = [...prev];
            const lastIdx = msgs.length - 1;
            if (msgs[lastIdx] && msgs[lastIdx].id === assistantMessageId) {
              msgs[lastIdx] = { ...msgs[lastIdx], content: accumulatedText };
            }
            return msgs;
          });
        }
      }

      setMessages(prev => {
        const msgs = [...prev];
        const lastIdx = msgs.length - 1;
        if (msgs[lastIdx] && msgs[lastIdx].id === assistantMessageId) {
          msgs[lastIdx] = { ...msgs[lastIdx], isStreaming: false };
        }
        return msgs;
      });
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        setError(err.message || 'Stream failed');
      }
    } finally {
      setIsStreaming(false);
      abortControllerRef.current = null;
    }
  }, [conversationId]);

  return {
    messages,
    sendMessage,
    stopGeneration,
    isStreaming,
    error,
    clearError,
  };
}
