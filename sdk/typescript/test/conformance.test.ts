import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import test from "node:test";

import { ccc } from "@ckb-ccc/core";

import {
  RegistryV2Discovery,
  calculateTypeId,
  decodeRegistryV2Record,
  encodeRegistryV2Record,
  normalizeReceiverIdentity,
  validateCreation,
  validateSuccessor,
} from "../src/index.js";

interface RecordCase {
  name: string;
  payload: string;
  valid: boolean;
  creation_valid: boolean;
}

interface TransitionCase {
  name: string;
  previous: string;
  next: string;
  action?: "update" | "transfer" | "revoke";
  previous_identity?: string;
  next_identity?: string;
  previous_lock?: string;
  next_lock?: string;
  valid: boolean;
}

interface CreationCase {
  name: string;
  record_case: string;
  first_input_tx_hash: string;
  first_input_index: number;
  first_input_since: number;
  output_index: number;
  code_hash: string;
  hash_type: string;
  args: string;
  valid: boolean;
}

interface ScriptCase {
  name: string;
  code_hash: string;
  hash_type: ccc.HashType;
  args: string;
  valid: boolean;
}

interface DiscoveryCase {
  name: string;
  cells: Array<{ receiver_identity: string; record_case: string }>;
  expected_active_identities: string[];
  expected_including_revoked_identities: string[];
  quarantined_identities: string[];
}

interface Corpus {
  schema_version: number;
  registry_script: { code_hash: string; hash_type: string };
  record_cases: RecordCase[];
  identity_cases: Array<{ name: string; value: string; valid: boolean }>;
  type_id_vectors: Array<{
    name: string;
    first_input_tx_hash: string;
    first_input_index: number;
    first_input_since: number;
    output_index: number;
    expected: string;
  }>;
  creation_cases: CreationCase[];
  transition_cases: TransitionCase[];
  script_cases: ScriptCase[];
  discovery_cases: DiscoveryCase[];
}

const corpus = JSON.parse(
  readFileSync(
    resolve(process.cwd(), "../../tests/registry/fixtures/registry_v2_conformance.json"),
    "utf8",
  ),
) as Corpus;
const deployment = {
  contractCodeHash: "0x" + "44".repeat(32),
  scriptHashType: "type" as const,
  allowMutableCode: true,
  contractCellDep: {
    outPoint: { txHash: "0x" + "99".repeat(32), index: 0 },
    depType: "code" as const,
  },
};
const recordCases = new Map(corpus.record_cases.map((item) => [item.name, item]));

function registryCell(
  receiverIdentity: string,
  payload: string,
  script: Partial<{ codeHash: string; hashType: ccc.HashType }> = {},
  index = 0,
): ccc.Cell {
  return ccc.Cell.from({
    outPoint: { txHash: "0x" + (index + 1).toString(16).padStart(64, "0"), index },
    cellOutput: {
      lock: { codeHash: "0x" + "33".repeat(32), hashType: "type", args: "0x1234" },
      type: {
        codeHash: script.codeHash ?? deployment.contractCodeHash,
        hashType: script.hashType ?? "type",
        args: receiverIdentity,
      },
    },
    outputData: ccc.hexFrom(new TextEncoder().encode(payload)),
  });
}

function fakeClient(pages: ccc.Cell[][]): ccc.Client & { calls: number } {
  const client = {
    calls: 0,
    async findCellsPaged() {
      const cells = pages[this.calls] ?? [];
      this.calls += 1;
      return { cells, lastCursor: `0x${this.calls.toString(16)}` };
    },
  };
  return client as unknown as ccc.Client & { calls: number };
}

test("all languages consume conformance corpus version 2", () => {
  assert.equal(corpus.schema_version, 2);
});

for (const item of corpus.record_cases) {
  test(`record: ${item.name}`, () => {
    let record;
    try {
      record = decodeRegistryV2Record(item.payload);
    } catch {
      record = undefined;
    }
    assert.equal(record !== undefined, item.valid);
    if (record !== undefined) {
      assert.equal(Buffer.from(encodeRegistryV2Record(record)).length > 0, true);
      assert.equal(
        (() => {
          try {
            validateCreation(record);
            return true;
          } catch {
            return false;
          }
        })(),
        item.creation_valid,
      );
    }
  });
}

for (const item of corpus.identity_cases) {
  test(`identity: ${item.name}`, () => {
    let valid = true;
    try {
      normalizeReceiverIdentity(item.value);
    } catch {
      valid = false;
    }
    assert.equal(valid, item.valid);
  });
}

for (const item of corpus.type_id_vectors) {
  test(`type id: ${item.name}`, () => {
    assert.equal(
      calculateTypeId({
        firstInputTxHash: item.first_input_tx_hash,
        firstInputIndex: item.first_input_index,
        firstInputSince: item.first_input_since,
        outputIndex: item.output_index,
      }),
      item.expected,
    );
  });
}

for (const item of corpus.creation_cases) {
  test(`creation: ${item.name}`, () => {
    let accepted = true;
    try {
      const record = recordCases.get(item.record_case);
      assert.ok(record, `missing record case ${item.record_case}`);
      validateCreation(decodeRegistryV2Record(record.payload));
      assert.equal(normalizeReceiverIdentity(item.code_hash), corpus.registry_script.code_hash);
      assert.equal(item.hash_type, corpus.registry_script.hash_type);
      assert.equal(
        normalizeReceiverIdentity(item.args),
        calculateTypeId({
          firstInputTxHash: item.first_input_tx_hash,
          firstInputIndex: item.first_input_index,
          firstInputSince: item.first_input_since,
          outputIndex: item.output_index,
        }),
      );
    } catch {
      accepted = false;
    }
    assert.equal(accepted, item.valid);
  });
}

for (const item of corpus.transition_cases) {
  test(`transition: ${item.name}`, () => {
    const previous = decodeRegistryV2Record(item.previous);
    const next = decodeRegistryV2Record(item.next);
    let valid = true;
    try {
      const previousIdentity = normalizeReceiverIdentity(
        item.previous_identity ?? "0x" + "11".repeat(32),
      );
      const nextIdentity = normalizeReceiverIdentity(
        item.next_identity ?? "0x" + "11".repeat(32),
      );
      if (previousIdentity !== nextIdentity) throw new Error("receiver_identity is immutable");
      validateSuccessor(previous, next);
    } catch {
      valid = false;
    }
    assert.equal(valid, item.valid);
    if (valid && item.action !== undefined) {
      const action =
        next.status === "revoked"
          ? "revoke"
          : item.previous_lock !== item.next_lock
            ? "transfer"
            : "update";
      assert.equal(action, item.action);
    }
  });
}

for (const item of corpus.script_cases) {
  test(`script: ${item.name}`, () => {
    const record = recordCases.get("valid_creation_with_stream")!;
    const cell = registryCell(item.args, record.payload, {
      codeHash: item.code_hash,
      hashType: item.hash_type,
    });
    const discovery = new RegistryV2Discovery(fakeClient([]), deployment);
    let valid = true;
    try {
      discovery.parseCell(cell);
    } catch {
      valid = false;
    }
    assert.equal(valid, item.valid);
  });
}

for (const item of corpus.discovery_cases) {
  test(`discovery: ${item.name}`, async () => {
    const cells = item.cells.map((definition, index) => {
      const record = recordCases.get(definition.record_case);
      assert.ok(record, `missing record case ${definition.record_case}`);
      return registryCell(definition.receiver_identity, record.payload, {}, index);
    });

    const active = await new RegistryV2Discovery(fakeClient([cells, []]), deployment).discover();
    const historical = await new RegistryV2Discovery(fakeClient([cells, []]), deployment).discover({
      includeInactive: true,
      includeRevoked: true,
    });

    assert.deepEqual(
      active.receivers.map((receiver) => receiver.receiver_identity),
      item.expected_active_identities,
    );
    assert.deepEqual(
      historical.receivers.map((receiver) => receiver.receiver_identity),
      item.expected_including_revoked_identities,
    );
    assert.deepEqual(active.quarantinedIdentities, item.quarantined_identities);
  });
}

test("discovery follows a changing cursor after short pages", async () => {
  const record = recordCases.get("valid_creation_with_stream")!;
  const first = registryCell("0x" + "11".repeat(32), record.payload, {}, 0);
  const second = registryCell("0x" + "22".repeat(32), record.payload, {}, 1);
  const client = fakeClient([[first], [second], []]);

  const result = await new RegistryV2Discovery(client, deployment).discover({ pageSize: 10 });

  assert.equal(client.calls, 3);
  assert.equal(result.receivers.length, 2);
});

test("discovery fails closed when pagination does not finish", async () => {
  const record = recordCases.get("valid_creation_with_stream")!;
  const first = registryCell("0x" + "11".repeat(32), record.payload, {}, 0);
  const client = fakeClient([[first]]);

  const result = await new RegistryV2Discovery(client, deployment).discover({ maxPages: 1 });

  assert.deepEqual(result.receivers, []);
  assert.equal(result.failures.some((failure) => failure.code === "pagination_limit"), true);
});
