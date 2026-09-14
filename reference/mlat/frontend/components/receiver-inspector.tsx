'use client';

import { ArrowUpRight, RadioTower, ShieldCheck } from 'lucide-react';
import Link from 'next/link';
import type { ReactNode } from 'react';
import { FactGrid, Inspector } from '@/components/operations-ui';
import { CopyValue } from '@/components/ui/copy-value';
import { RelativeTime } from '@/components/ui/relative-time';
import { StatusChip } from '@/components/ui/status-chip';
import { formatDateTime, titleCase, truncateMiddle } from '@/lib/format';
import {
  mlatStatusPresentation,
  registryStatusPresentation,
  type UnifiedReceiver,
} from '@/lib/receiver-state';

export function ReceiverInspector({
  receiver,
  lifecycle,
  actions,
  className,
  perspective = 'receivers',
}: {
  receiver: UnifiedReceiver | null;
  lifecycle?: ReactNode;
  actions?: ReactNode;
  className?: string;
  perspective?: 'receivers' | 'registry';
}) {
  if (!receiver) {
    return (
      <Inspector title="No receiver selected" subtitle={perspective === 'registry' ? 'Choose an identity to inspect its current owner and lifecycle' : 'Choose a receiver to inspect its identity and MLAT role'} className={className}>
        <div className="p-6 text-center text-xs leading-5 text-ink-quiet">
          <RadioTower className="mx-auto mb-3 size-5" />
          {perspective === 'registry' ? 'Canonical identity, owner, current state, lifecycle history, and transaction evidence appear here.' : 'Receiver identity, owner, lifecycle, health, MLAT role, and related aircraft appear here.'}
        </div>
      </Inspector>
    );
  }

  const registryState = registryStatusPresentation(receiver.registryStatus);
  const mlatState = mlatStatusPresentation(receiver.mlatStatus);
  const detailSource = receiver.registry ?? receiver.runtime;

  return (
    <Inspector
      title={receiver.label}
      subtitle={receiver.identity ? <CopyValue value={receiver.identity} displayValue={truncateMiddle(receiver.identity, 12, 10)} label="canonical receiver identity" /> : 'No canonical CKB identity'}
      status={<StatusChip label={perspective === 'registry' ? registryState.label : mlatState.label} tone={perspective === 'registry' ? registryState.tone : mlatState.tone} />}
      actions={actions}
      className={className}
    >
      <div className="grid gap-px bg-line sm:grid-cols-2">
        <div className="bg-graphite p-4">
          <p className="text-[11px] font-medium text-ink-quiet">Registry identity</p>
          <div className="mt-2"><StatusChip label={registryState.label} tone={registryState.tone} /></div>
        </div>
        <div className="bg-graphite p-4">
          <p className="text-[11px] font-medium text-ink-quiet">MLAT operation</p>
          <div className="mt-2"><StatusChip label={mlatState.label} tone={mlatState.tone} /></div>
        </div>
      </div>

      {perspective !== 'registry' ? <div className="border-b border-line p-4">
        <p className="text-xs font-semibold text-ink">Why this MLAT state</p>
        <p className="mt-1 text-xs leading-5 text-ink-quiet">{receiver.mlatReason}</p>
      </div> : null}

      <FactGrid items={[
        { label: 'Owner', value: receiver.ownerLockArgs ? <CopyValue value={receiver.ownerLockArgs} displayValue={truncateMiddle(receiver.ownerLockArgs, 9, 7)} label="owner address" /> : 'Not available' },
        { label: 'Published state', value: receiver.registryRecordStatus ? titleCase(receiver.registryRecordStatus) : 'Not published' },
        { label: 'Capabilities', value: receiver.capabilities.length ? receiver.capabilities.join(', ') : 'Not available' },
        { label: 'Last observation', value: receiver.lastObservationAt ? <RelativeTime timestamp={receiver.lastObservationAt} /> : 'Not available' },
      ]} />

      {receiver.relatedAircraftIds.length ? (
        <div className="border-b border-line p-4">
          <div className="flex items-center justify-between gap-3">
            <p className="text-xs font-semibold text-ink">Related aircraft</p>
            <span className="text-[11px] text-ink-quiet">Current window</span>
          </div>
          <div className="mt-2 space-y-1">
            {receiver.relatedAircraftIds.map((aircraftId) => (
              <Link key={aircraftId} href={`/app/aircraft?aircraft=${encodeURIComponent(aircraftId)}`} className="flex min-h-10 items-center justify-between gap-3 rounded-md px-2 text-xs text-ink-secondary outline-none hover:bg-graphite-hover hover:text-ink focus-visible:ring-2 focus-visible:ring-signal-blue">
                <span className="font-mono font-semibold">{aircraftId}</span>
                <ArrowUpRight className="size-3.5 text-ink-quiet" />
              </Link>
            ))}
          </div>
        </div>
      ) : null}

      {lifecycle ? (
        <div>
          <div className="border-b border-line px-4 py-3">
            <p className="text-xs font-semibold text-ink">Lifecycle</p>
            <p className="mt-0.5 text-[11px] text-ink-quiet">Owner-authorized Registry events for this identity</p>
          </div>
          {lifecycle}
        </div>
      ) : null}

      <details className="border-t border-line p-4">
        <summary className="cursor-pointer rounded-sm text-xs font-semibold text-ink-secondary outline-none focus-visible:ring-2 focus-visible:ring-signal-blue">Technical Registry details</summary>
        <dl className="mt-3 space-y-3 text-[11px]">
          <div><dt className="text-ink-quiet">Canonical Type ID</dt><dd className="mt-1 text-ink-secondary">{receiver.identity ? <CopyValue value={receiver.identity} label="canonical Type ID" className="w-full" /> : 'Not available'}</dd></div>
          <div><dt className="text-ink-quiet">Registry sequence</dt><dd className="mt-1 font-mono text-ink-secondary">{detailSource?.registry?.sequence ?? 'Not available'}</dd></div>
          <div><dt className="text-ink-quiet">Last Registry update</dt><dd className="mt-1 text-ink-secondary">{receiver.lastRegistryUpdateAt ? formatDateTime(receiver.lastRegistryUpdateAt) : 'Not available'}</dd></div>
          <div className="flex items-start gap-2 rounded-md bg-trust-cyan/[0.06] p-2.5 text-ink-quiet"><ShieldCheck className="mt-0.5 size-3.5 shrink-0 text-trust-cyan" />CKB proves lifecycle continuity and owner authorization. It does not prove physical location, receiver hardware, clock quality, or feed honesty.</div>
        </dl>
      </details>
    </Inspector>
  );
}
