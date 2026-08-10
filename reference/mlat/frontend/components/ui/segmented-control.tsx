'use client';

import { cn } from '@/lib/utils';

interface Segment<T extends string> {
  value: T;
  label: string;
}

export function SegmentedControl<T extends string>({ label, value, options, onValueChange, className }: { label: string; value: T; options: readonly Segment<T>[]; onValueChange: (value: T) => void; className?: string }) {
  return (
    <div role="group" aria-label={label} className={cn('inline-flex rounded-lg border border-line bg-[linear-gradient(180deg,rgba(18,22,27,0.98),rgba(12,15,19,0.96))] p-0.5 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]', className)}>
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          aria-pressed={value === option.value}
          onClick={() => onValueChange(option.value)}
          className={cn('h-8 rounded-md px-3 text-xs font-medium text-ink-quiet outline-none transition-[transform,background-color,color,box-shadow] duration-standard hover:text-ink focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-signal-blue', value === option.value && 'bg-[linear-gradient(180deg,rgba(53,64,78,0.9),rgba(31,37,45,0.92))] text-ink shadow-[inset_0_1px_0_rgba(255,255,255,0.05),0_10px_20px_-16px_rgba(91,156,255,0.8)]')}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
