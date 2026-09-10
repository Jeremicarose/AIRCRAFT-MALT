import assert from "node:assert/strict";
import test from "node:test";

import { ccc } from "@ckb-ccc/core";

import {
  RegistryV2Sdk,
  decodeRegistryV2Record,
  encodeRegistryV2CellData,
  type RegistryV2Record,
} from "../src/index.js";

const ownerLock = ccc.Script.from({
  codeHash: "0x" + "33".repeat(32),
  hashType: "type",
  args: "0x1234",
});
const nextOwnerLock = ccc.Script.from({
  codeHash: "0x" + "33".repeat(32),
  hashType: "type",
  args: "0x5678",
});
const contractData = "0x01020304";
const contractCodeHash = ccc.hashCkb(contractData);
const contractCellDep = {
  outPoint: { txHash: "0x" + "99".repeat(32), index: 0 },
  depType: "code" as const,
};
const receiverIdentity = "0x" + "11".repeat(32);
const initialRecord: RegistryV2Record = {
  schema_version: 2,
  receiver_id: "RECV_TEST",
  latitude: -1.286389,
  longitude: 36.817223,
  altitude: 1795,
  status: "online",
  capabilities: ["mode-s", "mlat"],
  sequence: 0n,
  updated_at: 1_700_000_000n,
};

function cell(
  outPoint: { txHash: string; index: number },
  lock: ccc.Script,
  type: ccc.Script | undefined,
  data: string,
): ccc.Cell {
  return ccc.Cell.from({
    outPoint,
    cellOutput: { capacity: 20_000_000_000n, lock, type },
    outputData: data,
  });
}

test("CCC signer lifecycle prepares create, update, transfer, and revoke transactions", async () => {
  const funding = cell(
    { txHash: "0x" + "aa".repeat(32), index: 1 },
    ownerLock,
    undefined,
    "0x",
  );
  const current = cell(
    { txHash: "0x" + "bb".repeat(32), index: 0 },
    ownerLock,
    ccc.Script.from({ codeHash: contractCodeHash, hashType: "data1", args: receiverIdentity }),
    ccc.hexFrom(new TextEncoder().encode(JSON.stringify({
      ...initialRecord,
      sequence: Number(initialRecord.sequence),
      updated_at: Number(initialRecord.updated_at),
    }))),
  );
  const client = {
    addressPrefix: "ckt",
    async getCellLive() {
      return cell(contractCellDep.outPoint, ownerLock, undefined, contractData);
    },
    async findCellsPaged(_key: unknown, _order: unknown, _limit: unknown, cursor?: string) {
      return cursor === undefined
        ? { cells: [current], lastCursor: "0x1" }
        : { cells: [], lastCursor: "0x1" };
    },
  } as unknown as ccc.Client;
  const submitted: ccc.Transaction[] = [];
  const signer = {
    client,
    async *findCells() {
      yield funding;
    },
    async getRecommendedAddressObj() {
      return { script: ownerLock };
    },
    async getAddressObjs() {
      return [{ script: ownerLock }];
    },
    async sendTransaction(transaction: ccc.Transaction) {
      submitted.push(transaction);
      return "0x" + "cc".repeat(32);
    },
  } as unknown as ccc.Signer;
  const completeInputs = ccc.Transaction.prototype.completeInputsByCapacity;
  const completeFee = ccc.Transaction.prototype.completeFeeBy;
  ccc.Transaction.prototype.completeInputsByCapacity = async () => 0;
  ccc.Transaction.prototype.completeFeeBy = async () => [0, false];

  try {
    const sdk = new RegistryV2Sdk(client, {
      contractCodeHash,
      scriptHashType: "data1",
      contractCellDep,
    });
    const created = await sdk.prepareCreate(signer, {
      receiver_id: initialRecord.receiver_id,
      latitude: initialRecord.latitude,
      longitude: initialRecord.longitude,
      altitude: initialRecord.altitude,
      status: initialRecord.status,
      capabilities: initialRecord.capabilities,
    });
    assert.equal(created.transaction.inputs[0]?.previousOutput.txHash, funding.outPoint.txHash);
    assert.equal(created.transaction.outputs[0]?.type?.args, created.receiver_identity);
    assert.equal(created.transaction.outputs[0]?.type?.codeHash, contractCodeHash);
    assert.equal(created.transaction.cellDeps.length, 1);
    const createdRecord = decodeRegistryV2Record(ccc.bytesFrom(created.transaction.outputsData[0]!));
    assert.equal(createdRecord.schema_version, 2);
    assert.equal(createdRecord.sequence, 0n);
    assert.equal(createdRecord.updated_at > 0n, true);

    const update = await sdk.prepareUpdate(signer, receiverIdentity, {
      latitude: -1.3,
      status: "degraded",
    });
    assert.equal(update.outputs[0]?.lock.eq(ownerLock), true);
    const updatedRecord = decodeRegistryV2Record(ccc.bytesFrom(update.outputsData[0]!));
    assert.equal(updatedRecord.receiver_id, initialRecord.receiver_id);
    assert.equal(updatedRecord.sequence, 1n);
    assert.equal(updatedRecord.updated_at >= initialRecord.updated_at, true);

    const recipientAddress = ccc.Address.from({ prefix: "ckt", script: nextOwnerLock }).toString();
    const transfer = await sdk.prepareTransfer(
      signer,
      receiverIdentity,
      recipientAddress,
    );
    assert.equal(transfer.outputs[0]?.lock.eq(nextOwnerLock), true);
    assert.equal(transfer.outputs[0]?.type?.args, receiverIdentity);
    await assert.rejects(
      sdk.prepareTransfer(
        signer,
        receiverIdentity,
        recipientAddress.replace(/^ckt/, "ckb"),
      ),
      /Recipient must be a valid ckt address/,
    );

    const revoke = await sdk.prepareRevoke(signer, receiverIdentity);
    const tombstone = decodeRegistryV2Record(ccc.bytesFrom(revoke.outputsData[0]!));
    assert.equal(tombstone.status, "revoked");
    assert.equal(tombstone.sequence, 1n);
    assert.equal(tombstone.stream_endpoint, undefined);

    const sent = await sdk.create(signer, initialRecord);
    assert.equal(sent.transactionHash, "0x" + "cc".repeat(32));
    assert.equal(submitted.length, 1);
    const wrongNetworkSigner = {
      ...signer,
      client: { addressPrefix: "ckb" },
    } as unknown as ccc.Signer;
    await assert.rejects(
      sdk.prepareCreate(wrongNetworkSigner, initialRecord),
      /Connected signer uses ckb, but the Registry client uses ckt/,
    );
  } finally {
    ccc.Transaction.prototype.completeInputsByCapacity = completeInputs;
    ccc.Transaction.prototype.completeFeeBy = completeFee;
  }
});

test("documented journey creates, discovers, updates, transfers, revokes, and verifies", async () => {
  const funding = cell(
    { txHash: "0x" + "aa".repeat(32), index: 1 },
    ownerLock,
    undefined,
    "0x",
  );
  let current: ccc.Cell | undefined;
  let submittedCount = 0;
  const client = {
    addressPrefix: "ckt",
    async getCellLive() {
      return cell(contractCellDep.outPoint, ownerLock, undefined, contractData);
    },
    async findCellsPaged(
      search: {
        script: { codeHash: string; args: string };
        scriptSearchMode: "exact" | "prefix";
      },
      _order: unknown,
      _limit: unknown,
      cursor?: string,
    ) {
      if (cursor !== undefined || current === undefined) {
        return { cells: [], lastCursor: cursor };
      }
      const type = current.cellOutput.type;
      const matches =
        type?.codeHash === search.script.codeHash &&
        (search.scriptSearchMode === "prefix" || type.args === search.script.args);
      return { cells: matches ? [current] : [], lastCursor: "0x1" };
    },
    async waitTransaction() {
      return { status: "committed", blockNumber: 1n };
    },
  } as unknown as ccc.Client;
  const signerFor = (lock: ccc.Script) => ({
    client,
    async *findCells() {
      yield funding;
    },
    async getRecommendedAddressObj() {
      return { script: lock };
    },
    async getAddressObjs() {
      return [{ script: lock }];
    },
    async sendTransaction(transactionValue: ccc.Transaction) {
      const transaction = ccc.Transaction.from(transactionValue);
      const output = transaction.outputs[0]!;
      const outputData = transaction.outputsData[0]!;
      submittedCount += 1;
      const transactionHash =
        "0x" + submittedCount.toString(16).padStart(64, "0");
      current = cell(
        { txHash: transactionHash, index: 0 },
        output.lock,
        output.type,
        outputData,
      );
      return transactionHash;
    },
  }) as unknown as ccc.Signer;
  const ownerSigner = signerFor(ownerLock);
  const recipientSigner = signerFor(nextOwnerLock);
  const recipientAddress = ccc.Address.from({ prefix: "ckt", script: nextOwnerLock }).toString();
  const completeInputs = ccc.Transaction.prototype.completeInputsByCapacity;
  const completeFee = ccc.Transaction.prototype.completeFeeBy;
  ccc.Transaction.prototype.completeInputsByCapacity = async () => 0;
  ccc.Transaction.prototype.completeFeeBy = async () => [0, false];

  try {
    const sdk = new RegistryV2Sdk(client, {
      contractCodeHash,
      scriptHashType: "data1",
      contractCellDep,
    });
    const created = await sdk.create(ownerSigner, {
      receiver_id: "RECV_JOURNEY",
      latitude: -1.286389,
      longitude: 36.817223,
      altitude: 1795,
      status: "online",
      capabilities: ["mode-s", "mlat"],
    });
    let observed = await sdk.waitForIndexedTransaction(
      created.receiver_identity,
      created.transactionHash,
      { pollIntervalMs: 1, indexerTimeoutMs: 100 },
    );
    assert.equal(observed.record.sequence, 0n);
    assert.equal(observed.record.status, "online");
    assert.equal(
      (await sdk.discovery.findByIdentity(created.receiver_identity))?.receiver_identity,
      created.receiver_identity,
    );

    const updateHash = await sdk.update(ownerSigner, created.receiver_identity, {
      status: "degraded",
      metadata_hash: "0x" + "ab".repeat(32),
    });
    observed = await sdk.waitForIndexedTransaction(created.receiver_identity, updateHash, {
      pollIntervalMs: 1,
      indexerTimeoutMs: 100,
    });
    assert.equal(observed.record.sequence, 1n);
    assert.equal(observed.record.status, "degraded");

    const transferHash = await sdk.transfer(
      ownerSigner,
      created.receiver_identity,
      recipientAddress,
    );
    observed = await sdk.waitForIndexedTransaction(created.receiver_identity, transferHash, {
      pollIntervalMs: 1,
      indexerTimeoutMs: 100,
    });
    assert.equal(observed.record.sequence, 2n);
    assert.equal(observed.provenance.ownerLock.args, nextOwnerLock.args);

    const revokeHash = await sdk.revoke(recipientSigner, created.receiver_identity);
    observed = await sdk.waitForIndexedTransaction(created.receiver_identity, revokeHash, {
      pollIntervalMs: 1,
      indexerTimeoutMs: 100,
    });
    assert.equal(observed.record.sequence, 3n);
    assert.equal(observed.record.status, "revoked");
    assert.equal(await sdk.discovery.findByIdentity(created.receiver_identity), undefined);
    assert.equal(
      (
        await sdk.discovery.findByIdentity(created.receiver_identity, {
          includeRevoked: true,
        })
      )?.record.status,
      "revoked",
    );
  } finally {
    ccc.Transaction.prototype.completeInputsByCapacity = completeInputs;
    ccc.Transaction.prototype.completeFeeBy = completeFee;
  }
});

test("history reads and validates the real create, update, transfer, and revoke chain", async () => {
  const type = ccc.Script.from({ codeHash: contractCodeHash, hashType: "data1", args: receiverIdentity });
  const records: RegistryV2Record[] = [
    initialRecord,
    { ...initialRecord, sequence: 1n, updated_at: 1_700_000_001n, status: "degraded" },
    { ...initialRecord, sequence: 2n, updated_at: 1_700_000_002n, status: "online" },
    { ...initialRecord, sequence: 3n, updated_at: 1_700_000_003n, status: "revoked" },
  ];
  const hashes = records.map((_, index) => "0x" + (index + 1).toString(16).padStart(64, "0"));
  const responses = new Map(hashes.map((hash, index) => {
    const lock = index < 2 ? ownerLock : nextOwnerLock;
    const transaction = ccc.Transaction.from({
      outputs: [{ capacity: 20_000_000_000n, lock, type }],
      outputsData: [encodeRegistryV2CellData(records[index]!)],
    });
    return [hash, ccc.ClientTransactionResponse.from({
      transaction,
      status: "committed",
      blockNumber: BigInt(100 + index),
    })] as const;
  }));
  let page = 0;
  const client = {
    addressPrefix: "ckt",
    async findTransactionsPaged() {
      page += 1;
      return page === 1
        ? {
            transactions: hashes.map((txHash, index) => ({
              txHash,
              blockNumber: BigInt(100 + index),
              txIndex: 0n,
              cells: [{ isInput: false, cellIndex: 0n }],
            })),
            lastCursor: "0x1",
          }
        : { transactions: [], lastCursor: "0x1" };
    },
    async getTransaction(txHash: string) {
      return responses.get(txHash);
    },
  } as unknown as ccc.Client;

  const events = await new RegistryV2Sdk(client, {
    contractCodeHash,
    scriptHashType: "data1",
    contractCellDep,
  })
    .history.discover(receiverIdentity);

  assert.deepEqual(events.map((event) => event.action), ["create", "update", "transfer", "revoke"]);
  assert.deepEqual(events.map((event) => event.record.sequence), [0n, 1n, 2n, 3n]);
  assert.equal(events.every((event) => event.receiver_identity === receiverIdentity), true);
});
