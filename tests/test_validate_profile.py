"""Deterministic tests for skills/init/scripts/validate_profile.py against the fixture repositories."""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tests.conftest import FIXTURES, PLUGIN

SCRIPT = PLUGIN / "skills" / "init" / "scripts" / "validate_profile.py"


def load_module():
    spec = importlib.util.spec_from_file_location("validate_profile", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


vp = load_module()


def run(fixture: str, *args: str) -> tuple[int, dict]:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(FIXTURES / fixture), "--json", *args],
        capture_output=True, text=True,
    )
    return proc.returncode, json.loads(proc.stdout)


def test_complete_profile_is_ready_everywhere():
    code, payload = run("app-docker")
    statuses = {name: cap["status"] for name, cap in payload["capabilities"].items()}
    assert statuses == {name: "ready" for name in vp.CAPABILITIES}, statuses
    assert code == 0
    assert payload["errors"] == []


def test_todo_trigger_blocks_release_and_absent_tables_are_not_applicable():
    code, payload = run("pypi-library")
    caps = payload["capabilities"]
    assert caps["release"]["status"] == "incomplete"
    assert "release.distribution_trigger" in caps["release"]["todos"]
    assert caps["smoke-e2e"]["status"] == "not-applicable"
    assert caps["process-discussions"]["status"] == "not-applicable"
    assert caps["triage"]["status"] == "ready"
    assert any("preset" in a for a in caps["triage"]["assumed"])
    assert caps["review-pr"]["status"] == "ready"
    assert code == 1


def test_missing_profile_reports_read_only_capabilities():
    code, payload = run("no-profile")
    assert code == 2
    assert payload["profile"] is None
    caps = payload["capabilities"]
    assert caps["review-pr"]["status"] == "ready"
    assert caps["triage"]["status"] == "ready"
    assert caps["release"]["status"] == "incomplete"
    assert ".maintainer/profile.toml" in caps["release"]["missing"]


def test_overlay_applies_preferences_and_rejects_policy():
    code, payload = run("overlay-override")
    overlay = payload["overlay"]
    assert "smoke.api_url" in overlay["applied"]
    assert "upstreams.example-lib" in overlay["applied"]
    assert "release.gates.mandatory" in overlay["rejected"]
    effective = payload["effective_profile"]
    assert effective["smoke"]["api_url"] == "http://localhost:9999"
    assert effective["release"]["gates"]["mandatory"] == ["validator", "notes-approved"]
    assert payload["capabilities"]["release"]["status"] == "ready"
    assert any("example-lib" in w for w in payload["capabilities"]["init"]["warnings"])
    assert code == 0


def test_single_capability_selection():
    code, payload = run("pypi-library", "--capability", "review-pr")
    assert list(payload["capabilities"]) == ["review-pr"]
    assert code == 0


@pytest.fixture
def scratch(tmp_path: Path) -> Path:
    shutil.copytree(FIXTURES / "app-docker", tmp_path / "repo")
    return tmp_path / "repo"


def rewrite(root: Path, old: str, new: str) -> None:
    profile = root / ".maintainer" / "profile.toml"
    text = profile.read_text()
    assert old in text
    profile.write_text(text.replace(old, new))


def test_unknown_schema_version_is_an_error(scratch: Path):
    rewrite(scratch, "schema_version = 1", "schema_version = 7")
    report, _, code = vp.validate(scratch, vp.CAPABILITIES)
    assert code == 1
    assert any("schema_version" in e for e in report.errors)


def test_confirm_marker_needs_confirmation(scratch: Path):
    rewrite(scratch, 'distribution_trigger = "gh release create"', 'distribution_trigger = "CONFIRM: gh release create"')
    report, _, code = vp.validate(scratch, ["release"])
    cap = report.capabilities["release"]
    assert cap["status"] == "needs-confirmation"
    assert cap["confirm"] == ["release.distribution_trigger"]
    assert code == 1


def test_absolute_and_missing_paths_are_rejected(scratch: Path):
    rewrite(scratch, 'changelog = "CHANGELOG.md"', 'changelog = "/etc/CHANGELOG.md"')
    rewrite(scratch, 'version_files = ["pyproject.toml"]', 'version_files = ["pyproject.toml", "missing.toml"]')
    report, _, _ = vp.validate(scratch, ["release"])
    missing = report.capabilities["release"]["missing"]
    assert any("absolute path" in m for m in missing)
    assert any("missing.toml" in m for m in missing)


def test_unknown_gate_and_bad_timeout_are_reported(scratch: Path):
    rewrite(scratch, 'mandatory = ["validator", "image-gate", "bucket-c", "notes-approved"]', 'mandatory = ["validator", "typo-gate"]')
    rewrite(scratch, 'timeout = "20m"', 'timeout = "twenty"')
    report, _, _ = vp.validate(scratch, ["release"])
    missing = report.capabilities["release"]["missing"]
    assert any("typo-gate" in m for m in missing)
    assert any("timeout" in m for m in missing)


def test_unknown_archetype_value_is_rejected(scratch: Path):
    rewrite(scratch, 'artifact = "app-docker"', 'artifact = "app-kubernetes"')
    report, _, _ = vp.validate(scratch, ["release"])
    assert any("project.artifact" in m for m in report.capabilities["release"]["missing"])


def test_unparsable_profile_exits_2(scratch: Path):
    (scratch / ".maintainer" / "profile.toml").write_text("schema_version = [unclosed\n")
    report, profile, code = vp.validate(scratch, vp.CAPABILITIES)
    assert code == 2 and profile is None
    assert any("parsed" in e for e in report.errors)


def test_text_output_lists_every_capability():
    proc = subprocess.run([sys.executable, str(SCRIPT), "--root", str(FIXTURES / "app-docker")], capture_output=True, text=True)
    assert proc.returncode == 0
    for name in vp.CAPABILITIES:
        assert name in proc.stdout
