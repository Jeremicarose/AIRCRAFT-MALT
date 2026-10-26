import type { ModeData, RegistryEvidenceData, StatusTone } from '@/lib/types';

export type ContractVerificationResult = 'evidence_unavailable' | 'not_configured' | 'mismatch' | 'unsafe_binding' | 'match';

export interface ContractVerificationAssessment {
  result: ContractVerificationResult;
  label: string;
  tone: StatusTone;
  explanation: string;
  nextAction: string;
}

export function assessRegistryContract(
  evidence: RegistryEvidenceData | null,
  mode: ModeData | null,
): ContractVerificationAssessment {
  if (!evidence) {
    return {
      result: 'evidence_unavailable',
      label: 'NOT TESTABLE',
      tone: 'attention',
      explanation: 'The saved deployment evidence bundle is unavailable, so the expected contract identity cannot be compared with runtime configuration.',
      nextAction: 'Restore the configured Registry evidence bundle, then reload this page.',
    };
  }

  const configuredCodeHash = mode?.receiver_registry_type_hash?.toLowerCase();
  const configuredHashType = mode?.receiver_registry_hash_type?.toLowerCase();
  const expectedCodeHash = evidence.contract.code_hash.toLowerCase();
  const expectedHashType = evidence.contract.hash_type.toLowerCase();

  if (!configuredCodeHash) {
    return {
      result: 'not_configured',
      label: 'NOT CONFIGURED',
      tone: 'failure',
      explanation: 'The runtime has no Registry contract code hash, so it cannot discover or verify Registry V2 cells.',
      nextAction: `Set RECEIVER_REGISTRY_TYPE_HASH to ${evidence.contract.code_hash}, set RECEIVER_REGISTRY_HASH_TYPE=${expectedHashType}, and restart the MLAT API.`,
    };
  }

  if (configuredCodeHash !== expectedCodeHash || configuredHashType !== expectedHashType) {
    return {
      result: 'mismatch',
      label: 'MISMATCH',
      tone: 'failure',
      explanation: 'The runtime configuration does not identify the same contract code and hash type as the saved deployment evidence.',
      nextAction: `Use the reviewed code hash and RECEIVER_REGISTRY_HASH_TYPE=${expectedHashType}, restart the MLAT API, then confirm this result changes to CONFIGURATION MATCH.`,
    };
  }

  if (!mode?.registry_code_immutable) {
    return {
      result: 'unsafe_binding',
      label: 'UNSAFE BINDING',
      tone: 'attention',
      explanation: 'The values match, but the runtime does not report an immutable data1 contract binding.',
      nextAction: 'Use the reviewed data1 deployment for live lifecycle actions. Keep historical mutable deployments read-only.',
    };
  }

  return {
    result: 'match',
    label: 'CONFIGURATION MATCH',
    tone: 'trust',
    explanation: 'The runtime code hash and hash type match the saved deployment evidence. This comparison does not perform a new live CKB query.',
    nextAction: mode.registry_discovery_live
      ? 'Registry discovery is connected. Inspect a receiver identity and its lifecycle transactions next.'
      : 'Restore CKB RPC and indexer discovery, then confirm Diagnostics reports live Registry discovery.',
  };
}
