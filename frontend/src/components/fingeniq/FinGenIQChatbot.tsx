'use client';

import React, { useState, useRef, useEffect } from 'react';

interface Message {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: string;
  modelUsed?: string;
  isStreaming?: boolean;
}

const MODEL_OPTIONS = [
  { id: 'gemini-3.7-flash', label: '♊ Gemini 3.7 Flash', desc: 'Google Vertex AI Flash Model' },
];

const SUGGESTED_PROMPTS = [
  'What is the difference between Equity and Mutual Funds?',
  'How do I calculate Debt-to-Equity ratio?',
  'Explain SEBI NISM certification requirements.',
  'What is a Covered Call options strategy?',
];

export default function FinGenIQChatbot() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome-1',
      sender: 'assistant',
      text: "ðŸ‘‹ Hello! I am **FinGenIQ AI Tutor** powered by **Google Gemini**.\n\nAsk me anything about financial education, investments, stock analysis, SEBI certifications, or budgeting!",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);
  const [input, setInput] = useState('');
  const [selectedModel, setSelectedModel] = useState('gemini-3.7-flash');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
      inputRef.current?.focus();
    }
  }, [isOpen, messages]);

  const handleSend = async (textToSend?: string) => {
    const queryText = (textToSend || input).trim();
    if (!queryText || isLoading) return;

    const userMsgId = `user-${Date.now()}`;
    const userMsg: Message = {
      id: userMsgId,
      sender: 'user',
      text: queryText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    const assistantMsgId = `assistant-${Date.now()}`;
    const assistantMsg: Message = {
      id: assistantMsgId,
      sender: 'assistant',
      text: '',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      modelUsed: selectedModel,
      isStreaming: true,
    };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: queryText,
          model: selectedModel,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      if (!response.body) {
        throw new Error('No response body received');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let accumulatedText = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.replace('data: ', '').trim();
            if (!dataStr) continue;
            try {
              const data = JSON.parse(dataStr);
              if (data.type === 'token' && data.content) {
                accumulatedText += data.content;
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMsgId
                      ? { ...msg, text: accumulatedText }
                      : msg
                  )
                );
              } else if (data.type === 'final_response' && data.content) {
                accumulatedText = data.content;
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMsgId
                      ? { ...msg, text: accumulatedText, isStreaming: false }
                      : msg
                  )
                );
              } else if (typeof data === 'string') {
                accumulatedText += data;
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMsgId
                      ? { ...msg, text: accumulatedText }
                      : msg
                  )
                );
              }
            } catch {
              // Plain text chunk fallback
              accumulatedText += dataStr;
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMsgId
                    ? { ...msg, text: accumulatedText }
                    : msg
                )
              );
            }
          }
        }
      }

      // Mark streaming done
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMsgId ? { ...msg, isStreaming: false } : msg
        )
      );
    } catch (err: any) {
      console.error('Chat error:', err);
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMsgId
            ? {
                ...msg,
                text: `âš ï¸ **Connection Error**: ${err.message || 'Unable to connect to AI server.'}`,
                isStreaming: false,
              }
            : msg
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      {/* Floating Widget Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          position: 'fixed',
          bottom: '24px',
          right: '24px',
          width: '56px',
          height: '56px',
          borderRadius: '50%',
          background: 'linear-gradient(135deg, #d4af37 0%, #aa7c11 100%)',
          color: '#0d0d0d',
          border: 'none',
          boxShadow: '0 8px 24px rgba(212, 175, 55, 0.35)',
          cursor: 'pointer',
          zIndex: 9999,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '24px',
          transition: 'transform 0.2s ease, boxShadow 0.2s ease',
        }}
        title="Open FinGenIQ AI Assistant"
        aria-label="Open AI Assistant"
      >
        {isOpen ? 'âœ•' : 'ðŸ’¬'}
      </button>

      {/* Chat Window Container */}
      {isOpen && (
        <div
          style={{
            position: 'fixed',
            bottom: '90px',
            right: '24px',
            width: '400px',
            maxWidth: 'calc(100vw - 32px)',
            height: '580px',
            maxHeight: 'calc(100vh - 120px)',
            backgroundColor: '#0f1115',
            border: '1px solid rgba(212, 175, 55, 0.25)',
            borderRadius: '16px',
            boxShadow: '0 16px 40px rgba(0, 0, 0, 0.6)',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            zIndex: 9999,
            fontFamily: 'Inter, system-ui, sans-serif',
          }}
        >
          {/* Header */}
          <div
            style={{
              padding: '14px 18px',
              background: 'linear-gradient(90deg, #161920 0%, #1a1e27 100%)',
              borderBottom: '1px solid rgba(212, 175, 55, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '8px',
                  background: 'rgba(212, 175, 55, 0.15)',
                  color: '#d4af37',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 'bold',
                  fontSize: '14px',
                }}
              >
                F
              </div>
              <div>
                <div style={{ color: '#f3f4f6', fontWeight: 600, fontSize: '14px' }}>
                  FinGenIQ AI Tutor
                </div>
                <div style={{ color: '#9ca3af', fontSize: '11px' }}>
                  Powered by Google Gemini
                </div>
              </div>
            </div>

            {/* Model Selector Dropdown */}
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              style={{
                backgroundColor: '#090a0d',
                color: '#d4af37',
                border: '1px solid rgba(212, 175, 55, 0.3)',
                borderRadius: '8px',
                padding: '4px 8px',
                fontSize: '11px',
                fontWeight: 500,
                outline: 'none',
                cursor: 'pointer',
              }}
            >
              {MODEL_OPTIONS.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.label}
                </option>
              ))}
            </select>
          </div>

          {/* Messages Area */}
          <div
            style={{
              flex: 1,
              padding: '16px',
              overflowY: 'auto',
              display: 'flex',
              flexDirection: 'column',
              gap: '12px',
              backgroundColor: '#090a0d',
            }}
          >
            {messages.map((msg) => (
              <div
                key={msg.id}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: msg.sender === 'user' ? 'flex-end' : 'flex-start',
                }}
              >
                <div
                  style={{
                    maxWidth: '85%',
                    padding: '10px 14px',
                    borderRadius:
                      msg.sender === 'user'
                        ? '14px 14px 2px 14px'
                        : '14px 14px 14px 2px',
                    backgroundColor:
                      msg.sender === 'user'
                        ? '#d4af37'
                        : '#161920',
                    color: msg.sender === 'user' ? '#0d0d0d' : '#e5e7eb',
                    fontSize: '13px',
                    lineHeight: '1.5',
                    border:
                      msg.sender === 'assistant'
                        ? '1px solid rgba(255, 255, 255, 0.08)'
                        : 'none',
                    wordBreak: 'break-word',
                    whiteSpace: 'pre-wrap',
                  }}
                >
                  {msg.text || (msg.isStreaming ? 'âš¡ Thinking...' : '')}
                </div>
                <div
                  style={{
                    fontSize: '10px',
                    color: '#6b7280',
                    marginTop: '3px',
                    padding: '0 4px',
                  }}
                >
                  {msg.timestamp}
                </div>
              </div>
            ))}

            {/* Suggested prompts on initial screen */}
            {messages.length === 1 && (
              <div style={{ marginTop: '12px' }}>
                <div style={{ fontSize: '11px', color: '#9ca3af', marginBottom: '8px' }}>
                  Suggested Questions:
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {SUGGESTED_PROMPTS.map((prompt, i) => (
                    <button
                      key={i}
                      onClick={() => handleSend(prompt)}
                      style={{
                        textAlign: 'left',
                        padding: '8px 12px',
                        backgroundColor: '#161920',
                        color: '#d1d5db',
                        border: '1px solid rgba(212, 175, 55, 0.15)',
                        borderRadius: '8px',
                        fontSize: '12px',
                        cursor: 'pointer',
                        transition: 'background 0.2s ease',
                      }}
                    >
                      ðŸ’¡ {prompt}
                    </button>
                  ))}
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div
            style={{
              padding: '12px 14px',
              backgroundColor: '#161920',
              borderTop: '1px solid rgba(212, 175, 55, 0.15)',
              display: 'flex',
              gap: '8px',
            }}
          >
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Ask FinGenIQ AI..."
              disabled={isLoading}
              style={{
                flex: 1,
                backgroundColor: '#090a0d',
                color: '#f3f4f6',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '8px',
                padding: '10px 12px',
                fontSize: '13px',
                outline: 'none',
              }}
            />
            <button
              onClick={() => handleSend()}
              disabled={isLoading || !input.trim()}
              style={{
                backgroundColor: input.trim() && !isLoading ? '#d4af37' : '#374151',
                color: input.trim() && !isLoading ? '#0d0d0d' : '#9ca3af',
                border: 'none',
                borderRadius: '8px',
                padding: '0 16px',
                fontWeight: 600,
                fontSize: '13px',
                cursor: input.trim() && !isLoading ? 'pointer' : 'default',
              }}
            >
              Send
            </button>
          </div>
        </div>
      )}
    </>
  );
}
