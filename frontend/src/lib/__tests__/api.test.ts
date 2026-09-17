import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  getStoredToken,
  storeToken,
  clearToken,
  fetchVisitorToken,
  streamChat,
  submitToolApproval,
  fetchMcpServers,
  toggleMcpServer,
} from '../api';

describe('Frontend Auth Token Persistence', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('stores and retrieves the JWT token correctly', () => {
    expect(getStoredToken()).toBeNull();

    storeToken('test-access-token-12345');
    expect(getStoredToken()).toBe('test-access-token-12345');
    expect(localStorage.setItem).toHaveBeenCalledWith('aarka-token', 'test-access-token-12345');
  });

  it('clears stored tokens on logout', () => {
    storeToken('temporary-token');
    expect(getStoredToken()).toBe('temporary-token');

    clearToken();
    expect(getStoredToken()).toBeNull();
    expect(localStorage.removeItem).toHaveBeenCalledWith('aarka-token');
  });
});

describe('fetchVisitorToken API Client', () => {
  it('requests visitor token and returns payload on 200 OK', async () => {
    const mockVisitorResponse = {
      access_token: 'mock-visitor-jwt',
      token_type: 'bearer',
      user_id: 'guest_visitor_123',
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockVisitorResponse,
    });

    const data = await fetchVisitorToken();
    expect(data.access_token).toBe('mock-visitor-jwt');
    expect(data.user_id).toBe('guest_visitor_123');
    expect(global.fetch).toHaveBeenCalledWith('/auth/visitor-token', expect.objectContaining({
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    }));
  });

  it('throws an error when visitor token endpoint returns non-200', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 503,
    });

    await expect(fetchVisitorToken()).rejects.toThrow('Visitor token request failed: HTTP 503');
  });
});

describe('streamChat SSE Parser', () => {
  it('yields content tokens from valid SSE stream', async () => {
    storeToken('authenticated-user-token');

    const sseLines = [
      'data: {"type": "content", "token": "Hello "}\n\n',
      'data: {"type": "content", "token": "world!"}\n\n',
      'data: {"type": "done", "finish_reason": "stop"}\n\n',
    ];

    const stream = new ReadableStream({
      start(controller) {
        for (const line of sseLines) {
          controller.enqueue(new TextEncoder().encode(line));
        }
        controller.close();
      },
    });

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      body: stream,
    });

    const chunks = [];
    for await (const chunk of streamChat('test query', 'session-123')) {
      chunks.push(chunk);
    }

    expect(chunks.length).toBe(3);
    expect(chunks[0]).toEqual({ type: 'content', token: 'Hello ' });
    expect(chunks[1]).toEqual({ type: 'content', token: 'world!' });
    expect(chunks[2]).toEqual({ type: 'done', finish_reason: 'stop' });
  });

  it('throws informative error on server failure', async () => {
    storeToken('valid-token');

    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      text: async () => 'Internal Server Error',
    });

    const streamGen = streamChat('test query', 'session-err');
    await expect(streamGen.next()).rejects.toThrow('Server returned status 500: Internal Server Error');
  });
});

describe('Tool Approval & MCP API Clients', () => {
  beforeEach(() => {
    storeToken('mock-auth-jwt');
  });

  it('submitToolApproval sends approval decision payload and returns response', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ status: 'ok', approval_id: 'appr-123', resolution: 'approve' }),
    });

    const res = await submitToolApproval('appr-123', 'approve');
    expect(res.status).toBe('ok');
    expect(res.resolution).toBe('approve');
    expect(global.fetch).toHaveBeenCalledWith('/codemode/approve', expect.objectContaining({
      method: 'POST',
      body: JSON.stringify({ approval_id: 'appr-123', decision: 'approve' }),
    }));
  });

  it('fetchMcpServers retrieves servers manifest', async () => {
    const mockManifest = { status: 'ok', servers: [{ id: 'filesystem', name: 'FS', enabled: true, tools: [] }] };
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockManifest,
    });

    const res = await fetchMcpServers();
    expect(res.servers.length).toBe(1);
    expect(res.servers[0].id).toBe('filesystem');
    expect(global.fetch).toHaveBeenCalledWith('/mcp/servers', expect.objectContaining({
      method: 'GET',
    }));
  });

  it('toggleMcpServer sends toggle payload and returns updated server info', async () => {
    const mockUpdated = { status: 'ok', server: { id: 'filesystem', enabled: false } };
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockUpdated,
    });

    const res = await toggleMcpServer('filesystem', false);
    expect(res.server.enabled).toBe(false);
    expect(global.fetch).toHaveBeenCalledWith('/mcp/toggle', expect.objectContaining({
      method: 'POST',
      body: JSON.stringify({ server_id: 'filesystem', enabled: false }),
    }));
  });
});

