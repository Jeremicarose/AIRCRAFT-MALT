'use client';

import { Check, Copy, TriangleAlert } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Tooltip } from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';

type CopyState = 'idle' | 'copied' | 'failed';

async function writeClipboard(value: string): Promise<void> {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(value);
    return;
  }

  const input = document.createElement('textarea');
  input.value = value;
  input.setAttribute('readonly', '');
  input.style.position = 'fixed';
  input.style.opacity = '0';
  document.body.appendChild(input);
  input.select();
  const copied = document.execCommand('copy');
  input.remove();
  if (!copied) throw new Error('Clipboard access was rejected.');
}

export function CopyValue({ value, displayValue = value, label, className }: { value: string; displayValue?: string; label: string; className?: string }) {
  const [state, setState] = useState<CopyState>('idle');
  const resetTimer = useRef<number | null>(null);

  useEffect(() => () => {
    if (resetTimer.current) window.clearTimeout(resetTimer.current);
  }, []);

  const copy = async () => {
    try {
      await writeClipboard(value);
      setState('copied');
    } catch {
      setState('failed');
    }
    if (resetTimer.current) window.clearTimeout(resetTimer.current);
    resetTimer.current = window.setTimeout(() => setState('idle'), 2_000);
  };

  const Icon = state === 'copied' ? Check : state === 'failed' ? TriangleAlert : Copy;
  const actionLabel = state === 'copied' ? `${label} copied` : state === 'failed' ? `Could not copy ${label}` : `Copy ${label}`;

  return (
    <span className={cn('inline-flex max-w-full items-center gap-1.5', className)}>
      <code className="min-w-0 truncate font-mono" title={value}>{displayValue}</code>
      <Tooltip label={actionLabel}>
        <Button type="button" variant="ghost" size="icon-sm" className="size-7 min-h-7 min-w-7" aria-label={actionLabel} onClick={() => void copy()}>
          <Icon className={cn('size-3.5', state === 'copied' && 'text-healthy', state === 'failed' && 'text-failure')} />
        </Button>
      </Tooltip>
      <span className="sr-only" aria-live="polite">{state === 'copied' ? `${label} copied to clipboard.` : state === 'failed' ? `${label} could not be copied.` : ''}</span>
    </span>
  );
}
