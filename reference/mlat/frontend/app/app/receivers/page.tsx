import { AppShell } from '@/components/app-shell';
import { ReceiversPage } from '@/components/pages/receivers-page';
import { fetchJsonSafe, fetchShellSnapshot, PUBLIC_POSITIONS_PATH } from '@/lib/api';
import type { PositionsResponse, RegistryEvidenceData } from '@/lib/types';

export default async function ReceiversRoute({ searchParams }: { searchParams: Promise<{ receiver?: string }> }) {
  const { receiver } = await searchParams;
  const [snapshot, registryEvidence, positionsData] = await Promise.all([
    fetchShellSnapshot(),
    fetchJsonSafe<RegistryEvidenceData | null>('/api/registry/evidence', null),
    fetchJsonSafe<PositionsResponse>(PUBLIC_POSITIONS_PATH, { positions: [] }),
  ]);
  return <AppShell pageKey="receivers" title="Receivers" description="Trace Registry identity, discovery eligibility, MLAT role, and related aircraft." snapshot={snapshot}><ReceiversPage receiverData={snapshot.receiverData} selectedReceiverId={receiver} modeData={snapshot.modeData} registryEvidence={registryEvidence} positionsData={positionsData} perspective="receivers" /></AppShell>;
}
