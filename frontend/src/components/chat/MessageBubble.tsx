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
import { CodeModeSandboxCard } from './CodeModeSandboxCard';

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

  // If the model wrapped normal response text inside a ```markdown or ```md block,
  // render it directly as rich formatted markdown instead of an ugly raw code box!
  if (language === 'markdown' || language === 'md') {
    return (
      <div className="my-2 not-prose text-[var(--text-primary)] leading-relaxed">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>
          {codeContent}
        </ReactMarkdown>
      </div>
    );
  }

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

  let displayContent = content
    .replace(/(?:\r?\n|\s)*(?:\*{1,2}|[\(\[])?\s*end of (?:answer|response|text|explanation)\s*(?:\*{1,2}|[\)\]])?\.?[\s`]*$/gi, '')
    .replace(/(?:\r?\n|\s)*---+\s*end\s+(?:of\s+)?(?:answer|response|disclaimer|text)\s*---+[\s`]*$/gi, '')
    .replace(/(?:\r?\n|\s)*(?:#Aarkaa(?:AI)?|#Aarka(?:AI)?)\b.*$/gi, '')
    .replace(/(?:\r?\n|\s)*(?:#[A-Za-z0-9_\-\/]+)+\s*$/gi, '')
    .trimEnd();

  // Strip accidental outer ```markdown or ```md wrapper so the response is never rendered inside a code box
  if (/^\s*```(?:markdown|md)\b/i.test(displayContent)) {
    displayContent = displayContent.replace(/^\s*```(?:markdown|md)[^\n]*\n?/i, '');
    displayContent = displayContent.replace(/\n?```\s*$/i, '');
  }

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
        {displayContent}
      </ReactMarkdown>
      {isStreaming && (
        <span className="inline-block w-1.5 h-4 ml-1 align-middle bg-[var(--accent-primary)] animate-pulse" />
      )}
    </div>
  );
}

export function MessageBubble({ message, onRetry }: MessageBubbleProps) {
  const { regenerateResponse, submitFeedback, isStreaming, resolveApproval } = useChatContext();
  const [copied, setCopied] = useState(false);
  const [feedback, setFeedback] = useState<'up' | 'down' | null>(message.feedback || null);
  const [showExportMenu, setShowExportMenu] = useState(false);
  const [showCorrectionBox, setShowCorrectionBox] = useState(false);
  const [correctionText, setCorrectionText] = useState('');
  const [correctionSubmitted, setCorrectionSubmitted] = useState(false);

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
    if (rating === 1) {
      setFeedback('up');
      setShowCorrectionBox(false);
      submitFeedback(message.id, 1);
    } else {
      setFeedback('down');
      setShowCorrectionBox(true);
      submitFeedback(message.id, -1);
    }
  };

  const handleSendCorrection = () => {
    if (correctionText.trim()) {
      submitFeedback(message.id, -1, correctionText.trim());
      setCorrectionSubmitted(true);
      setTimeout(() => {
        setShowCorrectionBox(false);
        setCorrectionSubmitted(false);
      }, 2000);
    } else {
      setShowCorrectionBox(false);
    }
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
                {(() => {
                  const cleanedContent = (message.content || '')
                    .replace(/(?:^|\n)This action requires your authorization before modifying the workspace:?\s*/gi, '')
                    .replace(/^(?:Thought:\s*|I already wrote this file.*|I made a mistake in the script.*)/gim, '')
                    .trim();

                  return cleanedContent ? (
                    <MarkdownRenderer
                      content={cleanedContent}
                      isStreaming={isMessageStreaming}
                    />
                  ) : null;
                })()}

                {message.codeModeExecution && (
                  <CodeModeSandboxCard execution={message.codeModeExecution} />
                )}

                {message.approvalRequest && (
                  <div className="my-2.5 flex items-center gap-2 px-3.5 py-2 rounded-xl bg-[var(--bg-tertiary)]/70 border border-[var(--border)] text-xs text-[var(--text-secondary)] font-mono">
                    {message.approvalRequest.status === 'approved' ? (
                      <>
                        <span className="flex items-center justify-center w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-400">
                          <Check className="w-3 h-3 stroke-[2.5]" />
                        </span>
                        <span className="text-[var(--text-primary)] font-semibold">
                          Authorized: {message.approvalRequest.tool_name}
                        </span>
                        <span className="text-[var(--text-tertiary)] text-[11px] truncate">
                          ({message.approvalRequest.human_summary || message.approvalRequest.description})
                        </span>
                      </>
                    ) : message.approvalRequest.status === 'rejected' ? (
                      <>
                        <span className="flex items-center justify-center w-5 h-5 rounded-full bg-red-500/20 text-red-400">
                          <AlertCircle className="w-3 h-3" />
                        </span>
                        <span className="text-[var(--text-primary)] font-semibold">
                          Denied: {message.approvalRequest.tool_name}
                        </span>
                        {message.approvalRequest.rejection_reason && (
                          <span className="text-red-400/80 text-[11px] truncate">
                            ({message.approvalRequest.rejection_reason})
                          </span>
                        )}
                      </>
                    ) : (
                      <>
                        <span className="relative flex h-2 w-2 mr-0.5">
                          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
                          <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500"></span>
                        </span>
                        <span className="text-[var(--text-primary)] font-medium">
                          Authorization Required for <code className="text-amber-400 font-bold">{message.approvalRequest.tool_name}</code>
                        </span>
                        <span className="text-amber-400/90 text-[11px] hidden sm:inline-flex items-center px-2 py-0.5 rounded-full border border-amber-500/30 bg-amber-500/10 font-mono">
                          Review action in modal dialog
                        </span>
                      </>
                    )}
                  </div>
                )}

                {isMessageStreaming && !message.content && !message.codeModeExecution && !message.approvalRequest && (
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
                    <div className="absolute left-0 bottom-full mb-1.5 w-48 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-xl shadow-[var(--shadow-float)] p-1.5 z-50 animate-slide-up backdrop-blur-md">
                      <button
                        onClick={handleExportPdf}
                        type="button"
                        className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-xs font-medium text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] transition-colors cursor-pointer text-left"
                      >
                        <FileText className="w-3.5 h-3.5 text-rose-500" />
                        <span>Export PDF</span>
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

          {/* Optional RLHF Correction Note Box */}
          {!isUser && showCorrectionBox && (
            <div className="w-full mt-2 p-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] shadow-sm text-xs space-y-2">
              <div className="flex items-center justify-between text-[var(--text-secondary)] font-medium">
                <span>What was wrong or could be improved? (Optional RLHF Note)</span>
                <button
                  type="button"
                  onClick={() => setShowCorrectionBox(false)}
                  className="text-[var(--text-tertiary)] hover:text-[var(--text-primary)] cursor-pointer"
                >
                  ✕
                </button>
              </div>
              <input
                type="text"
                value={correctionText}
                onChange={(e) => setCorrectionText(e.target.value)}
                placeholder="E.g., Please answer in concise bullet points with verified data..."
                className="w-full px-2.5 py-1.5 rounded-md bg-[var(--bg-primary)] border border-[var(--border)] text-[var(--text-primary)] placeholder-[var(--text-tertiary)] focus:outline-none focus:ring-1 focus:ring-rose-500 text-xs"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleSendCorrection();
                  }
                }}
              />
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-[var(--text-tertiary)]">
                  {correctionSubmitted ? '✓ Correction submitted to learning memory' : 'Feedback auto-tunes model responses'}
                </span>
                <div className="flex items-center gap-1.5">
                  <button
                    type="button"
                    onClick={() => setShowCorrectionBox(false)}
                    className="px-2 py-1 rounded text-[11px] text-[var(--text-tertiary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] cursor-pointer"
                  >
                    Skip
                  </button>
                  <button
                    type="button"
                    onClick={handleSendCorrection}
                    disabled={!correctionText.trim()}
                    className="px-2.5 py-1 rounded text-[11px] font-medium bg-rose-600 hover:bg-rose-500 disabled:opacity-40 text-white transition-colors cursor-pointer"
                  >
                    Submit Correction
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
