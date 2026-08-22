import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.AARKAAI_BACKEND_URL || 'http://127.0.0.1:5000';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    const authHeader = request.headers.get('Authorization');
    if (authHeader) {
      headers['Authorization'] = authHeader;
    }

    const payload = {
      user_id: body.user_id || 'web_user',
      rating: body.rating ?? 1,
      conversation_id: body.conversation_id ? String(body.conversation_id) : null,
      correction: body.correction || '',
    };

    const res = await fetch(`${BACKEND_URL}/rlhf`, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const errorText = await res.text().catch(() => 'RLHF error');
      return NextResponse.json({ status: 'error', detail: errorText }, { status: res.status });
    }

    const data = await res.json().catch(() => ({ status: 'success' }));
    return NextResponse.json(data);
  } catch (error: any) {
    return NextResponse.json({ status: 'error', detail: error.message }, { status: 500 });
  }
}
