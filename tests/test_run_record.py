"""Tests for skills/release/scripts/run_record.py: create, update, authorize, invalidate, resume."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

from tests.conftest import PLUGIN

SCRIPT = PLUGIN / "skills" / "release" / "scripts" / "run_record.py"


def load_module():
    spec = importlib.util.spec_from_file_location("run_record", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rr = load_module()


def run(*args: str) -> tuple[int, str]:
    proc = subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)
    return proc.returncode, proc.stdout.strip()


def new_record(root: Path, version: str = "1.4.0", commit: str = "abc123") -> Path:
    (root / ".maintainer").mkdir(parents=True, exist_ok=True)
    (root / ".maintainer" / "profile.toml").write_text("schema_version = 1\n")
    code, out = run("new", "--root", str(root), "--skill", "release", "--version", version, "--commit", commit, "--engine-version", "0.1.0")
    assert code == 0
    return Path(out)


def test_new_record_has_the_envelope(tmp_path: Path):
    path = new_record(tmp_path)
    record = json.loads(path.read_text())
    assert record["skill"] == "release"
    assert record["candidate"] == {"version": "1.4.0", "commit": "abc123", "digests": {}}
    assert record["profile_hash"].startswith("sha256:")
    assert record["verdict"] is None
    assert path.parent == tmp_path / ".maintainer" / "state" / "runs"


def test_update_checks_and_pending(tmp_path: Path):
    path = new_record(tmp_path)
    code, _ = run("update", str(path), "--phase", "artifact-gate", "--status", "passed", "--check", "image-gate=passed:reports/gate.log")
    assert code == 0
    code, _ = run("update", str(path), "--phase", "publish", "--status", "failed",
                  "--check", "registry-a=passed:manifest", "--check", "registry-b=failed:push timeout")
    assert code == 0
    code, out = run("pending", str(path))
    pend = json.loads(out)
    names = [p["phase"] for p in pend]
    assert "artifact-gate" not in names
    publish = next(p for p in pend if p["phase"] == "publish")
    assert [c["name"] for c in publish["checks"]] == ["registry-b"]
    assert names[0] == "scope"


def test_authorization_must_name_the_candidate(tmp_path: Path):
    path = new_record(tmp_path)
    code, _ = run("authorize", str(path), "--scope", "publish via make tag", "--candidate", "zzz999")
    assert code == 1
    code, _ = run("authorize", str(path), "--scope", "publish via make tag", "--candidate", "abc123")
    assert code == 0
    record = json.loads(path.read_text())
    go = next(p for p in record["phases"] if p["name"] == "go")
    assert go["authorizations"][0]["scope"] == "publish via make tag"


def test_candidate_change_invalidates_checks_and_authorizations(tmp_path: Path):
    path = new_record(tmp_path)
    run("update", str(path), "--phase", "scope", "--status", "passed")
    run("update", str(path), "--phase", "artifact-gate", "--status", "passed", "--check", "image-gate=passed:log")
    run("authorize", str(path), "--scope", "publish", "--candidate", "abc123")
    code, out = run("candidate", str(path), "--commit", "def456")
    assert code == 0 and "1 checks reset" in out
    record = json.loads(path.read_text())
    gate = next(p for p in record["phases"] if p["name"] == "artifact-gate")
    assert gate["status"] == "not-run"
    assert gate["checks"][0]["status"] == "not-run"
    assert gate["checks"][0]["invalidated_by"] == "def456"
    go = next(p for p in record["phases"] if p["name"] == "go")
    assert go["authorizations"][0]["revoked"] is True
    scope = next(p for p in record["phases"] if p["name"] == "scope")
    assert scope["status"] == "passed"


def test_latest_filters_by_version_and_finish_sets_verdict(tmp_path: Path):
    first = new_record(tmp_path, version="1.4.0")
    second = new_record(tmp_path, version="1.5.0", commit="fff000")
    code, out = run("latest", "--root", str(tmp_path), "--skill", "release", "--version", "1.4.0")
    assert code == 0 and json.loads(out)["path"] == str(first)
    code, out = run("latest", "--root", str(tmp_path), "--skill", "release")
    assert json.loads(out)["path"] == str(second)
    code, out = run("finish", str(second), "--verdict", "aborted", "--note", "owner postponed")
    assert code == 0
    record = json.loads(second.read_text())
    assert record["verdict"] == "aborted" and record["finished_at"]
    assert "owner postponed" in record["notes"]
    code, _ = run("finish", str(second), "--verdict", "MAYBE")
    assert code == 2


def test_latest_without_records_returns_null(tmp_path: Path):
    code, out = run("latest", "--root", str(tmp_path))
    assert code == 1 and out == "null"
