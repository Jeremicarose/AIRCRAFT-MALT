import { AppShell } from '@/components/app-shell';
import LiveMapPage from '@/components/pages/live-map-page';
import { fetchJsonSafe, fetchShellSnapshot } from '@/lib/api';
import type { PositionsResponse, ReceiversResponse } from '@/lib/types';

export default async function LiveMapRoute() {
  const [snapshot, positionsData, receiversData] = await Promise.all([
    fetchShellSnapshot(),
    fetchJsonSafe<PositionsResponse>('/api/positions/recent?seconds=600&limit=250', { positions: [] }),
    fetchJsonSafe<ReceiversResponse>('/api/receivers', { receivers: [] }),
  ]);
  return <AppShell pageKey="localization" title="Live map" description="Track aircraft and inspect the receiver geometry behind each solve." snapshot={snapshot}><LiveMapPage initialModeData={snapshot.modeData} initialHealthData={snapshot.healthData} initialPositionsData={positionsData} initialReceiversData={receiversData} /></AppShell>;
}
