'use client';

import {
  REGISTRY_V2_PUDGE_2026_07_30,
  RegistryV2Sdk,
  type DiscoveredReceiver,
  type RegistryHistoryEvent,
  type RegistryV2Record,
} from '@aircraft-malt/registry-v2';
import { ccc } from '@ckb-ccc/connector-react';
import type { Receiver } from '@/lib/types';

export const CKB_TESTNET_EXPLORER = 'https://pudge.explorer.nervos.org';

export const REGISTRY_V2_TESTNET_DEPLOYMENT = REGISTRY_V2_PUDGE_2026_07_30;

export function createRegistrySdk(client: ccc.Client): RegistryV2Sdk {
  return RegistryV2Sdk.testnet(client);
}

export async function withRegistryTimeout<T>(
  operation: Promise<T>,
  label: string,
  timeoutMs = 15_000,
): Promise<T> {
  let timeout: ReturnType<typeof setTimeout> | undefined;
  try {
    return await Promise.race([
      operation,
      new Promise<never>((_, reject) => {
        timeout = setTimeout(
          () => reject(new Error(`${label} timed out after ${timeoutMs}ms`)),
          timeoutMs,
        );
      }),
    ]);
  } finally {
    if (timeout) clearTimeout(timeout);
  }
}

export function explorerTransactionUrl(transactionHash: string): string {
  return `${CKB_TESTNET_EXPLORER}/transaction/${transactionHash}`;
}

export function discoveredReceiverToUi(receiver: DiscoveredReceiver): Receiver {
  return {
    receiver_id: receiver.receiver_identity,
    receiver_identity: receiver.receiver_identity,
    receiver_label: receiver.record.receiver_id,
    data_source: 'ckb_registry',
    latitude: receiver.record.latitude,
    longitude: receiver.record.longitude,
    altitude: receiver.record.altitude,
    status: receiver.record.status,
    updated_at: receiver.record.updated_at.toString(),
    capabilities: receiver.record.capabilities,
    registry: {
      sequence: receiver.record.sequence.toString(),
      updated_at: receiver.record.updated_at.toString(),
      owner_lock_args: receiver.provenance.ownerLock.args,
      owner_lock: {
        code_hash: receiver.provenance.ownerLock.codeHash,
        hash_type: receiver.provenance.ownerLock.hashType,
        args: receiver.provenance.ownerLock.args,
      },
      out_point: {
        tx_hash: receiver.provenance.outPoint.txHash,
        index: receiver.provenance.outPoint.index.toString(),
      },
      metadata_hash: receiver.record.metadata_hash ?? null,
      stream_endpoint: receiver.record.stream_endpoint,
      stream_protocol: receiver.record.stream_protocol,
      stream_format: receiver.record.stream_format,
    },
  };
}

function serializableRecord(record: RegistryV2Record) {
  return {
    ...record,
    sequence: record.sequence.toString(),
    updated_at: record.updated_at.toString(),
  };
}

export function receiverExport(receiver: DiscoveredReceiver, history?: RegistryHistoryEvent[]) {
  return {
    schema_version: 1,
    network: 'CKB testnet',
    exported_at: new Date().toISOString(),
    contract: {
      code_hash: REGISTRY_V2_TESTNET_DEPLOYMENT.contractCodeHash,
      deployment_out_point: {
        tx_hash: REGISTRY_V2_TESTNET_DEPLOYMENT.contractCellDep.outPoint.txHash,
        index: REGISTRY_V2_TESTNET_DEPLOYMENT.contractCellDep.outPoint.index.toString(),
      },
    },
    receiver: {
      receiver_identity: receiver.receiver_identity,
      record: serializableRecord(receiver.record),
      provenance: {
        out_point: {
          tx_hash: receiver.provenance.outPoint.txHash,
          index: receiver.provenance.outPoint.index.toString(),
        },
        owner_lock: {
          code_hash: receiver.provenance.ownerLock.codeHash,
          hash_type: receiver.provenance.ownerLock.hashType,
          args: receiver.provenance.ownerLock.args,
        },
      },
      lifecycle: history?.map((event) => ({
        action: event.action,
        transaction_hash: event.transactionHash,
        block_number: event.blockNumber.toString(),
        output_index: event.outputIndex.toString(),
        owner_lock: {
          code_hash: event.ownerLock.codeHash,
          hash_type: event.ownerLock.hashType,
          args: event.ownerLock.args,
        },
        record: serializableRecord(event.record),
      })) ?? [],
    },
  };
}

export function registryDirectoryExport(receivers: DiscoveredReceiver[]) {
  return {
    schema_version: 1,
    network: 'CKB testnet',
    exported_at: new Date().toISOString(),
    contract: {
      code_hash: REGISTRY_V2_TESTNET_DEPLOYMENT.contractCodeHash,
      deployment_out_point: {
        tx_hash: REGISTRY_V2_TESTNET_DEPLOYMENT.contractCellDep.outPoint.txHash,
        index: REGISTRY_V2_TESTNET_DEPLOYMENT.contractCellDep.outPoint.index.toString(),
      },
    },
    receivers: receivers.map((receiver) => receiverExport(receiver).receiver),
  };
}

export function downloadJson(filename: string, value: unknown): void {
  const blob = new Blob([`${JSON.stringify(value, null, 2)}\n`], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export function explainRegistryError(error: unknown): { message: string; technical: string } {
  const technical = error instanceof Error ? error.message : String(error);
  const lower = technical.toLowerCase();
  if (lower.includes('no plain capacity cell')) {
    return { message: 'This wallet has no plain testnet CKB cell available to fund the receiver record. Add testnet CKB, then try again.', technical };
  }
  if (lower.includes('does not own')) {
    return { message: 'The connected wallet is not the current owner of this receiver. Connect the owner wallet to continue.', technical };
  }
  if (lower.includes('rejected') || lower.includes('denied') || lower.includes('cancel')) {
    return { message: 'The wallet did not approve the transaction. Review the details and try again when ready.', technical };
  }
  if (lower.includes('timeout')) {
    return { message: 'The transaction was submitted but was not confirmed before the wait period ended. Check its testnet explorer page before trying again.', technical };
  }
  if (lower.includes('network') || lower.includes('fetch') || lower.includes('rpc')) {
    return { message: 'The CKB testnet service could not be reached. Check your connection and try again.', technical };
  }
  return { message: 'The registry action could not be completed. Review the technical details, correct any invalid field, and try again.', technical };
}
