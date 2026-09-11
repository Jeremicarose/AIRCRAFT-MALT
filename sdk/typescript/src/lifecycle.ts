import { ccc } from "@ckb-ccc/core";

import {
  RegistryV2Discovery,
  type DiscoveredReceiver,
  type RegistryDeployment,
} from "./discovery.js";
import { REGISTRY_V2_PUDGE } from "./deployments.js";
import { RegistryV2History } from "./history.js";
import {
  calculateTypeId,
  encodeRegistryV2CellData,
  normalizeReceiverIdentity,
  validateCreation,
  validateSuccessor,
  type RegistryV2Record,
} from "./record.js";

export interface PreparedCreate {
  receiver_identity: string;
  transaction: ccc.Transaction;
}

export interface SubmittedCreate {
  receiver_identity: string;
  transactionHash: string;
}

export type RegistryV2CreateInput = Omit<
  RegistryV2Record,
  "schema_version" | "sequence" | "updated_at"
> &
  Partial<Pick<RegistryV2Record, "schema_version" | "sequence" | "updated_at">>;

export type RegistryV2Update = Partial<
  Omit<RegistryV2Record, "schema_version" | "receiver_id" | "sequence" | "updated_at">
> & {
  updated_at?: bigint;
};

export type RegistryV2Owner = ccc.ScriptLike | string;

export interface WaitForIndexedTransactionOptions {
  confirmations?: number;
  indexerTimeoutMs?: number;
  pollIntervalMs?: number;
  transactionTimeoutMs?: number;
}

export interface WritableRegistryV2TestnetDeployment {
  contractCodeHash: string;
  contractTransactionHash: string;
  contractIndex: number;
}

function recordObject(value: unknown): Record<string, unknown> {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    throw new Error("Registry V2 record input must be an object");
  }
  return value as Record<string, unknown>;
}

function unixTime(): bigint {
  return BigInt(Math.floor(Date.now() / 1_000));
}

function nextTimestamp(previous: RegistryV2Record, value?: bigint): bigint {
  const candidate = value ?? unixTime();
  return candidate < previous.updated_at ? previous.updated_at : candidate;
}

function normalizeTransactionHash(value: string): string {
  if (!/^0x[0-9a-fA-F]{64}$/.test(value)) {
    throw new Error("transactionHash must be 0x-prefixed 32-byte hex");
  }
  return value.toLowerCase();
}

function normalizeContractCodeHash(value: string): string {
  if (!/^0x[0-9a-fA-F]{64}$/.test(value)) {
    throw new Error("contractCodeHash must be 0x-prefixed 32-byte hex");
  }
  return value.toLowerCase();
}

export class RegistryV2Sdk {
  readonly discovery: RegistryV2Discovery;
  readonly history: RegistryV2History;
  private deploymentVerification?: Promise<void>;

  constructor(
    readonly client: ccc.Client,
    readonly deployment: RegistryDeployment,
  ) {
    this.discovery = new RegistryV2Discovery(client, deployment);
    this.history = new RegistryV2History(client, deployment);
  }

  static testnet(client: ccc.Client): RegistryV2Sdk {
    if (client.addressPrefix !== "ckt") {
      throw new Error(
        `Registry V2 testnet requires a CKB testnet client with address prefix ckt; received ${client.addressPrefix}`,
      );
    }
    return new RegistryV2Sdk(client, REGISTRY_V2_PUDGE);
  }

  static writableTestnet(
    client: ccc.Client,
    deployment: WritableRegistryV2TestnetDeployment,
  ): RegistryV2Sdk {
    if (client.addressPrefix !== "ckt") {
      throw new Error(
        `Registry V2 testnet requires a CKB testnet client with address prefix ckt; received ${client.addressPrefix}`,
      );
    }
    if (!Number.isSafeInteger(deployment.contractIndex) || deployment.contractIndex < 0) {
      throw new Error("contractIndex must be a safe non-negative integer");
    }
    return new RegistryV2Sdk(client, {
      contractCodeHash: normalizeContractCodeHash(deployment.contractCodeHash),
      scriptHashType: "data1",
      contractCellDep: {
        outPoint: {
          txHash: normalizeTransactionHash(deployment.contractTransactionHash),
          index: deployment.contractIndex,
        },
        depType: "code",
      },
    });
  }

  async prepareCreate(
    signer: ccc.Signer,
    recordValue: RegistryV2CreateInput | RegistryV2Record,
  ): Promise<PreparedCreate> {
    await this.assertWritableDeployment();
    this.assertSignerNetwork(signer);
    const record = validateCreation({
      schema_version: 2,
      sequence: 0n,
      updated_at: unixTime(),
      ...recordObject(recordValue),
    });
    const fundingCell = await this.firstFundingCell(signer);
    const transaction = ccc.Transaction.default();
    transaction.addInput(fundingCell);
    const receiverIdentity = calculateTypeId({
      firstInputTxHash: fundingCell.outPoint.txHash,
      firstInputIndex: fundingCell.outPoint.index,
      outputIndex: 0,
    });
    const ownerLock = (await signer.getRecommendedAddressObj()).script;
    transaction.addOutput(
      {
        lock: ownerLock,
        type: {
          codeHash: this.discovery.contractCodeHash,
          hashType: this.deployment.scriptHashType,
          args: receiverIdentity,
        },
      },
      encodeRegistryV2CellData(record),
    );
    transaction.addCellDeps(this.deployment.contractCellDep);
    await transaction.completeInputsByCapacity(signer);
    await transaction.completeFeeBy(signer);
    return { receiver_identity: receiverIdentity, transaction };
  }

  async create(
    signer: ccc.Signer,
    record: RegistryV2CreateInput | RegistryV2Record,
  ): Promise<SubmittedCreate> {
    const prepared = await this.prepareCreate(signer, record);
    return {
      receiver_identity: prepared.receiver_identity,
      transactionHash: await signer.sendTransaction(prepared.transaction),
    };
  }

  async prepareUpdate(
    signer: ccc.Signer,
    receiverIdentityValue: string,
    nextRecord: RegistryV2Update | RegistryV2Record,
  ): Promise<ccc.Transaction> {
    await this.assertWritableDeployment();
    const current = await this.requireCurrentCell(receiverIdentityValue);
    const validated = validateSuccessor(current.record, {
      ...current.record,
      sequence: current.record.sequence + 1n,
      updated_at: nextTimestamp(current.record),
      ...recordObject(nextRecord),
    });
    return this.prepareSuccessor(signer, current.cell, validated, current.cell.cellOutput.lock);
  }

  async update(
    signer: ccc.Signer,
    receiverIdentity: string,
    nextRecord: RegistryV2Update | RegistryV2Record,
  ): Promise<string> {
    return signer.sendTransaction(await this.prepareUpdate(signer, receiverIdentity, nextRecord));
  }

  async prepareTransfer(
    signer: ccc.Signer,
    receiverIdentityValue: string,
    nextOwner: RegistryV2Owner,
    updatedAt?: bigint,
  ): Promise<ccc.Transaction> {
    await this.assertWritableDeployment();
    const current = await this.requireCurrentCell(receiverIdentityValue);
    const next = validateSuccessor(current.record, {
      ...current.record,
      sequence: current.record.sequence + 1n,
      updated_at: nextTimestamp(current.record, updatedAt),
    });
    let nextOwnerLock: ccc.Script;
    try {
      nextOwnerLock =
        typeof nextOwner === "string"
          ? (await ccc.Address.fromString(nextOwner, this.client)).script
          : ccc.Script.from(nextOwner);
    } catch (error) {
      const detail = error instanceof Error ? error.message : String(error);
      throw new Error(
        `Recipient must be a valid ${this.client.addressPrefix} address for this CKB network: ${detail}`,
      );
    }
    return this.prepareSuccessor(signer, current.cell, next, nextOwnerLock);
  }

  async transfer(
    signer: ccc.Signer,
    receiverIdentity: string,
    nextOwner: RegistryV2Owner,
    updatedAt?: bigint,
  ): Promise<string> {
    return signer.sendTransaction(
      await this.prepareTransfer(signer, receiverIdentity, nextOwner, updatedAt),
    );
  }

  async prepareRevoke(
    signer: ccc.Signer,
    receiverIdentityValue: string,
    updatedAt?: bigint,
  ): Promise<ccc.Transaction> {
    await this.assertWritableDeployment();
    const current = await this.requireCurrentCell(receiverIdentityValue);
    const next = validateSuccessor(current.record, {
      ...current.record,
      status: "revoked",
      sequence: current.record.sequence + 1n,
      updated_at: nextTimestamp(current.record, updatedAt),
      stream_endpoint: undefined,
      stream_protocol: undefined,
      stream_format: undefined,
    });
    return this.prepareSuccessor(signer, current.cell, next, current.cell.cellOutput.lock);
  }

  async revoke(
    signer: ccc.Signer,
    receiverIdentity: string,
    updatedAt?: bigint,
  ): Promise<string> {
    return signer.sendTransaction(await this.prepareRevoke(signer, receiverIdentity, updatedAt));
  }

  async waitForIndexedTransaction(
    receiverIdentityValue: string,
    transactionHashValue: string,
    options: WaitForIndexedTransactionOptions = {},
  ): Promise<DiscoveredReceiver> {
    const receiverIdentity = normalizeReceiverIdentity(receiverIdentityValue);
    const transactionHash = normalizeTransactionHash(transactionHashValue);
    const pollIntervalMs = Math.max(1, options.pollIntervalMs ?? 1_000);
    const indexerTimeoutMs = Math.max(1, options.indexerTimeoutMs ?? 60_000);
    const transactionTimeoutMs = Math.max(
      1,
      options.transactionTimeoutMs ?? 120_000,
    );
    const confirmed = await this.client
      .waitTransaction(
        transactionHash,
        Math.max(0, options.confirmations ?? 0),
        transactionTimeoutMs,
        pollIntervalMs,
      )
      .catch((error: unknown) => {
        const detail = error instanceof Error ? error.message : String(error);
        throw new Error(
          `Could not confirm Registry V2 transaction ${transactionHash}: ${detail}`,
        );
      });
    if (confirmed === undefined || confirmed.status !== "committed") {
      throw new Error(`Registry V2 transaction was not committed: ${transactionHash}`);
    }

    const deadline = Date.now() + indexerTimeoutMs;
    while (true) {
      const receiver = await this.discovery.findByIdentity(receiverIdentity, {
        includeInactive: true,
        includeRevoked: true,
      });
      if (receiver?.provenance.outPoint.txHash === transactionHash) {
        return receiver;
      }
      if (Date.now() >= deadline) {
        throw new Error(
          `Registry V2 transaction committed but was not indexed before timeout: ${transactionHash}`,
        );
      }
      await new Promise((resolve) => setTimeout(resolve, pollIntervalMs));
    }
  }

  async verifyWritableDeployment(): Promise<void> {
    this.assertWritableDeploymentConfiguration();
    const dependency = ccc.CellDep.from(this.deployment.contractCellDep);
    const contractCell = await this.client.getCellLive(dependency.outPoint, true);
    if (contractCell === undefined) {
      throw new Error(
        `Registry V2 contract dependency is not a live Pudge cell: ${dependency.outPoint.txHash}:${dependency.outPoint.index}`,
      );
    }
    const actualCodeHash = ccc.hashCkb(contractCell.outputData);
    if (actualCodeHash !== this.discovery.contractCodeHash) {
      throw new Error(
        `Registry V2 deployment code hash mismatch: configured ${this.discovery.contractCodeHash}, dependency contains ${actualCodeHash}`,
      );
    }
  }

  private async requireCurrentCell(receiverIdentityValue: string): Promise<{
    cell: ccc.Cell;
    record: RegistryV2Record;
  }> {
    const receiverIdentity = normalizeReceiverIdentity(receiverIdentityValue);
    let cursor: string | undefined;
    const cells: ccc.Cell[] = [];
    do {
      const page = await this.client.findCellsPaged(
        {
          script: {
            codeHash: this.discovery.contractCodeHash,
            hashType: this.deployment.scriptHashType,
            args: receiverIdentity,
          },
          scriptType: "type",
          scriptSearchMode: "exact",
          withData: true,
        },
        "asc",
        100,
        cursor,
      );
      cells.push(...page.cells);
      const next = page.lastCursor || undefined;
      if (page.cells.length === 0) break;
      if (next === undefined || next === cursor) {
        throw new Error(
          `Registry lookup for ${receiverIdentity} received an invalid pagination cursor`,
        );
      }
      cursor = next;
    } while (cells.length <= 2);

    if (cells.length !== 1) {
      throw new Error(
        cells.length === 0
          ? `No live Registry V2 cell found for ${receiverIdentity}`
          : `Duplicate live Registry V2 cells found for ${receiverIdentity}`,
      );
    }
    const cell = cells[0]!;
    const parsed = this.discovery.parseCell(cell);
    return { cell, record: parsed.record };
  }

  private async prepareSuccessor(
    signer: ccc.Signer,
    current: ccc.Cell,
    next: RegistryV2Record,
    nextOwnerLock: ccc.Script,
  ): Promise<ccc.Transaction> {
    this.assertSignerNetwork(signer);
    const signerLocks = (await signer.getAddressObjs()).map(({ script }) => script);
    if (!signerLocks.some((lock) => lock.eq(current.cellOutput.lock))) {
      throw new Error("Connected signer does not own the current Registry V2 cell");
    }
    const transaction = ccc.Transaction.default();
    transaction.addInput(current);
    transaction.addOutput(
      { lock: nextOwnerLock, type: current.cellOutput.type },
      encodeRegistryV2CellData(next),
    );
    transaction.addCellDeps(this.deployment.contractCellDep);
    await transaction.completeInputsByCapacity(signer);
    await transaction.completeFeeBy(signer);
    return transaction;
  }

  private async firstFundingCell(signer: ccc.Signer): Promise<ccc.Cell> {
    for await (const cell of signer.findCells(
      { scriptLenRange: [0, 1], outputDataLenRange: [0, 1] },
      true,
      "asc",
      20,
    )) {
      return cell;
    }
    throw new Error(
      "Connected signer has no plain CKB testnet capacity cell for Registry V2 creation; fund this public testnet address and wait for the funding transaction to be indexed",
    );
  }

  private assertSignerNetwork(signer: ccc.Signer): void {
    if (signer.client.addressPrefix !== this.client.addressPrefix) {
      throw new Error(
        `Connected signer uses ${signer.client.addressPrefix}, but the Registry client uses ${this.client.addressPrefix}`,
      );
    }
  }

  private assertWritableDeploymentConfiguration(): void {
    if (
      this.deployment.readOnly === true ||
      this.deployment.scriptHashType !== "data1"
    ) {
      throw new Error(
        "This Registry V2 deployment is historical and read-only; use a reviewed data1 deployment for lifecycle transactions",
      );
    }
  }

  private async assertWritableDeployment(): Promise<void> {
    this.assertWritableDeploymentConfiguration();
    if (this.deploymentVerification === undefined) {
      this.deploymentVerification = this.verifyWritableDeployment().catch((error: unknown) => {
        this.deploymentVerification = undefined;
        throw error;
      });
    }
    await this.deploymentVerification;
  }
}
