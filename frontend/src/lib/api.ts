import { StreamChunk, EffortLevel, ToolApprovalRequest, McpServerInfo } from '@/types';

const API_BASE = '/api';

export function getStoredToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('aarka-token') || localStorage.getItem('aarkaa-token');
}

export function storeToken(token: string): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem('aarka-token', token);
  }
}

export const setStoredToken = storeToken;

export function clearToken(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('aarka-token');
    localStorage.removeItem('aarkaa-token');
  }
}

export async function fetchVisitorToken(): Promise<{ access_token: string; token_type: string; user_id: string; name?: string }> {
  const res = await fetch('/auth/visitor-token', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });
  if (!res.ok) {
    throw new Error(`Visitor token request failed: HTTP ${res.status}`);
  }
  return res.json();
}

export async function* streamChat(
  query: string,
  sessionId: string,
  modelOverride?: string,
  effort?: EffortLevel,
  authToken?: string | null,
  signal?: AbortSignal
): AsyncGenerator<StreamChunk> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'Accept': 'text/event-stream',
  };
  
  let token = authToken || getStoredToken();
  if (!token) {
    try {
      const visitor = await fetchVisitorToken();
      if (visitor?.access_token) {
        token = visitor.access_token;
        storeToken(token);
      }
    } catch (e) {
      console.warn('Fallback visitor token fetch failed:', e);
    }
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const payload = {
    query,
    session_id: sessionId,
    model_override: modelOverride,
    effort: effort || 'medium',
    mode: effort === 'high' ? 'deep_reasoning' : 'production',
  };

  let response: Response;
  try {
    response = await fetch('/prompt/stream', {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
      signal,
    });
  } catch (err: any) {
    // Network error on /prompt/stream — rethrow so callers can surface a proper error message.
    throw err;
  }

  // If token is expired or unauthorized, automatically fetch a fresh visitor token and retry once
  if (response.status === 401) {
    clearToken();
    try {
      const visitor = await fetchVisitorToken();
      if (visitor?.access_token) {
        token = visitor.access_token;
        storeToken(token);
        headers['Authorization'] = `Bearer ${token}`;
        response = await fetch('/prompt/stream', {
          method: 'POST',
          headers,
          body: JSON.stringify(payload),
          signal,
        });
      }
    } catch (refreshErr) {
      console.warn('Auto token refresh on 401 failed:', refreshErr);
    }
  }

  if (!response.ok) {
    const errorText = await response.text().catch(() => `HTTP ${response.status}`);
    throw new Error(`Server returned status ${response.status}: ${errorText}`);
  }

  if (!response.body) {
    throw new Error('ReadableStream not supported.');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed.startsWith('data: ')) {
          const dataStr = trimmed.substring(6).trim();
          if (dataStr === '[DONE]') continue;
          try {
            const parsed: StreamChunk = JSON.parse(dataStr);
            if (!parsed.type && (parsed as any).event_type) {
              parsed.type = (parsed as any).event_type;
            }
            yield parsed;
          } catch (err) {
            console.warn('Non-JSON SSE chunk received:', dataStr);
          }
        }
      }
    }
  } catch (err) {
    try {
      await reader.cancel();
    } catch (_) {}
    throw err;
  } finally {
    reader.releaseLock();
  }
}

export function getAuthHeaders(): Record<string, string> {
  const token = getStoredToken();
  if (token) {
    return { Authorization: `Bearer ${token}` };
  }
  return {};
}

/**
 * Submit RLHF Feedback (Thumbs Up / Down)
 */
export async function submitFeedbackApi(
  rating: number,
  conversationId?: string | null,
  correction?: string,
  query?: string,
  response?: string,
  modelName: string = 'aarkaa-2.0'
): Promise<{ status: string; rlhf_id?: string }> {
  try {
    let token = getStoredToken();
    if (!token) {
      try {
        const visitor = await fetchVisitorToken();
        if (visitor?.access_token) {
          token = visitor.access_token;
          storeToken(token);
        }
      } catch (e) {
        console.warn('Fallback visitor token fetch failed for feedback:', e);
      }
    }

    const payload = {
      rating,
      conversation_id: conversationId || null,
      correction: correction && correction.trim() ? correction.trim() : null,
      query: query || '',
      response: response || '',
      model_name: modelName,
      timestamp: Date.now(),
    };

    let res = await fetch('/api/rlhf', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : getAuthHeaders()),
      },
      body: JSON.stringify(payload),
    });

    if (res.status === 401) {
      clearToken();
      try {
        const visitor = await fetchVisitorToken();
        if (visitor?.access_token) {
          token = visitor.access_token;
          storeToken(token);
          res = await fetch('/api/rlhf', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify(payload),
          });
        }
      } catch (retryErr) {
        console.warn('Visitor token refresh retry failed:', retryErr);
      }
    }

    if (!res.ok) {
      throw new Error(`Feedback failed with HTTP ${res.status}`);
    }

    return await res.json();
  } catch (err) {
    console.error('Error submitting RLHF feedback:', err);
    return { status: 'error' };
  }
}

function escapeHtml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

export type PdfTemplateId = 'gold' | 'indigo' | 'emerald' | 'crimson' | 'dark';

export interface PdfTemplateConfig {
  name: string;
  badge: string;
  bg: string;
  cardBg: string;
  cardBorder: string;
  textPrimary: string;
  textSecondary: string;
  accent: string;
  accentMuted: string;
  codeBg: string;
  codeBorder: string;
  tableHeaderBg: string;
  blockquoteBg: string;
  blockquoteBorder: string;
  blockquoteText: string;
  gradient: string;
}

export const PDF_TEMPLATES: Record<PdfTemplateId, PdfTemplateConfig> = {
  gold: {
    name: 'Executive Gold',
    badge: 'CONFIDENTIAL EXECUTIVE BRIEF',
    bg: '#0f172a',
    cardBg: '#1e293b',
    cardBorder: '#334155',
    textPrimary: '#f8fafc',
    textSecondary: '#94a3b8',
    accent: '#f59e0b',
    accentMuted: 'rgba(245, 158, 11, 0.15)',
    codeBg: '#090d16',
    codeBorder: '#334155',
    tableHeaderBg: '#1e293b',
    blockquoteBg: 'rgba(245, 158, 11, 0.08)',
    blockquoteBorder: '#f59e0b',
    blockquoteText: '#fde68a',
    gradient: 'linear-gradient(135deg, #020617 0%, #0f172a 50%, #1e293b 100%)',
  },
  indigo: {
    name: 'Enterprise Indigo',
    badge: 'OFFICIAL ENTERPRISE REPORT',
    bg: '#ffffff',
    cardBg: '#f8fafc',
    cardBorder: '#e2e8f0',
    textPrimary: '#0f172a',
    textSecondary: '#475569',
    accent: '#4f46e5',
    accentMuted: 'rgba(79, 70, 229, 0.1)',
    codeBg: '#1e1e2e',
    codeBorder: '#e2e8f0',
    tableHeaderBg: '#f1f5f9',
    blockquoteBg: '#f8fafc',
    blockquoteBorder: '#4f46e5',
    blockquoteText: '#312e81',
    gradient: 'linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%)',
  },
  emerald: {
    name: 'Venture Emerald',
    badge: 'VENTURE & GROWTH MEMO',
    bg: '#042f2e',
    cardBg: '#064e3b',
    cardBorder: '#0f766e',
    textPrimary: '#f0fdfa',
    textSecondary: '#99f6e4',
    accent: '#10b981',
    accentMuted: 'rgba(16, 185, 129, 0.15)',
    codeBg: '#021e1a',
    codeBorder: '#0f766e',
    tableHeaderBg: '#064e3b',
    blockquoteBg: 'rgba(16, 185, 129, 0.1)',
    blockquoteBorder: '#10b981',
    blockquoteText: '#a7f3d0',
    gradient: 'linear-gradient(135deg, #042f2e 0%, #064e3b 100%)',
  },
  crimson: {
    name: 'Risk & Healthcare Crimson',
    badge: 'RISK & COMPLIANCE ASSESSMENT',
    bg: '#270808',
    cardBg: '#450a0a',
    cardBorder: '#7f1d1d',
    textPrimary: '#fff1f2',
    textSecondary: '#fecdd3',
    accent: '#f43f5e',
    accentMuted: 'rgba(244, 63, 94, 0.15)',
    codeBg: '#1a0505',
    codeBorder: '#7f1d1d',
    tableHeaderBg: '#450a0a',
    blockquoteBg: 'rgba(244, 63, 94, 0.1)',
    blockquoteBorder: '#f43f5e',
    blockquoteText: '#fecdd3',
    gradient: 'linear-gradient(135deg, #270808 0%, #450a0a 100%)',
  },
  dark: {
    name: 'Cyber Dark',
    badge: 'TECHNICAL DEEP DIVE',
    bg: '#020617',
    cardBg: '#0b1329',
    cardBorder: '#1e293b',
    textPrimary: '#f8fafc',
    textSecondary: '#94a3b8',
    accent: '#06b6d4',
    accentMuted: 'rgba(6, 182, 212, 0.15)',
    codeBg: '#050b18',
    codeBorder: '#1e293b',
    tableHeaderBg: '#0b1329',
    blockquoteBg: 'rgba(6, 182, 212, 0.08)',
    blockquoteBorder: '#06b6d4',
    blockquoteText: '#a5f3fc',
    gradient: 'linear-gradient(135deg, #020617 0%, #0f172a 100%)',
  },
};

function markdownToSimpleHtml(markdown: string, theme: PdfTemplateConfig = PDF_TEMPLATES.gold): string {
  if (!markdown) return '';

  // Extract and preserve code blocks safely
  const codeBlocks: string[] = [];
  let html = markdown.replace(/```(\w+)?\n([\s\S]*?)```/g, (_m, _lang, code) => {
    const placeholder = `__CODE_BLOCK_${codeBlocks.length}__`;
    codeBlocks.push(
      `<pre style="background: ${theme.codeBg} !important; color: ${theme.textPrimary} !important; padding: 14px; border-radius: 8px; font-family: Consolas, Monaco, monospace; font-size: 12px; overflow-x: auto; margin: 16px 0; border: 1px solid ${theme.codeBorder};"><code>${escapeHtml(code.trim())}</code></pre>`
    );
    return placeholder;
  });

  // Extract and preserve inline code
  const inlineCodes: string[] = [];
  html = html.replace(/`([^`]+)`/g, (_m, code) => {
    const placeholder = `__INLINE_CODE_${inlineCodes.length}__`;
    inlineCodes.push(
      `<code style="background: ${theme.cardBg} !important; color: ${theme.accent} !important; padding: 2px 6px; border-radius: 4px; font-family: monospace; font-size: 0.9em; border: 1px solid ${theme.cardBorder};">${escapeHtml(code)}</code>`
    );
    return placeholder;
  });

  // Escape HTML in the remaining text before formatting
  html = escapeHtml(html);

  // Parse Markdown Tables
  html = html.replace(
    /((?:\|[^\n]+\|\r?\n)+)/g,
    (tableText) => {
      const rows = tableText.trim().split(/\r?\n/);
      if (rows.length < 2) return tableText;
      const isDelimiter = (r: string) => /^\|(\s*:?-+:?\s*\|)+$/.test(r.trim());
      if (!isDelimiter(rows[1])) return tableText;

      const parseCells = (r: string) =>
        r.split('|').slice(1, -1).map(c => c.trim());

      const headers = parseCells(rows[0]);
      const headerHtml = `<thead><tr>${headers.map(h => `<th style="background:${theme.tableHeaderBg} !important; color:${theme.accent} !important; padding:8px 10px; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.5px; border-bottom:2px solid ${theme.cardBorder}; text-align:left;">${h}</th>`).join('')}</tr></thead>`;

      const bodyRows = rows.slice(2).filter(r => r.trim().startsWith('|'));
      const bodyHtml = `<tbody>${bodyRows.map(r => {
        const cells = parseCells(r);
        return `<tr>${cells.map(c => `<td style="padding:7px 10px; font-size:12px; color:${theme.textSecondary} !important; border-bottom:1px solid ${theme.cardBorder};">${c}</td>`).join('')}</tr>`;
      }).join('')}</tbody>`;

      return `<div style="overflow-x:auto; margin:16px 0; border:1px solid ${theme.cardBorder}; border-radius:8px;"><table style="width:100%; border-collapse:collapse;">${headerHtml}${bodyHtml}</table></div>`;
    }
  );

  // Headers
  html = html.replace(/^### (.*$)/gim, `<h3 style="color: ${theme.accent} !important; font-size: 14px; font-weight: 700; margin: 18px 0 8px; text-transform: uppercase; letter-spacing: 0.5px;">$1</h3>`);
  html = html.replace(/^## (.*$)/gim, `<h2 style="color: ${theme.textPrimary} !important; font-size: 18px; font-weight: 700; margin: 22px 0 10px; border-bottom: 1px solid ${theme.cardBorder}; padding-bottom: 6px;">$1</h2>`);
  html = html.replace(/^# (.*$)/gim, `<h1 style="color: ${theme.textPrimary} !important; font-size: 22px; font-weight: 800; margin: 26px 0 12px; border-bottom: 2px solid ${theme.accent}; padding-bottom: 8px;"><span style="color:${theme.accent} !important;">$1</span></h1>`);

  // Blockquotes
  html = html.replace(/^&gt; (.*$)/gim, `<blockquote style="border-left: 4px solid ${theme.blockquoteBorder} !important; background: ${theme.blockquoteBg} !important; color: ${theme.blockquoteText} !important; padding: 10px 14px; margin: 14px 0; border-radius: 0 6px 6px 0; font-size: 12.5px;">$1</blockquote>`);

  // Bold & Italic
  html = html.replace(/\*\*([^*]+)\*\*/g, `<strong style="color: ${theme.textPrimary} !important;">$1</strong>`);
  html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');

  // Lists
  html = html.replace(/^\s*-\s+(.*$)/gim, `<li style="margin-bottom: 4px; color:${theme.textSecondary} !important;">$1</li>`);
  html = html.replace(/^\s*\*\s+(.*$)/gim, `<li style="margin-bottom: 4px; color:${theme.textSecondary} !important;">$1</li>`);
  html = html.replace(/^\s*(\d+)\.\s+(.*$)/gim, `<li style="margin-bottom: 4px; color:${theme.textSecondary} !important;">$2</li>`);

  // Wrap lists
  html = html.replace(/(<li[\s\S]*<\/li>)/gm, '<ul style="padding-left: 24px; margin: 12px 0;">$1</ul>');

  // Paragraphs
  const paragraphs = html.split(/\n\n+/);
  html = paragraphs
    .map(p => {
      const trimmed = p.trim();
      if (!trimmed) return '';
      if (trimmed.startsWith('<h') || trimmed.startsWith('<pre') || trimmed.startsWith('<ul') || trimmed.startsWith('<blockquote') || trimmed.startsWith('<div') || trimmed.startsWith('__CODE_BLOCK_')) {
        return trimmed;
      }
      return `<p style="margin: 0 0 12px; line-height: 1.7; color: ${theme.textSecondary} !important; font-size: 13px;">${trimmed.replace(/\n/g, '<br/>')}</p>`;
    })
    .join('\n');

  // Restore code blocks
  codeBlocks.forEach((code, idx) => {
    html = html.replace(`__CODE_BLOCK_${idx}__`, code);
  });
  inlineCodes.forEach((code, idx) => {
    html = html.replace(`__INLINE_CODE_${idx}__`, code);
  });

  return html;
}

/**
 * Export response to PDF with customizable template style
 */
export function exportToPdf(options: {
  title: string;
  content: string;
  modelUsed?: string;
  timestamp?: number | string;
  template?: PdfTemplateId;
}) {
  const selectedTemplate = options.template || 'gold';
  const theme = PDF_TEMPLATES[selectedTemplate] || PDF_TEMPLATES.gold;

  const dateStr = new Date(options.timestamp || Date.now()).toLocaleString('en-US', {
    dateStyle: 'medium',
    timeStyle: 'short',
  });

  const bodyHtml = markdownToSimpleHtml(options.content, theme);

  const printWindow = window.open('', '_blank');
  if (!printWindow) {
    alert('Please allow popups to export the PDF document.');
    return;
  }

  // Determine if this is a dark theme (bg is dark) — needed for print fallback
  const isDarkTheme = theme.bg !== '#ffffff';

  const documentHtml = `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>${escapeHtml(options.title)} — Aarka AI</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    @page {
      size: A4;
      margin: 14mm 15mm 14mm 15mm;
    }
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      -webkit-print-color-adjust: exact !important;
      print-color-adjust: exact !important;
      color-adjust: exact !important;
    }
    html {
      background: ${theme.bg} !important;
    }
    body {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      color: ${theme.textPrimary} !important;
      background: ${theme.bg} !important;
      line-height: 1.65;
      padding: 0;
      margin: 0;
      -webkit-print-color-adjust: exact !important;
      print-color-adjust: exact !important;
      color-adjust: exact !important;
    }
    /* Full-bleed background wrapper to force dark backgrounds in PDF print */
    .page-wrapper {
      background: ${theme.bg} !important;
      color: ${theme.textPrimary} !important;
      min-height: 100vh;
      padding: 24px 30px;
      max-width: 860px;
      margin: 0 auto;
    }
    .header {
      border-bottom: 1px solid ${theme.cardBorder};
      padding-bottom: 16px;
      margin-bottom: 24px;
    }
    .brand {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 10px;
    }
    .brand-title {
      font-size: 18px;
      font-weight: 800;
      letter-spacing: 1.5px;
      color: ${theme.accent} !important;
      text-transform: uppercase;
    }
    .badge {
      display: inline-block;
      padding: 3px 9px;
      border-radius: 9999px;
      font-size: 8px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      background: ${theme.accentMuted} !important;
      color: ${theme.accent} !important;
      border: 1px solid ${theme.accent};
    }
    .divider {
      height: 2px;
      background: linear-gradient(90deg, ${theme.accent}, ${theme.cardBorder}, transparent) !important;
      margin: 8px 0 16px;
    }
    .doc-title {
      font-size: 22px;
      font-weight: 800;
      color: ${theme.textPrimary} !important;
      margin: 0 0 6px 0;
      letter-spacing: -0.5px;
    }
    .meta-row {
      display: flex;
      align-items: center;
      gap: 12px;
      font-size: 11px;
      color: ${theme.textSecondary} !important;
    }
    .meta-tag {
      background: ${theme.cardBg} !important;
      padding: 2px 8px;
      border-radius: 6px;
      border: 1px solid ${theme.cardBorder};
      color: ${theme.accent} !important;
      font-weight: 600;
      font-size: 10px;
    }
    .content {
      font-size: 13px;
      color: ${theme.textSecondary} !important;
    }
    .content p {
      color: ${theme.textSecondary} !important;
    }
    .content h1, .content h2 {
      color: ${theme.textPrimary} !important;
    }
    .content h3 {
      color: ${theme.accent} !important;
    }
    .content strong {
      color: ${theme.textPrimary} !important;
    }
    .content li {
      color: ${theme.textSecondary} !important;
    }
    .content pre {
      background: ${theme.codeBg} !important;
      color: ${theme.textPrimary} !important;
    }
    .content blockquote {
      background: ${theme.blockquoteBg} !important;
      color: ${theme.blockquoteText} !important;
      border-left-color: ${theme.blockquoteBorder} !important;
    }
    .content table th {
      background: ${theme.tableHeaderBg} !important;
      color: ${theme.accent} !important;
    }
    .content table td {
      color: ${theme.textSecondary} !important;
    }
    .footer {
      margin-top: 40px;
      border-top: 1px solid ${theme.cardBorder};
      padding-top: 12px;
      font-size: 9.5px;
      color: ${theme.textSecondary} !important;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    @media print {
      html, body {
        background: ${theme.bg} !important;
        color: ${theme.textPrimary} !important;
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
        color-adjust: exact !important;
      }
      .page-wrapper {
        background: ${theme.bg} !important;
        padding: 0;
      }
      table, pre, blockquote { page-break-inside: avoid; }
      h1, h2, h3 { page-break-after: avoid; }
    }
  </style>
</head>
<body>
  <div class="page-wrapper">
    <div class="header">
      <div class="brand">
        <div class="brand-title">AARKAAI · ${escapeHtml(theme.name)}</div>
        <div class="badge">${escapeHtml(theme.badge)}</div>
      </div>
      <div class="divider"></div>
      <h1 class="doc-title">${escapeHtml(options.title)}</h1>
      <div class="meta-row">
        <span>Generated: ${escapeHtml(dateStr)}</span>
        <span>•</span>
        <span class="meta-tag">${escapeHtml(options.modelUsed || 'Aarka AI 2.0')}</span>
        <span>•</span>
        <span>Verified Autonomous Delivery</span>
      </div>
    </div>

    <div class="content">
      ${bodyHtml}
    </div>

    <div class="footer">
      <span>© 2026 AARKAAI. Precision Conversational Intelligence & Research Systems.</span>
      <span>STRICTLY CONFIDENTIAL · ARCHIVAL GRADE</span>
    </div>
  </div>

  <script>
    window.onload = function() {
      setTimeout(function() {
        window.print();
      }, 350);
    };
  </script>
</body>
</html>`;

  printWindow.document.open();
  printWindow.document.write(documentHtml);
  printWindow.document.close();
}

/**
 * Export response to Word DOC
 */
export function exportToWord(options: {
  title: string;
  content: string;
  modelUsed?: string;
  timestamp?: number | string;
}) {
  const dateStr = new Date(options.timestamp || Date.now()).toLocaleString('en-US', {
    dateStyle: 'medium',
    timeStyle: 'short',
  });

  const bodyHtml = markdownToSimpleHtml(options.content);

  const wordContent = `
<html xmlns:o='urn:schemas-microsoft-com:office:office' xmlns:w='urn:schemas-microsoft-com:office:word' xmlns='http://www.w3.org/TR/REC-html40'>
<head>
  <meta charset="utf-8">
  <title>${escapeHtml(options.title)}</title>
  <!--[if gte mso 9]>
  <xml>
  <w:WordDocument>
    <w:View>Print</w:View>
    <w:Zoom>100</w:Zoom>
    <w:DoNotOptimizeForBrowser/>
  </w:WordDocument>
  </xml>
  <![endif]-->
  <style>
    body {
      font-family: Arial, "Helvetica Neue", sans-serif;
      font-size: 11pt;
      line-height: 1.5;
      color: #1a1a1a;
      margin: 1in;
    }
    h1 { font-size: 18pt; font-weight: bold; color: #0f172a; margin-top: 18pt; margin-bottom: 6pt; }
    h2 { font-size: 14pt; font-weight: bold; color: #1e293b; margin-top: 14pt; margin-bottom: 4pt; }
    h3 { font-size: 12pt; font-weight: bold; color: #334155; margin-top: 10pt; margin-bottom: 2pt; }
    p { margin-bottom: 8pt; text-align: justify; }
    pre { background: #f1f5f9; padding: 8pt; border: 1pt solid #cbd5e1; font-family: Consolas, monospace; font-size: 9pt; }
    code { font-family: Consolas, monospace; font-size: 9.5pt; color: #d97706; }
    blockquote { border-left: 3pt solid #d97706; padding-left: 8pt; margin-left: 0; color: #92400e; font-style: italic; }
    table { border-collapse: collapse; width: 100%; margin: 10pt 0; }
    th, td { border: 1pt solid #cbd5e1; padding: 6pt; text-align: left; }
    th { background-color: #f8fafc; font-weight: bold; }
    .header-bar { border-bottom: 2pt solid #d97706; padding-bottom: 8pt; margin-bottom: 16pt; }
  </style>
</head>
<body>
  <div class="header-bar">
    <h1 style="margin: 0; color: #0f172a;">Aarka AI — ${escapeHtml(options.title)}</h1>
    <p style="font-size: 9pt; color: #64748b; margin-top: 4pt;">Model: ${escapeHtml(options.modelUsed || 'Aarka AI')} | Generated: ${escapeHtml(dateStr)}</p>
  </div>
  ${bodyHtml}
</body>
</html>`;

  const blob = new Blob(['\ufeff', wordContent], {
    type: 'application/msword',
  });

  const cleanFilename = (options.title || 'Aarka_AI_Document')
    .replace(/[^a-zA-Z0-9_-]/g, '_')
    .substring(0, 40);

  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${cleanFilename}_${Date.now()}.doc`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/**
 * Export response to Markdown
 */
export function exportToMarkdown(title: string, content: string) {
  const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
  const cleanFilename = (title || 'Aarka_AI_Document')
    .replace(/[^a-zA-Z0-9_-]/g, '_')
    .substring(0, 40);

  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${cleanFilename}_${Date.now()}.md`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/**
 * Fetch User Settings from Backend
 */
export async function fetchSettingsApi(): Promise<any> {
  const token = getStoredToken();
  if (!token) {
    return {};
  }
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
  };

  try {
    const res = await fetch('/api/settings', {
      method: 'GET',
      headers,
    });

    if (!res.ok) {
      return {};
    }

    return res.json();
  } catch (e) {
    return {};
  }
}

/**
 * Update User Settings in Backend
 */
export async function updateSettingsApi(settings: Record<string, any>): Promise<any> {
  const token = getStoredToken();
  if (!token) {
    throw new Error('Not authenticated. Settings saved locally only.');
  }
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
  };

  const res = await fetch('/api/settings', {
    method: 'PUT',
    headers,
    body: JSON.stringify(settings),
  });

  if (!res.ok) {
    const errorBody = await res.text().catch(() => 'Unknown error');
    throw new Error(`Failed to save settings (${res.status}): ${errorBody}`);
  }

  return res.json();
}

/**
 * Submit interactive approval or rejection decision for a pending tool mutation
 */
export async function submitToolApproval(
  approvalId: string,
  decision: 'approve' | 'deny',
  reason?: string,
  selectedMasterStrategy?: string
): Promise<{ status: string; approval_id: string; resolution: string; message?: string }> {
  // Client-intercepted gate IDs bypass backend POST to avoid unnecessary network latency or 404
  if (
    approvalId.startsWith('cmd-gate-') ||
    approvalId.startsWith('file-gate-') ||
    approvalId.startsWith('fin-gate-') ||
    approvalId.startsWith('local-gate-') ||
    approvalId.startsWith('client-gate-')
  ) {
    return {
      status: decision === 'approve' ? 'approved' : 'rejected',
      approval_id: approvalId,
      resolution: decision,
      message: 'Local gate resolved directly',
    };
  }
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...getAuthHeaders(),
  };

  const res = await fetch('/codemode/approve', {
    method: 'POST',
    headers,
    body: JSON.stringify({
      approval_id: approvalId,
      decision,
      reason,
      selected_master_strategy: selectedMasterStrategy,
    }),
  });

  if (!res.ok) {
    const errText = await res.text().catch(() => `HTTP ${res.status}`);
    throw new Error(`Approval submission failed (${res.status}): ${errText}`);
  }

  return res.json();
}

/**
 * Fetch connected MCP servers, tool manifests, permissions, and status
 */
export async function fetchMcpServers(): Promise<{ status: string; servers: McpServerInfo[] }> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...getAuthHeaders(),
  };

  const res = await fetch('/mcp/servers', {
    method: 'GET',
    headers,
  });

  if (!res.ok) {
    const errText = await res.text().catch(() => `HTTP ${res.status}`);
    throw new Error(`Failed to fetch MCP servers (${res.status}): ${errText}`);
  }

  return res.json();
}

/**
 * Toggle an MCP server (enable/disable) with active execution lock protection
 */
export async function toggleMcpServer(
  serverId: string,
  enabled: boolean
): Promise<{ status: string; server: McpServerInfo }> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...getAuthHeaders(),
  };

  const res = await fetch('/mcp/toggle', {
    method: 'POST',
    headers,
    body: JSON.stringify({
      server_id: serverId,
      enabled,
    }),
  });

  if (!res.ok) {
    const errText = await res.text().catch(() => `HTTP ${res.status}`);
    throw new Error(`Failed to toggle MCP server (${res.status}): ${errText}`);
  }

  return res.json();
}

