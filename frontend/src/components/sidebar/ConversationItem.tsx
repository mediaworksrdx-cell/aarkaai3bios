'use client';

import React, { useState } from 'react';
import { MessageSquare, Pencil, Trash2, Check, X } from 'lucide-react';
import { Conversation } from '@/types';

interface ConversationItemProps {
  conversation: Conversation;
  isActive: boolean;
  onSelect: () => void;
  onDelete: () => void;
  onRename: (title: string) => void;
}

export function ConversationItem({
  conversation,
  isActive,
  onSelect,
  onDelete,
  onRename,
}: ConversationItemProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(conversation.title || 'New Chat');

  const handleRenameSubmit = (e: React.FormEvent | React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (editTitle.trim()) {
      onRename(editTitle.trim());
    }
    setIsEditing(false);
  };

  const handleRenameCancel = (e: React.MouseEvent) => {
    e.stopPropagation();
    setEditTitle(conversation.title || 'New Chat');
    setIsEditing(false);
  };

  return (
    <div
      onClick={!isEditing ? onSelect : undefined}
      className={`
        group relative flex items-center p-2.5 my-0.5 rounded-xl cursor-pointer transition-all duration-150 text-xs
        ${isActive
          ? 'bg-[var(--bg-tertiary)] text-[var(--text-primary)] font-medium border border-[var(--border-accent)]'
          : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] border border-transparent'
        }
      `}
    >
      <div className="flex items-center flex-1 min-w-0 gap-2.5">
        <MessageSquare
          className={`w-3.5 h-3.5 flex-shrink-0 ${
            isActive ? 'text-[var(--accent-primary)]' : 'text-[var(--text-tertiary)]'
          }`}
        />

        {isEditing ? (
          <form onSubmit={handleRenameSubmit} className="flex-1 flex items-center min-w-0" onClick={(e) => e.stopPropagation()}>
            <input
              type="text"
              value={editTitle}
              onChange={(e) => setEditTitle(e.target.value)}
              autoFocus
              className="w-full bg-[var(--bg-primary)] text-[var(--text-primary)] text-xs px-2 py-0.5 rounded outline-none border border-[var(--border-accent)]"
            />
          </form>
        ) : (
          <span className="truncate flex-1 min-w-0">
            {conversation.title || 'New Chat'}
          </span>
        )}
      </div>

      {isEditing ? (
        <div className="flex items-center gap-1 ml-1 flex-shrink-0">
          <button onClick={handleRenameSubmit} type="button" className="p-1 hover:bg-[var(--bg-hover)] rounded text-green-500">
            <Check className="w-3 h-3" />
          </button>
          <button onClick={handleRenameCancel} type="button" className="p-1 hover:bg-[var(--bg-hover)] rounded text-[var(--text-tertiary)]">
            <X className="w-3 h-3" />
          </button>
        </div>
      ) : (
        <div className="flex items-center opacity-0 group-hover:opacity-100 transition-opacity ml-1 gap-0.5 flex-shrink-0">
          <button
            onClick={(e) => {
              e.stopPropagation();
              setIsEditing(true);
            }}
            type="button"
            className="p-1 hover:bg-[var(--bg-hover)] rounded text-[var(--text-tertiary)] hover:text-[var(--text-primary)] transition-colors"
            title="Rename"
          >
            <Pencil className="w-3 h-3" />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              if (confirm('Delete this conversation?')) onDelete();
            }}
            type="button"
            className="p-1 hover:bg-[var(--bg-hover)] rounded text-[var(--text-tertiary)] hover:text-red-400 transition-colors"
            title="Delete"
          >
            <Trash2 className="w-3 h-3" />
          </button>
        </div>
      )}
    </div>
  );
}
