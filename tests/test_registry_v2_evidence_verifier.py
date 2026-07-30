import hashlib
import json

from scripts.verify_registry_v2_evidence import verify_bundle


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value) + "\n")


def transaction_response(tx_hash, parent_hash, sequence, owner, identity, code_hash, status):
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
            "hash": tx_hash,
            "inputs": [
                {
                    "previous_output": {
                        "tx_hash": parent_hash,
                        "index": "0x0",
                    }
                }
            ],
            "outputs": [
                {
                    "capacity": "0x1",
                    "lock": {"args": owner},
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
    hashes = {name: "0x" + f"{index:02x}" * 32 for index, name in enumerate(
        ("deployment", "create", "update", "transfer", "revoke"), start=1
    )}
    identity = "0x" + "aa" * 32
    code_hash = "0x" + "bb" * 32
    owner_a = "0x" + "11" * 20
    owner_b = "0x" + "22" * 20
    write_json(
        bundle / "manifest.json",
        {
            "status": "complete",
            "contract": {
                "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
                "binary_ckb_data_hash": "0x" + ckb_digest,
                "type_script_hash_for_registry_code_hash": code_hash,
            },
            "receiver": {
                "identity_id": identity,
                "owner_a": {"lock_arg": owner_a},
                "owner_b": {"lock_arg": owner_b},
            },
            "lifecycle_funding": {
                "out_point": {"tx_hash": hashes["deployment"], "index": "0x0"}
            },
            "accepted_transactions": hashes,
            "rejected_attacks": [],
            "rpc_url": "https://testnet.invalid/rpc",
            "private_keys_included": False,
        },
    )
    write_json(bundle / "ci" / "local.json", {"pass": True})
    write_json(
        bundle / "ci" / "github.json",
        {
            "status": "completed",
            "conclusion": "success",
            "artifact": {
                "receiver_registry_sha256": hashlib.sha256(binary.read_bytes()).hexdigest()
            },
        },
    )
    write_json(
        bundle / "rpc" / "deployment-transaction.json",
        {"transaction": {"hash": hashes["deployment"]}, "tx_status": {"status": "committed"}},
    )
    stages = ("create", "update", "transfer", "revoke")
    parents = (hashes["deployment"], hashes["create"], hashes["update"], hashes["transfer"])
    owners = (owner_a, owner_a, owner_b, owner_b)
    statuses = ("online", "online", "online", "revoked")
    for sequence, (stage, parent, owner, status) in enumerate(zip(stages, parents, owners, statuses)):
        write_json(
            bundle / "rpc" / f"{stage}-transaction.json",
            transaction_response(
                hashes[stage], parent, sequence, owner, identity, code_hash, status
            ),
        )
        write_json(bundle / "discovery" / f"{stage}-indexer.json", {})
        write_json(bundle / "discovery" / f"{stage}-adapter.json", [])
    for stage, count in (("create", 1), ("update", 1), ("transfer", 1), ("revoke", 0)):
        write_json(
            bundle / "api" / f"{stage}-receivers.json",
            {"status_code": 200, "body": {"count": count}},
        )
    return bundle


def test_verifier_accepts_complete_consistent_bundle(tmp_path):
    report = verify_bundle(build_bundle(tmp_path))
    assert report["pass"] is True


def test_verifier_rejects_identity_mutation(tmp_path):
    bundle = build_bundle(tmp_path)
    transfer_path = bundle / "rpc" / "transfer-transaction.json"
    transfer = json.loads(transfer_path.read_text())
    transfer["transaction"]["outputs"][0]["type"]["args"] = "0x" + "cc" * 32
    write_json(transfer_path, transfer)

    report = verify_bundle(bundle)
    assert report["pass"] is False
    identity_check = next(check for check in report["checks"] if check["name"] == "immutable Receiver Identity")
    assert identity_check["pass"] is False
