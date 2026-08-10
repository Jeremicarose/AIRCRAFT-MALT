import { AppShell } from '@/components/app-shell';
import { AircraftPage } from '@/components/pages/aircraft-page';
import { fetchJsonSafe, fetchShellSnapshot } from '@/lib/api';
import type { Position, PositionsResponse } from '@/lib/types';

export default async function AircraftRoute({ searchParams }: { searchParams: Promise<{ aircraft?: string }> }) {
  const { aircraft: requestedAircraft } = await searchParams;
  const [snapshot, positionsData] = await Promise.all([
    fetchShellSnapshot(),
    fetchJsonSafe<PositionsResponse>('/api/positions/recent?seconds=600&limit=250', { positions: [] }),
  ]);
  const aircraftId = requestedAircraft ?? positionsData.positions[0]?.aircraft_id;
  const [latest, track] = aircraftId ? await Promise.all([
    fetchJsonSafe<Position | null>(`/api/aircraft/${encodeURIComponent(aircraftId)}/latest`, null),
    fetchJsonSafe<PositionsResponse>(`/api/aircraft/${encodeURIComponent(aircraftId)}/track?limit=120`, { positions: [] }),
  ]) : [null, { positions: [] }];
  return <AppShell pageKey="aircraft" title="Aircraft" description="Explore tracks, confidence history, and receiver contribution." snapshot={snapshot}><AircraftPage positionsData={positionsData} selectedAircraftId={aircraftId} initialLatest={latest} initialTrack={track} modeData={snapshot.modeData} receiverData={snapshot.receiverData} /></AppShell>;
}
