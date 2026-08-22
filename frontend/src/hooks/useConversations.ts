'use client';

import { useState, useEffect, useCallback } from 'react';
import { Conversation, Message } from '@/types';

const STORAGE_KEY = 'aarkaa-conversations';

export function useConversations() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        setConversations(JSON.parse(stored));
      } catch (e) {
        console.error('Failed to parse conversations', e);
      }
    }
  }, []);

  useEffect(() => {
    if (conversations.length > 0) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations));
    }
  }, [conversations]);

  const createConversation = useCallback((model: string = 'aarkaa-7b'): string => {
    const newId = crypto.randomUUID();
    const newConv: Conversation = {
      id: newId,
      title: 'New Chat',
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now(),
      model,
    };
    setConversations(prev => [newConv, ...prev]);
    setActiveConversationId(newId);
    return newId;
  }, []);

  const deleteConversation = useCallback((id: string) => {
    setConversations(prev => prev.filter(c => c.id !== id));
    if (activeConversationId === id) {
      setActiveConversationId(null);
    }
  }, [activeConversationId]);

  const renameConversation = useCallback((id: string, title: string) => {
    setConversations(prev => prev.map(c => 
      c.id === id ? { ...c, title, updatedAt: Date.now() } : c
    ));
  }, []);

  const setActiveConversation = useCallback((id: string) => {
    setActiveConversationId(id);
  }, []);

  const updateConversationMessages = useCallback((id: string, messages: Message[]) => {
    setConversations(prev => prev.map(c => {
      if (c.id === id) {
        let title = c.title;
        if (title === 'New Chat' && messages.length > 0) {
          const firstUserMessage = messages.find(m => m.role === 'user');
          if (firstUserMessage) {
            title = firstUserMessage.content.slice(0, 40) + (firstUserMessage.content.length > 40 ? '...' : '');
          }
        }
        return { ...c, messages, title, updatedAt: Date.now() };
      }
      return c;
    }));
  }, []);

  const getConversation = useCallback((id: string): Conversation | undefined => {
    return conversations.find(c => c.id === id);
  }, [conversations]);

  return {
    conversations,
    activeConversation: activeConversationId ? getConversation(activeConversationId) : undefined,
    activeConversationId,
    createConversation,
    deleteConversation,
    renameConversation,
    setActiveConversation,
    updateConversationMessages,
    getConversation,
  };
}
