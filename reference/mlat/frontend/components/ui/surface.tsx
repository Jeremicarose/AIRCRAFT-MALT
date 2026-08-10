import type { HTMLAttributes, ReactNode } from 'react';
import { cn } from '@/lib/utils';

export function Surface({ className, ...props }: HTMLAttributes<HTMLElement>) {
  return <section className={cn('rounded-lg border border-line bg-graphite', className)} {...props} />;
}

export function SectionHeader({ title, detail, action, className }: { title: string; detail?: string; action?: ReactNode; className?: string }) {
  return (
    <header className={cn('flex min-h-14 items-center justify-between gap-4 border-b border-line px-4 py-3', className)}>
      <div className="min-w-0">
        <h2 className="text-sm font-semibold text-ink">{title}</h2>
        {detail ? <p className="mt-0.5 text-pretty text-xs leading-4 text-ink-quiet">{detail}</p> : null}
      </div>
      {action ? <div className="shrink-0">{action}</div> : null}
    </header>
  );
}

export function EmptyState({ title, detail, action }: { title: string; detail?: string; action?: ReactNode }) {
  return (
    <div className="flex min-h-40 flex-col items-center justify-center px-6 py-10 text-center">
      <p className="text-sm font-semibold text-ink">{title}</p>
      {detail ? <p className="mt-1 max-w-sm text-xs leading-5 text-ink-quiet">{detail}</p> : null}
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  );
}
