import { ccc } from "@ckb-ccc/core";

import type { RegistryDeployment } from "./discovery.js";
import {
  decodeRegistryV2Record,
  normalizeReceiverIdentity,
  validateCreation,
  validateSuccessor,
  type RegistryV2Record,
} from "./record.js";

export type RegistryLifecycleAction = "create" | "update" | "transfer" | "revoke";

export interface RegistryHistoryEvent {
  action: RegistryLifecycleAction;
  receiver_identity: string;
  record: RegistryV2Record;
  ownerLock: ccc.Script;
  transactionHash: string;
  blockNumber: bigint;
  outputIndex: bigint;
}

export interface HistoryOptions {
  maxEvents?: number;
  maxPages?: number;
  pageSize?: number;
}

export class RegistryV2History {
  readonly contractCodeHash: string;

  constructor(
    readonly client: ccc.Client,
    readonly deployment: RegistryDeployment,
  ) {
    this.contractCodeHash = normalizeReceiverIdentity(deployment.contractCodeHash);
  }

  async discover(
    receiverIdentityValue: string,
    options: HistoryOptions = {},
  ): Promise<RegistryHistoryEvent[]> {
    const receiverIdentity = normalizeReceiverIdentity(receiverIdentityValue);
    const typeScript = ccc.Script.from({
      codeHash: this.contractCodeHash,
      hashType: this.deployment.scriptHashType,
      args: receiverIdentity,
    });
    const pageSize = Math.max(1, Math.min(options.pageSize ?? 100, 1_000));
    const maxPages = Math.max(1, options.maxPages ?? 100);
    const maxEvents = Math.max(1, options.maxEvents ?? 1_000);
    const indexed = new Map<string, { blockNumber: bigint }>();
    let cursor: string | undefined;
    let exhausted = false;

    for (let pageIndex = 0; pageIndex < maxPages; pageIndex += 1) {
      const page = await this.client.findTransactionsPaged(
        {
          script: typeScript,
          scriptType: "type",
          scriptSearchMode: "exact",
          groupByTransaction: true,
        },
        "asc",
        pageSize,
        cursor,
      );
      for (const transaction of page.transactions) {
        indexed.set(normalizeReceiverIdentity(transaction.txHash), {
          blockNumber: transaction.blockNumber,
        });
      }
      if (indexed.size > maxEvents) {
        throw new Error("Registry history exceeded maxEvents");
      }
      const nextCursor = page.lastCursor || undefined;
      if (page.transactions.length === 0) {
        exhausted = true;
        break;
      }
      if (nextCursor === undefined || nextCursor === cursor) {
        throw new Error("Registry history received an invalid pagination cursor");
      }
      cursor = nextCursor;
    }
    if (!exhausted) throw new Error("Registry history exceeded maxPages");

    const events: RegistryHistoryEvent[] = [];
    for (const [transactionHash, indexEntry] of indexed) {
      const response = await this.client.getTransaction(transactionHash);
      if (response === undefined || response.status !== "committed") {
        throw new Error(`Registry history transaction is not committed: ${transactionHash}`);
      }
      const matchingOutputs = response.transaction.outputs
        .map((output, outputIndex) => ({ output, outputIndex }))
        .filter(({ output }) => output.type?.eq(typeScript));
      if (matchingOutputs.length !== 1) {
        throw new Error(`Registry history transaction has ${matchingOutputs.length} matching outputs`);
      }
      const { output, outputIndex } = matchingOutputs[0]!;
      const outputData = response.transaction.outputsData[outputIndex];
      if (outputData === undefined) throw new Error("Registry history output data is missing");
      events.push({
        action: "update",
        receiver_identity: receiverIdentity,
        record: decodeRegistryV2Record(ccc.bytesFrom(outputData)),
        ownerLock: output.lock,
        transactionHash,
        blockNumber: response.blockNumber ?? indexEntry.blockNumber,
        outputIndex: BigInt(outputIndex),
      });
    }

    events.sort((left, right) =>
      left.record.sequence < right.record.sequence
        ? -1
        : left.record.sequence > right.record.sequence
          ? 1
          : 0,
    );
    for (const [index, event] of events.entries()) {
      if (index === 0) {
        validateCreation(event.record);
        event.action = "create";
        continue;
      }
      const previous = events[index - 1]!;
      validateSuccessor(previous.record, event.record);
      event.action =
        event.record.status === "revoked"
          ? "revoke"
          : event.ownerLock.eq(previous.ownerLock)
            ? "update"
            : "transfer";
    }
    return events;
  }
}
