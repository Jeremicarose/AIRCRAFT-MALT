'use client';

import { Archive, CircleHelp, Radio, TestTube2, TriangleAlert } from 'lucide-react';
import Link from 'next/link';
import { StatusChip } from '@/components/ui/status-chip';
import { dataSourceState } from '@/lib/data-source';
import { consoleRoutes } from '@/lib/routes';
import type { ModeData, ShellSnapshot, StatusTone } from '@/lib/types';

interface OrientationState {
  label: string;
  detail: string;
  tone: StatusTone;
  next: string;
  href?: string;
}

function orientationState(pageKey: string, snapshot: ShellSnapshot, cached: boolean): OrientationState {
  const source = dataSourceState(snapshot.modeData, { cached });
  if (pageKey === 'registry') {
    return {
      label: 'CKB TESTNET DIRECTORY',
      detail: 'Owner-authorized Registry facts are read from the public CKB indexer. They do not prove physical receiver behavior.',
      tone: 'trust',
      next: 'Select a receiver to compare its Registry, operational, and MLAT states.',
    };
  }
  if (pageKey === 'settings') {
    return {
      label: 'BROWSER-LOCAL',
      detail: 'These preferences affect this browser only. They do not change the MLAT runtime or Registry contract.',
      tone: 'neutral',
      next: 'Adjust a preference; the change is saved locally and applied immediately.',
    };
  }
  if (pageKey === 'environment') {
    const runtimeActive = snapshot.modeData?.runtime_status === 'active';
    const discoveryLive = snapshot.modeData?.registry_discovery_live === true;
    return {
      label: runtimeActive && discoveryLive && source.kind === 'live' ? 'READY FOR REVIEW' : 'ACTION REQUIRED',
      detail: !runtimeActive
        ? 'The MLAT runtime is not active.'
        : !discoveryLive
          ? 'The runtime is active, but live Registry discovery is not connected.'
          : source.detail,
      tone: runtimeActive && discoveryLive && source.kind === 'live' ? 'healthy' : 'attention',
      next: 'Follow the first Not ready recovery check and confirm its expected result.',
    };
  }
  if (pageKey === 'benchmark') {
    return {
      label: 'HISTORICAL RECORDING',
      detail: 'Pinned public observations exercise the numerical solver only. They are not live aircraft activity or full-pipeline evidence.',
      tone: 'replay',
      next: 'Compare the selected example with the complete 362-event baseline before interpreting accuracy.',
    };
  }

  const nextByPage: Record<string, { next: string; href?: string }> = {
    overview: { next: 'Open Pipeline to inspect the first stage blocking publishable evidence.', href: '/app/pipeline' },
    localization: { next: 'Select a marker to inspect the position, source, and supporting receiver context.' },
    aircraft: { next: 'Select an aircraft, then inspect only the receivers named by its MLAT solution.' },
    receivers: { next: 'Select a receiver to see why it is or is not contributing to MLAT.' },
    pipeline: { next: 'Select the highest-ranked blocker to read its evidence and operator action.' },
    metrics: { next: 'Use Diagnostics before treating replay or constrained metrics as production evidence.', href: '/app/environment' },
  };
  const current = nextByPage[pageKey] ?? { next: 'Inspect the current state before taking action.' };
  return { label: source.label, detail: source.detail, tone: source.tone, ...current };
}

export function PageOrientation({ pageKey, snapshot, cached = false }: { pageKey: string; snapshot: ShellSnapshot; cached?: boolean }) {
  const route = consoleRoutes.find((item) => item.key === pageKey);
  const state = orientationState(pageKey, snapshot, cached);
  const source = dataSourceState(snapshot.modeData, { cached });
  const benchmarkPage = pageKey === 'benchmark';
  const sourcePage = !['registry', 'settings', 'environment'].includes(pageKey);
  const presentedSource = benchmarkPage ? { kind: 'historical', label: 'Historical recording' } : source;
  const Icon = benchmarkPage
    ? Archive
    : sourcePage
    ? source.kind === 'live'
      ? Radio
      : source.kind === 'replay'
        ? Archive
        : source.kind === 'simulation'
          ? TestTube2
          : source.kind === 'cached'
            ? TriangleAlert
            : CircleHelp
    : pageKey === 'registry'
      ? Radio
      : pageKey === 'environment'
        ? TriangleAlert
        : CircleHelp;

  return (
    <section
      aria-label={sourcePage ? `Data source: ${presentedSource.label}` : 'Page orientation'}
      data-data-source={sourcePage ? presentedSource.kind : undefined}
      className="mb-4 grid overflow-hidden border-y border-line bg-graphite sm:grid-cols-3 sm:divide-x sm:divide-line"
    >
      <div className="flex min-w-0 gap-3 border-b border-line px-4 py-3 sm:border-b-0">
        <span className="flex size-8 shrink-0 items-center justify-center rounded-md bg-graphite-raised" aria-hidden="true"><Icon className="size-4 text-ink-secondary" /></span>
        <div className="min-w-0"><p className="text-xs font-semibold text-ink">What you are viewing</p><p className="mt-1 text-xs leading-5 text-ink-secondary">{route?.detail ?? 'Application workspace'}</p></div>
      </div>
      <div className="min-w-0 border-b border-line px-4 py-3 sm:border-b-0" aria-live="polite" aria-atomic="true">
        <p className="text-xs font-semibold text-ink">Current state</p>
        <div className="mt-1.5"><StatusChip label={state.label} tone={state.tone} /></div>
        <p className="mt-1.5 text-xs leading-5 text-ink-secondary">{state.detail}</p>
      </div>
      <div className="min-w-0 px-4 py-3">
        <p className="text-xs font-semibold text-ink">Next step</p>
        {state.href ? <Link href={state.href} className="mt-1 block rounded-sm text-xs font-medium leading-5 text-signal-blue outline-none hover:text-[#8db9ff] focus-visible:ring-2 focus-visible:ring-signal-blue">{state.next}</Link> : <p className="mt-1 text-xs font-medium leading-5 text-ink-secondary">{state.next}</p>}
      </div>
    </section>
  );
}

export function DataSourceBanner({ modeData, cached = false }: { modeData: ModeData | null; cached?: boolean }) {
  const source = dataSourceState(modeData, { cached });
  const Icon = source.kind === 'live'
    ? Radio
    : source.kind === 'replay'
      ? Archive
      : source.kind === 'simulation'
        ? TestTube2
        : source.kind === 'cached'
          ? TriangleAlert
          : CircleHelp;

  return (
    <section
      aria-label={`Data source: ${source.label}`}
      data-data-source={source.kind}
      className="mb-4 flex items-start gap-3 rounded-md border border-line bg-graphite px-4 py-3"
    >
      <span className="flex size-8 shrink-0 items-center justify-center rounded-md bg-graphite-raised" aria-hidden="true">
        <Icon className="size-4 text-ink-secondary" />
      </span>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <p className="text-sm font-semibold text-ink">Observation source</p>
          <StatusChip label={source.label} tone={source.tone} />
        </div>
        <p className="mt-1 max-w-3xl text-xs leading-5 text-ink-secondary">{source.detail}</p>
      </div>
    </section>
  );
}
