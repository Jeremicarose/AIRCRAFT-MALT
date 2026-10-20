import { HistoricalReplayPage, type ReplayOverview, type ReplayEvent } from '@/components/pages/historical-replay-page';
import { fetchJsonState } from '@/lib/api';

export default async function ReplayRoute({ searchParams }: { searchParams: Promise<{ offset?: string; event?: string }> }) {
  const query = await searchParams;
  const offset = /^\d{1,6}$/.test(query.offset ?? '') ? Math.min(Number(query.offset), 100_000) : 0;
  const [overview] = await Promise.all([
    fetchJsonState<ReplayOverview | null>(`/api/replay?limit=50&offset=${offset}`, null),
  ]);
  const eventId = /^\d{1,20}$/.test(query.event ?? '') ? query.event : overview.data?.events?.[0]?.event_id;
  const selected = eventId ? await fetchJsonState<ReplayEvent | null>(`/api/replay/events/${eventId}`, null) : { data: null, error: null };
  return <>
    <HistoricalReplayPage key={selected.data?.event_id ?? 'empty'} overview={overview.data} selected={selected.data} error={overview.error ?? selected.error} />
  </>;
}
