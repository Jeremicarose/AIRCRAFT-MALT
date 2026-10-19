import { ArrowUpRight, FileCheck2, ShieldAlert } from 'lucide-react';
import { WorkspacePanel } from '@/components/operations-ui';
import { CopyValue } from '@/components/ui/copy-value';
import { StatusChip } from '@/components/ui/status-chip';
import { assessRegistryContract } from '@/lib/contract-verification';
import { truncateMiddle } from '@/lib/format';
import { explorerTransactionUrl } from '@/lib/registry';
import type { ModeData, RegistryEvidenceData, StatusTone } from '@/lib/types';

interface VerificationItem {
  name: string;
  value: string;
  purpose: string;
  source: string;
  status: string;
  tone: StatusTone;
  copyLabel?: string;
  href?: string;
}

function VerificationRow({ item }: { item: VerificationItem }) {
  const value = item.href ? (
    <a href={item.href} target="_blank" rel="noreferrer" className="inline-flex min-w-0 items-center gap-1.5 font-mono text-xs font-semibold text-trust-cyan hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-signal-blue">
      <span className="truncate">{truncateMiddle(item.value, 12, 10)}</span><ArrowUpRight className="size-3.5 shrink-0" />
    </a>
  ) : item.copyLabel ? (
    <CopyValue value={item.value} displayValue={truncateMiddle(item.value, 12, 10)} label={item.copyLabel} className="max-w-full" />
  ) : <span className="text-xs font-semibold text-ink-secondary">{item.value}</span>;

  return (
    <div className="grid min-w-0 gap-x-5 gap-y-4 border-b border-line px-4 py-4 last:border-0 sm:grid-cols-2 xl:grid-cols-3 xl:items-start">
      <div className="min-w-0"><p className="text-[11px] font-semibold uppercase text-ink-quiet">Name</p><p className="mt-1 text-xs font-semibold text-ink">{item.name}</p></div>
      <div className="min-w-0"><p className="text-[11px] font-semibold uppercase text-ink-quiet">Value</p><div className="mt-1 min-w-0">{value}</div></div>
      <div className="min-w-0"><p className="text-[11px] font-semibold uppercase text-ink-quiet">Purpose</p><p className="mt-1 text-xs leading-5 text-ink-secondary">{item.purpose}</p></div>
      <div className="min-w-0"><p className="text-[11px] font-semibold uppercase text-ink-quiet">Source</p><p className="mt-1 break-all font-mono text-[11px] leading-5 text-ink-secondary">{item.source}</p></div>
      <div className="min-w-0"><p className="text-[11px] font-semibold uppercase text-ink-quiet">Status</p><div className="mt-1"><StatusChip label={item.status} tone={item.tone} /></div></div>
    </div>
  );
}

export function RegistryContractVerification({ evidence, mode }: { evidence: RegistryEvidenceData | null; mode: ModeData | null }) {
  const assessment = assessRegistryContract(evidence, mode);
  const expectedCodeHash = evidence?.contract.code_hash ?? 'Evidence unavailable';
  const expectedHashType = evidence?.contract.hash_type ?? 'Unknown';
  const configuredCodeHash = mode?.receiver_registry_type_hash || 'Not configured';
  const configuredHashType = mode?.receiver_registry_hash_type || 'Not configured';
  const codeMatches = Boolean(evidence && mode?.receiver_registry_type_hash && evidence.contract.code_hash.toLowerCase() === mode.receiver_registry_type_hash.toLowerCase());
  const hashTypeMatches = Boolean(evidence && mode?.receiver_registry_hash_type && evidence.contract.hash_type.toLowerCase() === mode.receiver_registry_hash_type.toLowerCase());
  const items: VerificationItem[] = [
    {
      name: 'Expected contract code hash',
      value: expectedCodeHash,
      purpose: 'Identifies the reviewed Registry V2 contract binary used by the saved lifecycle evidence.',
      source: evidence ? 'Saved testnet evidence manifest' : 'Unavailable',
      status: evidence ? 'EVIDENCE AVAILABLE' : 'UNAVAILABLE',
      tone: evidence ? 'trust' : 'attention',
      copyLabel: evidence ? 'expected Registry contract code hash' : undefined,
    },
    {
      name: 'Runtime contract code hash',
      value: configuredCodeHash,
      purpose: 'Tells the MLAT backend which exact Registry V2 scripts the CKB indexer may return.',
      source: 'RECEIVER_REGISTRY_TYPE_HASH',
      status: !mode?.receiver_registry_type_hash ? 'NOT CONFIGURED' : codeMatches ? 'MATCH' : 'MISMATCH',
      tone: !mode?.receiver_registry_type_hash || !codeMatches ? 'failure' : 'trust',
      copyLabel: mode?.receiver_registry_type_hash ? 'runtime Registry contract code hash' : undefined,
    },
    {
      name: 'Script hash type',
      value: `${configuredHashType} (expected ${expectedHashType})`,
      purpose: 'Controls how the Registry script binds to contract code. The reviewed deployment uses immutable data1 binding.',
      source: 'RECEIVER_REGISTRY_HASH_TYPE',
      status: hashTypeMatches && mode?.registry_code_immutable ? 'IMMUTABLE MATCH' : 'REVIEW',
      tone: hashTypeMatches && mode?.registry_code_immutable ? 'healthy' : 'attention',
    },
  ];

  if (evidence) {
    items.push({
      name: 'Deployment transaction',
      value: evidence.contract.deployment_transaction,
      purpose: 'Links the reviewed contract deployment to its public CKB testnet transaction.',
      source: `${evidence.network} saved evidence`,
      status: evidence.live_query ? 'LIVE QUERY' : 'SAVED EVIDENCE',
      tone: evidence.live_query ? 'healthy' : 'selection',
      href: explorerTransactionUrl(evidence.contract.deployment_transaction),
    });
  }

  return (
    <WorkspacePanel title="Registry contract verification" detail="Connect runtime configuration to the reviewed public CKB deployment without treating saved evidence as a live query." tone={assessment.tone}>
      <div className="flex flex-col gap-3 border-b border-line p-4 sm:flex-row sm:items-start">
        {assessment.result === 'match' ? <FileCheck2 className="mt-0.5 size-5 shrink-0 text-trust-cyan" /> : <ShieldAlert className="mt-0.5 size-5 shrink-0 text-attention" />}
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2"><p className="text-xs font-semibold text-ink">Configuration result</p><StatusChip label={assessment.label} tone={assessment.tone} /></div>
          <p className="mt-2 text-xs leading-5 text-ink-secondary">{assessment.explanation}</p>
          <p className="mt-2 text-xs leading-5 text-ink-secondary"><strong className="text-ink">Next action:</strong> {assessment.nextAction}</p>
        </div>
      </div>
      <div>{items.map((item) => <VerificationRow key={item.name} item={item} />)}</div>
      <div className="border-t border-line bg-graphite-raised/40 px-4 py-3 text-xs leading-5 text-ink-secondary">
        <strong className="text-ink">Trust boundary:</strong> this evidence can show the deployed code, public transactions, owner-authorized lifecycle, and runtime configuration. It does not prove a physical receiver exists, its claimed location is true, its feed is honest, or its clock is accurate.
      </div>
    </WorkspacePanel>
  );
}
