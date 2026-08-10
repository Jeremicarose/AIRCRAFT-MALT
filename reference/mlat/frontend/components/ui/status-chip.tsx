import { CircleCheck, CircleDashed, CircleX, Clock3, Radio, ShieldCheck, TriangleAlert, type LucideIcon } from 'lucide-react';
import type { StatusTone } from '@/lib/types';
import { cn } from '@/lib/utils';

const toneStyles: Record<StatusTone, string> = {
  healthy: 'bg-healthy/10 text-[#83e5ad]',
  attention: 'bg-attention/10 text-[#f2d77e]',
  replay: 'bg-replay/10 text-[#f6b67d]',
  failure: 'bg-failure/10 text-[#ff9ba0]',
  selection: 'bg-signal-blue/12 text-[#9fc4ff]',
  trust: 'bg-trust-cyan/10 text-[#9ce8f2]',
  neutral: 'bg-white/[0.055] text-ink-secondary',
};

const toneTextStyles: Record<StatusTone, string> = {
  healthy: 'text-healthy',
  attention: 'text-attention',
  replay: 'text-replay',
  failure: 'text-failure',
  selection: 'text-signal-blue',
  trust: 'text-trust-cyan',
  neutral: 'text-ink-quiet',
};

const toneSurfaceStyles: Record<StatusTone, string> = {
  healthy: 'bg-healthy/10 text-healthy',
  attention: 'bg-attention/10 text-attention',
  replay: 'bg-replay/10 text-replay',
  failure: 'bg-failure/10 text-failure',
  selection: 'bg-signal-blue/10 text-signal-blue',
  trust: 'bg-trust-cyan/10 text-trust-cyan',
  neutral: 'bg-white/[0.055] text-ink-quiet',
};

const toneIcons: Record<StatusTone, LucideIcon> = {
  healthy: CircleCheck,
  attention: TriangleAlert,
  replay: Clock3,
  failure: CircleX,
  selection: Radio,
  trust: ShieldCheck,
  neutral: CircleDashed,
};

export function toneTextClass(tone: StatusTone) {
  return toneTextStyles[tone];
}

export function toneSurfaceClass(tone: StatusTone) {
  return toneSurfaceStyles[tone];
}

export function StatusIcon({ tone = 'neutral', label, className }: { tone?: StatusTone; label?: string; className?: string }) {
  const Icon = toneIcons[tone];
  return (
    <span
      className={cn('flex size-7 shrink-0 items-center justify-center rounded-full', toneSurfaceStyles[tone], className)}
      role={label ? 'img' : undefined}
      aria-label={label}
      aria-hidden={label ? undefined : true}
    >
      <Icon className="size-3.5" strokeWidth={2.25} />
    </span>
  );
}

export function StatusChip({ label, tone = 'neutral', className }: { label: string; tone?: StatusTone; className?: string }) {
  const Icon = toneIcons[tone];
  return (
    <span className={cn('inline-flex h-6 shrink-0 items-center gap-1.5 rounded-full px-2 text-[11px] font-semibold leading-none', toneStyles[tone], className)}>
      <Icon aria-hidden="true" className="size-3" strokeWidth={2.25} />
      <span>{label}</span>
    </span>
  );
}

export function HealthIndicator({ tone = 'neutral', label }: { tone?: StatusTone; label: string }) {
  return (
    <span className="inline-flex items-center gap-2 text-xs font-medium text-ink-secondary">
      <span className={cn('size-1.5 rounded-full', {
        'bg-healthy': tone === 'healthy',
        'bg-attention': tone === 'attention',
        'bg-replay': tone === 'replay',
        'bg-failure': tone === 'failure',
        'bg-signal-blue': tone === 'selection',
        'bg-trust-cyan': tone === 'trust',
        'bg-ink-quiet': tone === 'neutral',
      })} />
      {label}
    </span>
  );
}
