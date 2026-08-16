#!/usr/bin/env python3
"""Verify a published Registry V2 testnet evidence bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import ssl
from typing import Any
import urllib.request

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
            ssl_context = ssl.create_default_context()
    with urllib.request.urlopen(request, timeout=30, context=ssl_context) as response:
        body = json.loads(response.read().decode())
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
    return json.loads(bytes.fromhex(data_hex[2:]).decode())


def first_output(response: dict[str, Any]) -> dict[str, Any]:
    return transaction_view(response)["outputs"][0]


def first_input_out_point(response: dict[str, Any]) -> dict[str, Any]:
    return transaction_view(response)["inputs"][0]["previous_output"]


def verify_bundle(bundle: Path, *, live: bool = False) -> dict[str, Any]:
    verification = Verification()
    checksums_pass, checksums_detail = verify_checksums(bundle)
    verification.require("bundle checksums", checksums_pass, checksums_detail)
    manifest_path = bundle / "manifest.json"
    verification.require("manifest exists", manifest_path.is_file(), str(manifest_path))
    if not manifest_path.is_file():
        return {"pass": False, "checks": verification.checks}
    manifest = load_json(manifest_path)
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
    verification.require("local CI evidence exists", local_ci_path.is_file(), str(local_ci_path))
    verification.require("GitHub CI evidence exists", github_ci_path.is_file(), str(github_ci_path))
    if local_ci_path.is_file():
        local_ci = load_json(local_ci_path)
        verification.require(
            "local CI passed", local_ci.get("pass") is True, str(local_ci.get("pass"))
        )
    if github_ci_path.is_file():
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

    if all(stage in saved for stage in LIFECYCLE_STAGES):
        create_parent = first_input_out_point(saved["create"])
        expected_funding = manifest["lifecycle_funding"]["out_point"]
        verification.require(
            "creation spends declared lifecycle funding",
            create_parent.get("tx_hash") == expected_funding["tx_hash"]
            and int(create_parent.get("index", "0x0"), 0) == int(expected_funding["index"], 0),
            str(create_parent),
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
        code_hashes = {output["type"]["code_hash"] for output in outputs.values()}
        verification.require(
            "immutable Receiver Identity",
            identities == {manifest["receiver"]["identity_id"]},
            str(sorted(identities)),
        )
        verification.require(
            "registry code hash",
            code_hashes == {manifest["contract"]["type_script_hash_for_registry_code_hash"]},
            str(sorted(code_hashes)),
        )
        locks = [outputs[stage]["lock"]["args"] for stage in LIFECYCLE_STAGES]
        expected_locks = [
            manifest["receiver"]["owner_a"]["lock_arg"],
            manifest["receiver"]["owner_a"]["lock_arg"],
            manifest["receiver"]["owner_b"]["lock_arg"],
            manifest["receiver"]["owner_b"]["lock_arg"],
        ]
        verification.require("ownership transfer lock lineage", locks == expected_locks, str(locks))

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
        expected_identity = manifest["receiver"]["identity_id"]
        expected_label = manifest["receiver"].get("label")
        expected_code_hash = manifest["contract"]["type_script_hash_for_registry_code_hash"]
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
                    and type_script.get("hash_type") == "type"
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
                    receiver.get("identity_id") == expected_identity
                    and receiver.get("receiver_id") == expected_label
                    and receiver.get("status") != "revoked"
                    and metadata.get("schema_version") == 2
                    and metadata.get("sequence") == sequence
                    and out_point.get("tx_hash") == expected_tx_hash
                    and int(out_point.get("index", "-1"), 0) == 0
                )
                adapter_detail += (
                    f" identity={receiver.get('identity_id')} sequence={metadata.get('sequence')}"
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

    return {
        "pass": verification.passed,
        "bundle": str(bundle),
        "live_rpc_checked": live,
        "checks": verification.checks,
    }


def main() -> None:
    args = parse_args()
    report = verify_bundle(Path(args.bundle).resolve(), live=args.live)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(rendered)
    print(rendered, end="")
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
