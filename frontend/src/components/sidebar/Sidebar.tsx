'use client';

import React, { useState, useMemo } from 'react';
import { Plus, X, LogIn, LogOut, Search, User as UserIcon, MessageSquare, Sparkles, Settings } from 'lucide-react';
import { ConversationItem } from './ConversationItem';
import { Conversation, User } from '@/types';
import { ThemeToggle } from '@/components/common/ThemeToggle';
import { useChatContext } from '@/context/ChatContext';

interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  user: User | null;
  onLogin: () => void;
  onLogout: () => void;
  onOpenSettings?: () => void;
}

export function Sidebar({
  isOpen,
  onToggle,
  user,
  onLogin,
  onLogout,
  onOpenSettings,
}: SidebarProps) {
  const {
    conversations,
    activeConversationId,
    setActiveConversationId,
    createConversation,
    deleteConversation,
    renameConversation,
    selectedModel,
    reasoningEffort,
  } = useChatContext();

  const [searchQuery, setSearchQuery] = useState('');

  const filteredConversations = useMemo(() => {
    if (!Array.isArray(conversations)) return [];
    if (!searchQuery.trim()) return conversations.filter(c => c && typeof c === 'object');
    return conversations
      .filter(c => c && typeof c === 'object')
      .filter(c => (c.title || '').toLowerCase().includes(searchQuery.toLowerCase()));
  }, [conversations, searchQuery]);

  const grouped = useMemo(() => {
    const today = new Date();
    const groups = {
      Today: [] as Conversation[],
      Yesterday: [] as Conversation[],
      'Last 7 Days': [] as Conversation[],
      Older: [] as Conversation[],
    };

    filteredConversations.forEach(c => {
      if (!c) return;
      const d = new Date(c.updatedAt || c.createdAt || Date.now());
      const diffTime = Math.abs(today.getTime() - d.getTime());
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

      if (diffDays <= 1 && today.getDate() === d.getDate()) {
        groups.Today.push(c);
      } else if (diffDays <= 2) {
        groups.Yesterday.push(c);
      } else if (diffDays <= 7) {
        groups['Last 7 Days'].push(c);
      } else {
        groups.Older.push(c);
      }
    });
    return groups;
  }, [filteredConversations]);

  const handleNewChat = () => {
    createConversation(selectedModel, reasoningEffort);
  };

  return (
    <aside
      className={`
        w-72 max-w-[85vw] h-full bg-[var(--bg-secondary)] border-r border-[var(--border)]
        flex flex-col flex-shrink-0 z-30 transition-all duration-300 select-none
      `}
    >
      {/* Sidebar Header */}
      <div className="p-4 border-b border-[var(--border)] flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-[var(--accent-muted)] border border-[var(--border-accent)] flex items-center justify-center text-[var(--accent-primary)] shadow-sm">
            <Sparkles className="w-4 h-4" />
          </div>
          <span className="font-display text-lg font-bold text-[var(--text-primary)] tracking-tight">
            Aarka <span className="text-[var(--accent-primary)] font-bold">AI</span>
          </span>
        </div>

        <button
          onClick={onToggle}
          type="button"
          className="p-1.5 rounded-lg text-[var(--text-tertiary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] transition-colors focus:outline-none"
          title="Close sidebar"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Action Controls */}
      <div className="p-3 space-y-2 flex-shrink-0">
        {/* New Chat Button */}
        <button
          onClick={handleNewChat}
          type="button"
          className={`
            w-full py-2.5 px-3.5 rounded-xl font-medium text-xs
            bg-[var(--accent-primary)] hover:bg-[var(--accent-hover)] text-white
            flex items-center justify-center gap-2 shadow-[var(--shadow-sm)]
            transition-all duration-200 hover:shadow-md
          `}
        >
          <Plus className="w-4 h-4 stroke-[2.5]" />
          <span>New Conversation</span>
        </button>

        {/* Search Box */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[var(--text-tertiary)]" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search conversations..."
            className={`
              w-full bg-[var(--bg-primary)] text-[var(--text-primary)] placeholder-[var(--text-tertiary)]
              text-xs pl-8 pr-3 py-1.5 rounded-xl border border-[var(--border)]
              focus:border-[var(--border-accent)] outline-none transition-all
            `}
          />
        </div>
      </div>

      {/* Conversation List */}
      <div className="flex-1 overflow-y-auto px-2 py-1 space-y-4">
        {conversations.length === 0 ? (
          <div className="text-center py-8 px-4 text-xs text-[var(--text-tertiary)]">
            No conversations yet. Start a new chat above.
          </div>
        ) : filteredConversations.length === 0 ? (
          <div className="text-center py-8 px-4 text-xs text-[var(--text-tertiary)]">
            No matching chats found.
          </div>
        ) : (
          Object.entries(grouped).map(([category, items]) => {
            if (items.length === 0) return null;
            return (
              <div key={category} className="space-y-1">
                <div className="px-2 py-1 text-[10px] font-semibold text-[var(--text-tertiary)] uppercase tracking-wider font-mono">
                  {category}
                </div>
                <div className="space-y-0.5">
                  {items.map((conv) => (
                    <ConversationItem
                      key={conv.id}
                      conversation={conv}
                      isActive={conv.id === activeConversationId}
                      onSelect={() => setActiveConversationId(conv.id)}
                      onDelete={() => deleteConversation(conv.id)}
                      onRename={(title) => renameConversation(conv.id, title)}
                    />
                  ))}
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Bottom Profile & Theme Panel */}
      <div className="p-3 border-t border-[var(--border)] bg-[var(--bg-tertiary)]/50 flex-shrink-0">
        <div className="flex items-center justify-between gap-2">
          {user ? (
            <div className="flex items-center gap-2.5 min-w-0 flex-1">
              <div className="w-8 h-8 rounded-full bg-[var(--bg-secondary)] border border-[var(--border)] flex items-center justify-center overflow-hidden flex-shrink-0">
                {user.picture ? (
                  <img src={user.picture} alt={user.name} className="w-full h-full object-cover" />
                ) : (
                  <UserIcon className="w-4 h-4 text-[var(--text-secondary)]" />
                )}
              </div>
              <div className="flex flex-col min-w-0">
                <span className="text-xs font-semibold text-[var(--text-primary)] truncate">{user.name}</span>
                <span className="text-[10px] text-[var(--text-tertiary)] truncate">{user.email}</span>
              </div>
            </div>
          ) : (
            <button
              onClick={onLogin}
              type="button"
              className="flex items-center gap-2 text-xs font-medium text-[var(--text-primary)] hover:text-[var(--accent-primary)] transition-colors"
            >
              <LogIn className="w-4 h-4 text-[var(--accent-primary)]" />
              <span>Sign In</span>
            </button>
          )}

          <div className="flex items-center gap-1">
            <button
              onClick={onOpenSettings}
              type="button"
              className="p-1.5 rounded-lg text-[var(--text-tertiary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] transition-colors cursor-pointer"
              title="Settings & Preferences"
            >
              <Settings className="w-4 h-4" />
            </button>
            {user && (
              <button
                onClick={onLogout}
                type="button"
                className="p-1.5 rounded-lg text-[var(--text-tertiary)] hover:text-red-400 hover:bg-[var(--bg-hover)] transition-colors cursor-pointer"
                title="Log Out"
              >
                <LogOut className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </div>
    </aside>
  );
}
