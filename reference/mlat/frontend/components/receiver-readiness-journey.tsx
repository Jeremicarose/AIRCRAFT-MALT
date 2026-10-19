'use client';

import { ArrowRight, Check, ChevronDown, CircleDashed, TriangleAlert } from 'lucide-react';
import Link from 'next/link';
import { buttonVariants } from '@/components/ui/button';
import type { UnifiedReceiver } from '@/lib/receiver-state';
import { cn } from '@/lib/utils';

type JourneyState = 'complete' | 'blocked' | 'waiting';

interface JourneyItem {
  label: string;
  detail: string;
  state: JourneyState;
}

function nextAction(receiver: UnifiedReceiver): { label: string; detail: string; href: string } {
  if (!receiver.identity) return { label: 'Register receiver', detail: 'Create a canonical Registry identity before this receiver can be qualified through Registry discovery.', href: '/app/registry' };
  if (receiver.registryStatus === 'revoked') return { label: 'Revocation is permanent', detail: 'This identity cannot return to the active pool. Historical lifecycle evidence remains available.', href: `/app/registry?receiver=${encodeURIComponent(receiver.identity)}` };
  if (receiver.registryStatus === 'conflict' || receiver.registryStatus === 'invalid') return { label: 'Resolve identity integrity', detail: 'The runtime fails closed until Registry discovery returns one valid canonical identity.', href: '/app/environment' };
  if (!receiver.registryEligible) return { label: 'Update Registry readiness', detail: 'Publish an online declaration with the MLAT capability, then refresh backend Registry discovery.', href: `/app/registry?receiver=${encodeURIComponent(receiver.identity)}` };
  if (receiver.operationalStatus !== 'online') return { label: 'Connect or restore the feed', detail: 'Configure the MLAT runtime to discover this identity and receive fresh qualified observations.', href: '/app/environment' };
  if (receiver.qualificationState !== 'QUALIFIED') return { label: 'Qualify receiver clock', detail: receiver.runtime?.qualification?.action ?? 'Verify timing source, synchronization, and clock uncertainty before MLAT participation.', href: '/app/environment' };
  if (receiver.mlatStatus !== 'contributing') return { label: 'Inspect the solve pipeline', detail: 'The receiver is eligible and online but is not included in a recent aircraft localization.', href: '/app/pipeline' };
  return { label: 'Inspect contributing aircraft', detail: 'Recent MLAT positions reference this receiver. Open an aircraft to inspect the solution and all contributors.', href: receiver.relatedAircraftIds[0] ? `/app/aircraft?aircraft=${encodeURIComponent(receiver.relatedAircraftIds[0])}` : '/app/aircraft' };
}

function journeyItems(receiver: UnifiedReceiver): JourneyItem[] {
  const hasIdentity = Boolean(receiver.identity);
  const registryActive = receiver.registryStatus === 'active';
  const discoveredByRuntime = Boolean(receiver.runtime && receiver.identity);
  const readinessPassed = receiver.registryEligible;
  const feedAvailable = receiver.operationalStatus === 'online';
  const qualified = receiver.qualificationState === 'QUALIFIED' && readinessPassed && feedAvailable;
  const clock = receiver.runtime?.qualification;
  const clockDetail = `Clock source: ${clock?.clock_source ?? 'not provided'}. Uncertainty: ${clock?.clock_uncertainty_ns == null ? 'not provided' : `${clock.clock_uncertainty_ns} ns`}. Required maximum: ${clock?.maximum_clock_uncertainty_ns == null ? 'not provided' : `${clock.maximum_clock_uncertainty_ns} ns`}.`;
  const contributing = receiver.mlatStatus === 'contributing';
  const usedInPosition = receiver.relatedAircraftIds.length > 0;
  const permanentBlock = ['revoked', 'conflict', 'invalid'].includes(receiver.registryStatus);

  const state = (complete: boolean, blocked = false): JourneyState => complete ? 'complete' : blocked ? 'blocked' : 'waiting';
  return [
    { label: '1. Receiver registered', detail: hasIdentity ? 'A Registry record exists on CKB.' : 'No canonical Registry record is attached.', state: state(hasIdentity) },
    { label: '2. Registry identity active', detail: registryActive ? 'The canonical identity is active.' : `Registry state: ${receiver.registryStatus.replace('_', ' ')}.`, state: state(registryActive, permanentBlock) },
    { label: '3. Discovered by MLAT runtime', detail: discoveredByRuntime ? 'The backend inventory uses this canonical identity.' : 'The backend has not matched this identity into its receiver inventory.', state: state(discoveredByRuntime, permanentBlock) },
    { label: '4. Registry readiness checked', detail: readinessPassed ? 'The record is declared online and includes the MLAT capability.' : 'The Registry status or capabilities do not pass the MLAT eligibility check.', state: state(readinessPassed, permanentBlock) },
    { label: '5. Observation feed available', detail: receiver.operationalReason, state: state(feedAvailable, receiver.operationalStatus === 'degraded' || receiver.operationalStatus === 'stale') },
    { label: '6. Qualified for MLAT', detail: `${qualified ? 'Registry, freshness, and clock checks pass.' : 'Clock qualification is required; registration alone does not qualify a receiver.'} ${clockDetail}`, state: state(qualified, permanentBlock) },
    { label: '7. Contributing observations', detail: contributing ? 'Recent MLAT solves reference this receiver.' : 'No recent MLAT solve currently references this receiver.', state: state(contributing, permanentBlock) },
    { label: '8. Used in aircraft position', detail: usedInPosition ? `${receiver.relatedAircraftIds.length} aircraft position${receiver.relatedAircraftIds.length === 1 ? '' : 's'} reference this receiver in the current window.` : 'No current aircraft position links to this receiver.', state: state(usedInPosition, permanentBlock) },
  ];
}

export function ReceiverReadinessJourney({ receiver }: { receiver: UnifiedReceiver }) {
  const action = nextAction(receiver);
  const items = journeyItems(receiver);
  const completed = items.filter((item) => item.state === 'complete').length;
  return (
    <section className="border-b border-line" aria-labelledby="receiver-readiness-title">
      <div className="border-b border-line px-4 py-3">
        <h3 id="receiver-readiness-title" className="text-sm font-semibold text-ink">Registry to MLAT journey</h3>
        <p className="mt-1 text-xs leading-5 text-ink-secondary">Registration creates identity. Contribution requires separate discovery, readiness, feed, and solve evidence.</p>
      </div>
      <div className="flex flex-col gap-3 bg-graphite-raised/45 p-4 sm:flex-row sm:items-center sm:justify-between" aria-label="Recommended next action">
        <div><p className="text-xs font-semibold text-ink">Next action: {action.label}</p><p className="mt-1 max-w-2xl text-xs leading-5 text-ink-secondary">{action.detail}</p></div>
        <Link href={action.href} className={buttonVariants({ variant: 'secondary', size: 'sm' })}>{action.label}<ArrowRight className="size-4" /></Link>
      </div>
      <details className="group">
        <summary className="flex min-h-11 cursor-pointer list-none items-center justify-between gap-3 px-4 py-3 text-xs font-semibold text-ink-secondary outline-none hover:bg-graphite-hover/55 hover:text-ink focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-signal-blue [&::-webkit-details-marker]:hidden">
          <span>View all 8 readiness stages ({completed} complete)</span>
          <ChevronDown className="size-4 shrink-0 transition-transform duration-standard group-open:rotate-180" aria-hidden="true" />
        </summary>
        <ol className="grid gap-px border-t border-line bg-line sm:grid-cols-2">
          {items.map((item) => {
            const Icon = item.state === 'complete' ? Check : item.state === 'blocked' ? TriangleAlert : CircleDashed;
            return (
              <li key={item.label} className="flex gap-3 bg-graphite p-3">
                <span className={cn('mt-0.5 flex size-6 shrink-0 items-center justify-center rounded-full', item.state === 'complete' ? 'bg-healthy/10 text-healthy' : item.state === 'blocked' ? 'bg-failure/10 text-failure' : 'bg-graphite-raised text-ink-quiet')} aria-hidden="true"><Icon className="size-3.5" /></span>
                <div><p className="text-xs font-semibold text-ink">{item.label}</p><p className="mt-0.5 text-xs leading-5 text-ink-quiet">{item.detail}</p></div>
              </li>
            );
          })}
        </ol>
      </details>
    </section>
  );
}
