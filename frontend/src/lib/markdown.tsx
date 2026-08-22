'use client';

import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Copy, Check } from 'lucide-react';

interface MarkdownRendererProps {
  content: string;
  className?: string;
  isStreaming?: boolean;
}

function CodeBlockComponent({ className, children, ...props }: any) {
  const [copied, setCopied] = useState(false);
  const match = /language-(\w+)/.exec(className || '');
  const language = match ? match[1] : '';
  const textContent = String(children).replace(/\n$/, '');

  // Detect if this is inline code or a multi-line code block
  const isInline = !match && !textContent.includes('\n');

  const handleCopy = () => {
    if (typeof navigator !== 'undefined' && navigator.clipboard) {
      navigator.clipboard.writeText(textContent);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (isInline) {
    return (
      <code className="bg-[var(--code-bg)] text-[var(--accent-primary)] px-1.5 py-0.5 rounded-md text-[0.88em] font-mono border border-[var(--border)]" {...props}>
        {children}
      </code>
    );
  }

  return (
    <div className="relative my-4 rounded-xl overflow-hidden bg-[var(--code-bg)] border border-[var(--border-strong)] shadow-[var(--shadow-sm)] group">
      {/* Code Header Bar */}
      <div className="flex items-center justify-between px-4 py-2 bg-[var(--bg-tertiary)] border-b border-[var(--border)] text-xs font-mono text-[var(--text-secondary)] select-none">
        <span className="font-semibold uppercase text-[11px] text-[var(--text-tertiary)] tracking-wider">
          {language || 'code'}
        </span>
        <button
          onClick={handleCopy}
          type="button"
          className="flex items-center gap-1.5 px-2 py-1 rounded-md text-[11px] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] transition-colors focus:outline-none"
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

      {/* Code Body */}
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

export function MarkdownRenderer({ content, className = '', isStreaming = false }: MarkdownRendererProps) {
  if (!content) return null;

  return (
    <div className={`prose ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          code: CodeBlockComponent,
          a: ({ node, ...props }: any) => (
            <a {...props} target="_blank" rel="noopener noreferrer" />
          ),
          table: ({ node, ...props }: any) => (
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
