import { StreamChunk, EffortLevel } from '@/types';

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
  
  const token = authToken || getStoredToken();
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
    if (signal?.aborted) throw err;
    response = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
      signal,
    });
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
    const payload = {
      rating,
      conversation_id: conversationId || null,
      correction: correction || '',
      query: query || '',
      response: response || '',
      model_name: modelName,
      timestamp: Date.now(),
    };

    const res = await fetch('/api/rlhf', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders(),
      },
      body: JSON.stringify(payload),
    });

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

function markdownToSimpleHtml(markdown: string): string {
  if (!markdown) return '';

  // Extract and preserve code blocks safely
  const codeBlocks: string[] = [];
  let html = markdown.replace(/```(\w+)?\n([\s\S]*?)```/g, (_m, _lang, code) => {
    const placeholder = `__CODE_BLOCK_${codeBlocks.length}__`;
    codeBlocks.push(
      `<pre style="background: #1e1e1e; color: #d4d4d4; padding: 14px; border-radius: 8px; font-family: Consolas, Monaco, monospace; font-size: 13px; overflow-x: auto; margin: 16px 0;"><code>${escapeHtml(code.trim())}</code></pre>`
    );
    return placeholder;
  });

  // Extract and preserve inline code
  const inlineCodes: string[] = [];
  html = html.replace(/`([^`]+)`/g, (_m, code) => {
    const placeholder = `__INLINE_CODE_${inlineCodes.length}__`;
    inlineCodes.push(
      `<code style="background: #f1f5f9; color: #d97706; padding: 2px 6px; border-radius: 4px; font-family: monospace; font-size: 0.9em; border: 1px solid #e2e8f0;">${escapeHtml(code)}</code>`
    );
    return placeholder;
  });

  // Escape HTML in the remaining text before formatting
  html = escapeHtml(html);

  // Headers
  html = html.replace(/^### (.*$)/gim, '<h3 style="color: #0f172a; font-size: 16px; font-weight: 700; margin: 18px 0 8px;">$1</h3>');
  html = html.replace(/^## (.*$)/gim, '<h2 style="color: #0f172a; font-size: 20px; font-weight: 700; margin: 22px 0 10px; border-bottom: 1px solid #e2e8f0; padding-bottom: 6px;">$1</h2>');
  html = html.replace(/^# (.*$)/gim, '<h1 style="color: #0f172a; font-size: 24px; font-weight: 800; margin: 26px 0 12px; border-bottom: 2px solid #cbd5e1; padding-bottom: 8px;">$1</h1>');

  // Blockquotes
  html = html.replace(/^&gt; (.*$)/gim, '<blockquote style="border-left: 4px solid #d97706; background: #fef3c7; color: #92400e; padding: 10px 14px; margin: 14px 0; border-radius: 0 6px 6px 0;">$1</blockquote>');

  // Bold & Italic
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');

  // Lists
  html = html.replace(/^\s*-\s+(.*$)/gim, '<li style="margin-bottom: 4px;">$1</li>');
  html = html.replace(/^\s*\*\s+(.*$)/gim, '<li style="margin-bottom: 4px;">$1</li>');
  html = html.replace(/^\s*(\d+)\.\s+(.*$)/gim, '<li style="margin-bottom: 4px;">$2</li>');

  // Wrap lists
  html = html.replace(/(<li[\s\S]*<\/li>)/gm, '<ul style="padding-left: 24px; margin: 12px 0;">$1</ul>');

  // Paragraphs
  const paragraphs = html.split(/\n\n+/);
  html = paragraphs
    .map(p => {
      const trimmed = p.trim();
      if (!trimmed) return '';
      if (trimmed.startsWith('<h') || trimmed.startsWith('<pre') || trimmed.startsWith('<ul') || trimmed.startsWith('<blockquote') || trimmed.startsWith('__CODE_BLOCK_')) {
        return trimmed;
      }
      return `<p style="margin: 0 0 12px; line-height: 1.65; color: #334155;">${trimmed.replace(/\n/g, '<br/>')}</p>`;
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
 * Export response to PDF
 */
export function exportToPdf(options: {
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

  const printWindow = window.open('', '_blank');
  if (!printWindow) {
    alert('Please allow popups to export the PDF document.');
    return;
  }

  const documentHtml = `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>${escapeHtml(options.title)} — Aarka AI</title>
  <style>
    @page {
      size: A4;
      margin: 20mm 15mm 20mm 15mm;
      @top-left {
        content: "AARKA AI — CONVERSATIONAL INTELLIGENCE";
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        font-size: 8px;
        font-weight: 700;
        color: #94a3b8;
      }
      @bottom-right {
        content: "Page " counter(page) " of " counter(pages);
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        font-size: 8px;
        color: #94a3b8;
      }
    }
    * { box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      color: #1e293b;
      background: #ffffff;
      line-height: 1.6;
      padding: 28px;
      max-width: 800px;
      margin: 0 auto;
    }
    .header {
      border-bottom: 2px solid #e2e8f0;
      padding-bottom: 16px;
      margin-bottom: 24px;
    }
    .brand {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 8px;
    }
    .brand-title {
      font-size: 20px;
      font-weight: 800;
      color: #0f172a;
      letter-spacing: -0.5px;
    }
    .brand-accent {
      color: #d97706;
    }
    .meta-tag {
      font-size: 11px;
      font-weight: 600;
      color: #64748b;
      background: #f1f5f9;
      padding: 4px 10px;
      border-radius: 9999px;
      border: 1px solid #e2e8f0;
    }
    .doc-title {
      font-size: 22px;
      font-weight: 800;
      color: #0f172a;
      margin: 0 0 6px 0;
      line-height: 1.3;
    }
    .doc-date {
      font-size: 12px;
      color: #64748b;
      margin: 0;
    }
    .content {
      font-size: 14px;
      color: #334155;
    }
    .footer {
      margin-top: 36px;
      border-top: 1px solid #e2e8f0;
      padding-top: 12px;
      font-size: 11px;
      color: #94a3b8;
      display: flex;
      justify-content: space-between;
    }
    @media print {
      body { padding: 0; }
    }
  </style>
</head>
<body>
  <div class="header">
    <div class="brand">
      <div class="brand-title">Aarka <span class="brand-accent">AI</span></div>
      <div class="meta-tag">${escapeHtml(options.modelUsed || 'Aarka AI')}</div>
    </div>
    <h1 class="doc-title">${escapeHtml(options.title)}</h1>
    <p class="doc-date">Generated on ${escapeHtml(dateStr)}</p>
  </div>

  <div class="content">
    ${bodyHtml}
  </div>

  <div class="footer">
    <span>© 2026 Aarka AI. High-Precision Conversational Intelligence.</span>
    <span>CONFIDENTIAL & VERIFIED</span>
  </div>

  <script>
    window.onload = function() {
      setTimeout(function() {
        window.print();
      }, 300);
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
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  const token = getStoredToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch('/api/settings', {
    method: 'GET',
    headers,
  });

  if (!res.ok) {
    throw new Error('Failed to fetch settings');
  }

  return res.json();
}

/**
 * Update User Settings in Backend
 */
export async function updateSettingsApi(settings: Record<string, any>): Promise<any> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  const token = getStoredToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch('/api/settings', {
    method: 'PUT',
    headers,
    body: JSON.stringify(settings),
  });

  if (!res.ok) {
    throw new Error('Failed to update settings');
  }

  return res.json();
}

