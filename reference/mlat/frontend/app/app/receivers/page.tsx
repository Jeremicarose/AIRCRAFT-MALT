import { AppShell } from '@/components/app-shell';
import { ReceiversPage } from '@/components/pages/receivers-page';
import { fetchJsonSafe, fetchShellSnapshot } from '@/lib/api';
import type { PositionsResponse } from '@/lib/types';

export default async function ReceiversRoute({ searchParams }: { searchParams: Promise<{ receiver?: string }> }) {
  const { receiver } = await searchParams;
  const [snapshot, positionsData] = await Promise.all([
    fetchShellSnapshot(),
    fetchJsonSafe<PositionsResponse>('/api/positions/recent?seconds=600&limit=250', { positions: [] }),
  ]);
  return <AppShell pageKey="receivers" title="Receivers" description="Inspect infrastructure health, coverage, identity, and lifecycle trust." snapshot={snapshot}><ReceiversPage receiverData={snapshot.receiverData} aircraftData={positionsData.positions} selectedReceiverId={receiver} modeData={snapshot.modeData} /></AppShell>;
}
