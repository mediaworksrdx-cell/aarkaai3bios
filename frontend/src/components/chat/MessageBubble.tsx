'use client';

import React, { useState } from 'react';
import { Message } from '@/types';
import {
  Sparkles,
  User,
  AlertCircle,
  Check,
  Copy,
  ThumbsUp,
  ThumbsDown,
  RotateCcw,
  FileText,
  FileDown,
  Download,
  Share2
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { MODEL_OPTIONS } from '@/styles/theme';
import { useChatContext } from '@/context/ChatContext';
import { exportToPdf, exportToWord, exportToMarkdown } from '@/lib/api';

interface MessageBubbleProps {
  message: Message;
  onRetry?: () => void;
}

function CodeBlock({ className, children, ...props }: any) {
  const [copied, setCopied] = useState(false);
  const match = /language-(\w+)/.exec(className || '');
  const language = match ? match[1] : '';
  const codeContent = String(children).replace(/\n$/, '');

  const handleCopy = () => {
    if (typeof navigator !== 'undefined' && navigator.clipboard) {
      navigator.clipboard.writeText(codeContent);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (match || codeContent.includes('\n')) {
    return (
      <div className="relative my-4 rounded-xl overflow-hidden bg-[var(--code-bg)] border border-[var(--border-strong)] shadow-[var(--shadow-sm)] group">
        <div className="flex items-center justify-between px-4 py-2 bg-[var(--bg-tertiary)] border-b border-[var(--border)] text-xs font-mono text-[var(--text-secondary)] select-none">
          <span className="font-semibold uppercase text-[11px] text-[var(--text-tertiary)] tracking-wider">
            {language || 'code'}
          </span>
          <button
            onClick={handleCopy}
            type="button"
            className="flex items-center gap-1.5 px-2 py-1 rounded-md text-[11px] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] transition-colors focus:outline-none cursor-pointer"
            title="Copy code"
          >
            {copied ? (
              <>
                <Check className="w-3.5 h-3.5 text-green-500" />
                <span className="text-green-500 font-medium">Copied</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5" />
                <span>Copy</span>
              </>
            )}
          </button>
        </div>
        <div className="p-4 overflow-x-auto text-xs sm:text-sm font-mono text-[var(--text-primary)] leading-relaxed">
          <pre className="!bg-transparent !p-0 !m-0 !border-none !shadow-none">
            <code className={className} {...props}>
              {children}
            </code>
          </pre>
        </div>
      </div>
    );
  }

  return (
    <code
      className="bg-[var(--code-bg)] text-[var(--accent-primary)] px-1.5 py-0.5 rounded-md text-[0.88em] font-mono border border-[var(--border)]"
      {...props}
    >
      {children}
    </code>
  );
}

function MarkdownRenderer({ content, className = '', isStreaming = false }: { content: string; className?: string; isStreaming?: boolean }) {
  if (!content) return null;

  return (
    <div className={`prose ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          code: CodeBlock,
          a: ({ node, ...props }) => (
            <a {...props} target="_blank" rel="noopener noreferrer" />
          ),
          table: ({ node, ...props }) => (
            <div className="overflow-x-auto my-3">
              <table {...props} />
            </div>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
      {isStreaming && (
        <span className="inline-block w-1.5 h-4 ml-1 align-middle bg-[var(--accent-primary)] animate-pulse" />
      )}
    </div>
  );
}

export function MessageBubble({ message, onRetry }: MessageBubbleProps) {
  const { regenerateResponse, submitFeedback, isStreaming } = useChatContext();
  const [copied, setCopied] = useState(false);
  const [feedback, setFeedback] = useState<'up' | 'down' | null>(message.feedback || null);
  const [showExportMenu, setShowExportMenu] = useState(false);

  const isUser = message.role === 'user';
  const isError = !!message.error;
  const isMessageStreaming = !!message.isStreaming;

  const modelInfo = message.modelUsed 
    ? MODEL_OPTIONS.find(m => m.id === message.modelUsed || m.label === message.modelUsed)
    : null;

  const timestampDate = message.timestamp && !isNaN(new Date(message.timestamp).getTime())
    ? new Date(message.timestamp)
    : new Date();

  const formattedTime = new Intl.DateTimeFormat('en-US', {
    hour: 'numeric',
    minute: 'numeric',
  }).format(timestampDate);

  const handleCopy = () => {
    if (!message.content) return;
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleFeedback = (rating: 1 | -1) => {
    const newFeedback = rating === 1 ? 'up' : 'down';
    setFeedback(newFeedback);
    submitFeedback(message.id, rating);
  };

  const handleRegenerate = () => {
    if (onRetry) {
      onRetry();
    } else {
      regenerateResponse(message.id);
    }
  };

  const handleExportPdf = () => {
    setShowExportMenu(false);
    exportToPdf({
      title: 'Aarka AI Response',
      content: message.content,
      modelUsed: modelInfo?.label || 'Aarka AI',
      timestamp: message.timestamp,
    });
  };

  const handleExportWord = () => {
    setShowExportMenu(false);
    exportToWord({
      title: 'Aarka AI Response',
      content: message.content,
      modelUsed: modelInfo?.label || 'Aarka AI',
      timestamp: message.timestamp,
    });
  };

  const handleExportMarkdown = () => {
    setShowExportMenu(false);
    exportToMarkdown('Aarka_AI_Response', message.content);
  };

  return (
    <div
      className={`flex w-full ${
        isUser ? 'justify-end' : 'justify-start'
      } mb-8 animate-slide-up`}
    >
      <div
        className={`flex gap-3.5 ${
          isUser
            ? 'flex-row-reverse max-w-[85%] sm:max-w-[78%]'
            : 'flex-row max-w-full sm:max-w-[88%]'
        }`}
      >
        {/* Avatar */}
        <div className="flex-shrink-0 mt-0.5">
          {isUser ? (
            <div className="w-8 h-8 rounded-full bg-[var(--bg-tertiary)] border border-[var(--border)] flex items-center justify-center text-[var(--text-secondary)] shadow-[var(--shadow-sm)]">
              <User className="w-4 h-4" />
            </div>
          ) : (
            <div className="w-8 h-8 rounded-full bg-[var(--accent-muted)] border border-[var(--border-accent)] flex items-center justify-center text-[var(--accent-primary)] shadow-[var(--shadow-sm)]">
              <Sparkles className="w-4 h-4" />
            </div>
          )}
        </div>

        {/* Content Container */}
        <div className="flex flex-col gap-1.5 min-w-0 flex-1">
          {/* Header info */}
          <div
            className={`flex items-center gap-2 px-1 text-xs text-[var(--text-tertiary)] ${
              isUser ? 'justify-end' : 'justify-start'
            }`}
          >
            <span className="font-semibold text-[var(--text-secondary)]">
              {isUser ? 'You' : (modelInfo?.label || 'Aarka AI')}
            </span>
            <span>·</span>
            <span>{formattedTime}</span>
          </div>

          {/* Bubble */}
          <div
            className={`
              relative p-4 sm:p-5 rounded-2xl transition-all duration-200
              ${
                isUser
                  ? 'bg-[var(--accent-muted)] border border-[var(--border-accent)] text-[var(--text-primary)] rounded-tr-sm shadow-[var(--shadow-sm)]'
                  : isError
                  ? 'bg-red-500/10 border border-red-500/30 text-[var(--text-primary)] rounded-tl-sm'
                  : 'bg-[var(--bg-secondary)] border border-[var(--border)] rounded-tl-sm shadow-[var(--shadow-sm)]'
              }
            `}
          >
            {isUser ? (
              <div className="whitespace-pre-wrap break-words text-sm sm:text-[0.95rem] leading-relaxed">
                {message.content}
              </div>
            ) : (
              <div className="min-w-0 text-sm sm:text-[0.95rem]">
                <MarkdownRenderer content={message.content} isStreaming={isMessageStreaming} />

                {isMessageStreaming && !message.content && (
                  <div className="flex items-center gap-1.5 py-2">
                    <span className="w-2 h-2 rounded-full bg-[var(--accent-primary)] pulsing-dot" style={{ animationDelay: '0ms' }} />
                    <span className="w-2 h-2 rounded-full bg-[var(--accent-primary)] pulsing-dot" style={{ animationDelay: '200ms' }} />
                    <span className="w-2 h-2 rounded-full bg-[var(--accent-primary)] pulsing-dot" style={{ animationDelay: '400ms' }} />
                  </div>
                )}
              </div>
            )}

            {/* Error state */}
            {isError && (
              <div className="flex items-center gap-2 mt-3 text-red-400 text-xs sm:text-sm">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{message.error}</span>
              </div>
            )}
          </div>

          {/* Complete Action Toolbar for Assistant Messages */}
          {!isUser && !isMessageStreaming && message.content && (
            <div className="flex flex-wrap items-center gap-1.5 px-1 mt-1">
              {/* Copy Button */}
              <button
                onClick={handleCopy}
                type="button"
                className="flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-medium text-[var(--text-tertiary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] transition-colors border border-transparent hover:border-[var(--border)] cursor-pointer"
                title="Copy message"
              >
                {copied ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-green-500" />
                    <span className="text-green-500 font-medium">Copied</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5" />
                    <span>Copy</span>
                  </>
                )}
              </button>

              {/* Feedback: Thumbs Up */}
              <button
                onClick={() => handleFeedback(1)}
                type="button"
                className={`p-1.5 rounded-lg text-xs transition-colors border cursor-pointer ${
                  feedback === 'up'
                    ? 'text-emerald-500 bg-emerald-500/10 border-emerald-500/30'
                    : 'text-[var(--text-tertiary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] border-transparent hover:border-[var(--border)]'
                }`}
                title="Good response"
              >
                <ThumbsUp className="w-3.5 h-3.5" />
              </button>

              {/* Feedback: Thumbs Down */}
              <button
                onClick={() => handleFeedback(-1)}
                type="button"
                className={`p-1.5 rounded-lg text-xs transition-colors border cursor-pointer ${
                  feedback === 'down'
                    ? 'text-rose-500 bg-rose-500/10 border-rose-500/30'
                    : 'text-[var(--text-tertiary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] border-transparent hover:border-[var(--border)]'
                }`}
                title="Poor response"
              >
                <ThumbsDown className="w-3.5 h-3.5" />
              </button>

              {/* Reload / Resend / Regenerate Button */}
              <button
                onClick={handleRegenerate}
                disabled={isStreaming}
                type="button"
                className="flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-medium text-[var(--text-tertiary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] transition-colors border border-transparent hover:border-[var(--border)] cursor-pointer disabled:opacity-50"
                title="Regenerate response"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Retry</span>
              </button>

              {/* Export Menu */}
              <div className="relative inline-block">
                <button
                  onClick={() => setShowExportMenu(!showExportMenu)}
                  type="button"
                  className="flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-medium text-[var(--text-tertiary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] transition-colors border border-transparent hover:border-[var(--border)] cursor-pointer"
                  title="Export response"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Export</span>
                </button>

                {showExportMenu && (
                  <>
                    <div
                      className="fixed inset-0 z-40"
                      onClick={() => setShowExportMenu(false)}
                    />
                    <div className="absolute left-0 bottom-full mb-1.5 w-44 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-xl shadow-[var(--shadow-float)] p-1.5 z-50 animate-slide-up backdrop-blur-md">
                      <button
                        onClick={handleExportPdf}
                        type="button"
                        className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-xs font-medium text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] transition-colors cursor-pointer text-left"
                      >
                        <FileText className="w-3.5 h-3.5 text-rose-500" />
                        <span>Export PDF (.pdf)</span>
                      </button>

                      <button
                        onClick={handleExportWord}
                        type="button"
                        className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-xs font-medium text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] transition-colors cursor-pointer text-left"
                      >
                        <FileDown className="w-3.5 h-3.5 text-blue-500" />
                        <span>Export Word (.doc)</span>
                      </button>

                      <button
                        onClick={handleExportMarkdown}
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

              {/* Model Badge */}
              {modelInfo && (
                <div className="flex items-center gap-1 text-[11px] font-medium text-[var(--text-tertiary)] ml-auto bg-[var(--bg-tertiary)] px-2 py-0.5 rounded-full border border-[var(--border)]">
                  <span>{modelInfo.icon}</span>
                  <span>{modelInfo.label}</span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
