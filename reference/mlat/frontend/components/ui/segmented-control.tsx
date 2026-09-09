'use client';

import { cn } from '@/lib/utils';

interface Segment<T extends string> {
  value: T;
  label: string;
}

export function SegmentedControl<T extends string>({ label, value, options, onValueChange, className }: { label: string; value: T; options: readonly Segment<T>[]; onValueChange: (value: T) => void; className?: string }) {
  return (
    <div role="group" aria-label={label} className={cn('inline-flex rounded-md border border-line bg-graphite-raised p-0.5', className)}>
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          aria-pressed={value === option.value}
          onClick={() => onValueChange(option.value)}
          className={cn('h-8 rounded px-3 text-xs font-medium text-ink-quiet outline-none transition-[background-color,color] duration-standard hover:text-ink focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-signal-blue', value === option.value && 'bg-graphite-hover text-ink')}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
