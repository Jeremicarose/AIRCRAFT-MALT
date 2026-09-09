import { NextResponse } from 'next/server';

export function GET() {
  return NextResponse.json({ status: 'ok', service: 'receiver-registry-operations' }, {
    headers: { 'Cache-Control': 'no-store' },
  });
}
