'use client';

import type {
  DiscoveredReceiver,
  RegistryV2CreateInput,
  RegistryV2Sdk,
  RegistryV2Update,
} from '@aircraft-malt/registry-v2';
import { ccc } from '@ckb-ccc/connector-react';
import { ArrowUpRight, Ban, Check, CircleAlert, FilePlus2, LoaderCircle, Pencil, Send, ShieldAlert } from 'lucide-react';
import { useEffect, useMemo, useState, type FormEvent, type ReactNode } from 'react';
import { WorkspacePanel } from '@/components/operations-ui';
import { Button } from '@/components/ui/button';
import { CopyValue } from '@/components/ui/copy-value';
import { ProgressBar } from '@/components/ui/progress-bar';
import { StatusChip } from '@/components/ui/status-chip';
import { WalletControl } from '@/components/wallet-control';
import { titleCase, truncateMiddle } from '@/lib/format';
import { explainRegistryError, explorerTransactionUrl } from '@/lib/registry';
import { cn } from '@/lib/utils';

type ActionKind = 'create' | 'update' | 'transfer' | 'revoke';
type TransactionPhase = 'idle' | 'preparing' | 'signature' | 'confirming' | 'complete' | 'error';

interface RecordFormState {
  receiverId: string;
  latitude: string;
  longitude: string;
  altitude: string;
  status: 'online' | 'offline' | 'degraded';
  capabilities: string[];
  streamEndpoint: string;
  streamProtocol: 'websocket-json' | 'command-jsonl';
  streamFormat: 'json' | 'jsonl';
  metadataHash: string;
}

const blankRecord: RecordFormState = {
  receiverId: '',
  latitude: '',
  longitude: '',
  altitude: '',
  status: 'online',
  capabilities: ['mode-s'],
  streamEndpoint: '',
  streamProtocol: 'websocket-json',
  streamFormat: 'json',
  metadataHash: '',
};

const actionOptions: Array<{ value: ActionKind; label: string; icon: typeof FilePlus2 }> = [
  { value: 'create', label: 'Create', icon: FilePlus2 },
  { value: 'update', label: 'Update', icon: Pencil },
  { value: 'transfer', label: 'Transfer', icon: Send },
  { value: 'revoke', label: 'Revoke', icon: Ban },
];

const phaseCopy: Record<Exclude<TransactionPhase, 'idle' | 'error'>, { label: string; value: number }> = {
  preparing: { label: 'Preparing the Registry V2 transaction', value: 20 },
  signature: { label: 'Waiting for wallet signature and submission', value: 45 },
  confirming: { label: 'Submitted; waiting for on-chain confirmation', value: 82 },
  complete: { label: 'Registry directory updated', value: 100 },
};

const inputClass = 'mt-1 h-10 w-full rounded-md border border-line bg-graphite-raised px-3 text-sm text-ink outline-none transition-colors placeholder:text-[#87919e] hover:border-[#3c4654] focus:border-signal-blue focus:ring-2 focus:ring-signal-blue/25 disabled:cursor-not-allowed disabled:opacity-60';
const labelClass = 'text-xs font-semibold text-ink-secondary';

function Field({ label, hint, children }: { label: string; hint?: string; children: ReactNode }) {
  return <label className="block min-w-0"><span className={labelClass}>{label}</span>{children}{hint ? <span className="mt-1 block text-[11px] leading-5 text-ink-quiet">{hint}</span> : null}</label>;
}

function ActionTarget({ receiver }: { receiver: DiscoveredReceiver }) {
  const statusTone = receiver.record.status === 'revoked'
    ? 'failure'
    : receiver.record.status === 'degraded'
      ? 'attention'
      : receiver.record.status === 'online'
        ? 'healthy'
        : 'neutral';

  return (
    <section className="mb-4 border-b border-line pb-4" aria-label={`Selected receiver ${receiver.record.receiver_id}`} data-registry-action-target>
      <div className="flex min-w-0 items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-[11px] font-semibold text-ink-quiet">Selected receiver</p>
          <p className="mt-1 break-words text-sm font-semibold text-ink">{receiver.record.receiver_id}</p>
          <div className="mt-1 text-[11px] text-ink-quiet">
            <CopyValue
              value={receiver.receiver_identity}
              displayValue={truncateMiddle(receiver.receiver_identity, 12, 10)}
              label="selected receiver Type ID"
            />
          </div>
        </div>
        <StatusChip label={titleCase(receiver.record.status)} tone={statusTone} />
      </div>
      <dl className="mt-3 grid gap-3 text-xs sm:grid-cols-2">
        <div className="min-w-0">
          <dt className="text-[11px] text-ink-quiet">Lifecycle sequence</dt>
          <dd className="mt-1 font-mono font-semibold text-ink-secondary">{receiver.record.sequence.toString()}</dd>
        </div>
        <div className="min-w-0">
          <dt className="text-[11px] text-ink-quiet">Current owner lock</dt>
          <dd className="mt-1 text-ink-secondary">
            <CopyValue
              value={receiver.provenance.ownerLock.args}
              displayValue={truncateMiddle(receiver.provenance.ownerLock.args, 9, 7)}
              label="current owner lock"
            />
          </dd>
        </div>
      </dl>
    </section>
  );
}

function recordFormFrom(receiver?: DiscoveredReceiver): RecordFormState {
  if (!receiver) return blankRecord;
  const record = receiver.record;
  return {
    receiverId: record.receiver_id,
    latitude: String(record.latitude),
    longitude: String(record.longitude),
    altitude: String(record.altitude),
    status: record.status === 'revoked' ? 'offline' : record.status,
    capabilities: record.capabilities,
    streamEndpoint: record.stream_endpoint ?? '',
    streamProtocol: record.stream_protocol ?? 'websocket-json',
    streamFormat: record.stream_format ?? 'json',
    metadataHash: record.metadata_hash ?? '',
  };
}

function createInput(form: RecordFormState): RegistryV2CreateInput {
  const endpoint = form.streamEndpoint.trim();
  const metadataHash = form.metadataHash.trim();
  return {
    receiver_id: form.receiverId.trim().toUpperCase(),
    latitude: Number(form.latitude),
    longitude: Number(form.longitude),
    altitude: Number(form.altitude),
    status: form.status,
    capabilities: form.capabilities,
    ...(endpoint ? {
      stream_endpoint: endpoint,
      stream_protocol: form.streamProtocol,
      stream_format: form.streamFormat,
    } : {}),
    ...(metadataHash ? { metadata_hash: metadataHash } : {}),
  };
}

function updateInput(form: RecordFormState): RegistryV2Update {
  const endpoint = form.streamEndpoint.trim();
  const metadataHash = form.metadataHash.trim();
  return {
    latitude: Number(form.latitude),
    longitude: Number(form.longitude),
    altitude: Number(form.altitude),
    status: form.status,
    capabilities: form.capabilities,
    stream_endpoint: endpoint || undefined,
    stream_protocol: endpoint ? form.streamProtocol : undefined,
    stream_format: endpoint ? form.streamFormat : undefined,
    metadata_hash: metadataHash || undefined,
  };
}

export function RegistryActionPanel({
  sdk,
  signer,
  selected,
  ownsSelected,
  onCommitted,
}: {
  sdk: RegistryV2Sdk;
  signer?: ccc.Signer;
  selected?: DiscoveredReceiver;
  ownsSelected: boolean;
  onCommitted: (receiverIdentity: string) => Promise<void>;
}) {
  const { open } = ccc.useCcc();
  const [action, setAction] = useState<ActionKind>('create');
  const [form, setForm] = useState<RecordFormState>(blankRecord);
  const [privacyAccepted, setPrivacyAccepted] = useState(false);
  const [recipientAddress, setRecipientAddress] = useState('');
  const [confirmationText, setConfirmationText] = useState('');
  const [phase, setPhase] = useState<TransactionPhase>('idle');
  const [transactionHash, setTransactionHash] = useState('');
  const [resultIdentity, setResultIdentity] = useState('');
  const [error, setError] = useState<{ message: string; technical: string } | null>(null);
  const busy = ['preparing', 'signature', 'confirming'].includes(phase);
  const selectedUnavailable = action !== 'create' && !selected;
  const revoked = selected?.record.status === 'revoked';
  const ownerRequired = action !== 'create' && !ownsSelected;
  const labelConfirmationRequired = action === 'transfer' || action === 'revoke';
  const expectedConfirmation = selected?.record.receiver_id ?? '';
  const deploymentReadOnly = sdk.deployment.readOnly === true;

  useEffect(() => {
    if (action === 'create') setForm(blankRecord);
    else setForm(recordFormFrom(selected));
    setPrivacyAccepted(false);
    setRecipientAddress('');
    setConfirmationText('');
    setPhase('idle');
    setTransactionHash('');
    setResultIdentity('');
    setError(null);
  }, [action, selected?.receiver_identity]);

  const blocker = useMemo(() => {
    if (deploymentReadOnly) {
      return 'This historical testnet deployment is read-only because its contract code can be replaced under the same type hash. Lifecycle actions require a reviewed data1 deployment.';
    }
    if (!signer) return 'Connect a CKB testnet wallet to prepare and sign this action.';
    if (selectedUnavailable) return 'Select an on-chain receiver from the directory first.';
    if (revoked && action !== 'create') return 'This receiver is permanently revoked. Its lifecycle cannot continue.';
    if (ownerRequired) return 'The connected wallet is not the current owner of this receiver.';
    return null;
  }, [action, deploymentReadOnly, ownerRequired, revoked, selectedUnavailable, signer]);

  const setCapability = (capability: string, checked: boolean) => {
    setForm((current) => ({
      ...current,
      capabilities: checked
        ? [...new Set([...current.capabilities, capability])]
        : current.capabilities.filter((item) => item !== capability),
    }));
  };

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (blocker || !signer || busy) return;
    if ((action === 'create' || action === 'update') && !privacyAccepted) return;
    if (labelConfirmationRequired && confirmationText !== expectedConfirmation) return;

    setError(null);
    setTransactionHash('');
    setResultIdentity('');
    setPhase('preparing');
    let submittedHash = '';
    try {
      let transaction: ccc.Transaction;
      let receiverIdentity = selected?.receiver_identity ?? '';
      if (action === 'create') {
        const prepared = await sdk.prepareCreate(signer, createInput(form));
        transaction = prepared.transaction;
        receiverIdentity = prepared.receiver_identity;
      } else if (action === 'update' && selected) {
        transaction = await sdk.prepareUpdate(
          signer,
          selected.receiver_identity,
          updateInput(form),
        );
      } else if (action === 'transfer' && selected) {
        transaction = await sdk.prepareTransfer(
          signer,
          selected.receiver_identity,
          recipientAddress.trim(),
        );
      } else if (action === 'revoke' && selected) {
        transaction = await sdk.prepareRevoke(
          signer,
          selected.receiver_identity,
        );
      } else {
        throw new Error('Select a receiver before preparing this action');
      }

      setResultIdentity(receiverIdentity);
      setPhase('signature');
      submittedHash = await signer.sendTransaction(transaction);
      setTransactionHash(submittedHash);
      setPhase('confirming');
      await sdk.waitForIndexedTransaction(receiverIdentity, submittedHash, {
        indexerTimeoutMs: 60_000,
        pollIntervalMs: 2_000,
        transactionTimeoutMs: 120_000,
      });
      await onCommitted(receiverIdentity);
      setPhase('complete');
    } catch (cause) {
      setError(explainRegistryError(cause));
      if (submittedHash) setTransactionHash(submittedHash);
      setPhase('error');
    }
  };

  const primaryLabel = action === 'create'
    ? 'Create receiver identity'
    : action === 'update'
      ? 'Update receiver record'
      : action === 'transfer'
        ? 'Transfer receiver ownership'
        : selected
          ? `Permanently revoke ${selected.record.receiver_id}`
          : 'Permanently revoke receiver';

  return (
    <WorkspacePanel
      title="Owner actions"
      detail={deploymentReadOnly ? 'Historical lifecycle evidence remains inspectable. New transactions are disabled until an immutable contract deployment is configured.' : 'Transactions are prepared by the Registry V2 SDK and signed in your wallet on CKB testnet.'}
      action={<WalletControl />}
      tone={action === 'revoke' ? 'failure' : 'trust'}
    >
      <div className="flex overflow-x-auto border-b border-line p-2" role="tablist" aria-label="Registry action">
        {actionOptions.map((option) => {
          const Icon = option.icon;
          return (
            <button
              key={option.value}
              type="button"
              role="tab"
              aria-selected={action === option.value}
              onClick={() => setAction(option.value)}
              disabled={busy}
              className={cn('flex h-9 min-w-[108px] flex-1 items-center justify-center gap-2 rounded-md px-3 text-xs font-semibold text-ink-quiet outline-none transition-colors hover:bg-graphite-hover hover:text-ink focus-visible:ring-2 focus-visible:ring-signal-blue disabled:opacity-45', action === option.value && (option.value === 'revoke' ? 'bg-failure/10 text-failure' : 'bg-signal-blue/10 text-signal-blue'))}
            >
              <Icon className="size-3.5" />{option.label}
            </button>
          );
        })}
      </div>

      <form onSubmit={submit} className="p-4">
        {action !== 'create' && selected ? <ActionTarget receiver={selected} /> : null}

        <div className="mb-4 flex items-start gap-3 rounded-md bg-graphite-raised/70 p-3">
          {action === 'revoke' ? <ShieldAlert className="mt-0.5 size-4 shrink-0 text-failure" /> : <CircleAlert className="mt-0.5 size-4 shrink-0 text-trust-cyan" />}
          <div className="text-xs leading-5 text-ink-secondary">
            {action === 'create' ? 'Create one stable Type ID for this receiver. Future changes keep the same identity.' : null}
            {action === 'update' ? 'Publish a new version of the selected record. Its identity and receiver label stay fixed while the sequence increases by one.' : null}
            {action === 'transfer' ? 'Move control to another testnet address. Only that new owner can authorize later changes.' : null}
            {action === 'revoke' ? 'Publish a terminal tombstone. This identity cannot be restored or reused after confirmation.' : null}
          </div>
        </div>

        {blocker ? (
          <div className="mb-4 flex flex-col gap-3 rounded-md border border-attention/35 bg-attention/[0.06] p-3 text-xs text-ink-secondary sm:flex-row sm:items-center">
            <span className="flex-1">{blocker}</span>
            {!signer && !deploymentReadOnly ? <Button type="button" size="sm" variant="primary" onClick={open}>Connect testnet wallet</Button> : null}
          </div>
        ) : null}

        {action === 'create' || action === 'update' ? (
          <div className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <Field label="Receiver label" hint={action === 'update' ? 'Labels are immutable after creation.' : 'Use 1-64 uppercase letters, numbers, underscores, or hyphens.'}>
                <input className={inputClass} required pattern="[A-Z0-9][A-Z0-9_-]{0,63}" value={form.receiverId} disabled={action === 'update'} onChange={(event) => setForm({ ...form, receiverId: event.target.value.toUpperCase() })} placeholder="RECV_NAIROBI_001" />
              </Field>
              <Field label="Status">
                <select className={inputClass} value={form.status} onChange={(event) => setForm({ ...form, status: event.target.value as RecordFormState['status'] })}>
                  <option value="online">Online</option><option value="degraded">Degraded</option><option value="offline">Offline</option>
                </select>
              </Field>
              <Field label="Latitude" hint="Decimal degrees, from -90 to 90.">
                <input className={inputClass} required type="number" inputMode="decimal" min="-90" max="90" step="any" value={form.latitude} onChange={(event) => setForm({ ...form, latitude: event.target.value })} placeholder="-1.286389" />
              </Field>
              <Field label="Longitude" hint="Decimal degrees, from -180 to 180.">
                <input className={inputClass} required type="number" inputMode="decimal" min="-180" max="180" step="any" value={form.longitude} onChange={(event) => setForm({ ...form, longitude: event.target.value })} placeholder="36.817223" />
              </Field>
              <Field label="Altitude in metres" hint="Height above mean sea level, from -500 to 20,000 metres.">
                <input className={inputClass} required type="number" inputMode="decimal" min="-500" max="20000" step="any" value={form.altitude} onChange={(event) => setForm({ ...form, altitude: event.target.value })} placeholder="1795" />
              </Field>
              <fieldset>
                <legend className={labelClass}>Capabilities</legend>
                <div className="mt-2 flex min-h-10 flex-wrap items-center gap-x-4 gap-y-2">
                  {['mode-s', 'adsb', 'mlat', 'raw'].map((capability) => (
                    <label key={capability} className="flex min-h-8 items-center gap-2 text-xs text-ink-secondary">
                      <input type="checkbox" checked={form.capabilities.includes(capability)} disabled={capability === 'mode-s'} onChange={(event) => setCapability(capability, event.target.checked)} className="size-4 accent-signal-blue" />
                      {capability === 'adsb' ? 'ADS-B' : capability.toUpperCase()}
                    </label>
                  ))}
                </div>
              </fieldset>
            </div>

            <details className="rounded-md border border-line bg-graphite-raised/40 p-3">
              <summary className="cursor-pointer text-xs font-semibold text-ink-secondary">Optional network feed and metadata</summary>
              <div className="mt-4 grid gap-4 md:grid-cols-2">
                <Field label="Stream endpoint" hint="Publish only an endpoint intended for network coordinators.">
                  <input className={inputClass} type="url" value={form.streamEndpoint} onChange={(event) => setForm({ ...form, streamEndpoint: event.target.value })} placeholder="wss://receiver.example/feed" />
                </Field>
                <Field label="Stream protocol">
                  <select className={inputClass} value={form.streamProtocol} onChange={(event) => setForm({ ...form, streamProtocol: event.target.value as RecordFormState['streamProtocol'] })}><option value="websocket-json">WebSocket JSON</option><option value="command-jsonl">Command JSONL</option></select>
                </Field>
                <Field label="Stream format">
                  <select className={inputClass} value={form.streamFormat} onChange={(event) => setForm({ ...form, streamFormat: event.target.value as RecordFormState['streamFormat'] })}><option value="json">JSON</option><option value="jsonl">JSONL</option></select>
                </Field>
                <Field label="Metadata hash" hint="Optional 0x-prefixed 32-byte hash of off-chain metadata.">
                  <input className={inputClass} pattern="0x[0-9a-fA-F]{64}" value={form.metadataHash} onChange={(event) => setForm({ ...form, metadataHash: event.target.value })} placeholder="0x…" />
                </Field>
              </div>
            </details>

            <label className="flex items-start gap-3 rounded-md border border-attention/35 bg-attention/[0.06] p-3 text-xs leading-5 text-ink-secondary">
              <input type="checkbox" checked={privacyAccepted} onChange={(event) => setPrivacyAccepted(event.target.checked)} className="mt-0.5 size-4 shrink-0 accent-signal-blue" />
              <span><strong className="text-ink">I understand the location is public.</strong> Coordinates and earlier values remain visible in CKB transaction history. Use a deliberately coarse site-area coordinate if an exact antenna location is sensitive.</span>
            </label>
          </div>
        ) : null}

        {action === 'transfer' ? (
          <div className="space-y-4">
            <Field label="New owner testnet address" hint="The address must start with ckt and belong to the intended recipient.">
              <input className={inputClass} required value={recipientAddress} onChange={(event) => setRecipientAddress(event.target.value)} placeholder="ckt1…" autoComplete="off" />
            </Field>
            <Field label={`Type ${expectedConfirmation || 'the receiver label'} to confirm`}>
              <input className={inputClass} required value={confirmationText} onChange={(event) => setConfirmationText(event.target.value)} autoComplete="off" />
            </Field>
          </div>
        ) : null}

        {action === 'revoke' ? (
          <div className="space-y-4">
            <div className="rounded-md border border-failure/35 bg-failure/[0.07] p-3 text-xs leading-5 text-ink-secondary"><strong className="text-[#ff9ba0]">{selected ? `Revoking ${selected.record.receiver_id} is permanent.` : 'Revocation is permanent.'}</strong> The current stream fields will be removed and this Type ID can never return to an active state.</div>
            <Field label={`Type ${expectedConfirmation || 'the receiver label'} to confirm`}>
              <input className={inputClass} required value={confirmationText} onChange={(event) => setConfirmationText(event.target.value)} autoComplete="off" />
            </Field>
          </div>
        ) : null}

        {phase !== 'idle' ? (
          <div className="mt-4 rounded-md border border-line bg-graphite-raised/50 p-3" aria-live="polite">
            {phase !== 'error' ? <>
              <div className="mb-2 flex items-center gap-2 text-xs font-semibold text-ink">
                {phase === 'complete' ? <Check className="size-4 text-healthy" /> : <LoaderCircle className="size-4 animate-spin text-signal-blue" />}
                {phaseCopy[phase].label}
              </div>
              <ProgressBar value={phaseCopy[phase].value} label="Registry transaction progress" tone={phase === 'complete' ? 'healthy' : 'selection'} />
            </> : error ? <div role="alert"><p className="text-xs font-semibold text-failure">Action not completed</p><p className="mt-1 text-xs leading-5 text-ink-secondary">{error.message}</p><details className="mt-2"><summary className="cursor-pointer text-[11px] text-ink-quiet">Technical details</summary><pre className="mt-2 max-h-32 overflow-auto whitespace-pre-wrap rounded bg-graphite p-2 font-mono text-[10px] text-ink-quiet">{error.technical}</pre></details></div> : null}
            {transactionHash ? <div className="mt-3 flex flex-wrap items-center gap-2"><a href={explorerTransactionUrl(transactionHash)} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1.5 text-xs font-semibold text-trust-cyan hover:underline">Verify transaction on CKB Explorer<ArrowUpRight className="size-3.5" /></a><CopyValue value={transactionHash} displayValue={`${transactionHash.slice(0, 10)}...${transactionHash.slice(-8)}`} label="transaction hash" className="text-[10px] text-ink-quiet" /></div> : null}
            {phase === 'complete' && resultIdentity ? <div className="mt-2 text-[10px] text-ink-quiet"><span className="mr-1">Receiver identity:</span><CopyValue value={resultIdentity} displayValue={`${resultIdentity.slice(0, 10)}...${resultIdentity.slice(-8)}`} label="receiver identity" /></div> : null}
          </div>
        ) : null}

        <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-line pt-4">
          <div className="flex items-center gap-2"><StatusChip label="CKB testnet" tone="trust" /><span className="text-[11px] text-ink-quiet">Your wallet shows the final transaction before signing.</span></div>
          <Button
            type="submit"
            variant={action === 'revoke' ? 'danger' : 'primary'}
            className={action === 'revoke' ? 'h-auto min-h-9 max-w-full whitespace-normal py-2 text-center' : undefined}
            disabled={Boolean(blocker) || busy || ((action === 'create' || action === 'update') && !privacyAccepted) || (labelConfirmationRequired && confirmationText !== expectedConfirmation)}
          >
            {busy ? <LoaderCircle className="size-4 animate-spin" /> : action === 'revoke' ? <Ban className="size-4" /> : action === 'transfer' ? <Send className="size-4" /> : action === 'update' ? <Pencil className="size-4" /> : <FilePlus2 className="size-4" />}
            {busy ? 'Transaction in progress' : primaryLabel}
          </Button>
        </div>
      </form>
    </WorkspacePanel>
  );
}
