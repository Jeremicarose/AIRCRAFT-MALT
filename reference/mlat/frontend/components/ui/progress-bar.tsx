'use client';

import { motion, useReducedMotion } from 'framer-motion';
import type { StatusTone } from '@/lib/types';
import { cn } from '@/lib/utils';

export function ProgressBar({ value, tone = 'selection', label }: { value: number; tone?: StatusTone; label: string }) {
  const reduceMotion = useReducedMotion();
  const safeValue = Number.isFinite(value) ? Math.max(0, Math.min(100, value)) : 0;
  return (
    <div className="h-1.5 overflow-hidden rounded-full bg-graphite-raised" role="progressbar" aria-label={label} aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(safeValue)}>
      <motion.div
        className={cn('h-full rounded-full', tone === 'healthy' ? 'bg-healthy' : tone === 'failure' ? 'bg-failure' : tone === 'attention' ? 'bg-attention' : tone === 'replay' ? 'bg-replay' : 'bg-signal-blue')}
        initial={false}
        animate={{ width: `${safeValue}%` }}
        transition={{ duration: reduceMotion ? 0 : 0.18, ease: [0.22, 1, 0.36, 1] }}
      />
    </div>
  );
}
