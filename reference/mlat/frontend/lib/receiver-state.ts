import { formatDateTime, truncateMiddle } from '@/lib/format';
import { classifyReceiverObservation, RECEIVER_STALE_AFTER_SECONDS, type ReceiverObservationFreshness } from '@/lib/receiver-freshness';
import { receiverReferenceIds, receiverReferencesInclude } from '@/lib/receiver-reference';
import type { InvestigationDockState, Position, Receiver, StatusTone } from '@/lib/types';

export const RECEIVER_IDENTITY_PATTERN = /^0x[0-9a-f]{64}$/i;

export type RegistryIdentityStatus = 'active' | 'revoked' | 'not_registered' | 'conflict';
export type MlatOperationalStatus = 'available' | 'contributing' | 'stale' | 'offline' | 'excluded' | 'unavailable';

export interface UnifiedReceiver {
  key: string;
  identity: string | null;
  label: string;
  registry: Receiver | null;
  runtime: Receiver | null;
  registryStatus: RegistryIdentityStatus;
  registryRecordStatus: string | null;
  mlatStatus: MlatOperationalStatus;
  mlatReason: string;
  mlatEligible: boolean;
  identityConflict: boolean;
  ownerLockArgs: string | null;
  capabilities: string[];
  lastObservationAt: number | null;
  lastRegistryUpdateAt: string | null;
  relatedAircraftIds: string[];
  source: Receiver['data_source'] | null;
}

export interface ReceiverDirectorySummary {
  registryIdentities: number;
  active: number;
  revoked: number;
  unavailable: number;
  mlatEligible: number;
  contributing: number;
  conflicts: number;
  currentRuntimePool: number;
  staleRuntime: number;
}

interface ReconcileReceiverOptions {
  registryReceivers?: Receiver[];
  runtimeReceivers?: Receiver[];
  positions?: Position[];
  conflictIdentities?: string[];
  nowSeconds?: number;
  staleAfterSeconds?: number;
  runtimeInventoryAvailable?: boolean;
}

function normalizedIdentity(value?: string | null): string | null {
  if (!value || !RECEIVER_IDENTITY_PATTERN.test(value)) return null;
  return value.toLowerCase();
}

function normalizedRegistryTimestamp(value: unknown): string | null {
  if (typeof value !== 'string' || !/^(0|[1-9][0-9]*)$/.test(value)) return null;
  try {
    const parsed = BigInt(value);
    return parsed > BigInt(0) && parsed <= ((BigInt(1) << BigInt(64)) - BigInt(1))
      ? value
      : null;
  } catch {
    return null;
  }
}

export function receiverIdentity(receiver?: Receiver | null): string | null {
  if (!receiver) return null;
  return normalizedIdentity(receiver.receiver_identity)
    ?? (receiver.data_source === 'ckb_registry' ? normalizedIdentity(receiver.receiver_id) : null);
}

export function receiverOperationalKey(receiver: Receiver): string {
  const identity = receiverIdentity(receiver);
  if (identity) return identity;
  const source = receiver.data_source ?? 'runtime';
  const prefix = `${source}:`;
  return receiver.receiver_id.startsWith(prefix)
    ? receiver.receiver_id
    : `${prefix}${receiver.receiver_id}`;
}

function groupByKey(receivers: Receiver[], registrySource: boolean): Map<string, Receiver[]> {
  const result = new Map<string, Receiver[]>();
  receivers.forEach((receiver) => {
    const identity = receiverIdentity(receiver);
    if (registrySource && !identity) return;
    const key = identity ?? receiverOperationalKey(receiver);
    result.set(key, [...(result.get(key) ?? []), receiver]);
  });
  return result;
}

function relatedAircraft(references: string[], positions: Position[]): string[] {
  return [...new Set(
    positions
      .filter((position) => position.correlation?.receiver_ids?.some(
        (receiverId) => receiverReferencesInclude(references, receiverId),
      ))
      .map((position) => position.aircraft_id),
  )].sort();
}

function operationalState({
  registryStatus,
  recordStatus,
  eligible,
  runtime,
  contributing,
  observationFreshness,
  runtimeInventoryAvailable,
}: {
  registryStatus: RegistryIdentityStatus;
  recordStatus: string | null;
  eligible: boolean;
  runtime: Receiver | null;
  contributing: boolean;
  observationFreshness: ReceiverObservationFreshness | null;
  runtimeInventoryAvailable: boolean;
}): Pick<UnifiedReceiver, 'mlatStatus' | 'mlatReason'> {
  if (registryStatus === 'conflict') {
    return { mlatStatus: 'excluded', mlatReason: 'Duplicate live cells claim this canonical identity. MLAT must fail closed.' };
  }
  if (registryStatus === 'revoked') {
    return { mlatStatus: 'excluded', mlatReason: 'The Registry identity is revoked and cannot participate in MLAT.' };
  }
  if (recordStatus === 'offline') {
    return { mlatStatus: 'offline', mlatReason: 'The Registry record is published as offline.' };
  }
  if (recordStatus === 'degraded' && !runtime) {
    return { mlatStatus: 'offline', mlatReason: 'The Registry record is degraded and is not in the current MLAT receiver pool.' };
  }
  if (registryStatus === 'active' && !eligible) {
    return {
      mlatStatus: 'excluded',
      mlatReason: recordStatus !== 'online'
        ? `The Registry record is ${recordStatus ?? 'not online'}.`
        : 'The receiver does not publish the MLAT capability.',
    };
  }
  if (!runtimeInventoryAvailable) {
    return { mlatStatus: 'unavailable', mlatReason: 'The MLAT receiver inventory could not be loaded, so operational status cannot be confirmed.' };
  }
  if (!runtime) {
    return { mlatStatus: 'offline', mlatReason: 'This active identity is not in the current MLAT receiver pool.' };
  }
  if (observationFreshness === 'invalid') {
    return { mlatStatus: 'unavailable', mlatReason: 'The receiver has no valid latest-observation timestamp, so availability cannot be confirmed.' };
  }
  if (observationFreshness === 'future') {
    return { mlatStatus: 'unavailable', mlatReason: 'The receiver latest-observation timestamp is implausibly far in the future.' };
  }
  if (observationFreshness === 'stale') {
    return { mlatStatus: 'stale', mlatReason: 'The receiver is known to MLAT, but its latest observation is stale.' };
  }
  if (contributing) {
    return { mlatStatus: 'contributing', mlatReason: 'Recent aircraft localizations include observations from this receiver.' };
  }
  return { mlatStatus: 'available', mlatReason: 'The receiver is available to MLAT but is not in a recent aircraft localization.' };
}

export function reconcileReceivers({
  registryReceivers = [],
  runtimeReceivers = [],
  positions = [],
  conflictIdentities = [],
  nowSeconds = Date.now() / 1000,
  staleAfterSeconds = RECEIVER_STALE_AFTER_SECONDS,
  runtimeInventoryAvailable = true,
}: ReconcileReceiverOptions): UnifiedReceiver[] {
  const registryByIdentity = groupByKey(registryReceivers, true);
  const runtimeByKey = groupByKey(runtimeReceivers, false);
  const explicitConflicts = new Set(conflictIdentities.map(normalizedIdentity).filter(Boolean) as string[]);
  const keys = new Set([...registryByIdentity.keys(), ...runtimeByKey.keys(), ...explicitConflicts]);

  return [...keys].sort().map((key) => {
    const registryRows = registryByIdentity.get(key) ?? [];
    const runtimeRows = runtimeByKey.get(key) ?? [];
    const registry = registryRows[0] ?? null;
    const runtime = runtimeRows[0] ?? null;
    const identity = normalizedIdentity(key);
    const identityConflict = explicitConflicts.has(key)
      || registryRows.length > 1
      || (identity !== null && runtimeRows.length > 1);
    const base = registry ?? runtime;
    const registryRecordStatus = registry?.status ?? (identity ? runtime?.status : null) ?? null;
    const registryStatus: RegistryIdentityStatus = identityConflict
      ? 'conflict'
      : identity === null
        ? 'not_registered'
        : registryRecordStatus === 'revoked'
          ? 'revoked'
          : 'active';
    const capabilities = [...new Set([...(registry?.capabilities ?? []), ...(runtime?.capabilities ?? [])])];
    const mlatEligible = registryStatus === 'active'
      && registryRecordStatus === 'online'
      && capabilities.includes('mlat');
    const lastObservationAt = Number.isFinite(Number(runtime?.last_seen))
      ? Number(runtime?.last_seen)
      : null;
    const observationFreshness = runtime
      ? classifyReceiverObservation(runtime.last_seen, nowSeconds, staleAfterSeconds)
      : null;
    const references = receiverReferenceIds(key, identity, runtime?.receiver_id);
    const isContributing = positions.some((position) =>
      position.correlation?.receiver_ids?.some(
        (receiverId) => receiverReferencesInclude(references, receiverId),
      ),
    );
    const mlat = operationalState({
      registryStatus,
      recordStatus: registryRecordStatus,
      eligible: identity === null ? Boolean(runtime) : mlatEligible,
      runtime,
      contributing: isContributing,
      observationFreshness,
      runtimeInventoryAvailable,
    });

    return {
      key,
      identity,
      label: base?.receiver_label || (identity ? base?.receiver_id : runtime?.receiver_id) || 'Unknown receiver',
      registry,
      runtime,
      registryStatus,
      registryRecordStatus,
      mlatStatus: mlat.mlatStatus,
      mlatReason: mlat.mlatReason,
      mlatEligible,
      identityConflict,
      ownerLockArgs: registry?.registry?.owner_lock_args ?? runtime?.registry?.owner_lock_args ?? null,
      capabilities,
      lastObservationAt,
      lastRegistryUpdateAt: normalizedRegistryTimestamp(
        registry?.registry?.updated_at
          ?? registry?.updated_at
          ?? runtime?.registry?.updated_at,
      ),
      relatedAircraftIds: relatedAircraft(references, positions),
      source: runtime?.data_source ?? registry?.data_source ?? null,
    };
  });
}

export function summarizeReceiverDirectory(receivers: UnifiedReceiver[]): ReceiverDirectorySummary {
  const registryReceivers = receivers.filter((receiver) => receiver.identity !== null);
  return {
    registryIdentities: registryReceivers.length,
    active: registryReceivers.filter((receiver) => receiver.registryStatus === 'active').length,
    revoked: registryReceivers.filter((receiver) => receiver.registryStatus === 'revoked').length,
    unavailable: registryReceivers.filter((receiver) => receiver.registryStatus === 'active' && receiver.runtime === null).length,
    mlatEligible: registryReceivers.filter((receiver) => receiver.mlatEligible).length,
    contributing: receivers.filter((receiver) => receiver.mlatStatus === 'contributing').length,
    conflicts: registryReceivers.filter((receiver) => receiver.identityConflict).length,
    currentRuntimePool: receivers.filter((receiver) => receiver.mlatStatus === 'available' || receiver.mlatStatus === 'contributing').length,
    staleRuntime: receivers.filter((receiver) => receiver.mlatStatus === 'stale').length,
  };
}

export function registryStatusPresentation(status: RegistryIdentityStatus): { label: string; tone: StatusTone } {
  if (status === 'active') return { label: 'Active identity', tone: 'trust' };
  if (status === 'revoked') return { label: 'Revoked identity', tone: 'failure' };
  if (status === 'conflict') return { label: 'Identity conflict', tone: 'failure' };
  return { label: 'Not registered', tone: 'neutral' };
}

export function mlatStatusPresentation(status: MlatOperationalStatus): { label: string; tone: StatusTone } {
  if (status === 'contributing') return { label: 'Contributing', tone: 'healthy' };
  if (status === 'available') return { label: 'Available', tone: 'selection' };
  if (status === 'stale') return { label: 'Stale', tone: 'attention' };
  if (status === 'offline') return { label: 'Offline', tone: 'neutral' };
  if (status === 'unavailable') return { label: 'Status unavailable', tone: 'attention' };
  return { label: 'Excluded', tone: 'failure' };
}

export function receiverDockState(
  receiver: UnifiedReceiver,
  options: { returnAircraftId?: string | null; includeRegistryAction?: boolean } = {},
): InvestigationDockState {
  const registryState = registryStatusPresentation(receiver.registryStatus);
  const mlatState = mlatStatusPresentation(receiver.mlatStatus);
  const receiverQuery = new URLSearchParams({ receiver: receiver.identity ?? receiver.key });
  if (options.returnAircraftId) receiverQuery.set('fromAircraft', options.returnAircraftId);
  const receiverHref = `/app/receivers?${receiverQuery.toString()}`;
  const actions: InvestigationDockState['actions'] = [
    { label: 'Open receiver details', href: receiverHref, tone: 'primary' },
  ];
  if (receiver.identity && options.includeRegistryAction) {
    actions.push({ label: 'Open Registry lifecycle', href: `/app/registry?receiver=${encodeURIComponent(receiver.identity)}`, tone: 'secondary' });
  }
  if (options.returnAircraftId) {
    actions.push({ label: `Return to ${options.returnAircraftId}`, href: `/app/aircraft?aircraft=${encodeURIComponent(options.returnAircraftId)}`, tone: 'secondary' });
  }

  return {
    entityType: 'receiver',
    title: receiver.label,
    subtitle: receiver.identity
      ? 'The same canonical Receiver Identity is used by Registry discovery, MLAT, and this inspector.'
      : 'This operational receiver has no CKB Receiver Identity and is not presented as registered.',
    statusLabel: mlatState.label,
    statusTone: mlatState.tone,
    facts: [
      { label: 'Canonical identity', value: receiver.identity ? truncateMiddle(receiver.identity, 10, 8) : 'Not registered', mono: Boolean(receiver.identity), tone: registryState.tone },
      { label: 'Owner', value: receiver.ownerLockArgs ? truncateMiddle(receiver.ownerLockArgs, 9, 7) : 'Not available', mono: Boolean(receiver.ownerLockArgs) },
      { label: 'Registry', value: registryState.label, tone: registryState.tone },
      { label: 'MLAT', value: mlatState.label, tone: mlatState.tone },
      { label: 'Published state', value: receiver.registryRecordStatus ?? 'Not published' },
      { label: 'Related aircraft', value: String(receiver.relatedAircraftIds.length) },
    ],
    timeline: [
      {
        title: 'Registry identity',
        detail: receiver.identity
          ? `${registryState.label}. The Type ID remains stable across owner and metadata changes.`
          : 'No Registry identity is attached to this receiver.',
        tone: registryState.tone,
      },
      {
        title: 'Receiver discovery',
        detail: receiver.identityConflict
          ? 'Discovery quarantined this identity instead of selecting one conflicting record.'
          : receiver.runtime
            ? 'The receiver is present in the current MLAT inventory.'
            : 'The receiver is not present in the current MLAT inventory.',
        tone: receiver.identityConflict ? 'failure' : receiver.runtime ? 'healthy' : 'attention',
      },
      { title: 'MLAT role', detail: receiver.mlatReason, tone: mlatState.tone },
      {
        title: 'Recent activity',
        detail: receiver.lastObservationAt
          ? `Latest observation ${formatDateTime(receiver.lastObservationAt)}.`
          : 'No receiver observation timestamp is available.',
        tone: receiver.lastObservationAt ? mlatState.tone : 'neutral',
      },
    ],
    evidence: receiver.identityConflict
      ? [{ title: 'Identity integrity', detail: 'More than one live record claims this canonical Type ID. No record was selected for MLAT.', state: 'Fail closed', tone: 'failure' }]
      : undefined,
    actions,
  };
}
