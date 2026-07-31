import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run_reproducible_benchmark.py"


def run_bundle(output: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(RUNNER), "--output-dir", str(output), *extra],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def bundle_bytes(bundle: Path) -> dict[str, bytes]:
    return {
        path.relative_to(bundle).as_posix(): path.read_bytes()
        for path in bundle.rglob("*")
        if path.is_file()
    }


def test_reproducible_benchmark_is_byte_identical(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"

    first_run = run_bundle(first)
    second_run = run_bundle(second)

    assert first_run.returncode == 0, first_run.stderr
    assert second_run.returncode == 0, second_run.stderr
    assert bundle_bytes(first) == bundle_bytes(second)
    assert json.loads(first_run.stdout)["pass"] is True


def test_reproducible_benchmark_cannot_claim_live_validation(tmp_path):
    bundle = tmp_path / "bundle"
    result = run_bundle(bundle)

    assert result.returncode == 0, result.stderr
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    report = json.loads((bundle / "accuracy.json").read_text(encoding="utf-8"))
    assert manifest["deterministic"] is True
    assert manifest["live_validation"] is False
    assert report["evidence_status"] == "pipeline_only"
    assert report["provenance"]["benchmarkable"] is False
    assert report["provenance"]["data_provenance"] == "synthetic"
    assert report["matched_records"] == 3


def test_reproducible_benchmark_verifier_detects_tampering(tmp_path):
    bundle = tmp_path / "bundle"
    assert run_bundle(bundle).returncode == 0
    with (bundle / "accuracy.json").open("a", encoding="utf-8") as handle:
        handle.write(" ")

    result = run_bundle(bundle, "--verify-only")

    assert result.returncode != 0
    assert "Checksum mismatch for accuracy.json" in result.stderr
