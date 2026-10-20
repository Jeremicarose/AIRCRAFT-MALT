import LiveMapPage from '@/components/pages/live-map-page';
import { fetchJsonState, fetchShellSnapshot, PUBLIC_POSITIONS_PATH } from '@/lib/api';
import type { PositionsResponse, ReceiversResponse } from '@/lib/types';

export default async function LiveMapRoute({ searchParams }: { searchParams: Promise<{ aircraft?: string; receiver?: string }> }) {
  const { aircraft, receiver } = await searchParams;
  const [snapshot, positionsState, receiversState] = await Promise.all([
    fetchShellSnapshot(),
    fetchJsonState<PositionsResponse>(PUBLIC_POSITIONS_PATH, { positions: [] }),
    fetchJsonState<ReceiversResponse>('/api/receivers', { receivers: [] }),
  ]);
  return <><LiveMapPage initialModeData={snapshot.modeData} initialHealthData={snapshot.healthData} initialPositionsData={positionsState.data} initialPositionsError={positionsState.error} initialReceiversData={receiversState.data} initialReceiversError={receiversState.error} initialSelectedAircraftId={aircraft} initialSelectedReceiverId={receiver} /></>;
}
