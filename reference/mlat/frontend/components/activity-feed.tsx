'use client';

import { ArrowUpRight, Plane, RadioTower } from 'lucide-react';
import Link from 'next/link';
import { RelativeTime } from '@/components/ui/relative-time';
import { percent, toneFromScore } from '@/lib/format';
import type { Position, Receiver, StatusTone } from '@/lib/types';
import { cn } from '@/lib/utils';
import { useOperatorStore } from '@/lib/operator-store';

type ActivityItem = {
  id: string;
  timestamp: number;
  title: string;
  detail: string;
  tone: StatusTone;
  kind: 'aircraft' | 'receiver';
  focus: string;
};

export function ActivityFeed({ aircraft, receivers, limit = 8 }: { aircraft: Position[]; receivers: Receiver[]; limit?: number }) {
  const setInvestigationContext = useOperatorStore((state) => state.setInvestigationContext);
  const events: ActivityItem[] = [
    ...aircraft.map((item) => ({
      id: `aircraft-${item.aircraft_id}-${item.timestamp}`,
      timestamp: Number(item.timestamp ?? 0),
      title: `Aircraft ${item.aircraft_id}`,
      detail: `Position solved at ${percent(item.quality?.score, 0)} confidence`,
      tone: toneFromScore(item.quality?.score),
      kind: 'aircraft' as const,
      focus: item.aircraft_id,
    })),
    ...receivers.map((receiver) => ({
      id: `receiver-${receiver.receiver_id}-${receiver.last_seen}`,
      timestamp: Number(receiver.last_seen ?? 0),
      title: receiver.receiver_id,
      detail: 'Receiver heartbeat received',
      tone: String(receiver.status).toLowerCase() === 'online' ? 'healthy' as StatusTone : 'failure' as StatusTone,
      kind: 'receiver' as const,
      focus: receiver.receiver_id,
    })),
  ].filter((item) => item.timestamp > 0).sort((a, b) => b.timestamp - a.timestamp).slice(0, limit);

  if (!events.length) return <div className="grid min-h-48 place-items-center px-6 text-center text-xs text-ink-quiet">Activity will appear when receiver heartbeats and solved positions arrive.</div>;

  return (
    <ol className="divide-y divide-line">
      {events.map((event) => {
        const Icon = event.kind === 'aircraft' ? Plane : RadioTower;
        const href = event.kind === 'aircraft' ? `/app/aircraft?aircraft=${encodeURIComponent(event.title.replace('Aircraft ', ''))}` : `/app/receivers?receiver=${encodeURIComponent(event.title)}`;
        return (
          <li key={event.id}>
            <Link href={href} onClick={() => setInvestigationContext({ focus: event.focus })} className="grid grid-cols-[58px_28px_minmax(0,1fr)_16px] items-start gap-3 px-4 py-3 outline-none transition-colors duration-standard hover:bg-graphite-hover/45 focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-signal-blue">
              <time dateTime={new Date(event.timestamp * 1000).toISOString()} className="pt-1 text-right text-[10px] text-ink-quiet"><RelativeTime timestamp={event.timestamp} fallback="now" /></time>
              <span className={cn('flex size-7 items-center justify-center rounded-full', event.tone === 'healthy' ? 'bg-healthy/10 text-healthy' : event.tone === 'attention' ? 'bg-attention/10 text-attention' : event.tone === 'failure' ? 'bg-failure/10 text-failure' : 'bg-signal-blue/10 text-signal-blue')}><Icon aria-hidden="true" className="size-3.5" /></span>
              <div className="min-w-0"><p className="truncate text-xs font-semibold text-ink">{event.title}</p><p className="mt-0.5 truncate text-[11px] text-ink-quiet">{event.detail}</p></div>
              <ArrowUpRight aria-hidden="true" className="mt-1 size-3.5 text-ink-quiet" />
            </Link>
          </li>
        );
      })}
    </ol>
  );
}
