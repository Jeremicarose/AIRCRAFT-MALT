import type { LucideIcon } from 'lucide-react';
import type { ReactNode } from 'react';
import { toneSurfaceClass, toneTextClass } from '@/components/ui/status-chip';
import { Surface } from '@/components/ui/surface';
import type { StatusTone } from '@/lib/types';
import { cn } from '@/lib/utils';

export interface StatItem {
  label: string;
  value: ReactNode;
  detail?: ReactNode;
  tone?: StatusTone;
  icon?: LucideIcon;
  visualization?: ReactNode;
}

const layoutClasses = {
  four: 'sm:grid-cols-2 xl:grid-cols-4',
  five: 'sm:grid-cols-2 xl:grid-cols-5',
};

export function StatStrip({ items, layout = 'four', className }: { items: StatItem[]; layout?: keyof typeof layoutClasses; className?: string }) {
  return (
    <Surface className={cn('overflow-hidden rounded-xl bg-[linear-gradient(180deg,rgba(17,21,26,0.95),rgba(9,12,16,0.98))] shadow-[inset_0_1px_0_rgba(255,255,255,0.03),0_24px_50px_-42px_rgba(0,0,0,0.9)]', className)}>
      <dl className={cn('grid divide-y divide-line sm:divide-x sm:divide-y-0', layoutClasses[layout])}>
        {items.map((item) => {
          const Icon = item.icon;
          const tone = item.tone ?? 'neutral';
          return (
            <div key={item.label} className="flex min-w-0 items-center justify-between gap-3 px-4 py-4 transition-colors duration-standard hover:bg-white/[0.015]">
              <div className="flex min-w-0 items-center gap-3">
                {Icon ? <span className={cn('flex size-8 shrink-0 items-center justify-center rounded-lg', toneSurfaceClass(tone))}><Icon aria-hidden="true" className="size-4" /></span> : null}
                <div className="min-w-0">
                  <dt className="truncate text-[11px] uppercase tracking-[0.14em] text-ink-quiet">{item.label}</dt>
                  <dd className="mt-1 truncate text-xl font-semibold leading-none text-ink tabular-nums">{item.value}</dd>
                  {item.detail ? <p className="mt-1.5 truncate text-[10px] text-ink-quiet">{item.detail}</p> : null}
                </div>
              </div>
              {item.visualization ?? (!Icon ? <span aria-hidden="true" className={cn('h-px w-14 shrink-0', toneTextClass(tone).replace('text-', 'bg-'))} /> : null)}
            </div>
          );
        })}
      </dl>
    </Surface>
  );
}
