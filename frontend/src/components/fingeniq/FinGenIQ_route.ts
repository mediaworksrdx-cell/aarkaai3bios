import { NextRequest, NextResponse } from 'next/server';

// â”€â”€â”€ Service Authentication â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
// Uses a dedicated service API key for backend communication.
// The key must match the API_KEY configured on the backend.
// NEVER self-mint JWTs â€” only the backend issues user tokens.
const FINGENIQ_SERVICE_KEY = process.env.FINGENIQ_SERVICE_API_KEY || '';
const BACKEND_URL = process.env.BACKEND_URL || process.env.AARKAAI_BACKEND_URL || 'http://127.0.0.1:5000';

export async function POST(req: NextRequest) {
  try {
    const { message, model = 'gemini-3.7-flash' } = await req.json();

    if (!message || typeof message !== 'string') {
      return NextResponse.json({ error: 'Message is required' }, { status: 400 });
    }

    if (!FINGENIQ_SERVICE_KEY) {
      console.error('FINGENIQ_SERVICE_API_KEY is not configured');
      return NextResponse.json(
        { error: 'Service configuration error' },
        { status: 500 }
      );
    }

    // Map FinGenIQ model selection → Backend model overrides
    const modelOverride = 'gemini-3.7-flash';

    // Call backend prompt streaming endpoint using service API key
    const res = await fetch(`${BACKEND_URL}/prompt/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': FINGENIQ_SERVICE_KEY,
      },
      body: JSON.stringify({
        query: message,
        model_override: modelOverride,
        mode: 'production',
      }),
    });

    if (!res.ok) {
      const errorText = await res.text();
      console.error(`Backend API error (${res.status}): ${errorText}`);
      return NextResponse.json(
        { error: 'AI service temporarily unavailable. Please try again.' },
        { status: 502 }
      );
    }

    // Stream SSE back to the client
    const stream = new ReadableStream({
      async start(controller) {
        if (!res.body) {
          controller.close();
          return;
        }
        const reader = res.body.getReader();
        const decoder = new TextDecoder();

        try {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            const chunk = decoder.decode(value, { stream: true });
            controller.enqueue(new TextEncoder().encode(chunk));
          }
        } catch (err) {
          controller.error(err);
        } finally {
          controller.close();
        }
      },
    });

    return new Response(stream, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    });
  } catch (error: any) {
    console.error('FinGenIQ Chat Proxy Error:', error);
    return NextResponse.json(
      { error: 'Internal server error. Please try again.' },
      { status: 500 }
    );
  }
}
