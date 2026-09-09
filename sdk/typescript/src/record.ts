import { ccc } from "@ckb-ccc/core";

import { isJsonFloat, isJsonInteger, parseStrictJson } from "./strict-json.js";

export const REGISTRY_SCHEMA_VERSION = 2 as const;
export const U64_MAX = (1n << 64n) - 1n;
export const DEFAULT_MAX_RECORD_BYTES = 16 * 1024;

export type ReceiverStatus = "online" | "offline" | "degraded" | "revoked";

export interface RegistryV2Record {
  schema_version: 2;
  receiver_id: string;
  latitude: number;
  longitude: number;
  altitude: number;
  status: ReceiverStatus;
  capabilities: string[];
  sequence: bigint;
  updated_at: bigint;
  stream_endpoint?: string;
  stream_protocol?: "websocket-json" | "command-jsonl";
  stream_format?: "json" | "jsonl";
  metadata_hash?: string;
}

const REQUIRED_FIELDS = [
  "schema_version",
  "receiver_id",
  "latitude",
  "longitude",
  "altitude",
  "status",
  "capabilities",
  "sequence",
  "updated_at",
] as const;
const OPTIONAL_FIELDS = [
  "stream_endpoint",
  "stream_protocol",
  "stream_format",
  "metadata_hash",
] as const;
const ALLOWED_FIELDS = new Set<string>([...REQUIRED_FIELDS, ...OPTIONAL_FIELDS]);
const RECEIVER_ID = /^[A-Z0-9][A-Z0-9_-]{0,63}$/;
const CAPABILITY = /^[a-z0-9][a-z0-9_-]{0,31}$/;
const BYTE32 = /^0x[0-9a-fA-F]{64}$/;
const textEncoder = new TextEncoder();

function matchesExactly(pattern: RegExp, value: string): boolean {
  return pattern.exec(value)?.[0] === value;
}

function hasOnlyUnicodeScalars(value: string): boolean {
  for (let index = 0; index < value.length; index += 1) {
    const codeUnit = value.charCodeAt(index);
    if (codeUnit >= 0xd800 && codeUnit <= 0xdbff) {
      const next = value.charCodeAt(index + 1);
      if (next < 0xdc00 || next > 0xdfff) return false;
      index += 1;
    } else if (codeUnit >= 0xdc00 && codeUnit <= 0xdfff) {
      return false;
    }
  }
  return true;
}

function objectFrom(value: unknown): Record<string, unknown> {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    throw new Error("receiver record must be a JSON object");
  }
  return value as Record<string, unknown>;
}

function u64From(value: unknown, field: string, positive = false): bigint {
  let result: bigint;
  if (isJsonInteger(value)) {
    if (value.raw.startsWith("-")) throw new Error(`${field} must use unsigned JSON syntax`);
    result = BigInt(value.raw);
  } else if (typeof value === "bigint") {
    result = value;
  } else if (typeof value === "number" && Number.isSafeInteger(value) && !Object.is(value, -0)) {
    result = BigInt(value);
  } else {
    throw new Error(`${field} must be an exact u64 integer`);
  }
  if (result < (positive ? 1n : 0n) || result > U64_MAX) {
    throw new Error(`${field} must fit u64`);
  }
  return result;
}

function numberFrom(value: unknown, field: string): number {
  const result = isJsonInteger(value)
    ? Number(value.raw)
    : isJsonFloat(value)
      ? value.value
      : value;
  if (typeof result !== "number" || !Number.isFinite(result)) {
    throw new Error(`${field} must be a finite number`);
  }
  return result;
}

function optionalText(
  value: unknown,
  field: string,
  maxBytes: number,
): string | undefined {
  if (value === null || value === undefined) return undefined;
  if (
    typeof value !== "string" ||
    value.length === 0 ||
    !hasOnlyUnicodeScalars(value) ||
    [...value].some((character) => character === '"' || character === "\\" || character.charCodeAt(0) < 0x20) ||
    textEncoder.encode(value).length > maxBytes
  ) {
    throw new Error(`${field} must contain 1-${maxBytes} UTF-8 bytes`);
  }
  return value;
}

export function normalizeReceiverIdentity(value: unknown): string {
  if (
    typeof value !== "string" ||
    value.length !== 66 ||
    !matchesExactly(BYTE32, value)
  ) {
    throw new Error("receiver_identity must be 0x-prefixed 32-byte hex");
  }
  return value.toLowerCase();
}

export function validateRegistryV2Record(value: unknown): RegistryV2Record {
  const input = objectFrom(value);
  const unknownFields = Object.keys(input).filter((field) => !ALLOWED_FIELDS.has(field));
  if (unknownFields.length > 0) {
    throw new Error(`receiver record contains unknown fields: ${unknownFields.sort().join(", ")}`);
  }
  for (const field of REQUIRED_FIELDS) {
    if (!Object.hasOwn(input, field)) throw new Error(`receiver record is missing ${field}`);
  }

  const schemaVersion = u64From(input.schema_version, "schema_version");
  if (schemaVersion !== 2n) throw new Error("schema_version must be 2");
  if (
    typeof input.receiver_id !== "string" ||
    !matchesExactly(RECEIVER_ID, input.receiver_id)
  ) {
    throw new Error("receiver_id must be 1-64 uppercase ASCII identifier characters");
  }

  const latitude = numberFrom(input.latitude, "latitude");
  const longitude = numberFrom(input.longitude, "longitude");
  const altitude = numberFrom(input.altitude, "altitude");
  if (latitude < -90 || latitude > 90) throw new Error("latitude out of bounds");
  if (longitude < -180 || longitude > 180) throw new Error("longitude out of bounds");
  if (altitude < -500 || altitude > 20_000) throw new Error("altitude out of bounds");

  if (
    typeof input.status !== "string" ||
    !["online", "offline", "degraded", "revoked"].includes(input.status)
  ) {
    throw new Error("unsupported receiver status");
  }
  if (!Array.isArray(input.capabilities) || input.capabilities.length < 1 || input.capabilities.length > 8) {
    throw new Error("capabilities must contain 1-8 values");
  }
  const capabilities = input.capabilities.map((capability) => {
    if (typeof capability !== "string" || !matchesExactly(CAPABILITY, capability)) {
      throw new Error("capabilities contain an invalid value");
    }
    return capability;
  });
  if (new Set(capabilities).size !== capabilities.length) {
    throw new Error("capabilities must be unique");
  }
  if (!capabilities.includes("mode-s")) throw new Error("capabilities must include mode-s");

  const sequence = u64From(input.sequence, "sequence");
  const updatedAt = u64From(input.updated_at, "updated_at", true);
  const streamEndpoint = optionalText(input.stream_endpoint, "stream_endpoint", 256);
  const streamProtocol = optionalText(input.stream_protocol, "stream_protocol", 32);
  const streamFormat = optionalText(input.stream_format, "stream_format", 16);
  const metadataHash = optionalText(input.metadata_hash, "metadata_hash", 66);

  if (streamProtocol !== undefined && !["websocket-json", "command-jsonl"].includes(streamProtocol)) {
    throw new Error("unsupported stream_protocol");
  }
  if (streamFormat !== undefined && !["json", "jsonl"].includes(streamFormat)) {
    throw new Error("unsupported stream_format");
  }
  if (streamEndpoint !== undefined && streamProtocol === undefined) {
    throw new Error("stream_endpoint requires stream_protocol");
  }
  if (metadataHash !== undefined && !matchesExactly(BYTE32, metadataHash)) {
    throw new Error("metadata_hash must be 0x-prefixed 32-byte hex");
  }
  if (input.status === "revoked" && [streamEndpoint, streamProtocol, streamFormat].some((item) => item !== undefined)) {
    throw new Error("revoked records cannot advertise a stream");
  }

  return {
    schema_version: REGISTRY_SCHEMA_VERSION,
    receiver_id: input.receiver_id,
    latitude,
    longitude,
    altitude,
    status: input.status as ReceiverStatus,
    capabilities,
    sequence,
    updated_at: updatedAt,
    ...(streamEndpoint === undefined ? {} : { stream_endpoint: streamEndpoint }),
    ...(streamProtocol === undefined ? {} : { stream_protocol: streamProtocol as RegistryV2Record["stream_protocol"] }),
    ...(streamFormat === undefined ? {} : { stream_format: streamFormat as RegistryV2Record["stream_format"] }),
    ...(metadataHash === undefined ? {} : { metadata_hash: metadataHash }),
  };
}

export function validateCreation(value: unknown): RegistryV2Record {
  const record = validateRegistryV2Record(value);
  if (record.sequence !== 0n) throw new Error("creation sequence must be 0");
  if (record.status === "revoked") throw new Error("a receiver cannot be created revoked");
  return record;
}

export function validateSuccessor(previousValue: unknown, nextValue: unknown): RegistryV2Record {
  const previous = validateRegistryV2Record(previousValue);
  const next = validateRegistryV2Record(nextValue);
  if (previous.status === "revoked") throw new Error("revoked receiver identities are terminal");
  if (next.receiver_id !== previous.receiver_id) throw new Error("receiver_id is immutable");
  if (previous.sequence === U64_MAX || next.sequence !== previous.sequence + 1n) {
    throw new Error("sequence must increment by exactly one");
  }
  if (next.updated_at < previous.updated_at) throw new Error("updated_at cannot move backwards");
  return next;
}

export function decodeRegistryV2Record(
  payload: string | Uint8Array,
  maxBytes = DEFAULT_MAX_RECORD_BYTES,
): RegistryV2Record {
  let source: string;
  if (typeof payload === "string") {
    source = payload;
    if (!hasOnlyUnicodeScalars(source)) throw new Error("receiver record must contain valid Unicode");
    if (textEncoder.encode(source).length > maxBytes) throw new Error("receiver record exceeds the byte limit");
  } else {
    if (payload.length > maxBytes) throw new Error("receiver record exceeds the byte limit");
    source = new TextDecoder("utf-8", { fatal: true }).decode(payload);
  }
  return validateRegistryV2Record(parseStrictJson(source));
}

function jsonString(value: string): string {
  return JSON.stringify(value);
}

export function encodeRegistryV2Record(value: unknown): Uint8Array {
  const record = validateRegistryV2Record(value);
  const fields = [
    `"schema_version":2`,
    `"receiver_id":${jsonString(record.receiver_id)}`,
    `"latitude":${JSON.stringify(record.latitude)}`,
    `"longitude":${JSON.stringify(record.longitude)}`,
    `"altitude":${JSON.stringify(record.altitude)}`,
    `"status":${jsonString(record.status)}`,
    `"capabilities":${JSON.stringify(record.capabilities)}`,
    `"sequence":${record.sequence.toString()}`,
    `"updated_at":${record.updated_at.toString()}`,
  ];
  if (record.stream_endpoint !== undefined) fields.push(`"stream_endpoint":${jsonString(record.stream_endpoint)}`);
  if (record.stream_protocol !== undefined) fields.push(`"stream_protocol":${jsonString(record.stream_protocol)}`);
  if (record.stream_format !== undefined) fields.push(`"stream_format":${jsonString(record.stream_format)}`);
  if (record.metadata_hash !== undefined) fields.push(`"metadata_hash":${jsonString(record.metadata_hash)}`);
  return textEncoder.encode(`{${fields.join(",")}}`);
}

export function encodeRegistryV2CellData(value: unknown): ccc.Hex {
  return ccc.hexFrom(encodeRegistryV2Record(value));
}

export interface TypeIdInput {
  firstInputTxHash: string;
  firstInputIndex: number | bigint;
  firstInputSince?: number | bigint;
  outputIndex?: number | bigint;
}

function boundedInteger(value: number | bigint, maximum: bigint, field: string): bigint {
  if (typeof value === "number" && !Number.isSafeInteger(value)) {
    throw new Error(`${field} must be an exact integer`);
  }
  const result = BigInt(value);
  if (result < 0n || result > maximum) throw new Error(`${field} is outside its integer width`);
  return result;
}

export function calculateTypeId(input: TypeIdInput): string {
  const txHash = normalizeReceiverIdentity(input.firstInputTxHash);
  const previousIndex = boundedInteger(input.firstInputIndex, 0xffff_ffffn, "firstInputIndex");
  const since = boundedInteger(input.firstInputSince ?? 0, U64_MAX, "firstInputSince");
  const outputIndex = boundedInteger(input.outputIndex ?? 0, U64_MAX, "outputIndex");
  const cellInput = ccc.CellInput.from({
    previousOutput: { txHash, index: previousIndex },
    since,
  });
  return ccc.hashCkb(cellInput.toBytes(), ccc.numLeToBytes(outputIndex, 8));
}
