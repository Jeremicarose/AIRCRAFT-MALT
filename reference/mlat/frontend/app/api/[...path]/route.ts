import { NextRequest, NextResponse } from 'next/server';
import { apiUrl } from '@/lib/api';

const publicReadPrefixes = [
  'aircraft',
  'benchmark/latest',
  'evidence/',
  'health',
  'pipeline',
  'positions/recent',
  'readiness',
  'receivers',
  'registry/evidence',
  'system/mode',
];

function isPublicReadPath(path: string): boolean {
  return publicReadPrefixes.some((prefix) => path === prefix || (prefix.endsWith('/') && path.startsWith(prefix)) || path.startsWith(`${prefix}/`));
}

export async function GET(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path: segments } = await context.params;
  if (!segments.length || segments.some((segment) => !segment || segment === '.' || segment === '..')) {
    return NextResponse.json({ error: 'Invalid API path.' }, { status: 400 });
  }

  const path = segments.join('/');
  if (!isPublicReadPath(path)) {
    return NextResponse.json({ error: 'This endpoint is not available through the public application.' }, { status: 404 });
  }

  try {
    const upstream = await fetch(`${apiUrl(`/api/${path}`)}${request.nextUrl.search}`, {
      cache: 'no-store',
      headers: { Accept: request.headers.get('accept') ?? 'application/json' },
      signal: request.signal,
    });
    const body = await upstream.arrayBuffer();
    return new NextResponse(body, {
      status: upstream.status,
      headers: {
        'Cache-Control': 'no-store',
        'Content-Type': upstream.headers.get('content-type') ?? 'application/json',
      },
    });
  } catch {
    return NextResponse.json(
      { error: 'The receiver service is unavailable. Wait a moment and try again.' },
      { status: 503, headers: { 'Cache-Control': 'no-store' } },
    );
  }
}
