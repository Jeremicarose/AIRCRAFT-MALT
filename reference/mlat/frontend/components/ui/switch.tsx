'use client';

import { cn } from '@/lib/utils';

export function Switch({ checked, onCheckedChange, label, disabled = false }: { checked: boolean; onCheckedChange: (checked: boolean) => void; label: string; disabled?: boolean }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      disabled={disabled}
      onClick={() => onCheckedChange(!checked)}
      className={cn('relative h-5 w-9 shrink-0 rounded-full border border-line bg-graphite-raised outline-none transition-[background-color,border-color] duration-standard focus-visible:ring-2 focus-visible:ring-signal-blue focus-visible:ring-offset-2 focus-visible:ring-offset-graphite disabled:cursor-not-allowed disabled:opacity-45', checked && 'border-signal-blue bg-signal-blue')}
    >
      <span aria-hidden="true" className={cn('absolute left-0.5 top-0.5 size-3.5 rounded-full bg-ink-secondary transition-transform duration-standard', checked && 'translate-x-4 bg-graphite-deep')} />
    </button>
  );
}
