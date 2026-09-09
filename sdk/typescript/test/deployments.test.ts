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
  assert.throws(
    () => RegistryV2Sdk.testnet({ addressPrefix: "ckb" } as ccc.Client),
    /requires a CKB testnet client/,
  );
});
