import { AppShell } from '@/components/app-shell';
import { HistoricalReplayPage, type ReplayOverview, type ReplayEvent } from '@/components/pages/historical-replay-page';
import { fetchJsonState, fetchShellSnapshot } from '@/lib/api';

export default async function ReplayRoute({ searchParams }: { searchParams: Promise<{ offset?: string; event?: string }> }) {
  const query = await searchParams;
  const offset = /^\d{1,6}$/.test(query.offset ?? '') ? Math.min(Number(query.offset), 100_000) : 0;
  const [snapshot, overview] = await Promise.all([
    fetchShellSnapshot(), fetchJsonState<ReplayOverview | null>(`/api/replay?limit=50&offset=${offset}`, null),
  ]);
  const eventId = /^\d{1,20}$/.test(query.event ?? '') ? query.event : overview.data?.events?.[0]?.event_id;
  const selected = eventId ? await fetchJsonState<ReplayEvent | null>(`/api/replay/events/${eventId}`, null) : { data: null, error: null };
  return <AppShell pageKey="replay" title="Historical replay" description="Inspect recorded event stages, receiver geometry, and solver results." snapshot={snapshot}>
    <HistoricalReplayPage key={selected.data?.event_id ?? 'empty'} overview={overview.data} selected={selected.data} error={overview.error ?? selected.error} />
  </AppShell>;
}
