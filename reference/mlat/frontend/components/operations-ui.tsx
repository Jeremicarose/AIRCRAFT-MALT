'use client';

import { motion } from 'framer-motion';
import { ArrowUpRight, ShieldCheck } from 'lucide-react';
import Link from 'next/link';
import type { ReactNode } from 'react';
import type { InvestigationAction, InvestigationCard, InvestigationEvent, InvestigationFact, StatusTone } from '@/lib/types';
import { cn } from '@/lib/utils';
import { StatusChip, StatusIcon } from '@/components/ui/status-chip';
import { buttonVariants } from '@/components/ui/button';

export function EvidenceCard({ title, state, tone = 'neutral', children, action }: { title: string; state?: string; tone?: StatusTone; children: ReactNode; action?: ReactNode }) {
  return (
    <motion.div layout className="border-b border-line py-3 last:border-0" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.18, ease: [0.22, 1, 0.36, 1] }}>
      <div className="flex items-center justify-between gap-3"><p className="text-xs font-semibold text-ink">{title}</p>{state ? <StatusChip label={state} tone={tone} /> : null}</div>
      <div className="mt-2 text-xs leading-5 text-ink-quiet">{children}</div>
      {action ? <div className="mt-2">{action}</div> : null}
    </motion.div>
  );
}

export function Inspector({ title, subtitle, status, actions, children, className }: { title: string; subtitle?: ReactNode; status?: ReactNode; actions?: ReactNode; children: ReactNode; className?: string }) {
  return (
    <aside className={cn('overflow-hidden rounded-lg border border-line bg-graphite', className)}>
      <div className="border-b border-line p-4">
        <div className="flex items-start justify-between gap-3"><div className="min-w-0"><h2 className="truncate text-base font-semibold text-ink">{title}</h2>{subtitle ? <p className="mt-1 text-xs text-ink-quiet">{subtitle}</p> : null}</div>{status}</div>
        {actions ? <div className="mt-3 flex gap-2">{actions}</div> : null}
      </div>
      {children}
    </aside>
  );
}

export function FactGrid({ items }: { items: Array<{ label: string; value: ReactNode; mono?: boolean }> }) {
  return <dl className="grid grid-cols-2 gap-px bg-line">{items.map((item) => <div key={item.label} className="min-w-0 bg-graphite px-4 py-3"><dt className="text-[11px] font-medium text-ink-quiet">{item.label}</dt><dd className={cn('mt-1 truncate text-xs font-semibold text-ink-secondary tabular-nums', item.mono && 'font-mono')}>{item.value}</dd></div>)}</dl>;
}

export function Timeline({ items }: { items: Array<{ title: string; detail: ReactNode; tone?: StatusTone; meta?: string }> }) {
  return <ol className="p-4">{items.map((item, index) => { const tone = item.tone ?? 'neutral'; return <li key={`${item.title}-${index}`} className="relative flex gap-3 pb-4 last:pb-0"><StatusIcon tone={tone} label={`${item.title}: ${tone}`} className="relative z-10 mt-0.5 size-5" />{index < items.length - 1 ? <span aria-hidden="true" className="absolute left-[9px] top-5 h-[calc(100%-14px)] w-px bg-line" /> : null}<div className="min-w-0"><div className="flex items-center gap-2"><p className="text-xs font-semibold text-ink">{item.title}</p>{item.meta ? <span className="text-[11px] text-ink-quiet">{item.meta}</span> : null}</div><p className="mt-0.5 text-xs leading-5 text-ink-quiet">{item.detail}</p></div></li>; })}</ol>;
}

export function ConfidenceGauge({ value, label = 'Confidence', detail = 'Latest solve quality', color = '#5b9cff' }: { value: number; label?: string; detail?: string; color?: string }) {
  const safeValue = Number.isFinite(value) ? Math.max(0, Math.min(1, value)) : 0;
  const degrees = safeValue * 360;
  return <div className="flex items-center gap-3"><div className="relative size-14 rounded-full" style={{ background: `conic-gradient(${color} ${degrees}deg, #242a32 ${degrees}deg)` }} role="img" aria-label={`${label}: ${Math.round(safeValue * 100)} percent`}><div className="absolute inset-[5px] flex items-center justify-center rounded-full bg-graphite text-[11px] font-semibold text-ink tabular-nums" aria-hidden="true">{Math.round(safeValue * 100)}%</div></div><div><p className="text-xs font-semibold text-ink">{label}</p><p className="mt-0.5 text-[11px] text-ink-quiet">{detail}</p></div></div>;
}

export function TrustRow({ label = 'Registry identity verified', detail }: { label?: string; detail: string }) {
  return <div className="flex items-start gap-3 p-4"><div className="flex size-8 shrink-0 items-center justify-center rounded-md bg-trust-cyan/10"><ShieldCheck className="size-4 text-trust-cyan" /></div><div className="min-w-0"><p className="text-xs font-semibold text-ink">{label}</p><p className="mt-1 truncate font-mono text-[11px] text-ink-quiet">{detail}</p></div></div>;
}

export function InvestigationFacts({ items }: { items: InvestigationFact[] }) {
  return (
    <dl className="grid gap-2 p-4 sm:grid-cols-2">
      {items.map((item) => (
        <div key={item.label} className="rounded-md border border-line bg-graphite-raised/55 px-3 py-2.5">
          <dt className="text-[10px] font-semibold uppercase tracking-[0.16em] text-ink-quiet">{item.label}</dt>
          <dd className={cn('mt-1 text-xs font-semibold text-ink-secondary', item.mono && 'font-mono', item.tone === 'healthy' && 'text-healthy', item.tone === 'attention' && 'text-attention', item.tone === 'failure' && 'text-failure', item.tone === 'trust' && 'text-trust-cyan')}>{item.value}</dd>
        </div>
      ))}
    </dl>
  );
}

export function InvestigationTimeline({ items }: { items: InvestigationEvent[] }) {
  return <Timeline items={items.map((item) => ({ title: item.title, detail: item.detail, tone: item.tone, meta: item.meta }))} />;
}

export function InvestigationEvidenceList({ items }: { items: InvestigationCard[] }) {
  return (
    <div className="px-4 py-2">
      {items.map((item) => (
        <EvidenceCard key={`${item.title}-${item.detail}`} title={item.title} state={item.state} tone={item.tone}>
          {item.detail}
        </EvidenceCard>
      ))}
    </div>
  );
}

export function InvestigationActions({ actions }: { actions: InvestigationAction[] }) {
  return (
    <div className="flex flex-wrap gap-2 p-4">
      {actions.map((action) => (
        <Link key={`${action.href}-${action.label}`} href={action.href} className={buttonVariants({ variant: action.tone === 'primary' ? 'primary' : 'secondary', size: 'sm' })}>
          {action.label}
        </Link>
      ))}
    </div>
  );
}

export function WorkspaceHeader({ eyebrow, title, description, status, actions, rail }: { eyebrow?: string; title: string; description?: ReactNode; status?: ReactNode; actions?: ReactNode; rail?: ReactNode }) {
  return (
    <motion.div layout initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2, ease: [0.22, 1, 0.36, 1] }} className="overflow-hidden rounded-xl border border-line bg-[linear-gradient(180deg,rgba(17,21,26,0.97),rgba(10,13,17,0.94))] shadow-[inset_0_1px_0_rgba(255,255,255,0.04),0_24px_60px_-42px_rgba(0,0,0,0.85)]">
      <div className="p-5">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
          <div className="min-w-0">
            {eyebrow ? <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-trust-cyan">{eyebrow}</p> : null}
            <h2 className="mt-1 text-lg font-semibold text-ink sm:text-xl">{title}</h2>
            {description ? <div className="mt-2 max-w-3xl text-sm leading-6 text-ink-quiet">{description}</div> : null}
          </div>
          <div className="flex flex-wrap items-center gap-2">{status}{actions}</div>
        </div>
      </div>
      {rail ? <div className="border-t border-line/80 bg-[#0d1116]/86 px-5 py-3">{rail}</div> : null}
    </motion.div>
  );
}

export function WorkspacePanel({ title, detail, action, children, className, tone = 'neutral', padded = false, chrome }: { title: string; detail?: string; action?: ReactNode; children: ReactNode; className?: string; tone?: StatusTone; padded?: boolean; chrome?: ReactNode }) {
  const glow = tone === 'failure'
    ? 'shadow-[inset_0_1px_0_rgba(255,255,255,0.02),0_0_0_1px_rgba(239,107,114,0.08)]'
    : tone === 'attention'
      ? 'shadow-[inset_0_1px_0_rgba(255,255,255,0.02),0_0_0_1px_rgba(230,196,93,0.08)]'
      : tone === 'trust'
        ? 'shadow-[inset_0_1px_0_rgba(255,255,255,0.02),0_0_0_1px_rgba(104,213,232,0.08)]'
        : 'shadow-[inset_0_1px_0_rgba(255,255,255,0.02)]';
  return (
    <motion.section layout initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.18, ease: [0.22, 1, 0.36, 1] }} className={cn('overflow-hidden rounded-xl border border-line bg-[linear-gradient(180deg,rgba(14,18,23,0.98),rgba(10,13,17,0.96))]', glow, className)}>
      <div className="flex min-h-14 items-center justify-between gap-4 border-b border-line px-4 py-3">
        <div className="min-w-0">
          <h3 className="text-sm font-semibold text-ink">{title}</h3>
          {detail ? <p className="mt-0.5 text-xs leading-5 text-ink-quiet">{detail}</p> : null}
        </div>
        <div className="flex shrink-0 items-center gap-2">{chrome}{action ? <div className="shrink-0">{action}</div> : null}</div>
      </div>
      <div className={cn(padded && 'p-4')}>{children}</div>
    </motion.section>
  );
}

export function WorkspaceSplit({ primary, secondary, secondaryWidth = '360px', className }: { primary: ReactNode; secondary: ReactNode; secondaryWidth?: string; className?: string }) {
  return <div className={cn('grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(320px,var(--secondary-width))]', className)} style={{ ['--secondary-width' as string]: secondaryWidth }}>{primary}{secondary}</div>;
}

export function SignalMarquee({ items }: { items: Array<{ label: string; value: string; tone?: StatusTone }> }) {
  if (!items.length) return null;
  return (
    <div className="flex gap-2 overflow-x-auto">
      {items.map((item) => (
        <div key={`${item.label}-${item.value}`} className="min-w-[140px] rounded-lg border border-line/80 bg-graphite-raised/45 px-3 py-2.5">
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-ink-quiet">{item.label}</p>
          <p className={cn('mt-1 text-sm font-semibold text-ink-secondary', item.tone === 'healthy' && 'text-healthy', item.tone === 'attention' && 'text-attention', item.tone === 'failure' && 'text-failure', item.tone === 'trust' && 'text-trust-cyan', item.tone === 'selection' && 'text-selection')}>{item.value}</p>
        </div>
      ))}
    </div>
  );
}

export function IssueList({ items }: { items: Array<{ title: string; detail: string; tone: StatusTone; href?: string; meta?: string }> }) {
  if (!items.length) {
    return <div className="grid min-h-40 place-items-center px-6 text-center text-xs text-ink-quiet">No current issues are ranked for operator review.</div>;
  }
  return (
    <div className="divide-y divide-line">
      {items.map((item, index) => {
        const content = (
          <>
            <div className="flex min-w-0 items-start gap-3">
              <span className={cn('mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-full text-[11px] font-semibold', item.tone === 'failure' ? 'bg-failure/10 text-failure' : item.tone === 'attention' ? 'bg-attention/10 text-attention' : item.tone === 'trust' ? 'bg-trust-cyan/10 text-trust-cyan' : item.tone === 'healthy' ? 'bg-healthy/10 text-healthy' : 'bg-signal-blue/10 text-signal-blue')}>{index + 1}</span>
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <p className="text-xs font-semibold text-ink">{item.title}</p>
                  {item.meta ? <span className="text-[10px] uppercase tracking-[0.14em] text-ink-quiet">{item.meta}</span> : null}
                </div>
                <p className="mt-1 text-xs leading-5 text-ink-quiet">{item.detail}</p>
              </div>
            </div>
            {item.href ? <ArrowUpRight className="mt-0.5 size-3.5 shrink-0 text-ink-quiet" /> : null}
          </>
        );
        return item.href ? (
          <Link key={`${item.title}-${index}`} href={item.href} className="flex items-start justify-between gap-3 px-4 py-3 outline-none transition-colors duration-standard hover:bg-graphite-hover/55 focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-signal-blue">
            {content}
          </Link>
        ) : (
          <div key={`${item.title}-${index}`} className="flex items-start justify-between gap-3 px-4 py-3">
            {content}
          </div>
        );
      })}
    </div>
  );
}

export function ActivityRail({ items }: { items: Array<{ title: string; detail: string; meta?: string; tone?: StatusTone; href?: string }> }) {
  if (!items.length) {
    return <div className="grid min-h-32 place-items-center px-6 text-center text-xs text-ink-quiet">No live activity is available in this window.</div>;
  }
  return (
    <div className="space-y-2 p-4">
      {items.map((item, index) => {
        const row = (
          <>
            <StatusIcon tone={item.tone ?? 'neutral'} className="size-6" />
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <p className="truncate text-xs font-semibold text-ink">{item.title}</p>
                {item.meta ? <span className="text-[10px] text-ink-quiet">{item.meta}</span> : null}
              </div>
              <p className="mt-0.5 text-[11px] leading-5 text-ink-quiet">{item.detail}</p>
            </div>
            {item.href ? <ArrowUpRight className="size-3.5 shrink-0 text-ink-quiet" /> : null}
          </>
        );
        const classes = cn('flex items-start gap-3 rounded-lg border border-line/70 bg-graphite-raised/35 px-3 py-2.5 transition-[transform,background-color,border-color] duration-standard', item.tone === 'failure' && 'border-failure/20', item.tone === 'attention' && 'border-attention/20', item.tone === 'trust' && 'border-trust-cyan/20');
        return item.href ? (
          <motion.div key={`${item.title}-${index}`} layout initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.16, delay: index * 0.02, ease: [0.22, 1, 0.36, 1] }}>
            <Link href={item.href} className={cn(classes, 'outline-none hover:-translate-y-0.5 hover:bg-graphite-hover focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-signal-blue')}>
              {row}
            </Link>
          </motion.div>
        ) : (
          <motion.div key={`${item.title}-${index}`} layout initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.16, delay: index * 0.02, ease: [0.22, 1, 0.36, 1] }} className={classes}>
            {row}
          </motion.div>
        );
      })}
    </div>
  );
}
