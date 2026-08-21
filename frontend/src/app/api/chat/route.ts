import { NextRequest, NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';
export const maxDuration = 300;

const BACKEND_URL = process.env.AARKAAI_BACKEND_URL || 'http://127.0.0.1:5000';

export async function POST(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const isStream = searchParams.get('stream') !== 'false';

  try {
    const body = await request.json();

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Accept': 'text/event-stream, application/json',
    };

    const authHeader = request.headers.get('Authorization');
    if (authHeader) {
      headers['Authorization'] = authHeader;
    }

    let modelOverride = body.model_override || 'aarka-2.0';
    const effort = body.effort || 'medium';

    // Map to active backend engine targets
    if (modelOverride === 'gemini-2.5' || modelOverride.startsWith('gemini')) {
      modelOverride = 'gemini-2.5';
    } else {
      modelOverride = 'aarka-2.0';
    }

    const payload = {
      query: body.query || '',
      session_id: body.session_id || '1',
      model_override: modelOverride,
      effort: effort,
      mode: effort === 'high' ? 'deep_reasoning' : 'production',
    };

    if (isStream) {
      let backendResponse: globalThis.Response;
      try {
        backendResponse = await fetch(`${BACKEND_URL}/prompt/stream`, {
          method: 'POST',
          headers,
          body: JSON.stringify(payload),
        });
      } catch (e: any) {
        const fallbackUrl = BACKEND_URL.includes('127.0.0.1')
          ? BACKEND_URL.replace('127.0.0.1', 'localhost')
          : 'http://127.0.0.1:5000';
        backendResponse = await fetch(`${fallbackUrl}/prompt/stream`, {
          method: 'POST',
          headers,
          body: JSON.stringify(payload),
        });
      }

      if (!backendResponse.ok) {
        const errorText = await backendResponse.text().catch(() => 'Unknown error');
        return NextResponse.json(
          { error: `Backend error: ${backendResponse.status}`, detail: errorText },
          { status: backendResponse.status }
        );
      }

      if (!backendResponse.body) {
        return NextResponse.json(
          { error: 'No response body from backend' },
          { status: 502 }
        );
      }

      // Relay SSE stream
      return new Response(backendResponse.body, {
        status: 200,
        headers: {
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache, no-transform',
          'Connection': 'keep-alive',
          'X-Accel-Buffering': 'no',
        },
      });
    } else {
      let backendResponse = await fetch(`${BACKEND_URL}/prompt`, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
      });

      if (!backendResponse.ok) {
        const errorText = await backendResponse.text().catch(() => 'Unknown error');
        return NextResponse.json(
          { error: `Backend error: ${backendResponse.status}`, detail: errorText },
          { status: backendResponse.status }
        );
      }

      const data = await backendResponse.json();
      return NextResponse.json({
        response: data.response || '',
        model_used: data.model_used || 'unknown',
      });
    }
  } catch (error: any) {
    console.error('[api/chat] Proxy error:', error);

    return NextResponse.json(
      { error: error.message || 'Internal proxy error' },
      { status: 502 }
    );
  }
}
