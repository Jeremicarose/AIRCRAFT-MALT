import { StatusChip } from '@/components/ui/status-chip';
import type { DataSourceState } from '@/lib/data-source';
import { cn } from '@/lib/utils';

export function MapSourceBadge({ source, className, detail = true }: { source: DataSourceState; className?: string; detail?: boolean }) {
  return (
    <div
      role="status"
      aria-label={`Map source: ${source.label}`}
      data-map-source={source.kind}
      className={cn('flex max-w-[min(520px,calc(100%-24px))] items-center gap-2 rounded-md border border-line bg-graphite/95 px-2.5 py-2 shadow-map backdrop-blur-sm', className)}
    >
      <StatusChip label={`${source.label} MAP`} tone={source.tone} />
      {detail ? <span className="hidden min-w-0 truncate text-xs text-ink-secondary md:block">{source.detail}</span> : null}
    </div>
  );
}
