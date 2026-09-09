import { ccc } from "@ckb-ccc/core";

import {
  DEFAULT_MAX_RECORD_BYTES,
  decodeRegistryV2Record,
  normalizeReceiverIdentity,
  type RegistryV2Record,
} from "./record.js";

export interface RegistryDeployment {
  contractCodeHash: string;
  contractCellDep: ccc.CellDepLike;
  scriptHashType: "data1" | "type";
  allowMutableCode?: boolean;
  readOnly?: boolean;
}

export interface DiscoveryOptions {
  includeInactive?: boolean;
  includeRevoked?: boolean;
  maxCells?: number;
  maxPages?: number;
  maxRecordBytes?: number;
  pageSize?: number;
  nowSeconds?: bigint;
  maxFutureRecordSkewSeconds?: bigint;
}

export interface RegistryProvenance {
  outPoint: { txHash: string; index: bigint };
  ownerLock: { codeHash: string; hashType: ccc.HashType; args: string };
  typeScript: { codeHash: string; hashType: ccc.HashType; args: string };
}

export interface DiscoveredReceiver {
  receiver_identity: string;
  record: RegistryV2Record;
  provenance: RegistryProvenance;
}

export interface DiscoveryFailure {
  code: "duplicate_identity" | "invalid_cell" | "pagination_limit";
  message: string;
  outPoint?: { txHash: string; index: bigint };
  receiver_identity?: string;
}

export interface DiscoveryResult {
  receivers: DiscoveredReceiver[];
  quarantinedIdentities: string[];
  failures: DiscoveryFailure[];
  pagesScanned: number;
  cellsScanned: number;
}

function outPointOf(cell: ccc.Cell): { txHash: string; index: bigint } {
  return { txHash: cell.outPoint.txHash, index: cell.outPoint.index };
}

export class RegistryV2Discovery {
  readonly contractCodeHash: string;

  constructor(
    readonly client: ccc.Client,
    readonly deployment: RegistryDeployment,
  ) {
    if (deployment.scriptHashType === "type" && deployment.allowMutableCode !== true) {
      throw new Error(
        "Registry deployments using hashType=type have mutable code; set allowMutableCode only for explicit historical compatibility",
      );
    }
    this.contractCodeHash = normalizeReceiverIdentity(deployment.contractCodeHash);
  }

  async discover(options: DiscoveryOptions = {}): Promise<DiscoveryResult> {
    const pageSize = Math.max(1, Math.min(options.pageSize ?? 100, 1_000));
    const maxPages = Math.max(1, options.maxPages ?? 1_000);
    const maxCells = Math.max(1, options.maxCells ?? 10_000);
    const maxRecordBytes = Math.max(1, options.maxRecordBytes ?? DEFAULT_MAX_RECORD_BYTES);
    const nowSeconds = options.nowSeconds ?? BigInt(Math.floor(Date.now() / 1_000));
    const maxFutureRecordSkewSeconds = options.maxFutureRecordSkewSeconds ?? 300n;
    if (nowSeconds < 0n || maxFutureRecordSkewSeconds < 0n) {
      throw new Error("Registry discovery time values must be non-negative");
    }
    const failures: DiscoveryFailure[] = [];
    const byIdentity = new Map<string, DiscoveredReceiver>();
    const seenIdentities = new Set<string>();
    const duplicates = new Set<string>();
    let cursor: string | undefined;
    let exhausted = false;
    let pagesScanned = 0;
    let cellsScanned = 0;

    for (; pagesScanned < maxPages; pagesScanned += 1) {
      const page = await this.client.findCellsPaged(
        {
          script: {
            codeHash: this.contractCodeHash,
            hashType: this.deployment.scriptHashType,
            args: "0x",
          },
          scriptType: "type",
          scriptSearchMode: "prefix",
          withData: true,
        },
        "asc",
        pageSize,
        cursor,
      );
      cellsScanned += page.cells.length;
      if (cellsScanned > maxCells) {
        failures.push({ code: "pagination_limit", message: "Registry discovery exceeded maxCells" });
        byIdentity.clear();
        break;
      }

      for (const cell of page.cells) {
        let receiverIdentity: string | undefined;
        try {
          receiverIdentity = this.receiverIdentityOf(cell);
          if (duplicates.has(receiverIdentity)) continue;
          if (seenIdentities.has(receiverIdentity)) {
            duplicates.add(receiverIdentity);
            byIdentity.delete(receiverIdentity);
            failures.push({
              code: "duplicate_identity",
              message: `Duplicate live Registry cells for ${receiverIdentity}`,
              receiver_identity: receiverIdentity,
              outPoint: outPointOf(cell),
            });
            continue;
          }
          seenIdentities.add(receiverIdentity);

          const receiver = this.parseCell(cell, maxRecordBytes);
          byIdentity.set(receiver.receiver_identity, receiver);
        } catch (error) {
          failures.push({
            code: "invalid_cell",
            message: error instanceof Error ? error.message : String(error),
            outPoint: outPointOf(cell),
            receiver_identity: receiverIdentity,
          });
        }
      }

      const nextCursor = page.lastCursor || undefined;
      if (page.cells.length === 0) {
        exhausted = true;
        pagesScanned += 1;
        break;
      }
      if (nextCursor === undefined || nextCursor === cursor) {
        failures.push({
          code: "pagination_limit",
          message: "Registry indexer returned an invalid cursor after a non-empty page",
        });
        byIdentity.clear();
        exhausted = true;
        pagesScanned += 1;
        break;
      }
      cursor = nextCursor;
    }

    if (!exhausted && pagesScanned >= maxPages) {
      failures.push({ code: "pagination_limit", message: "Registry discovery exceeded maxPages" });
      byIdentity.clear();
    }

    const receivers = [...byIdentity.values()]
      .filter(({ record }) => {
        if (record.updated_at > nowSeconds + maxFutureRecordSkewSeconds) return false;
        if (record.status === "revoked") return options.includeRevoked === true;
        if (record.status !== "online") return options.includeInactive === true;
        return true;
      })
      .sort((left, right) => left.receiver_identity.localeCompare(right.receiver_identity));
    return {
      receivers,
      quarantinedIdentities: [...duplicates].sort(),
      failures,
      pagesScanned,
      cellsScanned,
    };
  }

  async findByIdentity(
    receiverIdentityValue: string,
    options: DiscoveryOptions = {},
  ): Promise<DiscoveredReceiver | undefined> {
    const receiverIdentity = normalizeReceiverIdentity(receiverIdentityValue);
    const pageSize = Math.max(1, Math.min(options.pageSize ?? 100, 1_000));
    const maxPages = Math.max(1, options.maxPages ?? 100);
    const maxCells = Math.max(1, options.maxCells ?? 10);
    const cells: ccc.Cell[] = [];
    let cursor: string | undefined;
    let exhausted = false;

    for (let pageIndex = 0; pageIndex < maxPages; pageIndex += 1) {
      const page = await this.client.findCellsPaged(
        {
          script: {
            codeHash: this.contractCodeHash,
            hashType: this.deployment.scriptHashType,
            args: receiverIdentity,
          },
          scriptType: "type",
          scriptSearchMode: "exact",
          withData: true,
        },
        "asc",
        pageSize,
        cursor,
      );
      cells.push(...page.cells);
      if (cells.length > maxCells) {
        throw new Error(`Registry lookup for ${receiverIdentity} exceeded maxCells`);
      }
      const nextCursor = page.lastCursor || undefined;
      if (page.cells.length === 0) {
        exhausted = true;
        break;
      }
      if (nextCursor === undefined || nextCursor === cursor) {
        throw new Error(
          `Registry lookup for ${receiverIdentity} received an invalid pagination cursor`,
        );
      }
      cursor = nextCursor;
    }

    if (!exhausted) {
      throw new Error(`Registry lookup for ${receiverIdentity} exceeded maxPages`);
    }
    if (cells.length === 0) return undefined;
    if (cells.length > 1) {
      throw new Error(`Duplicate live Registry V2 cells found for ${receiverIdentity}`);
    }

    let receiver: DiscoveredReceiver;
    try {
      receiver = this.parseCell(cells[0]!, options.maxRecordBytes);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      throw new Error(`Invalid live Registry V2 cell for ${receiverIdentity}: ${message}`);
    }
    if (receiver.record.status === "revoked") {
      return options.includeRevoked === true ? receiver : undefined;
    }
    if (receiver.record.status !== "online" && options.includeInactive !== true) {
      return undefined;
    }
    return receiver;
  }

  parseCell(cell: ccc.Cell, maxRecordBytes = DEFAULT_MAX_RECORD_BYTES): DiscoveredReceiver {
    const receiverIdentity = this.receiverIdentityOf(cell);
    const type = cell.cellOutput.type!;
    const data = ccc.bytesFrom(cell.outputData);
    const record = decodeRegistryV2Record(data, maxRecordBytes);
    return {
      receiver_identity: receiverIdentity,
      record,
      provenance: {
        outPoint: outPointOf(cell),
        ownerLock: {
          codeHash: cell.cellOutput.lock.codeHash,
          hashType: cell.cellOutput.lock.hashType,
          args: cell.cellOutput.lock.args,
        },
        typeScript: { codeHash: type.codeHash, hashType: type.hashType, args: type.args },
      },
    };
  }

  private receiverIdentityOf(cell: ccc.Cell): string {
    const type = cell.cellOutput.type;
    if (type === undefined) throw new Error("Registry cell has no type script");
    if (type.hashType !== this.deployment.scriptHashType) {
      throw new Error("Registry type script hashType does not match the configured deployment");
    }
    if (type.codeHash !== this.contractCodeHash) {
      throw new Error("Registry cell code hash does not match the configured V2 contract");
    }
    return normalizeReceiverIdentity(type.args);
  }
}
