'use client';

import * as Dialog from '@radix-ui/react-dialog';
import { Command } from 'cmdk';
import { Activity, Crosshair, Database, Gauge, Heart, History, Layers3, Map, Plane, RadioTower, Search, Settings, SlidersHorizontal, Star, Workflow, X } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { consoleRoutes } from '@/lib/routes';
import type { ShellSnapshot } from '@/lib/types';
import { useOperatorStore } from '@/lib/operator-store';
import { Button } from '@/components/ui/button';

const icons = { overview: Gauge, localization: Map, aircraft: Plane, receivers: RadioTower, pipeline: Workflow, metrics: Activity, environment: Database, settings: Settings };

export function CommandPalette({ snapshot }: { snapshot: ShellSnapshot }) {
  const router = useRouter();
  const open = useOperatorStore((state) => state.commandOpen);
  const setOpen = useOperatorStore((state) => state.setCommandOpen);
  const selectedAircraftId = useOperatorStore((state) => state.selectedAircraftId);
  const selectedReceiverId = useOperatorStore((state) => state.selectedReceiverId);
  const rightDockOpen = useOperatorStore((state) => state.rightDockOpen);
  const setRightDockOpen = useOperatorStore((state) => state.setRightDockOpen);
  const showReceiverLinks = useOperatorStore((state) => state.showReceiverLinks);
  const showUncertainty = useOperatorStore((state) => state.showUncertainty);
  const toggleReceiverLinks = useOperatorStore((state) => state.toggleReceiverLinks);
  const toggleUncertainty = useOperatorStore((state) => state.toggleUncertainty);
  const investigation = useOperatorStore((state) => state.investigation);
  const setInvestigationContext = useOperatorStore((state) => state.setInvestigationContext);
  const routeHistory = useOperatorStore((state) => state.routeHistory);
  const starredRoutes = useOperatorStore((state) => state.starredRoutes);
  const recentInvestigations = useOperatorStore((state) => state.recentInvestigations);
  const toggleStarredRoute = useOperatorStore((state) => state.toggleStarredRoute);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        setOpen(!open);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [open, setOpen]);

  const select = (href: string) => {
    setOpen(false);
    router.push(href);
  };

  const runAction = (action: () => void) => {
    action();
    setOpen(false);
  };

  return (
    <Dialog.Root open={open} onOpenChange={setOpen}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-modal-backdrop bg-black/55 backdrop-blur-[2px] motion-safe:animate-in motion-safe:fade-in" />
        <Dialog.Content className="fixed left-1/2 top-[12vh] z-modal w-[min(680px,calc(100vw-32px))] -translate-x-1/2 overflow-hidden rounded-lg border border-[#343c48] bg-[#11151a] shadow-overlay focus:outline-none motion-safe:animate-in motion-safe:fade-in motion-safe:zoom-in-[0.98]">
          <Dialog.Title className="sr-only">Search the console</Dialog.Title>
          <Dialog.Description className="sr-only">Open a page, aircraft, receiver, or shell action.</Dialog.Description>
          <Command loop className="[&_[cmdk-group-heading]]:px-3 [&_[cmdk-group-heading]]:pb-1 [&_[cmdk-group-heading]]:pt-3 [&_[cmdk-group-heading]]:text-[11px] [&_[cmdk-group-heading]]:font-semibold [&_[cmdk-group-heading]]:uppercase [&_[cmdk-group-heading]]:tracking-[0.16em] [&_[cmdk-group-heading]]:text-ink-quiet">
            <div className="flex h-12 items-center gap-3 border-b border-line px-4">
              <Search aria-hidden="true" className="size-4 text-ink-quiet" />
              <Command.Input autoFocus placeholder="Search routes, entities, or console actions" className="h-full min-w-0 flex-1 bg-transparent text-sm text-ink outline-none placeholder:text-ink-quiet" />
              <Dialog.Close asChild><Button variant="ghost" size="icon-sm" aria-label="Close command palette"><X className="size-4" /></Button></Dialog.Close>
            </div>
            <Command.List className="max-h-[480px] overflow-y-auto p-2">
              <Command.Empty className="px-3 py-10 text-center text-sm text-ink-quiet">No matching command.</Command.Empty>
              <Command.Group heading="Pages">
                {consoleRoutes.map((route) => {
                  const Icon = icons[route.key as keyof typeof icons] ?? SlidersHorizontal;
                  return (
                    <Command.Item key={route.key} value={`${route.label} ${route.detail} ${route.group}`} onSelect={() => select(route.href)} className="flex cursor-default items-center gap-3 rounded-md px-3 py-2.5 text-sm text-ink-secondary outline-none data-[selected=true]:bg-graphite-hover data-[selected=true]:text-ink">
                      <Icon aria-hidden="true" className="size-4 text-ink-quiet" />
                      <span className="flex-1">{route.label}</span>
                      <span className="text-xs text-ink-quiet">{route.group}</span>
                    </Command.Item>
                  );
                })}
              </Command.Group>

              <Command.Group heading="Operator actions">
                <Command.Item value={`dock ${rightDockOpen ? 'hide' : 'show'} inspector`} onSelect={() => runAction(() => setRightDockOpen(!rightDockOpen))} className="flex cursor-default items-center gap-3 rounded-md px-3 py-2.5 text-sm text-ink-secondary outline-none data-[selected=true]:bg-graphite-hover data-[selected=true]:text-ink">
                  <Layers3 className="size-4 text-ink-quiet" />
                  <span className="flex-1">{rightDockOpen ? 'Hide' : 'Show'} investigation dock</span>
                  <span className="text-xs text-ink-quiet">Shell</span>
                </Command.Item>
                <Command.Item value={`toggle receiver links ${showReceiverLinks ? 'on' : 'off'}`} onSelect={() => runAction(() => toggleReceiverLinks())} className="flex cursor-default items-center gap-3 rounded-md px-3 py-2.5 text-sm text-ink-secondary outline-none data-[selected=true]:bg-graphite-hover data-[selected=true]:text-ink">
                  <Crosshair className="size-4 text-ink-quiet" />
                  <span className="flex-1">{showReceiverLinks ? 'Hide' : 'Show'} receiver geometry</span>
                  <span className="text-xs text-ink-quiet">Map</span>
                </Command.Item>
                <Command.Item value={`toggle uncertainty ${showUncertainty ? 'on' : 'off'}`} onSelect={() => runAction(() => toggleUncertainty())} className="flex cursor-default items-center gap-3 rounded-md px-3 py-2.5 text-sm text-ink-secondary outline-none data-[selected=true]:bg-graphite-hover data-[selected=true]:text-ink">
                  <Crosshair className="size-4 text-ink-quiet" />
                  <span className="flex-1">{showUncertainty ? 'Hide' : 'Show'} uncertainty ring</span>
                  <span className="text-xs text-ink-quiet">Map</span>
                </Command.Item>
                <Command.Item value="set investigation range 10 minutes" onSelect={() => runAction(() => setInvestigationContext({ timeRange: '10m' }))} className="flex cursor-default items-center gap-3 rounded-md px-3 py-2.5 text-sm text-ink-secondary outline-none data-[selected=true]:bg-graphite-hover data-[selected=true]:text-ink">
                  <Gauge className="size-4 text-ink-quiet" />
                  <span className="flex-1">Set investigation window to 10m</span>
                  <span className="text-xs text-ink-quiet">Context</span>
                </Command.Item>
                <Command.Item value="set investigation range 1 hour" onSelect={() => runAction(() => setInvestigationContext({ timeRange: '1h' }))} className="flex cursor-default items-center gap-3 rounded-md px-3 py-2.5 text-sm text-ink-secondary outline-none data-[selected=true]:bg-graphite-hover data-[selected=true]:text-ink">
                  <Gauge className="size-4 text-ink-quiet" />
                  <span className="flex-1">Set investigation window to 1h</span>
                  <span className="text-xs text-ink-quiet">Context</span>
                </Command.Item>
              </Command.Group>

              {starredRoutes.length ? (
                <Command.Group heading="Starred workspaces">
                  {starredRoutes.map((routeKey) => {
                    const route = consoleRoutes.find((item) => item.key === routeKey);
                    if (!route) return null;
                    const Icon = icons[route.key as keyof typeof icons] ?? SlidersHorizontal;
                    return (
                      <Command.Item key={route.key} value={`starred route ${route.label}`} onSelect={() => select(route.href)} className="flex cursor-default items-center gap-3 rounded-md px-3 py-2.5 text-sm text-ink-secondary outline-none data-[selected=true]:bg-graphite-hover data-[selected=true]:text-ink">
                        <Star className="size-4 text-amber-300" />
                        <Icon className="size-4 text-ink-quiet" />
                        <span className="flex-1">{route.label}</span>
                        <span className="text-xs text-ink-quiet">{route.group}</span>
                      </Command.Item>
                    );
                  })}
                </Command.Group>
              ) : null}

              {routeHistory.length ? (
                <Command.Group heading="Recent routes">
                  {routeHistory.map((route) => {
                    const Icon = icons[route.key as keyof typeof icons] ?? SlidersHorizontal;
                    return (
                      <Command.Item key={`${route.key}-${route.visitedAt}`} value={`recent route ${route.label}`} onSelect={() => select(route.href)} className="flex cursor-default items-center gap-3 rounded-md px-3 py-2.5 text-sm text-ink-secondary outline-none data-[selected=true]:bg-graphite-hover data-[selected=true]:text-ink">
                        <History className="size-4 text-ink-quiet" />
                        <Icon className="size-4 text-ink-quiet" />
                        <span className="flex-1">{route.label}</span>
                        <span className="text-xs text-ink-quiet">Recent</span>
                      </Command.Item>
                    );
                  })}
                </Command.Group>
              ) : null}

              {recentInvestigations.length ? (
                <Command.Group heading="Recent investigations">
                  {recentInvestigations.map((entry) => (
                    <Command.Item
                      key={`${entry.id}-${entry.updatedAt}`}
                      value={`recent investigation ${entry.title} ${entry.focus ?? ''}`}
                      onSelect={() => runAction(() => {
                        if (entry.routeKey) setInvestigationContext({ routeKey: entry.routeKey, focus: entry.focus ?? entry.title });
                        if (entry.href) router.push(entry.href);
                      })}
                      className="flex cursor-default items-center gap-3 rounded-md px-3 py-2.5 text-sm text-ink-secondary outline-none data-[selected=true]:bg-graphite-hover data-[selected=true]:text-ink"
                    >
                      <Heart className="size-4 text-ink-quiet" />
                      <span className="flex-1 truncate">{entry.title}</span>
                      <span className="text-xs text-ink-quiet">{entry.statusLabel ?? 'Pinned'}</span>
                    </Command.Item>
                  ))}
                </Command.Group>
              ) : null}

              {(selectedAircraftId || selectedReceiverId || investigation.timeRange) ? (
                <Command.Group heading="Pinned context">
                  {selectedAircraftId ? (
                    <Command.Item value={`selected aircraft ${selectedAircraftId}`} onSelect={() => select(`/app/aircraft?aircraft=${encodeURIComponent(selectedAircraftId)}`)} className="flex cursor-default items-center gap-3 rounded-md px-3 py-2.5 text-sm text-ink-secondary outline-none data-[selected=true]:bg-graphite-hover data-[selected=true]:text-ink">
                      <Plane className="size-4 text-ink-quiet" />
                      <span className="flex-1">Open pinned aircraft {selectedAircraftId}</span>
                      <span className="text-xs text-ink-quiet">Investigate</span>
                    </Command.Item>
                  ) : null}
                  {selectedReceiverId ? (
                    <Command.Item value={`selected receiver ${selectedReceiverId}`} onSelect={() => select(`/app/receivers?receiver=${encodeURIComponent(selectedReceiverId)}`)} className="flex cursor-default items-center gap-3 rounded-md px-3 py-2.5 text-sm text-ink-secondary outline-none data-[selected=true]:bg-graphite-hover data-[selected=true]:text-ink">
                      <RadioTower className="size-4 text-ink-quiet" />
                      <span className="flex-1">Open pinned receiver {selectedReceiverId}</span>
                      <span className="text-xs text-ink-quiet">Investigate</span>
                    </Command.Item>
                  ) : null}
                  {investigation.timeRange ? (
                    <Command.Item value={`investigation range ${investigation.timeRange}`} onSelect={() => runAction(() => undefined)} className="flex cursor-default items-center gap-3 rounded-md px-3 py-2.5 text-sm text-ink-secondary outline-none data-[selected=true]:bg-graphite-hover data-[selected=true]:text-ink">
                      <Gauge className="size-4 text-ink-quiet" />
                      <span className="flex-1">Investigation window {investigation.timeRange}</span>
                      <span className="text-xs text-ink-quiet">Shared</span>
                    </Command.Item>
                  ) : null}
                </Command.Group>
              ) : null}

              {snapshot.aircraftData?.aircraft?.length ? (
                <Command.Group heading="Aircraft">
                  {snapshot.aircraftData.aircraft.slice(0, 12).map((aircraft) => (
                    <Command.Item key={aircraft} value={`aircraft ${aircraft}`} onSelect={() => select(`/app/aircraft?aircraft=${encodeURIComponent(aircraft)}`)} className="flex cursor-default items-center gap-3 rounded-md px-3 py-2.5 text-sm text-ink-secondary outline-none data-[selected=true]:bg-graphite-hover data-[selected=true]:text-ink">
                      <Plane className="size-4 text-ink-quiet" /><span>{aircraft}</span>
                    </Command.Item>
                  ))}
                </Command.Group>
              ) : null}
              {snapshot.receiverData?.receivers?.length ? (
                <Command.Group heading="Receivers">
                  {snapshot.receiverData.receivers.slice(0, 12).map((receiver) => (
                    <Command.Item key={receiver.receiver_id} value={`receiver ${receiver.receiver_id}`} onSelect={() => select(`/app/receivers?receiver=${encodeURIComponent(receiver.receiver_id)}`)} className="flex cursor-default items-center gap-3 rounded-md px-3 py-2.5 text-sm text-ink-secondary outline-none data-[selected=true]:bg-graphite-hover data-[selected=true]:text-ink">
                      <RadioTower className="size-4 text-ink-quiet" /><span>{receiver.receiver_id}</span>
                    </Command.Item>
                  ))}
                </Command.Group>
              ) : null}
            </Command.List>
            <div className="flex h-9 items-center gap-4 border-t border-line px-4 text-[11px] text-ink-quiet"><span>Enter to run</span><span>↑↓ to navigate</span><span>Esc to close</span></div>
          </Command>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
