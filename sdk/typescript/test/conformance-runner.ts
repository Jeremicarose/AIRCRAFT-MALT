import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { ccc } from "@ckb-ccc/core";

import {
  RegistryV2Discovery,
  calculateTypeId,
  decodeRegistryV2Record,
  normalizeReceiverIdentity,
  validateCreation,
  validateSuccessor,
  type RegistryV2Record,
} from "../src/index.js";

interface NamedCase {
  name: string;
}

interface RecordCase extends NamedCase {
  payload: string;
}

interface Corpus {
  schema_version: number;
  registry_script: { code_hash: string; hash_type: string };
  discovery_policy: { observed_at: number; max_future_skew_seconds: number };
  record_cases: Array<RecordCase & { valid: boolean; creation_valid: boolean }>;
  identity_cases: Array<NamedCase & { value: string; valid: boolean }>;
  type_id_vectors: Array<
    NamedCase & {
      first_input_tx_hash: string;
      first_input_index: number;
      first_input_since: number;
      output_index: number;
      expected: string;
    }
  >;
  creation_cases: Array<
    NamedCase & {
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
  >;
  transition_cases: Array<
    NamedCase & {
      previous: string;
      next: string;
      previous_identity?: string;
      next_identity?: string;
      previous_lock?: string;
      next_lock?: string;
      action?: "update" | "transfer" | "revoke";
      valid: boolean;
    }
  >;
  script_cases: Array<
    NamedCase & {
      code_hash: string;
      hash_type: ccc.HashType;
      args: string;
      valid: boolean;
    }
  >;
  discovery_cases: Array<
    NamedCase & {
      cells: Array<{ receiver_identity: string; record_case: string }>;
      expected_active_identities: string[];
      expected_including_revoked_identities: string[];
      quarantined_identities: string[];
    }
  >;
}

interface CaseResult {
  id: string;
  outcome: Record<string, unknown>;
}

const DEFAULT_IDENTITY = "0x" + "11".repeat(32);

function f64Bits(value: number): string {
  const buffer = new ArrayBuffer(8);
  new DataView(buffer).setFloat64(0, value, false);
  return `0x${new DataView(buffer).getBigUint64(0, false).toString(16).padStart(16, "0")}`;
}

function canonicalRecord(record: RegistryV2Record): Record<string, unknown> {
  return {
    schema_version: record.schema_version,
    receiver_id: record.receiver_id,
    latitude_f64_bits: f64Bits(record.latitude),
    longitude_f64_bits: f64Bits(record.longitude),
    altitude_f64_bits: f64Bits(record.altitude),
    status: record.status,
    capabilities: record.capabilities,
    sequence: record.sequence.toString(),
    updated_at: record.updated_at.toString(),
    stream_endpoint: record.stream_endpoint ?? null,
    stream_protocol: record.stream_protocol ?? null,
    stream_format: record.stream_format ?? null,
    metadata_hash: record.metadata_hash ?? null,
  };
}

function registryCell(
  receiverIdentity: string,
  payload: string,
  codeHash: string,
  hashType: ccc.HashType = "type",
  index = 0,
): ccc.Cell {
  return ccc.Cell.from({
    outPoint: { txHash: "0x" + (index + 1).toString(16).padStart(64, "0"), index },
    cellOutput: {
      lock: { codeHash: "0x" + "33".repeat(32), hashType: "type", args: "0x1234" },
      type: { codeHash, hashType, args: receiverIdentity },
    },
    outputData: ccc.hexFrom(new TextEncoder().encode(payload)),
  });
}

function fakeClient(pages: ccc.Cell[][]): ccc.Client {
  let calls = 0;
  return {
    async findCellsPaged() {
      const cells = pages[calls] ?? [];
      calls += 1;
      return { cells, lastCursor: `0x${calls.toString(16)}` };
    },
  } as unknown as ccc.Client;
}

async function evaluate(corpus: Corpus): Promise<CaseResult[]> {
  const results: CaseResult[] = [];
  const records = new Map(corpus.record_cases.map((item) => [item.name, item]));
  const add = (category: string, item: NamedCase, outcome: Record<string, unknown>) => {
    results.push({ id: `${category}/${item.name}`, outcome });
  };

  for (const item of corpus.record_cases) {
    try {
      const record = decodeRegistryV2Record(item.payload);
      let creationAccepted = true;
      try {
        validateCreation(record);
      } catch {
        creationAccepted = false;
      }
      add("record", item, {
        accepted: true,
        creation_accepted: creationAccepted,
        record: canonicalRecord(record),
      });
    } catch {
      add("record", item, { accepted: false, creation_accepted: false, record: null });
    }
  }

  for (const item of corpus.identity_cases) {
    try {
      add("identity", item, {
        accepted: true,
        normalized: normalizeReceiverIdentity(item.value),
      });
    } catch {
      add("identity", item, { accepted: false, normalized: null });
    }
  }

  for (const item of corpus.type_id_vectors) {
    try {
      add("type_id", item, {
        accepted: true,
        value: calculateTypeId({
          firstInputTxHash: item.first_input_tx_hash,
          firstInputIndex: item.first_input_index,
          firstInputSince: item.first_input_since,
          outputIndex: item.output_index,
        }),
      });
    } catch {
      add("type_id", item, { accepted: false, value: null });
    }
  }

  for (const item of corpus.creation_cases) {
    try {
      const record = records.get(item.record_case);
      if (record === undefined) throw new Error(`missing record case ${item.record_case}`);
      validateCreation(decodeRegistryV2Record(record.payload));
      const codeHash = normalizeReceiverIdentity(item.code_hash);
      const registryCodeHash = normalizeReceiverIdentity(corpus.registry_script.code_hash);
      const receiverIdentity = normalizeReceiverIdentity(item.args);
      const expectedIdentity = calculateTypeId({
        firstInputTxHash: item.first_input_tx_hash,
        firstInputIndex: item.first_input_index,
        firstInputSince: item.first_input_since,
        outputIndex: item.output_index,
      });
      if (
        codeHash !== registryCodeHash ||
        item.hash_type !== corpus.registry_script.hash_type ||
        receiverIdentity !== expectedIdentity
      ) {
        throw new Error("creation script does not satisfy Registry V2 Type ID rules");
      }
      add("creation", item, { accepted: true, receiver_identity: receiverIdentity });
    } catch {
      add("creation", item, { accepted: false, receiver_identity: null });
    }
  }

  for (const item of corpus.transition_cases) {
    try {
      const previous = decodeRegistryV2Record(item.previous);
      const next = decodeRegistryV2Record(item.next);
      const previousIdentity = normalizeReceiverIdentity(
        item.previous_identity ?? DEFAULT_IDENTITY,
      );
      const nextIdentity = normalizeReceiverIdentity(item.next_identity ?? DEFAULT_IDENTITY);
      if (previousIdentity !== nextIdentity) throw new Error("receiver_identity is immutable");
      validateSuccessor(previous, next);
      const action =
        next.status === "revoked"
          ? "revoke"
          : item.previous_lock !== item.next_lock
            ? "transfer"
            : "update";
      add("transition", item, { accepted: true, action });
    } catch {
      add("transition", item, { accepted: false, action: null });
    }
  }

  for (const item of corpus.script_cases) {
    try {
      const record = records.get("valid_creation_with_stream");
      if (record === undefined) throw new Error("missing valid record case");
      const cell = registryCell(
        item.args,
        record.payload,
        item.code_hash,
        item.hash_type,
      );
      const discovery = new RegistryV2Discovery(fakeClient([]), {
        contractCodeHash: corpus.registry_script.code_hash,
        scriptHashType: corpus.registry_script.hash_type as "data1" | "type",
        allowMutableCode: corpus.registry_script.hash_type === "type",
        contractCellDep: {
          outPoint: { txHash: "0x" + "99".repeat(32), index: 0 },
          depType: "code",
        },
      });
      const receiver = discovery.parseCell(cell);
      add("script", item, {
        accepted: true,
        receiver_identity: receiver.receiver_identity,
      });
    } catch {
      add("script", item, { accepted: false, receiver_identity: null });
    }
  }

  for (const item of corpus.discovery_cases) {
    const cells = item.cells.map((definition, index) => {
      const record = records.get(definition.record_case);
      if (record === undefined) throw new Error(`missing record case ${definition.record_case}`);
      return registryCell(
        definition.receiver_identity,
        record.payload,
        corpus.registry_script.code_hash,
        corpus.registry_script.hash_type as ccc.HashType,
        index,
      );
    });
    const deployment = {
      contractCodeHash: corpus.registry_script.code_hash,
      scriptHashType: corpus.registry_script.hash_type as "data1" | "type",
      allowMutableCode: corpus.registry_script.hash_type === "type",
      contractCellDep: {
        outPoint: { txHash: "0x" + "99".repeat(32), index: 0 },
        depType: "code" as const,
      },
    };
    const discoveryOptions = {
      nowSeconds: BigInt(corpus.discovery_policy.observed_at),
      maxFutureRecordSkewSeconds: BigInt(corpus.discovery_policy.max_future_skew_seconds),
    };
    const active = await new RegistryV2Discovery(fakeClient([cells, []]), deployment).discover(
      discoveryOptions,
    );
    const historical = await new RegistryV2Discovery(
      fakeClient([cells, []]),
      deployment,
    ).discover({ ...discoveryOptions, includeInactive: true, includeRevoked: true });
    add("discovery", item, {
      active_identities: active.receivers.map((receiver) => receiver.receiver_identity),
      including_revoked_identities: historical.receivers.map(
        (receiver) => receiver.receiver_identity,
      ),
      quarantined_identities: active.quarantinedIdentities,
    });
  }
  return results;
}

const corpusPath = resolve(
  process.argv[2] ?? "../../tests/registry/fixtures/registry_v2_conformance.json",
);
const corpus = JSON.parse(readFileSync(corpusPath, "utf8")) as Corpus;
const output = {
  implementation: "typescript",
  corpus_schema_version: corpus.schema_version,
  results: await evaluate(corpus),
};
process.stdout.write(JSON.stringify(output));
