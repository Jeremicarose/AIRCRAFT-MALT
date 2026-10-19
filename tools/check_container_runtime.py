#!/usr/bin/env python3
"""Exercise built backend/frontend images locally without publishing or using secrets."""

import argparse
import json
from pathlib import Path
import subprocess
import time
import urllib.request
import uuid


def command(*args):
    return subprocess.check_output(["docker", *args], text=True).strip()


def wait_http(url, expected_service=None):
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=3) as response:
                payload = json.load(response)
            if expected_service is None or payload.get("service") == expected_service:
                return payload
        except (OSError, ValueError):
            pass
        time.sleep(0.5)
    raise RuntimeError(f"Container did not become healthy at {url}")


def wait_positions(base):
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        rows = wait_http(base + "/api/positions/recent").get("positions", [])
        if rows:
            assert all(row["data_provenance"] == "SYNTHETIC" for row in rows)
            return rows
        time.sleep(0.5)
    raise RuntimeError("Synthetic processor did not deliver a stored solution through the API")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend-image", default="mlat-system:ci")
    parser.add_argument("--frontend-image", default="mlat-frontend:ci")
    parser.add_argument("--output", type=Path, default=Path("artifacts/container-smoke.json"))
    args = parser.parse_args()
    suffix = uuid.uuid4().hex[:10]
    network, volume, backend, frontend, processor, restored = (
        f"mlat-smoke-{suffix}-{name}"
        for name in ("network", "data", "api", "web", "processor", "restore")
    )
    created = []
    report = {
        "status": "NOT RUN",
        "data_provenance": "SYNTHETIC",
        "checks": {},
        "limitations": [
            "Local container validation, not a production deployment or physical receiver campaign.",
            "Restore uses the same candidate image; application-version rollback requires a separately approved previous image.",
        ],
    }
    try:
        command("info")
        report["image_ids"] = {
            "backend": command("image", "inspect", "--format", "{{.Id}}", args.backend_image),
            "frontend": command("image", "inspect", "--format", "{{.Id}}", args.frontend_image),
        }
        command("network", "create", network)
        created.append(("network", network))
        command("volume", "create", volume)
        created.append(("volume", volume))
        command(
            "run",
            "--pull=never",
            "-d",
            "--init",
            "--name",
            backend,
            "--network",
            network,
            "--mount",
            f"type=volume,src={volume},dst=/app/data",
            "-p",
            "127.0.0.1::5000",
            "-e",
            "DATABASE_PATH=/app/data/smoke.db",
            "-e",
            "FOURDSKY_TRANSPORT=simulation",
            "-e",
            "DEMO_MODE=true",
            "-e",
            "ENABLE_BACKGROUND_BROADCASTER=false",
            args.backend_image,
            "mlat-api",
        )
        created.append(("container", backend))
        api_port = command("port", backend, "5000/tcp").rsplit(":", 1)[1]
        base = f"http://127.0.0.1:{api_port}"
        wait_http(base + "/healthz", "MLAT API")
        uid = int(command("exec", backend, "id", "-u"))
        assert uid != 0
        report["checks"]["backend_non_root_uid"] = uid
        report["checks"]["solver_evidence_available"] = (
            wait_http(base + "/api/evidence/solver-benchmark/latest")["compact_dataset"][
                "event_counts"
            ]["total"]
            == 362
        )
        command(
            "run",
            "--pull=never",
            "-d",
            "--init",
            "--name",
            processor,
            "--network",
            network,
            "--mount",
            f"type=volume,src={volume},dst=/app/data",
            "-e",
            "DATABASE_PATH=/app/data/smoke.db",
            "-e",
            "MLAT_ENV_FILE=/dev/null",
            "-e",
            "FOURDSKY_TRANSPORT=simulation",
            "-e",
            "DEMO_MODE=true",
            "-e",
            "SIMULATE_IF_UNAVAILABLE=true",
            "-e",
            "STATS_INTERVAL_SECONDS=5",
            args.backend_image,
            "mlat-processor",
        )
        created.append(("container", processor))
        before = wait_positions(base)
        assert int(command("exec", processor, "id", "-u")) != 0
        report["checks"]["processor_to_storage_to_api"] = True
        command("stop", "--time", "10", processor)
        assert command("inspect", "--format", "{{.State.ExitCode}}", processor) == "0"
        before = wait_positions(base)
        command("restart", "--time", "10", backend)
        # Docker can allocate a new host port for an ephemeral binding on restart.
        api_port = command("port", backend, "5000/tcp").rsplit(":", 1)[1]
        base = f"http://127.0.0.1:{api_port}"
        wait_http(base + "/healthz")
        assert wait_http(base + "/api/positions/recent")["positions"][0]["id"] == before[0]["id"]
        report["checks"]["persistence_after_restart"] = True
        api_log = subprocess.run(
            ["docker", "logs", backend], capture_output=True, text=True, check=True
        )
        assert (
            "Control server error" not in api_log.stdout + api_log.stderr
        ), "Gunicorn control socket failed under the non-root API user"
        report["checks"]["non_root_control_socket_startup"] = True
        for operation, source, destination in (
            ("backup", "/app/data/smoke.db", "/app/data/backup.db"),
            ("restore", "/app/data/backup.db", "/app/data/restored.db"),
        ):
            result = json.loads(
                command(
                    "exec",
                    backend,
                    "python",
                    "/app/tools/mlat/database_snapshot.py",
                    operation,
                    "--source",
                    source,
                    "--destination",
                    destination,
                )
            )
            assert result["status"] == "PASS" and result["integrity"] == "ok"
        command(
            "run",
            "--pull=never",
            "-d",
            "--init",
            "--name",
            restored,
            "--network",
            network,
            "--mount",
            f"type=volume,src={volume},dst=/app/data",
            "-p",
            "127.0.0.1::5000",
            "-e",
            "DATABASE_PATH=/app/data/restored.db",
            "-e",
            "FOURDSKY_TRANSPORT=simulation",
            "-e",
            "DEMO_MODE=true",
            "-e",
            "ENABLE_BACKGROUND_BROADCASTER=false",
            args.backend_image,
            "mlat-api",
        )
        created.append(("container", restored))
        restore_port = command("port", restored, "5000/tcp").rsplit(":", 1)[1]
        restored_rows = wait_positions(f"http://127.0.0.1:{restore_port}")
        assert {row["id"] for row in restored_rows} == {row["id"] for row in before}
        report["checks"]["backup_restore_and_restarted_api"] = True
        command(
            "run",
            "--pull=never",
            "-d",
            "--init",
            "--name",
            frontend,
            "--network",
            network,
            "-p",
            "127.0.0.1::3000",
            "-e",
            f"MLAT_API_INTERNAL_URL=http://{backend}:5000",
            args.frontend_image,
        )
        created.append(("container", frontend))
        web_port = command("port", frontend, "3000/tcp").rsplit(":", 1)[1]
        wait_http(f"http://127.0.0.1:{web_port}/healthz", "receiver-registry-operations")
        assert int(command("exec", frontend, "id", "-u")) != 0
        assert (
            wait_http(f"http://127.0.0.1:{web_port}/api/positions/recent")["positions"][0][
                "data_provenance"
            ]
            == "SYNTHETIC"
        )
        report["checks"]["frontend_build_and_proxy"] = True
        command("stop", "--time", "10", backend)
        assert command("inspect", "--format", "{{.State.ExitCode}}", backend) == "0"
        report["checks"]["graceful_api_shutdown"] = True
        assert all(report["checks"].values())
        report["status"] = "PASS"
    except FileNotFoundError:
        report.update(status="BLOCKED", reason="Docker executable is unavailable")
    except (
        OSError,
        ValueError,
        AssertionError,
        subprocess.CalledProcessError,
        RuntimeError,
    ) as exc:
        report.update(status="FAIL", reason=str(exc))
    finally:
        for kind, name in reversed(created):
            if kind == "container":
                log = subprocess.run(
                    ["docker", "logs", "--tail", "30", name], capture_output=True, text=True
                )
                report.setdefault("container_logs", {})[name] = log.stdout + log.stderr
                subprocess.run(["docker", "rm", "-f", name], capture_output=True)
            else:
                subprocess.run(["docker", kind, "rm", name], capture_output=True)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
