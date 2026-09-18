import json
import re

from tools import check_release_readiness as readiness


def workflow_job(source: str, name: str) -> str:
    match = re.search(
        rf"^  {re.escape(name)}:\n(?P<body>.*?)(?=^  [a-z0-9-]+:\n|\Z)",
        source,
        flags=re.MULTILINE | re.DOTALL,
    )
    assert match is not None, f"workflow job {name} was not found"
    return match.group("body")


def test_repository_release_checks_pass():
    assert [check.detail for check in readiness.repository_checks() if not check.passed] == []


def test_frontend_ci_installs_local_sdk_dependencies_first():
    workflow = (readiness.ROOT / ".github/workflows/reproducibility.yml").read_text(
        encoding="utf-8"
    )
    sdk_install = "working-directory: sdk/typescript\n        run: npm ci"

    for job_name, frontend_step in (
        ("frontend-build", "- name: Install locked frontend dependencies"),
        ("frontend-browser", "- name: Install locked application dependencies"),
    ):
        job = workflow_job(workflow, job_name)
        assert sdk_install in job
        assert job.index(sdk_install) < job.index(frontend_step)


def test_stable_release_rejects_incomplete_example_manifest():
    checks = readiness.stable_release_checks(
        readiness.ROOT / "release" / "release.example.json",
        release_ref="v1.0.0",
    )

    failed = {check.name for check in checks if not check.passed}
    assert "release manifest version" in failed
    assert "independent security review" in failed
    assert "immutable signed lifecycle evidence" in failed
    assert "reviewed binary matches lifecycle deployment" in failed
    assert "browser and accessibility evidence" in failed


def test_stable_release_requires_hardened_operations(tmp_path):
    manifest = json.loads(
        (readiness.ROOT / "release" / "release.example.json").read_text(encoding="utf-8")
    )
    manifest["release_version"] = "v1.0.0"
    manifest["operations"]["rate_limit_enabled"] = False
    path = tmp_path / "release.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    checks = readiness.stable_release_checks(path, release_ref="v1.0.0")

    operations = next(check for check in checks if check.name == "production operation settings")
    assert operations.passed is False


def test_public_https_url_rejects_local_private_and_placeholder_hosts():
    assert readiness.is_public_https_url("https://registry.aircraft-malt.org") is True
    assert readiness.is_public_https_url("http://registry.aircraft-malt.org") is False
    assert readiness.is_public_https_url("https://localhost") is False
    assert readiness.is_public_https_url("https://127.0.0.1") is False
    assert readiness.is_public_https_url("https://10.0.0.1") is False
    assert readiness.is_public_https_url("https://release-host.example") is False
    assert readiness.is_public_https_url("https://registry.example.org") is False
