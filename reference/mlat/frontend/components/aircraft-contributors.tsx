'use client';

import { ArrowUpRight, RadioTower } from 'lucide-react';
import Link from 'next/link';
import { StatusChip } from '@/components/ui/status-chip';
import type { DataSourceState } from '@/lib/data-source';
import { receiverReferenceIds, receiverReferencesInclude } from '@/lib/receiver-reference';
import { operationalStatusPresentation, registryStatusPresentation, RECEIVER_IDENTITY_PATTERN, type UnifiedReceiver } from '@/lib/receiver-state';

function receiverForContribution(receiverId: string, receivers: UnifiedReceiver[]): UnifiedReceiver | null {
  return receivers.find((receiver) => receiverReferencesInclude(
    receiverReferenceIds(receiver.key, receiver.identity, receiver.runtime?.receiver_id),
    receiverId,
  )) ?? null;
}

function contributionLabel(source: DataSourceState): string {
  if (source.kind === 'live') return 'LIVE CONTRIBUTION';
  if (source.kind === 'replay') return 'REPLAY CONTRIBUTION';
  if (source.kind === 'simulation') return 'SYNTHETIC CONTRIBUTION';
  if (source.kind === 'cached') return 'CACHED CONTRIBUTION';
  return 'SOURCE UNKNOWN';
}

export function AircraftContributors({
  contributions,
  receivers,
  source,
  onInspect,
}: {
  contributions: Map<string, number>;
  receivers: UnifiedReceiver[];
  source: DataSourceState;
  onInspect: (receiverKey: string) => void;
}) {
  const rows = [...contributions.entries()].sort((a, b) => b[1] - a[1]).slice(0, 8);

  return (
    <section className="border-b border-line" aria-labelledby="aircraft-contributors-title">
      <div className="flex items-start justify-between gap-3 border-b border-line px-4 py-3">
        <div>
          <p id="aircraft-contributors-title" className="text-xs font-semibold text-ink">MLAT solution → contributing receivers</p>
          <p className="mt-1 text-xs leading-5 text-ink-quiet">These receiver IDs come from the selected aircraft position records. Registry and operational state are shown separately.</p>
          {source.kind !== 'live' ? <p className="mt-1 text-xs leading-5 text-replay">This is {source.label.toLowerCase()} contribution evidence, not live receiver participation.</p> : null}
        </div>
        <StatusChip label={source.label} tone={source.tone} />
      </div>
      <div className="divide-y divide-line">
        {rows.map(([id, count], index) => {
          const receiver = receiverForContribution(id, receivers);
          const registryState = receiver ? registryStatusPresentation(receiver.registryStatus) : null;
          const operationalState = receiver ? operationalStatusPresentation(receiver.operationalStatus) : null;
          const statusId = `receiver-contribution-status-${index}`;
          const content = (
            <>
              <div className="min-w-0 flex-1">
                <p className="truncate text-xs font-semibold text-ink">{receiver?.label ?? id}</p>
                <p className="mt-0.5 truncate font-mono text-[11px] text-ink-quiet">{receiver?.identity ?? (RECEIVER_IDENTITY_PATTERN.test(id) ? id : 'No canonical Registry identity')}</p>
                <p className="mt-1 text-[11px] text-ink-secondary">{count} contributing {count === 1 ? 'position' : 'positions'} in this loaded track</p>
              </div>
              <div className="hidden max-w-[150px] flex-col items-end gap-1 sm:flex">
                <StatusChip label={contributionLabel(source)} tone={source.tone} />
                {registryState ? <StatusChip label={`Registry: ${registryState.label}`} tone={registryState.tone} /> : <StatusChip label="Registry: unavailable" tone="attention" />}
                {operationalState ? <StatusChip label={`Operational: ${operationalState.label}`} tone={operationalState.tone} /> : <StatusChip label="Operational: unavailable" tone="attention" />}
              </div>
              {receiver || RECEIVER_IDENTITY_PATTERN.test(id) ? <ArrowUpRight className="size-3.5 shrink-0 text-ink-quiet" /> : null}
            </>
          );
          const screenReaderStatus = <span id={statusId} className="sr-only">Source: {source.label}. Registry: {registryState?.label ?? 'Unavailable'}. Operational: {operationalState?.label ?? 'Unavailable'}. {count} contributing positions.</span>;

          if (receiver) {
            return <button key={id} type="button" aria-label={`Inspect receiver ${receiver.label}`} aria-describedby={statusId} onClick={() => onInspect(receiver.key)} className="flex min-h-16 w-full items-center gap-3 px-4 py-3 text-left outline-none hover:bg-graphite-hover focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-signal-blue">{content}{screenReaderStatus}</button>;
          }
          if (RECEIVER_IDENTITY_PATTERN.test(id)) {
            return <Link key={id} href={`/app/registry?receiver=${encodeURIComponent(id)}`} aria-describedby={statusId} className="flex min-h-16 items-center gap-3 px-4 py-3 outline-none hover:bg-graphite-hover focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-signal-blue">{content}{screenReaderStatus}</Link>;
          }
          return <div key={id} className="flex min-h-16 items-center gap-3 px-4 py-3">{content}{screenReaderStatus}</div>;
        })}
        {!rows.length ? <p className="px-4 py-5 text-xs leading-5 text-ink-quiet">Contributing receivers unavailable. The selected position records do not provide contributor identities.</p> : null}
      </div>
    </section>
  );
}
