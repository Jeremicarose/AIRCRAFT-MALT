import hashlib
import json
import urllib.error

import pytest

from ckb_registry.record import calculate_type_id
from tools.registry.verify_registry_v2_evidence import (
    Verification,
    calculate_transaction_hash,
    rpc,
    verify_data1_reports,
    verify_bundle,
)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value) + "\n")


def write_checksums(bundle):
    lines = []
    for path in sorted(bundle.rglob("*")):
        if path.is_file() and path.name != "checksums.sha256":
            relative = path.relative_to(bundle).as_posix()
            lines.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {relative}")
    (bundle / "checksums.sha256").write_text("\n".join(lines) + "\n")


def transaction_response(parent_hash, sequence, owner, identity, code_hash, status):
    record = {
        "schema_version": 2,
        "receiver_id": "RECV_TEST",
        "latitude": -1.2,
        "longitude": 36.8,
        "altitude": 1700.0,
        "status": status,
        "capabilities": ["mode-s", "mlat"],
        "sequence": sequence,
        "updated_at": 1_700_000_000 + sequence,
    }
    return {
        "transaction": {
            "hash": "",
            "version": "0x0",
            "cell_deps": [],
            "header_deps": [],
            "inputs": [
                {
                    "since": "0x0",
                    "previous_output": {
                        "tx_hash": parent_hash,
                        "index": "0x0",
                    },
                }
            ],
            "outputs": [
                {
                    "capacity": "0x174876e800",
                    "lock": {
                        "args": owner,
                        "code_hash": "0x" + "cc" * 32,
                        "hash_type": "type",
                    },
                    "type": {
                        "args": identity,
                        "code_hash": code_hash,
                        "hash_type": "type",
                    },
                }
            ],
            "outputs_data": ["0x" + json.dumps(record).encode().hex()],
        },
        "tx_status": {"status": "committed"},
    }


def build_bundle(tmp_path):
    bundle = tmp_path / "evidence"
    binary = bundle / "contract" / "receiver-registry"
    binary.parent.mkdir(parents=True)
    binary.write_bytes(b"registry-v2-test-binary")
    ckb_digest = hashlib.blake2b(
        binary.read_bytes(), digest_size=32, person=b"ckb-default-hash"
    ).hexdigest()
    deployment_transaction = {
        "hash": "",
        "version": "0x0",
        "cell_deps": [],
        "header_deps": [],
        "inputs": [],
        "outputs": [],
        "outputs_data": [],
    }
    deployment_transaction["hash"] = calculate_transaction_hash(deployment_transaction)
    hashes = {"deployment": deployment_transaction["hash"]}
    identity = calculate_type_id(
        first_input_tx_hash=hashes["deployment"],
        first_input_index=0,
        first_input_since=0,
        output_index=0,
    )
    code_hash = "0x" + "bb" * 32
    owner_a = "0x" + "11" * 20
    owner_b = "0x" + "22" * 20
    manifest = {
        "status": "complete",
        "contract": {
            "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
            "binary_ckb_data_hash": "0x" + ckb_digest,
            "type_script_hash_for_registry_code_hash": code_hash,
        },
        "receiver": {
            "identity_id": identity,
            "label": "RECV_TEST",
            "owner_a": {"lock_arg": owner_a},
            "owner_b": {"lock_arg": owner_b},
        },
        "lifecycle_funding": {"out_point": {"tx_hash": hashes["deployment"], "index": "0x0"}},
        "accepted_transactions": hashes,
        "rejected_attacks": [],
        "rpc_url": "https://testnet.invalid/rpc",
        "private_keys_included": False,
        "source": {
            "contract_source_commit": "1" * 40,
            "lifecycle_tooling_commit": "2" * 40,
        },
    }
    write_json(bundle / "ci" / "local.json", {"pass": True})
    write_json(
        bundle / "ci" / "github.json",
        {
            "status": "completed",
            "conclusion": "success",
            "head_sha": "2" * 40,
            "artifact": {
                "receiver_registry_sha256": hashlib.sha256(binary.read_bytes()).hexdigest()
            },
        },
    )
    write_json(
        bundle / "rpc" / "deployment-transaction.json",
        {"transaction": deployment_transaction, "tx_status": {"status": "committed"}},
    )
    stages = ("create", "update", "transfer", "revoke")
    owners = (owner_a, owner_a, owner_b, owner_b)
    statuses = ("online", "online", "online", "revoked")
    parent = hashes["deployment"]
    for sequence, (stage, owner, status) in enumerate(zip(stages, owners, statuses)):
        response = transaction_response(parent, sequence, owner, identity, code_hash, status)
        transaction = response["transaction"]
        hashes[stage] = calculate_transaction_hash(transaction)
        transaction["hash"] = hashes[stage]
        parent = hashes[stage]
        write_json(
            bundle / "rpc" / f"{stage}-transaction.json",
            response,
        )
        write_json(
            bundle / "discovery" / f"{stage}-indexer.json",
            {
                "last_cursor": "0x00",
                "objects": [
                    {
                        "out_point": {"tx_hash": hashes[stage], "index": "0x0"},
                        "output": transaction["outputs"][0],
                        "output_data": transaction["outputs_data"][0],
                    }
                ],
            },
        )
        adapter = []
        if status != "revoked":
            adapter = [
                {
                    "identity_id": identity,
                    "receiver_id": "RECV_TEST",
                    "status": status,
                    "metadata": {
                        "schema_version": 2,
                        "sequence": sequence,
                        "out_point": {"tx_hash": hashes[stage], "index": "0x0"},
                    },
                }
            ]
        write_json(bundle / "discovery" / f"{stage}-adapter.json", adapter)
    write_json(bundle / "manifest.json", manifest)
    for stage, count in (("create", 1), ("update", 1), ("transfer", 1), ("revoke", 0)):
        write_json(
            bundle / "api" / f"{stage}-receivers.json",
            {"status_code": 200, "body": {"count": count}},
        )
    write_checksums(bundle)
    return bundle


def test_verifier_accepts_complete_consistent_bundle(tmp_path):
    report = verify_bundle(build_bundle(tmp_path))
    assert report["pass"] is True


def test_live_chain_scope_does_not_claim_missing_ci_provenance(tmp_path):
    bundle = build_bundle(tmp_path)
    (bundle / "ci" / "local.json").unlink()
    (bundle / "ci" / "github.json").unlink()
    write_checksums(bundle)

    report = verify_bundle(bundle, require_ci_provenance=False)

    assert report["pass"] is True
    assert report["ci_provenance_checked"] is False
    assert not any("CI" in check["name"] for check in report["checks"])


def test_data1_reports_enforce_indexer_pagination_and_runtime_revocation(tmp_path):
    bundle = tmp_path / "data1-evidence"
    identity = "0x" + "11" * 32
    code_hash = "0x" + "22" * 32
    revoke_hash = "0x" + "33" * 32
    indexer_checks = {
        name: True
        for name in (
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
        )
    }
    runtime_checks = {
        name: True
        for name in (
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
        )
    }
    write_json(
        bundle / "real-indexer-verification.json",
        {
            "pass": True,
            "receiver_identity": identity,
            "code_hash": code_hash,
            "checks": indexer_checks,
        },
    )
    runtime = {
        "pass": True,
        "receiver_identity": identity,
        "revocation_tx_hash": revoke_hash,
        "registry_script": {"code_hash": code_hash, "hash_type": "data1"},
        "discovered_active_count": 0,
        "active_receiver_ids_after": [],
        "database_receiver_ids_after": [],
        "solver_receiver_ids_after": [],
        "checks": runtime_checks,
    }
    write_json(bundle / "runtime-revocation-verification.json", runtime)

    verification = Verification()
    verify_data1_reports(
        verification,
        bundle,
        receiver_identity=identity,
        code_hash=code_hash,
        revoke_transaction_hash=revoke_hash,
    )
    assert verification.passed is True

    runtime["checks"]["canonical_identity_removed_from_database"] = False
    write_json(bundle / "runtime-revocation-verification.json", runtime)
    verification = Verification()
    verify_data1_reports(
        verification,
        bundle,
        receiver_identity=identity,
        code_hash=code_hash,
        revoke_transaction_hash=revoke_hash,
    )
    assert verification.passed is False


def test_rpc_translates_connection_failures(monkeypatch):
    def fail_request(*args, **kwargs):
        raise urllib.error.URLError("certificate verify failed")

    monkeypatch.setattr("urllib.request.urlopen", fail_request)

    with pytest.raises(RuntimeError, match="CKB RPC request.*certificate verify failed"):
        rpc("https://testnet.invalid/rpc", "get_transaction", ["0x" + "11" * 32])


def test_verifier_rejects_identity_mutation(tmp_path):
    bundle = build_bundle(tmp_path)
    transfer_path = bundle / "rpc" / "transfer-transaction.json"
    transfer = json.loads(transfer_path.read_text())
    transfer["transaction"]["outputs"][0]["type"]["args"] = "0x" + "cc" * 32
    write_json(transfer_path, transfer)

    report = verify_bundle(bundle)
    assert report["pass"] is False
    identity_check = next(
        check for check in report["checks"] if check["name"] == "immutable Receiver Identity"
    )
    assert identity_check["pass"] is False


def test_verifier_rejects_checksum_mismatch(tmp_path):
    bundle = build_bundle(tmp_path)
    (bundle / "api" / "create-receivers.json").write_text("{}\n")

    report = verify_bundle(bundle)

    assert report["pass"] is False
    checksum_check = next(
        check for check in report["checks"] if check["name"] == "bundle checksums"
    )
    assert checksum_check["pass"] is False
    assert "api/create-receivers.json" in checksum_check["detail"]


def test_verifier_rejects_empty_discovery_snapshot(tmp_path):
    bundle = build_bundle(tmp_path)
    write_json(bundle / "discovery" / "create-adapter.json", [])
    write_checksums(bundle)

    report = verify_bundle(bundle)

    assert report["pass"] is False
    discovery_check = next(
        check for check in report["checks"] if check["name"] == "create adapter discovery"
    )
    assert discovery_check["pass"] is False


def test_verifier_rejects_tooling_commit_mismatch(tmp_path):
    bundle = build_bundle(tmp_path)
    github_path = bundle / "ci" / "github.json"
    github = json.loads(github_path.read_text())
    github["head_sha"] = "3" * 40
    write_json(github_path, github)
    write_checksums(bundle)

    report = verify_bundle(bundle)

    assert report["pass"] is False
    source_check = next(
        check for check in report["checks"] if check["name"] == "tooling source binding"
    )
    assert source_check["pass"] is False
