'use client';

import { useEffect, useState } from 'react';

function formatRelative(timestamp: unknown, now: number): string {
  const numeric = Number(timestamp);
  if (!Number.isFinite(numeric)) return 'unavailable';
  const seconds = Math.max(0, Math.round(now / 1000 - numeric));
  if (seconds < 60) return `${seconds}s ago`;
  if (seconds < 3600) return `${Math.round(seconds / 60)}m ago`;
  return `${Math.round(seconds / 3600)}h ago`;
}

export function RelativeTime({ timestamp, fallback = 'recently' }: { timestamp: unknown; fallback?: string }) {
  const [now, setNow] = useState<number | null>(null);
  useEffect(() => {
    setNow(Date.now());
    const timer = window.setInterval(() => setNow(Date.now()), 15_000);
    return () => window.clearInterval(timer);
  }, []);
  return <span>{now == null ? fallback : formatRelative(timestamp, now)}</span>;
}
