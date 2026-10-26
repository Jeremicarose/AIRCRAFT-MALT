'use client';

import { ArrowRight, Award, Check, Compass, Pause, Play, RotateCcw, X } from 'lucide-react';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import { Button, buttonVariants } from '@/components/ui/button';
import { useMissionStore } from '@/lib/mission-store';
import { missionProgress, missions, totalMissionPoints } from '@/lib/missions';
import { cn } from '@/lib/utils';

export function MissionShortcut({ collapsed }: { collapsed: boolean }) {
  const completed = useMissionStore((state) => state.completed);
  const enabled = useMissionStore((state) => state.enabled);
  const progress = missionProgress(completed);
  return <Link href="/app/guide" aria-label={`Explorer missions: ${completed.length} of ${missions.length} complete${enabled ? '' : ', paused'}`} className={cn('flex items-center gap-2 rounded-md px-2 py-2 text-xs text-ink-secondary hover:bg-graphite-hover focus-visible:outline-2', collapsed && 'justify-center')}>
    <Compass className="size-4 shrink-0 text-signal-blue" aria-hidden="true" />
    {!collapsed ? <span className="min-w-0 flex-1"><span className="flex items-center justify-between gap-2 font-semibold"><span>Explorer missions</span><span className="text-ink-quiet">{enabled ? `${completed.length}/${missions.length}` : 'Paused'}</span></span><span aria-hidden="true" className="mt-2 block h-1 overflow-hidden rounded-full bg-line"><span className="block h-full origin-left bg-signal-blue transition-transform duration-standard" style={{ transform: `scaleX(${progress.percent / 100})` }} /></span></span> : null}
  </Link>;
}

export function MissionFeedback() {
  const latest = useMissionStore((state) => state.latest);
  const dismiss = useMissionStore((state) => state.dismiss);
  const mission = missions.find((item) => item.id === latest);
  useEffect(() => { if (latest) { const timer = setTimeout(dismiss, 6500); return () => clearTimeout(timer); } }, [latest, dismiss]);
  return <div aria-live="polite" aria-atomic="true" className="pointer-events-none fixed bottom-4 right-4 z-toast max-w-[calc(100vw-2rem)]">
    {mission ? <div key={mission.id} className="mission-earned pointer-events-auto flex max-w-sm items-start gap-3 rounded-lg border border-signal-blue/50 bg-graphite-raised p-4">
      <Award className="mt-0.5 size-5 shrink-0 text-signal-blue" aria-hidden="true" />
      <div className="min-w-0"><p className="text-sm font-semibold text-ink">{mission.badge} earned <span className="text-signal-blue">+{mission.points} XP</span></p><Link href="/app/guide" className="mt-1 inline-block text-xs text-ink-secondary underline underline-offset-4">View your learning progress</Link></div>
      <Button variant="ghost" size="icon-sm" onClick={dismiss} aria-label="Dismiss mission update"><X className="size-4" /></Button>
    </div> : null}
  </div>;
}

export function MissionChallenge({ kind }: { kind: 'source' | 'benchmark' }) {
  const completed = useMissionStore((state) => state.completed.includes(kind));
  const enabled = useMissionStore((state) => state.enabled);
  const hydrated = useMissionStore((state) => state.hydrated);
  const complete = useMissionStore((state) => state.complete);
  const [answer, setAnswer] = useState<string | null>(null);
  useEffect(() => { if (!completed) setAnswer(null); }, [completed]);
  const source = kind === 'source';
  const options = source ? [
    { id: 'hardware', label: 'The receiver is physically present with an accurate clock.' },
    { id: 'authorization', label: 'The recorded owner lock and lifecycle state follow the contract rules.' },
    { id: 'accuracy', label: 'Every observation from the receiver is accurate.' },
  ] : [
    { id: 'truth', label: 'The calculated position is independently verified ground truth.' },
    { id: 'fit', label: 'The timing observations fit the model; actual position error can still be large.' },
    { id: 'live', label: 'The historical benchmark proves a live receiver deployment.' },
  ];
  const correct = source ? 'authorization' : 'fit';
  const explanation = source
    ? 'The owner lock sets who can authorize spending the registry cell. CKB enforces lifecycle rules; hardware location, clock quality, and observation truth need separate evidence.'
    : 'Residual measures model fit. Geometry and timing errors can still produce a wrong position, so inspect reference error and rejected events too.';
  return <section id={`${kind}-challenge`} aria-label={source ? 'Source challenge' : 'Benchmark challenge'} className="scroll-mt-36 rounded-lg border border-line bg-graphite p-4 sm:p-5">
    <div className="flex flex-wrap items-center justify-between gap-2"><h3 className="text-sm font-semibold text-ink">{source ? 'What does a CKB Registry record verify?' : 'What does a small solver residual tell you?'}</h3><span className="text-xs font-semibold text-signal-blue">{completed ? 'Badge earned' : `${source ? 25 : 50} XP challenge`}</span></div>
    {completed ? <p className="mt-3 text-sm leading-6 text-ink-secondary"><Check className="mr-2 inline size-4 text-healthy" aria-hidden="true" />{explanation}</p> : <fieldset disabled={!enabled || !hydrated} className="mt-4 space-y-2">
      <legend className="sr-only">Choose the accurate interpretation</legend>
      {options.map((option) => <button key={option.id} type="button" aria-pressed={answer === option.id} onClick={() => { setAnswer(option.id); if (option.id === correct) complete(kind); }} className={cn('block w-full rounded-md border border-line px-3 py-3 text-left text-sm leading-5 text-ink-secondary transition-colors hover:border-signal-blue hover:text-ink focus-visible:outline-2 disabled:opacity-50', answer === option.id && 'border-attention text-attention')}>
        {option.label}
      </button>)}
    </fieldset>}
    {!enabled && !completed ? <p className="mt-3 text-xs text-ink-quiet">Missions are paused. Resume them in Explorer missions.</p> : null}
    <p role="status" className="mt-3 text-xs leading-5 text-ink-secondary">{answer && answer !== correct && !completed ? `Try again. ${explanation}` : ''}</p>
  </section>;
}

export function ExplorerMissionsPage() {
  const completed = useMissionStore((state) => state.completed);
  const enabled = useMissionStore((state) => state.enabled);
  const hydrated = useMissionStore((state) => state.hydrated);
  const setEnabled = useMissionStore((state) => state.setEnabled);
  const reset = useMissionStore((state) => state.reset);
  const [confirmReset, setConfirmReset] = useState(false);
  const progress = missionProgress(completed);
  return <div className="space-y-6" data-explorer-missions>
    <div className="flex flex-wrap items-start justify-between gap-4 border-b border-line pb-5">
      <div className="max-w-2xl"><h2 className="text-2xl font-semibold text-ink">Turn curiosity into a useful investigation.</h2><p className="mt-3 text-sm leading-6 text-ink-secondary">Six missions take you from receiver identity to a report someone can reproduce. Earn experience points (XP) and badges while learning what each piece of evidence really means.</p></div>
      <Button variant="secondary" size="sm" disabled={!hydrated} onClick={() => setEnabled(!enabled)}>{enabled ? <Pause className="size-4" /> : <Play className="size-4" />}{enabled ? 'Pause missions' : 'Resume missions'}</Button>
    </div>
    <div className="border-b border-line pb-4 xl:hidden" aria-label="Mission progress summary">
      <div className="flex justify-between gap-3 text-xs"><span className="font-semibold text-ink">{progress.rank}</span><span className="text-signal-blue">{progress.points} / {totalMissionPoints} XP</span></div>
      <progress value={progress.points} max={totalMissionPoints} aria-label="Mobile learning experience points" className="mission-progress mt-2 h-1.5 w-full" />
      <p className="mt-1 text-xs text-ink-quiet">{completed.length} of {missions.length} missions completed{enabled ? '' : ' · Missions paused'}</p>
    </div>
    <div className="grid items-start gap-6 xl:grid-cols-[minmax(0,1fr)_300px]">
      <div><ol aria-label="Explorer missions" className="divide-y divide-line border-y border-line">
        {missions.map((mission, index) => { const done = completed.includes(mission.id); return <li key={mission.id} className="flex gap-3 py-5 sm:gap-4">
          <span aria-hidden="true" className={cn('mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-full border text-xs font-semibold', done ? 'border-healthy/40 bg-healthy/10 text-healthy' : 'border-line text-ink-quiet')}>{done ? <Check className="size-4" /> : index + 1}</span>
          <div className="min-w-0 flex-1"><div className="flex flex-wrap items-center justify-between gap-2"><h3 className="text-sm font-semibold text-ink">{mission.title}</h3><span className={cn('text-xs font-medium', done ? 'text-healthy' : 'text-signal-blue')}>{done ? 'Completed' : `+${mission.points} XP`}</span></div><p className="mt-2 max-w-xl text-sm leading-6 text-ink-secondary">{mission.detail}</p><p className="mt-1 text-xs leading-5 text-ink-quiet">{mission.requirement}</p><Link href={mission.href} className="mt-3 inline-flex min-h-9 items-center gap-2 rounded-sm text-xs font-semibold text-signal-blue hover:text-ink focus-visible:outline-2">{done ? 'Revisit mission' : mission.action}<ArrowRight className="size-3.5" /></Link></div>
        </li>; })}
      </ol><div className="mt-6"><MissionChallenge kind="source" /></div></div>
      <aside aria-label="Learning progress" className="rounded-lg border border-line bg-graphite-raised p-5 xl:sticky xl:top-36">
        <Compass className="size-7 text-signal-blue" aria-hidden="true" /><p className="mt-4 text-xs text-ink-quiet">Your explorer level{enabled ? '' : ' · Paused'}</p><h3 className="mt-1 text-lg font-semibold text-ink">{progress.rank}</h3>
        <div className="mt-4 flex justify-between text-xs text-ink-secondary"><span>{completed.length} of {missions.length} missions</span><span>{progress.points} / {totalMissionPoints} XP</span></div>
        <progress value={progress.points} max={totalMissionPoints} aria-label="Learning experience points" className="mission-progress mt-2 h-2 w-full" />
        <p className="mt-4 text-xs leading-5 text-ink-secondary">{progress.next ? `Up next: ${progress.next.title}.` : 'All six badges earned. You have explored the complete investigation workflow.'}</p>
        <div className="mt-5 border-t border-line pt-4"><h4 className="text-xs font-semibold text-ink">Your badges</h4><ul className="mt-3 space-y-3">{missions.map((mission) => <li key={mission.id} className={cn('flex items-center gap-2 text-xs', completed.includes(mission.id) ? 'text-ink' : 'text-ink-quiet')}><Award className={cn('size-4', completed.includes(mission.id) && 'text-signal-blue')} aria-hidden="true" /><span>{mission.badge}</span><span className="sr-only">{completed.includes(mission.id) ? ', earned' : ', not yet earned'}</span></li>)}</ul></div>
        <p className="mt-5 border-t border-line pt-4 text-xs leading-5 text-ink-quiet">Learning progress is saved in this browser only. If browser storage is blocked, it lasts for this visit. Points are not tokens, receiver qualifications, or a production-readiness score. No wallet is needed.</p>
        {confirmReset ? <div className="mt-4 text-xs"><p className="leading-5 text-ink-secondary">Clear your six mission badges in this browser? Application data is unaffected.</p><div className="mt-3 flex flex-wrap gap-2"><Button size="sm" variant="secondary" onClick={() => { reset(); setConfirmReset(false); }}>Reset progress</Button><Button size="sm" variant="ghost" onClick={() => setConfirmReset(false)}>Keep progress</Button></div></div> : <button type="button" disabled={!completed.length} onClick={() => setConfirmReset(true)} className="mt-4 flex min-h-9 items-center gap-2 rounded-sm text-xs text-ink-secondary hover:text-ink focus-visible:outline-2 disabled:opacity-50"><RotateCcw className="size-3.5" />Reset learning progress</button>}
      </aside>
    </div>
    <div className="flex flex-wrap items-center justify-between gap-4 border-t border-line pt-4"><p className="max-w-2xl text-xs leading-5 text-ink-quiet">Missions never require signing a transaction or declaring a receiver ready. Some need an available service; the replay mission needs historical replay mode.</p><Link href="/app/environment" className={buttonVariants({ variant: 'secondary', size: 'sm' })}>Check available services<ArrowRight className="size-4" /></Link></div>
  </div>;
}
