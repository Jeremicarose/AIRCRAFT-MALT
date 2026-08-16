#!/usr/bin/env python3
"""Build and verify the byte-reproducible benchmark evidence bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "tools" / "mlat"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from benchmark_mlat_against_reference import build_report, load_jsonl  # noqa: E402

GENERATED_AT = "2024-03-09T16:00:03Z"
DEFAULT_BUNDLE = ROOT / "evidence" / "mlat-reference" / "reproducible-benchmark-v1"
FIXTURES = ROOT / "reference" / "mlat" / "benchmarks" / "fixtures"
PACKAGE_SOURCES = {
    "inputs/mlat.jsonl": FIXTURES / "reproducible-mlat.jsonl",
    "inputs/readiness.json": ROOT
    / "reference"
    / "mlat"
    / "benchmarks"
    / "fixtures"
    / "reproducible-readiness.json",
    "inputs/reference.jsonl": ROOT
    / "reference"
    / "mlat"
    / "benchmarks"
    / "fixtures"
    / "reproducible-reference.jsonl",
    "source/Dockerfile": ROOT / "Dockerfile",
    "source/benchmark_mlat_against_reference.py": ROOT
    / "tools"
    / "mlat"
    / "benchmark_mlat_against_reference.py",
    "source/pyproject.toml": ROOT / "pyproject.toml",
    "source/python-version.txt": ROOT / ".python-version",
    "source/requirements-build.in": ROOT / "requirements-build.in",
    "source/requirements-dev.lock": ROOT / "requirements-dev.lock",
    "source/requirements.lock": ROOT / "requirements.lock",
    "source/reproducibility-workflow.yml": ROOT / ".github" / "workflows" / "reproducibility.yml",
    "source/run_reproducible_benchmark.py": Path(__file__).resolve(),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def canonicalize(value: Any) -> Any:
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("Benchmark output contains a non-finite number")
        rounded = round(value, 9)
        return 0.0 if rounded == 0 else rounded
    if isinstance(value, list):
        return [canonicalize(item) for item in value]
    if isinstance(value, dict):
        return {key: canonicalize(item) for key, item in value.items()}
    return value


def copy_sources(bundle: Path) -> None:
    for relative, source in PACKAGE_SOURCES.items():
        if not source.is_file():
            raise FileNotFoundError(f"Required reproducibility source is missing: {source}")
        destination = bundle / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)


def artifact_metadata(bundle: Path, relative_paths: set[str]) -> dict[str, dict[str, int | str]]:
    return {
        relative: {
            "bytes": (bundle / relative).stat().st_size,
            "sha256": sha256(bundle / relative),
        }
        for relative in sorted(relative_paths)
    }


def build_bundle(bundle: Path) -> dict[str, Any]:
    bundle.mkdir(parents=True, exist_ok=True)
    copy_sources(bundle)

    mlat_path = bundle / "inputs" / "mlat.jsonl"
    reference_path = bundle / "inputs" / "reference.jsonl"
    readiness_path = bundle / "inputs" / "readiness.json"
    readiness = json.loads(readiness_path.read_text(encoding="utf-8"))
    report = build_report(
        load_jsonl(mlat_path),
        load_jsonl(reference_path),
        mlat_path=mlat_path,
        reference_path=reference_path,
        time_tolerance_seconds=0.25,
        reference_source="deterministic-fixture",
        region="fixture-grid",
        data_provenance="synthetic",
        runtime_snapshot=readiness,
        runtime_snapshot_path=readiness_path,
    )
    report["generated_at"] = GENERATED_AT
    report["provenance"]["fixture"] = True
    report["provenance"][
        "claim_scope"
    ] = "Deterministic regression evidence only; not live receiver or accuracy proof."
    report = canonicalize(report)
    write_json(bundle / "accuracy.json", report)

    packaged = set(PACKAGE_SOURCES) | {"accuracy.json"}
    manifest = {
        "schema_version": 1,
        "benchmark_id": "mlat-reference-matching-v1",
        "generated_at": GENERATED_AT,
        "deterministic": True,
        "live_validation": False,
        "claim_scope": "Algorithm and evidence-format reproducibility using synthetic fixtures.",
        "python_target": (bundle / "source" / "python-version.txt")
        .read_text(encoding="utf-8")
        .strip(),
        "artifacts": artifact_metadata(bundle, packaged),
    }
    write_json(bundle / "manifest.json", manifest)

    checksum_targets = packaged | {"manifest.json"}
    checksums = "\n".join(
        f"{sha256(bundle / relative)}  {relative}" for relative in sorted(checksum_targets)
    )
    (bundle / "checksums.sha256").write_text(checksums + "\n", encoding="ascii")
    return manifest


def expected_bundle_files() -> set[str]:
    return set(PACKAGE_SOURCES) | {"accuracy.json", "manifest.json", "checksums.sha256"}


def verify_bundle(bundle: Path) -> dict[str, Any]:
    if not bundle.is_dir():
        raise ValueError(f"Benchmark bundle does not exist: {bundle}")
    actual_files = {
        path.relative_to(bundle).as_posix() for path in bundle.rglob("*") if path.is_file()
    }
    expected_files = expected_bundle_files()
    if actual_files != expected_files:
        missing = sorted(expected_files - actual_files)
        unexpected = sorted(actual_files - expected_files)
        raise ValueError(f"Bundle file set mismatch; missing={missing}, unexpected={unexpected}")

    checksum_path = bundle / "checksums.sha256"
    checksum_entries: dict[str, str] = {}
    for line_number, line in enumerate(
        checksum_path.read_text(encoding="ascii").splitlines(), start=1
    ):
        try:
            expected_hash, relative = line.split("  ", 1)
        except ValueError as exc:
            raise ValueError(f"Malformed checksum line {line_number}") from exc
        if Path(relative).is_absolute() or ".." in Path(relative).parts:
            raise ValueError(f"Unsafe checksum path: {relative}")
        checksum_entries[relative] = expected_hash

    expected_checksum_files = expected_files - {"checksums.sha256"}
    if set(checksum_entries) != expected_checksum_files:
        raise ValueError("Checksum file does not cover the complete bundle")
    for relative, expected_hash in checksum_entries.items():
        observed_hash = sha256(bundle / relative)
        if observed_hash != expected_hash:
            raise ValueError(
                f"Checksum mismatch for {relative}: "
                f"expected {expected_hash}, observed {observed_hash}"
            )

    for relative, source in PACKAGE_SOURCES.items():
        if sha256(bundle / relative) != sha256(source):
            raise ValueError(f"Packaged source is stale: {relative}")

    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("deterministic") is not True or manifest.get("live_validation") is not False:
        raise ValueError("Manifest claim scope is invalid")
    if set(manifest.get("artifacts", {})) != set(PACKAGE_SOURCES) | {"accuracy.json"}:
        raise ValueError("Manifest artifact coverage is incomplete")
    for relative, metadata in manifest["artifacts"].items():
        if metadata.get("sha256") != sha256(bundle / relative):
            raise ValueError(f"Manifest hash mismatch for {relative}")
        if metadata.get("bytes") != (bundle / relative).stat().st_size:
            raise ValueError(f"Manifest byte count mismatch for {relative}")

    report = json.loads((bundle / "accuracy.json").read_text(encoding="utf-8"))
    provenance = report.get("provenance", {})
    if report.get("evidence_status") != "pipeline_only":
        raise ValueError("Synthetic fixture must remain pipeline-only evidence")
    if (
        provenance.get("benchmarkable") is not False
        or provenance.get("data_provenance") != "synthetic"
    ):
        raise ValueError("Synthetic fixture was incorrectly labelled as benchmarkable or live")

    return {
        "bundle": str(bundle),
        "bundle_sha256": sha256(checksum_path),
        "files_verified": len(checksum_entries),
        "pass": True,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_BUNDLE)
    parser.add_argument("--verify-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    bundle = args.output_dir.resolve()
    if not args.verify_only:
        build_bundle(bundle)
    result = verify_bundle(bundle)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
