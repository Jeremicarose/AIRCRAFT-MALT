'use client';

import { Search, X } from 'lucide-react';
import type { InputHTMLAttributes } from 'react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface SearchFieldProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'onChange' | 'type' | 'value'> {
  value: string;
  onValueChange: (value: string) => void;
  label: string;
  rootClassName?: string;
  inputClassName?: string;
  elevated?: boolean;
}

export function SearchField({ value, onValueChange, label, rootClassName, inputClassName, elevated = false, ...props }: SearchFieldProps) {
  return (
    <div className={cn('relative min-w-0', rootClassName)}>
      <Search aria-hidden="true" className="pointer-events-none absolute left-3 top-1/2 z-10 size-3.5 -translate-y-1/2 text-ink-quiet" />
      <input
        {...props}
        type="search"
        value={value}
        onChange={(event) => onValueChange(event.target.value)}
        aria-label={label}
        className={cn(
          'h-9 w-full appearance-none rounded-md border border-line bg-graphite-raised pl-9 pr-9 text-xs text-ink outline-none transition-[border-color,background-color,box-shadow] duration-standard placeholder:text-ink-secondary hover:border-[#3c4654] focus:border-signal-blue focus:ring-2 focus:ring-signal-blue/20 focus:shadow-[0_0_0_1px_rgba(104,213,232,0.14)] [&::-webkit-search-cancel-button]:hidden',
          elevated && 'bg-graphite/95 shadow-map backdrop-blur-sm',
          inputClassName,
        )}
      />
      {value ? (
        <Button type="button" variant="ghost" size="icon-sm" onClick={() => onValueChange('')} aria-label={`Clear ${label.toLowerCase()}`} className="absolute right-0.5 top-0.5 size-8">
          <X className="size-3.5" />
        </Button>
      ) : null}
    </div>
  );
}
