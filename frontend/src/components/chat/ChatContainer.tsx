'use client';

import React, { useEffect, useRef, useState } from 'react';
import { WelcomeScreen } from './WelcomeScreen';
import { MessageBubble } from './MessageBubble';
import { ChatInput } from './ChatInput';
import { useChatContext } from '@/context/ChatContext';
import { ThemeToggle } from '@/components/common/ThemeToggle';
import { Menu, Plus, Download, FileText, FileDown, Share2 } from 'lucide-react';
import { exportToPdf, exportToWord, exportToMarkdown } from '@/lib/api';

interface ChatContainerProps {
  onToggleSidebar?: () => void;
  isSidebarOpen?: boolean;
}

export function ChatContainer({
  onToggleSidebar,
  isSidebarOpen,
}: ChatContainerProps) {
  const {
    messages,
    sendMessage,
    stopGeneration,
    isStreaming,
    selectedModel,
    setSelectedModel,
    reasoningEffort,
    setReasoningEffort,
    createConversation,
    activeConversation,
  } = useChatContext();

  const [showExportMenu, setShowExportMenu] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isStreaming]);

  const handleSend = (text: string) => {
    sendMessage(text, selectedModel, reasoningEffort);
  };

  const handleNewChat = () => {
    createConversation(selectedModel, reasoningEffort);
  };

  const getFullConversationText = () => {
    return messages
      .map(
        m =>
          `### ${m.role === 'user' ? 'User' : 'Aarka AI'}\n\n${m.content}\n`
      )
      .join('\n---\n\n');
  };

  const handleExportFullPdf = () => {
    setShowExportMenu(false);
    exportToPdf({
      title: activeConversation?.title || 'Aarka AI Conversation',
      content: getFullConversationText(),
      modelUsed: selectedModel === 'gemini-2.5' ? 'Google Gemini 2.5' : 'Aarka AI',
    });
  };

  const handleExportFullWord = () => {
    setShowExportMenu(false);
    exportToWord({
      title: activeConversation?.title || 'Aarka AI Conversation',
      content: getFullConversationText(),
      modelUsed: selectedModel === 'gemini-2.5' ? 'Google Gemini 2.5' : 'Aarka AI',
    });
  };

  const handleExportFullMarkdown = () => {
    setShowExportMenu(false);
    exportToMarkdown(
      (activeConversation?.title || 'Aarka_AI_Chat').replace(/\s+/g, '_'),
      getFullConversationText()
    );
  };

  return (
    <div className="flex flex-col h-full bg-[var(--bg-primary)] relative overflow-hidden">
      {/* Top Header Bar */}
      <header className="flex items-center justify-between px-4 py-3 border-b border-[var(--border)] bg-[var(--bg-secondary)]/85 backdrop-blur-md z-20 flex-shrink-0">
        <div className="flex items-center gap-3">
          <button
            onClick={onToggleSidebar}
            type="button"
            className="p-2 rounded-xl text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] transition-colors focus:outline-none cursor-pointer"
            aria-label="Toggle Sidebar"
          >
            <Menu className="w-5 h-5" />
          </button>

          <div className="flex items-center gap-2">
            <span className="font-display text-lg text-[var(--text-primary)] tracking-tight font-bold">
              Aarka <span className="text-[var(--accent-primary)] font-bold">AI</span>
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Export Full Chat Button (when chat has messages) */}
          {messages.length > 0 && (
            <div className="relative inline-block">
              <button
                onClick={() => setShowExportMenu(!showExportMenu)}
                type="button"
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[var(--bg-tertiary)] hover:bg-[var(--bg-hover)] border border-[var(--border)] text-xs font-medium text-[var(--text-primary)] transition-all shadow-[var(--shadow-sm)] cursor-pointer"
                title="Export entire chat"
              >
                <Download className="w-3.5 h-3.5 text-[var(--accent-primary)]" />
                <span className="hidden sm:inline">Export</span>
              </button>

              {showExportMenu && (
                <>
                  <div
                    className="fixed inset-0 z-40"
                    onClick={() => setShowExportMenu(false)}
                  />
                  <div className="absolute right-0 top-full mt-2 w-48 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-xl shadow-[var(--shadow-float)] p-1.5 z-50 animate-slide-up backdrop-blur-md">
                    <button
                      onClick={handleExportFullPdf}
                      type="button"
                      className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-xs font-medium text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] transition-colors cursor-pointer text-left"
                    >
                      <FileText className="w-3.5 h-3.5 text-rose-500" />
                      <span>Export as PDF (.pdf)</span>
                    </button>

                    <button
                      onClick={handleExportFullWord}
                      type="button"
                      className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-xs font-medium text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] transition-colors cursor-pointer text-left"
                    >
                      <FileDown className="w-3.5 h-3.5 text-blue-500" />
                      <span>Export as Word (.doc)</span>
                    </button>

                    <button
                      onClick={handleExportFullMarkdown}
                      type="button"
                      className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-xs font-medium text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] transition-colors cursor-pointer text-left"
                    >
                      <Share2 className="w-3.5 h-3.5 text-amber-500" />
                      <span>Export Markdown (.md)</span>
                    </button>
                  </div>
                </>
              )}
            </div>
          )}

          <button
            onClick={handleNewChat}
            type="button"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[var(--bg-tertiary)] hover:bg-[var(--bg-hover)] border border-[var(--border)] text-xs font-medium text-[var(--text-primary)] transition-all shadow-[var(--shadow-sm)] cursor-pointer"
            title="Start a new chat"
          >
            <Plus className="w-3.5 h-3.5 text-[var(--accent-primary)]" />
            <span className="hidden sm:inline">New Chat</span>
          </button>
        </div>
      </header>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto w-full">
        {messages.length === 0 ? (
          <WelcomeScreen onSelectPrompt={handleSend} selectedModel={selectedModel} />
        ) : (
          <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6 w-full flex flex-col">
            {messages.map((msg) => (
              <MessageBubble
                key={msg.id}
                message={msg}
              />
            ))}
            <div ref={messagesEndRef} className="h-6" />
          </div>
        )}
      </div>

      {/* Chat Input Bar */}
      <ChatInput
        onSend={handleSend}
        onStop={stopGeneration}
        isStreaming={isStreaming}
        selectedModel={selectedModel}
        onModelChange={setSelectedModel}
        reasoningEffort={reasoningEffort}
        onEffortChange={setReasoningEffort}
      />
    </div>
  );
}
