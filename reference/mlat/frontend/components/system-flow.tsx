'use client';

import { ArrowRight, Check, CircleDashed, CircleX, Clock3, type LucideIcon } from 'lucide-react';
import type { StatusTone } from '@/lib/types';
import { cn } from '@/lib/utils';

export interface FlowNode {
  id: string;
  label: string;
  detail?: string;
  tone: StatusTone;
  icon?: LucideIcon;
}

function NodeIcon({ node }: { node: FlowNode }) {
  if (node.icon) {
    const Icon = node.icon;
    return <Icon className="size-4" />;
  }
  if (node.tone === 'healthy') return <Check className="size-4" />;
  if (node.tone === 'failure') return <CircleX className="size-4" />;
  if (node.tone === 'replay') return <Clock3 className="size-4" />;
  return <CircleDashed className="size-4" />;
}

export function SystemFlow({ nodes, ariaLabel }: { nodes: FlowNode[]; ariaLabel: string }) {
  return (
    <ol aria-label={ariaLabel} className="flex flex-wrap items-center gap-y-5 px-5 py-5">
      {nodes.map((node, index) => (
        <li key={node.id} className="flex min-w-0 basis-1/2 items-start sm:basis-1/3 md:basis-1/4 xl:basis-auto xl:flex-1">
          <div className="min-w-0 flex-1 text-center">
            <span className={cn('mx-auto flex size-9 items-center justify-center rounded-full border', node.tone === 'healthy' ? 'border-healthy/30 bg-healthy/10 text-healthy' : node.tone === 'failure' ? 'border-failure/30 bg-failure/10 text-failure' : node.tone === 'replay' ? 'border-replay/30 bg-replay/10 text-replay' : node.tone === 'trust' ? 'border-trust-cyan/30 bg-trust-cyan/10 text-trust-cyan' : 'border-attention/30 bg-attention/10 text-attention')}><NodeIcon node={node} /></span>
            <p className="mt-2 min-h-8 text-pretty text-xs font-semibold leading-4 text-ink">{node.label}</p>
            {node.detail ? <p className="mt-0.5 truncate text-[10px] text-ink-quiet">{node.detail}</p> : null}
            <span className="sr-only">Status: {node.tone}</span>
          </div>
          {index < nodes.length - 1 ? <div aria-hidden="true" className="relative mx-1 mt-[18px] h-px w-5 shrink-0 bg-line"><ArrowRight className="absolute -right-1 -top-[6px] size-3 text-ink-quiet" />{node.tone === 'healthy' ? <span className="absolute -top-0.5 right-0 size-1 rounded-full bg-healthy" /> : null}</div> : null}
        </li>
      ))}
    </ol>
  );
}
