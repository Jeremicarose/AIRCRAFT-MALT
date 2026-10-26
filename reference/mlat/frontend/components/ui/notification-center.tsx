'use client';

import * as DropdownMenu from '@radix-ui/react-dropdown-menu';
import { AlertTriangle, Bell, CheckCircle2, RadioTower, ShieldAlert } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { operatorNotices } from '@/lib/operator-notices';
import type { ShellSnapshot } from '@/lib/types';
import { cn } from '@/lib/utils';
import { useOperatorStore } from '@/lib/operator-store';

const noticeIcons = {
  runtime: AlertTriangle,
  registry: ShieldAlert,
  receivers: RadioTower,
};

export function NotificationCenter({ snapshot }: { snapshot: ShellSnapshot }) {
  const setInvestigationContext = useOperatorStore((state) => state.setInvestigationContext);
  const notices = operatorNotices(snapshot);
  const attentionCount = notices.length;

  return (
    <DropdownMenu.Root>
      <DropdownMenu.Trigger asChild>
        <Button variant="ghost" size="icon-sm" className="relative" aria-label={`Notifications${attentionCount ? `, ${attentionCount} need attention` : ''}`}>
          <Bell className="size-4" />
          {attentionCount ? <span className="absolute right-1 top-1 size-1.5 rounded-full bg-attention" /> : null}
        </Button>
      </DropdownMenu.Trigger>
      <DropdownMenu.Portal>
        <DropdownMenu.Content align="end" sideOffset={8} className="z-dropdown w-[min(360px,calc(100vw-24px))] overflow-hidden rounded-lg border border-line bg-[#11151a] shadow-overlay">
          <div className="flex items-center justify-between border-b border-line px-4 py-3"><div><p className="text-xs font-semibold text-ink">Notifications</p><p className="mt-0.5 text-[10px] text-ink-quiet">Errors and warnings that require action</p></div><span className="text-[11px] text-ink-quiet">{notices.length}</span></div>
          <div className="max-h-[380px] overflow-y-auto">{notices.length ? notices.map((notice) => {
            const Icon = noticeIcons[notice.id as keyof typeof noticeIcons] ?? AlertTriangle;
            return <DropdownMenu.Item key={notice.id} asChild><Link href={notice.href} onClick={() => setInvestigationContext({ focus: notice.focus })} className="flex items-start gap-3 border-b border-line px-4 py-3 outline-none last:border-0 hover:bg-graphite-hover focus:bg-graphite-hover"><span className={cn('mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-full', notice.tone === 'failure' ? 'bg-failure/10 text-failure' : 'bg-attention/10 text-attention')}><Icon className="size-3.5" /></span><span className="min-w-0"><span className={cn('mb-1 block text-[10px] font-semibold uppercase', notice.severity === 'error' ? 'text-failure' : 'text-attention')}>{notice.severity}</span><strong className="block text-xs font-semibold text-ink">{notice.title}</strong><span className="mt-1 block text-[11px] leading-4 text-ink-quiet">{notice.detail}</span></span></Link></DropdownMenu.Item>;
          }) : <div className="flex items-center gap-3 px-4 py-5"><CheckCircle2 className="size-4 text-healthy" /><p className="text-xs text-ink-secondary">No errors or warnings require action.</p></div>}</div>
          <DropdownMenu.Item asChild><Link href="/app/pipeline" onClick={() => setInvestigationContext({ focus: 'pipeline' })} className="block border-t border-line px-4 py-3 text-center text-xs font-semibold text-signal-blue outline-none hover:bg-graphite-hover focus:bg-graphite-hover">Open pipeline debugger</Link></DropdownMenu.Item>
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  );
}
