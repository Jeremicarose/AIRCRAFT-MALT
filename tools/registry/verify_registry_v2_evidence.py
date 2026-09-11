#!/usr/bin/env python3
"""Verify a published Registry V2 testnet evidence bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import ssl
import sys
from typing import Any
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ckb_registry.record import (
    calculate_type_id,
    decode_registry_v2_record,
)

ACCEPTED_STAGES = ("deployment", "create", "update", "transfer", "revoke")
LIFECYCLE_STAGES = ("create", "update", "transfer", "revoke")
COMMIT_PATTERN = re.compile(r"[0-9a-f]{40}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify Registry V2 evidence")
    parser.add_argument(
        "--bundle",
        default="evidence/registry-v2-testnet-2026-07-30-final",
        help="Evidence bundle directory",
    )
    parser.add_argument("--live", action="store_true", help="Re-query the public CKB RPC")
    parser.add_argument(
        "--live-chain-only",
        action="store_true",
        help=(
            "Verify checksums, binary, saved transaction bodies, and live chain state "
            "without claiming that CI provenance is included in the bundle"
        ),
    )
    parser.add_argument(
        "--saved-chain-only",
        action="store_true",
        help=(
            "Verify saved chain, indexer, and runtime evidence without requiring "
            "CI provenance or making network requests"
        ),
    )
    parser.add_argument("--output", help="Optional JSON verification report")
    return parser.parse_args()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ckb_hash(path: Path) -> str:
    return (
        "0x"
        + hashlib.blake2b(path.read_bytes(), digest_size=32, person=b"ckb-default-hash").hexdigest()
    )


def _number(value: Any, field: str) -> int:
    try:
        result = int(value, 0) if isinstance(value, str) else int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} is not an integer") from exc
    if result < 0:
        raise ValueError(f"{field} must be non-negative")
    return result


def _hex_bytes(value: Any, field: str, length: int | None = None) -> bytes:
    if not isinstance(value, str) or not value.startswith("0x") or len(value) % 2:
        raise ValueError(f"{field} must be 0x-prefixed hexadecimal")
    try:
        result = bytes.fromhex(value[2:])
    except ValueError as exc:
        raise ValueError(f"{field} must be hexadecimal") from exc
    if length is not None and len(result) != length:
        raise ValueError(f"{field} must contain {length} bytes")
    return result


def _u32(value: int) -> bytes:
    return value.to_bytes(4, "little")


def _u64(value: int) -> bytes:
    return value.to_bytes(8, "little")


def _fixvec(items: list[bytes]) -> bytes:
    return _u32(len(items)) + b"".join(items)


def _dynvec(items: list[bytes]) -> bytes:
    if not items:
        return _u32(4)
    header_size = 4 + 4 * len(items)
    offsets: list[bytes] = []
    offset = header_size
    for item in items:
        offsets.append(_u32(offset))
        offset += len(item)
    return _u32(offset) + b"".join(offsets) + b"".join(items)


def _molecule_bytes(value: Any, field: str) -> bytes:
    raw = _hex_bytes(value, field)
    return _u32(len(raw)) + raw


def _script_bytes(script: dict[str, Any], field: str) -> bytes:
    hash_types = {"data": 0, "type": 1, "data1": 2, "data2": 4}
    hash_type = script.get("hash_type")
    if hash_type not in hash_types:
        raise ValueError(f"{field}.hash_type is invalid")
    return _dynvec(
        [
            _hex_bytes(script.get("code_hash"), f"{field}.code_hash", 32),
            bytes([hash_types[hash_type]]),
            _molecule_bytes(script.get("args"), f"{field}.args"),
        ]
    )


def raw_transaction_bytes(transaction: dict[str, Any]) -> bytes:
    dep_types = {"code": 0, "dep_group": 1}
    cell_deps = []
    for index, dep in enumerate(transaction.get("cell_deps", [])):
        out_point = dep.get("out_point") or {}
        dep_type = dep_types.get(dep.get("dep_type"))
        if dep_type is None:
            raise ValueError(f"cell_deps[{index}].dep_type is invalid")
        cell_deps.append(
            _hex_bytes(out_point.get("tx_hash"), f"cell_deps[{index}].tx_hash", 32)
            + _number(out_point.get("index"), f"cell_deps[{index}].index").to_bytes(4, "little")
            + bytes([dep_type])
        )

    inputs = []
    for index, item in enumerate(transaction.get("inputs", [])):
        out_point = item.get("previous_output") or {}
        inputs.append(
            _u64(_number(item.get("since", 0), f"inputs[{index}].since"))
            + _hex_bytes(out_point.get("tx_hash"), f"inputs[{index}].tx_hash", 32)
            + _number(out_point.get("index"), f"inputs[{index}].index").to_bytes(4, "little")
        )

    outputs = []
    for index, output in enumerate(transaction.get("outputs", [])):
        type_script = output.get("type")
        outputs.append(
            _dynvec(
                [
                    _u64(_number(output.get("capacity"), f"outputs[{index}].capacity")),
                    _script_bytes(output.get("lock") or {}, f"outputs[{index}].lock"),
                    (
                        b""
                        if type_script is None
                        else _script_bytes(type_script, f"outputs[{index}].type")
                    ),
                ]
            )
        )

    raw = _dynvec(
        [
            _u32(_number(transaction.get("version", 0), "version")),
            _fixvec(cell_deps),
            _fixvec(
                [
                    _hex_bytes(value, f"header_deps[{index}]", 32)
                    for index, value in enumerate(transaction.get("header_deps", []))
                ]
            ),
            _fixvec(inputs),
            _dynvec(outputs),
            _dynvec(
                [
                    _molecule_bytes(value, f"outputs_data[{index}]")
                    for index, value in enumerate(transaction.get("outputs_data", []))
                ]
            ),
        ]
    )
    return raw


def calculate_transaction_hash(transaction: dict[str, Any]) -> str:
    return (
        "0x"
        + hashlib.blake2b(
            raw_transaction_bytes(transaction),
            digest_size=32,
            person=b"ckb-default-hash",
        ).hexdigest()
    )


def verify_checksums(bundle: Path) -> tuple[bool, str]:
    checksum_path = bundle / "checksums.sha256"
    if not checksum_path.is_file():
        return False, "checksums.sha256 is missing"

    errors: list[str] = []
    declared: dict[str, str] = {}
    try:
        lines = checksum_path.read_text(encoding="ascii").splitlines()
    except (OSError, UnicodeError) as exc:
        return False, f"cannot read checksums.sha256: {exc}"

    for line_number, line in enumerate(lines, start=1):
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if match is None:
            errors.append(f"line {line_number}: invalid checksum entry")
            continue
        digest, relative_name = match.groups()
        relative = PurePosixPath(relative_name)
        if relative.is_absolute() or ".." in relative.parts or relative_name == "checksums.sha256":
            errors.append(f"line {line_number}: unsafe path {relative_name!r}")
            continue
        if relative_name in declared:
            errors.append(f"line {line_number}: duplicate path {relative_name}")
            continue
        declared[relative_name] = digest

    actual_files: set[str] = set()
    for path in bundle.rglob("*"):
        if path == checksum_path or not path.is_file():
            continue
        relative_name = path.relative_to(bundle).as_posix()
        actual_files.add(relative_name)
        if path.is_symlink():
            errors.append(f"{relative_name}: symbolic links are not allowed")

    missing = sorted(actual_files - declared.keys())
    unexpected = sorted(declared.keys() - actual_files)
    if missing:
        errors.append("missing entries: " + ", ".join(missing))
    if unexpected:
        errors.append("entries without files: " + ", ".join(unexpected))

    for relative_name in sorted(actual_files & declared.keys()):
        path = bundle.joinpath(*PurePosixPath(relative_name).parts)
        observed = sha256(path)
        if observed != declared[relative_name]:
            errors.append(
                f"{relative_name}: expected {declared[relative_name]}, observed {observed}"
            )

    if errors:
        return False, "; ".join(errors)
    return True, f"verified {len(actual_files)} files"


def rpc(url: str, method: str, params: list[Any]) -> Any:
    request = urllib.request.Request(
        url,
        data=json.dumps({"id": 1, "jsonrpc": "2.0", "method": method, "params": params}).encode(),
        headers={"Content-Type": "application/json", "User-Agent": "mlat-registry-v2-verifier/1"},
        method="POST",
    )
    ssl_context = None
    if url.startswith("https://"):
        try:
            import certifi

            ssl_context = ssl.create_default_context(cafile=certifi.where())
        except ImportError:
            default_paths = ssl.get_default_verify_paths()
            system_ca = Path("/etc/ssl/cert.pem")
            ssl_context = (
                ssl.create_default_context(cafile=str(system_ca))
                if default_paths.cafile is None and system_ca.is_file()
                else ssl.create_default_context()
            )
    try:
        with urllib.request.urlopen(request, timeout=30, context=ssl_context) as response:
            body = json.loads(response.read().decode())
    except urllib.error.URLError as exc:
        reason = str(exc.reason)
        hint = (
            " Check this machine's CA certificate store."
            if isinstance(exc.reason, ssl.SSLCertVerificationError)
            else ""
        )
        raise RuntimeError(
            f"CKB RPC request to {url} failed while calling {method}: {reason}.{hint}"
        ) from None
    if body.get("error") is not None:
        raise RuntimeError(json.dumps(body["error"], sort_keys=True))
    return body["result"]


class Verification:
    def __init__(self) -> None:
        self.checks: list[dict[str, Any]] = []

    def require(self, name: str, condition: bool, detail: str) -> None:
        self.checks.append({"name": name, "pass": bool(condition), "detail": detail})

    @property
    def passed(self) -> bool:
        return all(check["pass"] for check in self.checks)


def transaction_view(response: dict[str, Any]) -> dict[str, Any]:
    transaction = response.get("transaction")
    if not isinstance(transaction, dict):
        return {}
    inner = transaction.get("inner")
    return inner if isinstance(inner, dict) else transaction


def record_from_transaction(response: dict[str, Any]) -> dict[str, Any]:
    transaction = transaction_view(response)
    data_hex = transaction["outputs_data"][0]
    return decode_registry_v2_record(bytes.fromhex(data_hex[2:])).to_payload_dict()


def first_output(response: dict[str, Any]) -> dict[str, Any]:
    return transaction_view(response)["outputs"][0]


def first_input_out_point(response: dict[str, Any]) -> dict[str, Any]:
    return transaction_view(response)["inputs"][0]["previous_output"]


def verify_data1_reports(
    verification: Verification,
    bundle: Path,
    *,
    receiver_identity: str,
    code_hash: str,
    revoke_transaction_hash: str,
) -> None:
    indexer_path = bundle / "real-indexer-verification.json"
    verification.require("real indexer report exists", indexer_path.is_file(), str(indexer_path))
    if indexer_path.is_file():
        try:
            report = load_json(indexer_path)
            required = {
                "canonical_identity_matches",
                "data1_code_binding_matches",
                "duplicate_output_attack_rejected",
                "exact_identity_has_one_live_cell",
                "exact_query_exhausted",
                "exact_query_used_multiple_pages",
                "live_record_is_revoked",
                "prefix_has_one_live_registry_cell",
                "prefix_query_exhausted",
                "prefix_query_used_multiple_pages",
            }
            checks = report.get("checks") if isinstance(report, dict) else None
            valid = (
                report.get("pass") is True
                and report.get("receiver_identity") == receiver_identity
                and report.get("code_hash") == code_hash
                and isinstance(checks, dict)
                and all(checks.get(name) is True for name in required)
            )
            detail = f"identity={report.get('receiver_identity')} checks={len(checks or {})}"
        except (AttributeError, json.JSONDecodeError, OSError, TypeError):
            valid = False
            detail = "invalid JSON report"
        verification.require("real indexer pagination and binding", valid, detail)

    runtime_path = bundle / "runtime-revocation-verification.json"
    verification.require(
        "runtime revocation report exists", runtime_path.is_file(), str(runtime_path)
    )
    if runtime_path.is_file():
        try:
            report = load_json(runtime_path)
            required = {
                "canonical_identity_removed_from_active_pool",
                "canonical_identity_removed_from_database",
                "canonical_identity_removed_from_solver_positions",
                "no_feed_task_left_for_revoked_receiver",
                "old_feed_task_cancelled",
                "real_indexer_refresh_succeeded",
                "real_indexer_returned_no_active_receiver",
                "rebind_contains_no_revoked_receiver",
                "rebind_preserved_message_callback",
                "runtime_start_time_unchanged",
                "same_process_without_manual_restart",
                "stream_rebound_automatically_once",
            }
            checks = report.get("checks") if isinstance(report, dict) else None
            script = report.get("registry_script") if isinstance(report, dict) else None
            valid = (
                report.get("pass") is True
                and report.get("receiver_identity") == receiver_identity
                and report.get("revocation_tx_hash") == revoke_transaction_hash
                and script == {"code_hash": code_hash, "hash_type": "data1"}
                and report.get("discovered_active_count") == 0
                and report.get("active_receiver_ids_after") == []
                and report.get("database_receiver_ids_after") == []
                and report.get("solver_receiver_ids_after") == []
                and isinstance(checks, dict)
                and all(checks.get(name) is True for name in required)
            )
            detail = f"identity={report.get('receiver_identity')} checks={len(checks or {})}"
        except (AttributeError, json.JSONDecodeError, OSError, TypeError):
            valid = False
            detail = "invalid JSON report"
        verification.require("same-process revocation removal", valid, detail)


def verify_bundle(
    bundle: Path,
    *,
    live: bool = False,
    require_ci_provenance: bool = True,
) -> dict[str, Any]:
    verification = Verification()
    checksums_pass, checksums_detail = verify_checksums(bundle)
    verification.require("bundle checksums", checksums_pass, checksums_detail)
    manifest_path = bundle / "manifest.json"
    verification.require("manifest exists", manifest_path.is_file(), str(manifest_path))
    if not manifest_path.is_file():
        return {"pass": False, "checks": verification.checks}
    manifest = load_json(manifest_path)
    receiver_manifest = manifest.get("receiver") or {}
    expected_receiver_identity = receiver_manifest.get(
        "receiver_identity", receiver_manifest.get("identity_id")
    )
    verification.require(
        "receiver_identity present",
        isinstance(expected_receiver_identity, str),
        str(expected_receiver_identity),
    )
    verification.require(
        "manifest status complete",
        manifest.get("status") == "complete",
        str(manifest.get("status")),
    )
    verification.require(
        "private keys excluded",
        manifest.get("private_keys_included") is False,
        str(manifest.get("private_keys_included")),
    )

    binary_path = bundle / "contract" / "receiver-registry"
    verification.require("contract binary exists", binary_path.is_file(), str(binary_path))
    if binary_path.is_file():
        verification.require(
            "contract SHA-256",
            sha256(binary_path) == manifest["contract"]["binary_sha256"],
            manifest["contract"]["binary_sha256"],
        )
        verification.require(
            "contract CKB data hash",
            ckb_hash(binary_path) == manifest["contract"]["binary_ckb_data_hash"],
            manifest["contract"]["binary_ckb_data_hash"],
        )

    local_ci_path = bundle / "ci" / "local.json"
    github_ci_path = bundle / "ci" / "github.json"
    if require_ci_provenance:
        verification.require(
            "local CI evidence exists", local_ci_path.is_file(), str(local_ci_path)
        )
        verification.require(
            "GitHub CI evidence exists", github_ci_path.is_file(), str(github_ci_path)
        )
    if require_ci_provenance and local_ci_path.is_file():
        local_ci = load_json(local_ci_path)
        verification.require(
            "local CI passed", local_ci.get("pass") is True, str(local_ci.get("pass"))
        )
    if require_ci_provenance and github_ci_path.is_file():
        github_ci = load_json(github_ci_path)
        verification.require(
            "GitHub CI passed",
            github_ci.get("status") == "completed" and github_ci.get("conclusion") == "success",
            f"{github_ci.get('status')}/{github_ci.get('conclusion')}",
        )
        verification.require(
            "GitHub artifact matches deployment binary",
            github_ci.get("artifact", {}).get("receiver_registry_sha256")
            == manifest["contract"]["binary_sha256"],
            str(github_ci.get("artifact", {}).get("receiver_registry_sha256")),
        )
        source = manifest.get("source", {})
        contract_commit = source.get("contract_source_commit")
        tooling_commit = source.get("lifecycle_tooling_commit")
        source_commits_valid = all(
            isinstance(value, str) and COMMIT_PATTERN.fullmatch(value)
            for value in (contract_commit, tooling_commit)
        )
        verification.require(
            "source commits pinned",
            source_commits_valid,
            f"contract={contract_commit} tooling={tooling_commit}",
        )
        verification.require(
            "tooling source binding",
            source_commits_valid and github_ci.get("head_sha") == tooling_commit,
            f"manifest={tooling_commit} GitHub={github_ci.get('head_sha')}",
        )

    accepted = manifest["accepted_transactions"]
    expected_code_hash = manifest["contract"]["type_script_hash_for_registry_code_hash"]
    expected_hash_type = manifest["contract"].get("registry_script_hash_type", "type")
    verification.require(
        "registry script hash type",
        expected_hash_type in {"data1", "type"},
        str(expected_hash_type),
    )
    if expected_hash_type == "data1":
        verification.require(
            "immutable data1 code binding",
            expected_code_hash == manifest["contract"]["binary_ckb_data_hash"],
            f"code_hash={expected_code_hash} data_hash={manifest['contract']['binary_ckb_data_hash']}",
        )
        verify_data1_reports(
            verification,
            bundle,
            receiver_identity=expected_receiver_identity,
            code_hash=expected_code_hash,
            revoke_transaction_hash=accepted["revoke"],
        )
    saved: dict[str, dict[str, Any]] = {}
    for stage in ACCEPTED_STAGES:
        path = bundle / "rpc" / f"{stage}-transaction.json"
        verification.require(f"{stage} RPC response exists", path.is_file(), str(path))
        if not path.is_file():
            continue
        response = load_json(path)
        saved[stage] = response
        status = response.get("tx_status", {}).get("status")
        verification.require(f"{stage} committed", status == "committed", str(status))
        observed_hash = transaction_view(response).get("hash")
        verification.require(
            f"{stage} transaction hash",
            observed_hash == accepted[stage],
            f"expected={accepted[stage]} observed={observed_hash}",
        )
        try:
            calculated_hash = calculate_transaction_hash(transaction_view(response))
        except (KeyError, OverflowError, TypeError, ValueError) as exc:
            calculated_hash = f"invalid transaction body: {exc}"
        verification.require(
            f"{stage} transaction body hash",
            calculated_hash == accepted[stage],
            f"expected={accepted[stage]} calculated={calculated_hash}",
        )

    if all(stage in saved for stage in LIFECYCLE_STAGES):
        create_parent = first_input_out_point(saved["create"])
        expected_funding = manifest["lifecycle_funding"]["out_point"]
        verification.require(
            "creation spends declared lifecycle funding",
            create_parent.get("tx_hash") == expected_funding["tx_hash"]
            and int(create_parent.get("index", "0x0"), 0) == int(expected_funding["index"], 0),
            str(create_parent),
        )
        create_input = transaction_view(saved["create"])["inputs"][0]
        try:
            calculated_identity = calculate_type_id(
                first_input_tx_hash=create_parent["tx_hash"],
                first_input_index=_number(create_parent["index"], "creation input index"),
                first_input_since=_number(create_input.get("since", 0), "creation input since"),
                output_index=0,
            )
        except (KeyError, TypeError, ValueError) as exc:
            calculated_identity = f"invalid Type ID input: {exc}"
        verification.require(
            "creation Type ID derivation",
            calculated_identity == expected_receiver_identity,
            f"manifest={expected_receiver_identity} calculated={calculated_identity}",
        )
        expected_parents = {
            "update": accepted["create"],
            "transfer": accepted["update"],
            "revoke": accepted["transfer"],
        }
        for stage, expected_parent in expected_parents.items():
            parent = first_input_out_point(saved[stage])
            verification.require(
                f"{stage} spends previous registry cell",
                parent.get("tx_hash") == expected_parent
                and int(parent.get("index", "0x0"), 0) == 0,
                str(parent),
            )

        records = {stage: record_from_transaction(saved[stage]) for stage in LIFECYCLE_STAGES}
        labels = {record["receiver_id"] for record in records.values()}
        sequences = [records[stage]["sequence"] for stage in LIFECYCLE_STAGES]
        statuses = [records[stage]["status"] for stage in LIFECYCLE_STAGES]
        verification.require("receiver label immutable", len(labels) == 1, str(sorted(labels)))
        verification.require("sequence is 0,1,2,3", sequences == [0, 1, 2, 3], str(sequences))
        verification.require(
            "revocation is final accepted state", statuses[-1] == "revoked", str(statuses)
        )

        outputs = {stage: first_output(saved[stage]) for stage in LIFECYCLE_STAGES}
        identities = {output["type"]["args"] for output in outputs.values()}
        type_scripts = [outputs[stage]["type"] for stage in LIFECYCLE_STAGES]
        verification.require(
            "immutable Receiver Identity",
            identities == {expected_receiver_identity},
            str(sorted(identities)),
        )
        verification.require(
            "complete registry type script",
            all(
                script
                == {
                    "args": expected_receiver_identity,
                    "code_hash": expected_code_hash,
                    "hash_type": expected_hash_type,
                }
                for script in type_scripts
            ),
            json.dumps(type_scripts, sort_keys=True),
        )
        locks = [outputs[stage]["lock"] for stage in LIFECYCLE_STAGES]
        expected_locks = [
            manifest["receiver"]["owner_a"]["lock_arg"],
            manifest["receiver"]["owner_a"]["lock_arg"],
            manifest["receiver"]["owner_b"]["lock_arg"],
            manifest["receiver"]["owner_b"]["lock_arg"],
        ]
        lock_args = [lock.get("args") for lock in locks]
        verification.require(
            "ownership transfer lock lineage",
            lock_args == expected_locks
            and locks[0] == locks[1]
            and locks[2] == locks[3]
            and locks[0] != locks[2],
            json.dumps(locks, sort_keys=True),
        )

    for attack in manifest.get("rejected_attacks", []):
        response_path = bundle / "responses" / f"attack-{attack}.json"
        tx_path = bundle / "transactions" / f"attack-{attack}.json"
        verification.require(
            f"{attack} response exists", response_path.is_file(), str(response_path)
        )
        verification.require(f"{attack} signed tx exists", tx_path.is_file(), str(tx_path))
        if response_path.is_file() and tx_path.is_file():
            response = load_json(response_path)
            tx_file = load_json(tx_path)
            signatures = tx_file.get("signatures", {})
            verification.require(
                f"{attack} was signed",
                any(values for values in signatures.values()),
                f"signature groups={len(signatures)}",
            )
            verification.require(
                f"{attack} rejected",
                response.get("expected") == "rejected" and response.get("returncode") != 0,
                response.get("stderr") or response.get("stdout") or "no rejection output",
            )
            verification.require(
                f"{attack} transaction file hash",
                response.get("signed_tx_file_sha256") == sha256(tx_path),
                response.get("signed_tx_file_sha256", "missing"),
            )

    for sequence, stage in enumerate(LIFECYCLE_STAGES):
        indexer_path = bundle / "discovery" / f"{stage}-indexer.json"
        adapter_path = bundle / "discovery" / f"{stage}-adapter.json"
        expected_identity = expected_receiver_identity
        expected_label = manifest["receiver"].get("label")
        expected_tx_hash = accepted[stage]

        indexer_valid = False
        indexer_detail = str(indexer_path)
        if indexer_path.is_file():
            indexer = load_json(indexer_path)
            objects = indexer.get("objects") if isinstance(indexer, dict) else None
            if isinstance(objects, list) and len(objects) == 1:
                cell = objects[0]
                output = cell.get("output", {})
                type_script = output.get("type") or {}
                out_point = cell.get("out_point", {})
                transaction = transaction_view(saved.get(stage, {}))
                indexer_valid = (
                    out_point.get("tx_hash") == expected_tx_hash
                    and int(out_point.get("index", "-1"), 0) == 0
                    and type_script.get("args") == expected_identity
                    and type_script.get("code_hash") == expected_code_hash
                    and type_script.get("hash_type") == expected_hash_type
                    and output == first_output(saved[stage])
                    and cell.get("output_data") == transaction.get("outputs_data", [None])[0]
                )
                indexer_detail = f"count=1 identity={type_script.get('args')} out_point={out_point}"
            else:
                count = len(objects) if isinstance(objects, list) else "invalid"
                indexer_detail = f"objects={count}"
        verification.require(f"{stage} indexer discovery", indexer_valid, indexer_detail)

        adapter_valid = False
        adapter_detail = str(adapter_path)
        if adapter_path.is_file():
            adapter = load_json(adapter_path)
            expected_count = 0 if stage == "revoke" else 1
            adapter_valid = isinstance(adapter, list) and len(adapter) == expected_count
            adapter_detail = (
                f"count={len(adapter)}" if isinstance(adapter, list) else "not a JSON array"
            )
            if adapter_valid and expected_count == 1:
                receiver = adapter[0]
                metadata = receiver.get("metadata", {})
                out_point = metadata.get("out_point", {})
                adapter_valid = (
                    receiver.get("receiver_identity", receiver.get("identity_id"))
                    == expected_identity
                    and receiver.get("receiver_id") == expected_label
                    and receiver.get("status") != "revoked"
                    and metadata.get("schema_version") == 2
                    and metadata.get("sequence") == sequence
                    and out_point.get("tx_hash") == expected_tx_hash
                    and int(out_point.get("index", "-1"), 0) == 0
                )
                adapter_detail += (
                    " identity="
                    f"{receiver.get('receiver_identity', receiver.get('identity_id'))}"
                    f" sequence={metadata.get('sequence')}"
                )
        verification.require(f"{stage} adapter discovery", adapter_valid, adapter_detail)

    api_files = {
        path.stem.removesuffix("-receivers"): path for path in (bundle / "api").glob("*.json")
    }
    verification.require("API responses captured", len(api_files) >= 4, str(len(api_files)))
    for stage, expected_count in (("create", 1), ("update", 1), ("transfer", 1), ("revoke", 0)):
        path = api_files.get(stage)
        if path is None:
            continue
        capture = load_json(path)
        body = capture.get("body") or {}
        verification.require(
            f"{stage} API response",
            capture.get("status_code") == 200 and body.get("count") == expected_count,
            f"status={capture.get('status_code')} count={body.get('count')}",
        )

    if live:
        for stage, tx_hash in accepted.items():
            response = rpc(manifest["rpc_url"], "get_transaction", [tx_hash])
            status = None if response is None else response.get("tx_status", {}).get("status")
            verification.require(f"live {stage} committed", status == "committed", str(status))
            live_transaction = transaction_view(response or {})
            verification.require(
                f"live {stage} transaction body",
                live_transaction == transaction_view(saved.get(stage, {})),
                (
                    "live RPC body matches saved body"
                    if live_transaction == transaction_view(saved.get(stage, {}))
                    else "live RPC body differs from saved evidence"
                ),
            )

        contract_out_point = manifest["contract"]["out_point"]
        live_contract = rpc(manifest["rpc_url"], "get_live_cell", [contract_out_point, True])
        live_contract_hash = (((live_contract or {}).get("cell") or {}).get("data") or {}).get(
            "hash"
        )
        verification.require(
            "live contract cell and binary",
            (live_contract or {}).get("status") == "live"
            and live_contract_hash == manifest["contract"]["binary_ckb_data_hash"],
            f"status={(live_contract or {}).get('status')} data_hash={live_contract_hash}",
        )

    return {
        "pass": verification.passed,
        "bundle": str(bundle),
        "live_rpc_checked": live,
        "ci_provenance_checked": require_ci_provenance,
        "checks": verification.checks,
    }


def main() -> None:
    args = parse_args()
    try:
        report = verify_bundle(
            Path(args.bundle).resolve(),
            live=args.live or args.live_chain_only,
            require_ci_provenance=not (args.live_chain_only or args.saved_chain_only),
        )
    except RuntimeError as exc:
        raise SystemExit(f"Registry V2 verification could not complete: {exc}") from None
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(rendered)
    print(rendered, end="")
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
