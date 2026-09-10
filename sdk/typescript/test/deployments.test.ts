import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import { ccc } from "@ckb-ccc/core";

import { REGISTRY_V2_PUDGE_2026_07_30, RegistryV2Sdk } from "../src/index.js";

test("historical Pudge deployment matches the signed evidence manifest", () => {
  const manifest = JSON.parse(
    readFileSync(
      "../../evidence/registry-v2-testnet-2026-07-30-final/manifest.json",
      "utf8",
    ),
  ) as {
    contract: {
      out_point: { tx_hash: string; index: string };
      type_script_hash_for_registry_code_hash: string;
    };
  };

  assert.equal(
    REGISTRY_V2_PUDGE_2026_07_30.contractCodeHash,
    manifest.contract.type_script_hash_for_registry_code_hash,
  );
  assert.equal(
    REGISTRY_V2_PUDGE_2026_07_30.contractCellDep.outPoint.txHash,
    manifest.contract.out_point.tx_hash,
  );
  assert.equal(
    REGISTRY_V2_PUDGE_2026_07_30.contractCellDep.outPoint.index,
    Number.parseInt(manifest.contract.out_point.index, 16),
  );
});

test("testnet factory rejects a mainnet client and uses the documented Pudge deployment", () => {
  const testnetClient = { addressPrefix: "ckt" } as ccc.Client;
  const registry = RegistryV2Sdk.testnet(testnetClient);

  assert.equal(registry.deployment, REGISTRY_V2_PUDGE_2026_07_30);
  assert.equal(registry.deployment.readOnly, true);
  assert.throws(
    () => RegistryV2Sdk.testnet({ addressPrefix: "ckb" } as ccc.Client),
    /requires a CKB testnet client/,
  );
});

test("writable testnet factory derives an immutable data1 deployment", () => {
  const testnetClient = { addressPrefix: "ckt" } as ccc.Client;
  const registry = RegistryV2Sdk.writableTestnet(testnetClient, {
    contractCodeHash: "0x" + "AA".repeat(32),
    contractTransactionHash: "0x" + "BB".repeat(32),
    contractIndex: 2,
  });

  assert.deepEqual(registry.deployment, {
    contractCodeHash: "0x" + "aa".repeat(32),
    scriptHashType: "data1",
    contractCellDep: {
      outPoint: {
        txHash: "0x" + "bb".repeat(32),
        index: 2,
      },
      depType: "code",
    },
  });
  assert.throws(
    () => RegistryV2Sdk.writableTestnet(testnetClient, {
      contractCodeHash: "0x1234",
      contractTransactionHash: "0x" + "bb".repeat(32),
      contractIndex: 0,
    }),
    /contractCodeHash must be 0x-prefixed 32-byte hex/,
  );
  assert.throws(
    () => RegistryV2Sdk.writableTestnet(testnetClient, {
      contractCodeHash: "0x" + "aa".repeat(32),
      contractTransactionHash: "0x" + "bb".repeat(32),
      contractIndex: -1,
    }),
    /contractIndex must be a safe non-negative integer/,
  );
});

test("lifecycle writes reject every mutable type-hash deployment", async () => {
  const testnetClient = { addressPrefix: "ckt" } as ccc.Client;
  const mutable = new RegistryV2Sdk(testnetClient, {
    contractCodeHash: "0x" + "aa".repeat(32),
    scriptHashType: "type",
    allowMutableCode: true,
    contractCellDep: {
      outPoint: { txHash: "0x" + "bb".repeat(32), index: 0 },
      depType: "code",
    },
  });

  await assert.rejects(
    mutable.prepareCreate({} as ccc.Signer, {
      receiver_id: "RECV_MUTABLE",
      latitude: 0,
      longitude: 0,
      altitude: 0,
      status: "online",
      capabilities: ["mode-s"],
    }),
    /historical and read-only; use a reviewed data1 deployment/,
  );
});

test("deployment verification detects a mismatched contract binary", async () => {
  const contractData = "0x01020304";
  const actualCodeHash = ccc.hashCkb(contractData);
  const contractTransactionHash = "0x" + "bb".repeat(32);
  const client = {
    addressPrefix: "ckt",
    async getCellLive() {
      return ccc.Cell.from({
        outPoint: { txHash: contractTransactionHash, index: 0 },
        cellOutput: {
          capacity: 10_000_000_000n,
          lock: {
            codeHash: "0x" + "00".repeat(32),
            hashType: "data1",
            args: "0x",
          },
        },
        outputData: contractData,
      });
    },
  } as unknown as ccc.Client;

  await RegistryV2Sdk.writableTestnet(client, {
    contractCodeHash: actualCodeHash,
    contractTransactionHash,
    contractIndex: 0,
  }).verifyWritableDeployment();

  await assert.rejects(
    RegistryV2Sdk.writableTestnet(client, {
      contractCodeHash: "0x" + "aa".repeat(32),
      contractTransactionHash,
      contractIndex: 0,
    }).verifyWritableDeployment(),
    /deployment code hash mismatch/,
  );
});
