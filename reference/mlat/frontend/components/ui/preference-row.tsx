import type { LucideIcon } from 'lucide-react';
import type { ReactNode } from 'react';

export function PreferenceRow({ icon: Icon, title, detail, control }: { icon: LucideIcon; title: string; detail: string; control: ReactNode }) {
  return (
    <div className="flex items-center gap-3 border-b border-line px-4 py-4 last:border-0">
      <span className="flex size-8 shrink-0 items-center justify-center rounded-md bg-graphite-raised"><Icon aria-hidden="true" className="size-4 text-ink-quiet" /></span>
      <div className="min-w-0 flex-1"><p className="text-xs font-semibold text-ink">{title}</p><p className="mt-1 text-pretty text-[11px] leading-4 text-ink-quiet">{detail}</p></div>
      <div className="shrink-0">{control}</div>
    </div>
  );
}
