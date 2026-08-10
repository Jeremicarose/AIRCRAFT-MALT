'use client';

import * as DropdownMenu from '@radix-ui/react-dropdown-menu';
import { AlertTriangle, Bell, CheckCircle2, Clock3, RadioTower, ShieldAlert } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import type { ShellSnapshot, StatusTone } from '@/lib/types';
import { cn } from '@/lib/utils';
import { useOperatorStore } from '@/lib/operator-store';

type Notice = { id: string; title: string; detail: string; tone: StatusTone; icon: typeof Bell; href: string; focus?: string };

export function NotificationCenter({ snapshot }: { snapshot: ShellSnapshot }) {
  const mode = snapshot.modeData;
  const receiverCount = snapshot.receiverData?.count ?? snapshot.receiverData?.receivers?.length ?? 0;
  const selectedAircraftId = useOperatorStore((state) => state.selectedAircraftId);
  const selectedReceiverId = useOperatorStore((state) => state.selectedReceiverId);
  const setInvestigationContext = useOperatorStore((state) => state.setInvestigationContext);
  const notices: Notice[] = [];
  if (!mode) notices.push({ id: 'runtime', title: 'Runtime unavailable', detail: 'The environment endpoint did not respond.', tone: 'failure', icon: AlertTriangle, href: '/app/environment', focus: 'runtime' });
  if (mode?.demo_mode || mode?.simulation_mode || mode?.synthetic_feed_mode) notices.push({ id: 'replay', title: 'Replay source active', detail: 'Current activity is synthetic and cannot support live claims.', tone: 'replay', icon: Clock3, href: '/app/environment', focus: 'replay' });
  if (!mode?.receiver_registry_type_hash) notices.push({ id: 'registry', title: 'Registry trust pending', detail: 'No Registry V2 type hash is configured.', tone: 'attention', icon: ShieldAlert, href: '/app/receivers', focus: 'registry' });
  if (receiverCount < 4) notices.push({ id: 'receivers', title: 'Receiver geometry insufficient', detail: `${receiverCount} receivers visible, four are required.`, tone: 'failure', icon: RadioTower, href: '/app/receivers', focus: 'geometry' });
  if (selectedAircraftId) notices.push({ id: 'aircraft-focus', title: 'Pinned aircraft context', detail: `Investigation is centered on ${selectedAircraftId}.`, tone: 'selection', icon: Bell, href: `/app/aircraft?aircraft=${encodeURIComponent(selectedAircraftId)}`, focus: selectedAircraftId });
  if (selectedReceiverId) notices.push({ id: 'receiver-focus', title: 'Pinned receiver context', detail: `Receiver ${selectedReceiverId} remains selected across pages.`, tone: 'selection', icon: Bell, href: `/app/receivers?receiver=${encodeURIComponent(selectedReceiverId)}`, focus: selectedReceiverId });
  const attentionCount = notices.filter((notice) => notice.tone === 'failure' || notice.tone === 'attention').length;

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
          <div className="flex items-center justify-between border-b border-line px-4 py-3"><div><p className="text-xs font-semibold text-ink">Notifications</p><p className="mt-0.5 text-[10px] text-ink-quiet">Current operator attention and pinned context</p></div><span className="text-[11px] text-ink-quiet">{notices.length}</span></div>
          <div className="max-h-[380px] overflow-y-auto">{notices.length ? notices.map((notice) => {
            const Icon = notice.icon;
            return <DropdownMenu.Item key={notice.id} asChild><Link href={notice.href} onClick={() => setInvestigationContext({ focus: notice.focus ?? notice.id })} className="flex items-start gap-3 border-b border-line px-4 py-3 outline-none last:border-0 hover:bg-graphite-hover focus:bg-graphite-hover"><span className={cn('mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-full', notice.tone === 'failure' ? 'bg-failure/10 text-failure' : notice.tone === 'replay' ? 'bg-replay/10 text-replay' : notice.tone === 'selection' ? 'bg-signal-blue/10 text-signal-blue' : notice.tone === 'healthy' ? 'bg-healthy/10 text-healthy' : 'bg-attention/10 text-attention')}><Icon className="size-3.5" /></span><span className="min-w-0"><strong className="block text-xs font-semibold text-ink">{notice.title}</strong><span className="mt-1 block text-[11px] leading-4 text-ink-quiet">{notice.detail}</span></span></Link></DropdownMenu.Item>;
          }) : <div className="flex items-center gap-3 px-4 py-5"><CheckCircle2 className="size-4 text-healthy" /><p className="text-xs text-ink-secondary">No current operator notifications.</p></div>}</div>
          <DropdownMenu.Item asChild><Link href="/app/pipeline" onClick={() => setInvestigationContext({ focus: 'pipeline' })} className="block border-t border-line px-4 py-3 text-center text-xs font-semibold text-signal-blue outline-none hover:bg-graphite-hover focus:bg-graphite-hover">Open pipeline debugger</Link></DropdownMenu.Item>
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  );
}
