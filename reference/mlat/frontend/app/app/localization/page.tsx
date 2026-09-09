import { AppShell } from '@/components/app-shell';
import LiveMapPage from '@/components/pages/live-map-page';
import { fetchJsonSafe, fetchJsonState, fetchShellSnapshot, PUBLIC_POSITIONS_PATH } from '@/lib/api';
import type { PositionsResponse, ReceiversResponse } from '@/lib/types';

export default async function LiveMapRoute({ searchParams }: { searchParams: Promise<{ aircraft?: string; receiver?: string }> }) {
  const { aircraft, receiver } = await searchParams;
  const [snapshot, positionsState, receiversData] = await Promise.all([
    fetchShellSnapshot(),
    fetchJsonState<PositionsResponse>(PUBLIC_POSITIONS_PATH, { positions: [] }),
    fetchJsonSafe<ReceiversResponse>('/api/receivers', { receivers: [] }),
  ]);
  return <AppShell pageKey="localization" title="Live map" description="Select aircraft or receivers and keep their evidence in context." snapshot={snapshot}><LiveMapPage initialModeData={snapshot.modeData} initialHealthData={snapshot.healthData} initialPositionsData={positionsState.data} initialPositionsError={positionsState.error} initialReceiversData={receiversData} initialSelectedAircraftId={aircraft} initialSelectedReceiverId={receiver} /></AppShell>;
}
