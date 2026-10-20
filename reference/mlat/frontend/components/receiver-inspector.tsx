'use client';

import { ArrowUpRight, RadioTower, ShieldCheck, Stethoscope } from 'lucide-react';
import Link from 'next/link';
import type { ReactNode } from 'react';
import { FactGrid, Inspector } from '@/components/operations-ui';
import { ReceiverReadinessJourney } from '@/components/receiver-readiness-journey';
import { CopyValue } from '@/components/ui/copy-value';
import { RelativeTime } from '@/components/ui/relative-time';
import { StatusChip } from '@/components/ui/status-chip';
import { formatDateTime, titleCase, truncateMiddle } from '@/lib/format';
import type { DataSourceState } from '@/lib/data-source';
import {
  mlatStatusPresentation,
  operationalStatusPresentation,
  registryStatusPresentation,
  type UnifiedReceiver,
} from '@/lib/receiver-state';

export function ReceiverInspector({
  receiver,
  lifecycle,
  actions,
  className,
  perspective = 'receivers',
  operationalSource,
  collapsible = false,
  expanded = true,
  onExpandedChange,
}: {
  receiver: UnifiedReceiver | null;
  lifecycle?: ReactNode;
  actions?: ReactNode;
  className?: string;
  perspective?: 'receivers' | 'registry';
  operationalSource?: DataSourceState;
  collapsible?: boolean;
  expanded?: boolean;
  onExpandedChange?: (expanded: boolean) => void;
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
  const operationalState = operationalStatusPresentation(receiver.operationalStatus);
  const detailSource = receiver.registry ?? receiver.runtime;
  const declaredStream = receiver.registry?.registry?.stream_endpoint ?? null;
  const sourceLabel = operationalSource?.label ?? titleCase(receiver.source ?? 'unknown');

  return (
    <Inspector
      title={receiver.label}
      subtitle={receiver.identity ? <CopyValue value={receiver.identity} displayValue={truncateMiddle(receiver.identity, 12, 10)} label="canonical receiver identity" /> : 'No canonical CKB identity'}
      status={<StatusChip label={perspective === 'registry' ? registryState.label : mlatState.label} tone={perspective === 'registry' ? registryState.tone : mlatState.tone} />}
      actions={actions}
      className={className}
      collapsible={collapsible}
      expanded={expanded}
      onExpandedChange={onExpandedChange}
    >
      <div className="grid gap-px bg-line sm:grid-cols-3">
        <div className="bg-graphite p-4">
          <p className="text-xs font-medium text-ink-quiet">Registry identity</p>
          <div className="mt-2"><StatusChip label={registryState.label} tone={registryState.tone} /></div>
        </div>
        <div className="bg-graphite p-4">
          <p className="text-xs font-medium text-ink-quiet">Operational state</p>
          <div className="mt-2"><StatusChip label={operationalState.label} tone={operationalState.tone} /></div>
        </div>
        <div className="bg-graphite p-4">
          <p className="text-xs font-medium text-ink-quiet">MLAT state</p>
          <div className="mt-2"><StatusChip label={mlatState.label} tone={mlatState.tone} /></div>
        </div>
      </div>

      <div className="border-b border-line p-4">
        <p className="text-xs font-semibold text-ink">Current interpretation</p>
        <p className="mt-1 text-xs leading-5 text-ink-secondary">The Registry identity is {registryState.label.toLowerCase()}, the runtime reports {operationalState.label.toLowerCase()}, and MLAT reports {mlatState.label.toLowerCase()}.</p>
        <p className="mt-1 text-xs leading-5 text-ink-quiet">{receiver.mlatReason}</p>
      </div>

      <ReceiverReadinessJourney receiver={receiver} />

      <section className="border-b border-line" aria-labelledby="receiver-registry-facts">
        <div className="border-b border-line px-4 py-3"><h3 id="receiver-registry-facts" className="text-sm font-semibold text-ink">Registry facts</h3><p className="mt-1 text-xs leading-5 text-ink-quiet">Owner-authorized identity, lifecycle, and owner-provided metadata published on CKB.</p></div>
        <FactGrid items={[
          { label: 'Canonical Receiver Identity', value: receiver.identity ? <CopyValue value={receiver.identity} displayValue={truncateMiddle(receiver.identity, 12, 10)} label="canonical receiver identity" /> : 'Not registered' },
          { label: 'Current owner', value: receiver.ownerLockArgs ? <CopyValue value={receiver.ownerLockArgs} displayValue={truncateMiddle(receiver.ownerLockArgs, 9, 7)} label="owner address" /> : 'Not available' },
          { label: 'Owner-declared status', value: receiver.registryRecordStatus ? titleCase(receiver.registryRecordStatus) : 'Not published' },
          { label: 'Owner-declared capabilities', value: receiver.capabilities.length ? receiver.capabilities.join(', ') : 'Not available' },
        ]} />
        <p className="px-4 py-3 text-xs leading-5 text-ink-quiet">These facts prove identity continuity and authorized lifecycle changes. They do not prove hardware existence, location, feed honesty, or clock accuracy.</p>
        {lifecycle ? (
          <div className="border-t border-line">
            <div className="border-b border-line px-4 py-3"><h4 className="text-xs font-semibold text-ink">Lifecycle and transactions</h4><p className="mt-1 text-xs text-ink-quiet">Owner-authorized create, update, transfer, and revoke events for this identity.</p></div>
            {lifecycle}
          </div>
        ) : null}
      </section>

      <section className="border-b border-line" aria-labelledby="receiver-operational-observations">
        <div className="border-b border-line px-4 py-3"><h3 id="receiver-operational-observations" className="text-sm font-semibold text-ink">Operational observations</h3><p className="mt-1 text-xs leading-5 text-ink-quiet">Runtime presence and timing evidence, separate from owner-published Registry claims.</p></div>
        <FactGrid items={[
          { label: 'Runtime inventory', value: receiver.runtime ? 'Discovered by MLAT runtime' : 'Not present in runtime' },
          { label: 'Observed feed state', value: operationalState.label },
          { label: 'Latest observation', value: receiver.lastObservationAt ? <RelativeTime timestamp={receiver.lastObservationAt} /> : 'Not available' },
          { label: 'Observation source', value: sourceLabel },
        ]} />
        <div className="flex flex-col gap-3 px-4 py-3 sm:flex-row sm:items-center sm:justify-between"><p className="text-xs leading-5 text-ink-quiet">{receiver.operationalReason}</p><Link href="/app/environment" className="inline-flex min-h-8 shrink-0 items-center gap-2 rounded-md border border-line px-2.5 text-xs font-semibold text-ink-secondary outline-none hover:bg-graphite-hover hover:text-ink focus-visible:ring-2 focus-visible:ring-signal-blue"><Stethoscope className="size-3.5" />Open diagnostics</Link></div>
      </section>

      <section className="border-b border-line" aria-labelledby="receiver-mlat-derived">
        <div className="border-b border-line px-4 py-3"><h3 id="receiver-mlat-derived" className="text-sm font-semibold text-ink">MLAT-derived state</h3><p className="mt-1 text-xs leading-5 text-ink-quiet">Eligibility and contribution computed from Registry checks plus current runtime evidence.</p></div>
        <FactGrid items={[
          { label: 'Registry eligibility', value: receiver.mlatEligible ? 'Eligible' : 'Not eligible' },
          { label: 'Current contribution', value: mlatState.label },
          { label: 'Related aircraft', value: String(receiver.relatedAircraftIds.length) },
          { label: 'Source', value: sourceLabel },
        ]} />
        <p className="px-4 py-3 text-xs leading-5 text-ink-quiet">{receiver.mlatReason}</p>

        {receiver.relatedAircraftIds.length ? (
        <div className="border-t border-line p-4">
          <div className="flex items-center justify-between gap-3">
            <p className="text-xs font-semibold text-ink">Related aircraft</p>
            <span className="text-xs text-ink-quiet">Current window</span>
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
      </section>

      <details className="border-t border-line p-4">
        <summary className="cursor-pointer rounded-sm text-xs font-semibold text-ink-secondary outline-none focus-visible:ring-2 focus-visible:ring-signal-blue">Technical Registry details</summary>
        <dl className="mt-3 space-y-3 text-xs">
          <div><dt className="text-ink-quiet">Canonical Type ID</dt><dd className="mt-1 text-ink-secondary">{receiver.identity ? <CopyValue value={receiver.identity} label="canonical Type ID" className="w-full" /> : 'Not available'}</dd></div>
          <div><dt className="text-ink-quiet">Registry sequence</dt><dd className="mt-1 font-mono text-ink-secondary">{detailSource?.registry?.sequence ?? 'Not available'}</dd></div>
          <div><dt className="text-ink-quiet">Last Registry update</dt><dd className="mt-1 text-ink-secondary">{receiver.lastRegistryUpdateAt ? formatDateTime(receiver.lastRegistryUpdateAt) : 'Not available'}</dd></div>
          <div><dt className="text-ink-quiet">Owner-declared stream endpoint</dt><dd className="mt-1 break-all font-mono text-ink-secondary">{declaredStream ?? 'Not published'}</dd></div>
          <div><dt className="text-ink-quiet">Owner-declared stream format</dt><dd className="mt-1 text-ink-secondary">{[receiver.registry?.registry?.stream_protocol, receiver.registry?.registry?.stream_format].filter(Boolean).join(' / ') || 'Not published'}</dd></div>
          <div className="flex items-start gap-2 rounded-md bg-trust-cyan/[0.06] p-2.5 text-ink-quiet"><ShieldCheck className="mt-0.5 size-3.5 shrink-0 text-trust-cyan" />CKB proves lifecycle continuity and owner authorization. It does not prove physical location, receiver hardware, clock quality, or feed honesty.</div>
        </dl>
      </details>
    </Inspector>
  );
}
