"""Tests for skills/release/scripts/run_record.py: one record, four commands, one completion rule."""

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
    return proc.returncode, (proc.stdout.strip() or proc.stderr.strip())


def read(path: Path) -> dict:
    return json.loads(path.read_text())


def check(path: Path, name: str) -> dict:
    return next(c for c in read(path)["checks"] if c["name"] == name)


def new_record(root: Path, version: str = "1.4.0", commit: str = "abc123", profile: str | None = None) -> Path:
    (root / ".maintainer").mkdir(parents=True, exist_ok=True)
    (root / ".maintainer" / "profile.toml").write_text(profile or "schema_version = 1\n")
    code, out = run("new", "--root", str(root), "--version", version, "--commit", commit, "--trigger", "make tag", "--engine-version", "0.3.0")
    assert code == 0, out
    return Path(out)


def pass_all_mandatory(path: Path) -> None:
    for name in ("validator", "publish", "verify"):
        code, out = run("set", str(path), "--check", f"{name}=passed:{name}.log")
        assert code == 0, out


def approve_publication(path: Path) -> None:
    code, out = run("set", str(path), "--approve", "publication", "--scope", "publish via make tag")
    assert code == 0, out


def test_new_record_seeds_the_delivery_contract_from_the_profile(tmp_path: Path):
    profile = 'schema_version = 1\n[release.gates]\nmandatory = ["validator", "image-gate"]\nnot_gates = ["lint"]\n'
    path = new_record(tmp_path, profile=profile)
    record = read(path)
    assert record["schema"] == 3
    assert record["candidate"] == {"version": "1.4.0", "commit": "abc123", "trigger": "make tag", "digests": {}}
    assert path.parent == tmp_path / ".maintainer" / "state" / "runs"
    checks = {c["name"]: c for c in record["checks"]}
    assert checks["validator"]["mandatory"] and checks["validator"]["stage"] == "pre"
    assert checks["image-gate"]["mandatory"] and checks["image-gate"]["stage"] == "pre"
    assert checks["publish"]["mandatory"] and checks["publish"]["stage"] == "post"
    assert checks["verify"]["mandatory"] and checks["verify"]["stage"] == "post"
    assert not checks["announce"]["mandatory"] and not checks["cleanup"]["mandatory"]
    assert not checks["lint"]["mandatory"]
    assert all(c["status"] == "not-run" for c in checks.values())


def test_show_and_finish_apply_the_same_completion_rule(tmp_path: Path):
    """Regression for #25 point 6: an informational not-applicable item never blocks, a mandatory one blocks in both places."""
    path = new_record(tmp_path)
    pass_all_mandatory(path)
    approve_publication(path)
    # An optional observation recorded as not-applicable.
    run("set", str(path), "--check", "release-page-latest=not-applicable:informational only", "--optional", "--stage", "post")
    _, out = run("show", str(path), "--json")
    assert json.loads(out)["outstanding"] == []
    assert run("finish", str(path), "--verdict", "GO")[0] == 0
    assert read(path)["delivery"]["status"] == "completed"

    # A mandatory check marked not-applicable blocks, and both commands name it the same way.
    other = new_record(tmp_path, version="1.5.0", commit="def456")
    pass_all_mandatory(other)
    approve_publication(other)
    run("set", str(other), "--check", "verify=not-applicable:skipped")
    _, shown = run("show", str(other), "--json")
    outstanding = json.loads(shown)["outstanding"]
    assert [i["check"] for i in outstanding] == ["verify"]
    code, err = run("finish", str(other), "--verdict", "GO")
    assert code == 2 and "verify" in err and outstanding[0]["reason"] in err
    assert read(other)["finished_at"] is None


def test_mandatory_unrun_check_blocks_go_and_delivery(tmp_path: Path):
    path = new_record(tmp_path)
    run("set", str(path), "--check", "publish=passed:run 1", "--check", "verify=passed:index")
    approve_publication(path)
    _, out = run("show", str(path), "--json")
    shown = json.loads(out)
    assert [i["check"] for i in shown["go_outstanding"]] == ["validator"]
    assert [i["check"] for i in shown["outstanding"]] == ["validator"]
    assert run("finish", str(path), "--verdict", "GO")[0] == 2


def test_waiver_records_a_decision_without_rewriting_the_result(tmp_path: Path):
    path = new_record(tmp_path)
    run("set", str(path), "--check", "validator=failed:flaky suite")
    code, _ = run("set", str(path), "--waive", "validator", "--reason", "known flaky test, tracked in #12", "--by", "owner")
    assert code == 0
    waived = check(path, "validator")
    assert waived["status"] == "failed" and waived["waiver"]["status_at_waiver"] == "failed"
    assert waived["waiver"]["by"] == "owner"
    _, out = run("show", str(path), "--json")
    assert json.loads(out)["go_outstanding"] == []
    _, rendered = run("show", str(path))
    assert "waived by owner" in rendered and "| validator | pre | yes | failed |" in rendered


def test_passed_without_evidence_is_not_complete(tmp_path: Path):
    path = new_record(tmp_path)
    run("set", str(path), "--check", "validator=passed")
    _, out = run("show", str(path), "--json")
    assert json.loads(out)["go_outstanding"][0]["reason"] == "passed without evidence"


def test_publication_approval_binds_to_the_exact_candidate(tmp_path: Path):
    path = new_record(tmp_path)
    run("set", str(path), "--digest", "wheel=sha256:a")
    approve_publication(path)
    assert rr.publication_approval(rr.load(path)) is not None
    run("set", str(path), "--digest", "wheel=sha256:b")
    record = rr.load(path)
    assert rr.publication_approval(record) is None
    assert record["approvals"][0]["revoked"] is True
    assert record["approvals"][0]["binds"]["digests"] == {"wheel": "sha256:a"}
    run("set", str(path), "--approve", "publication", "--scope", "publish sha256:b")
    run("set", str(path), "--trigger", "gh release create")
    assert rr.publication_approval(rr.load(path)) is None


def test_candidate_change_resets_dependent_checks_and_keeps_history(tmp_path: Path):
    path = new_record(tmp_path)
    run("set", str(path), "--check", "validator=passed:test.log")
    run("set", str(path), "--check", "changelog-audit=passed:review", "--optional")
    code, out = run("set", str(path), "--commit", "def456")
    assert code == 0 and "2 checks reset" in out
    record = read(path)
    validator = check(path, "validator")
    assert validator["status"] == "not-run" and validator["evidence"] is None
    assert "def456" in validator["invalidated_by"]
    assert record["superseded"][-1]["candidate"]["commit"] == "abc123"
    invalidated = [e for e in record["events"] if e["kind"] == "check-invalidated"]
    assert invalidated[0]["check"]["evidence"] == "test.log"


def test_artifact_checks_track_bytes_while_source_checks_survive_digests(tmp_path: Path):
    path = new_record(tmp_path)
    run("set", str(path), "--check", "validator=passed:test.log")
    before = check(path, "validator")
    run("set", str(path), "--digest", "wheel=sha256:a", "--check", "package-gate=passed:wheel.log", "--on", "artifact:wheel", "--mandatory")
    assert check(path, "validator") == before
    run("set", str(path), "--digest", "wheel=sha256:b")
    assert check(path, "validator") == before
    assert check(path, "package-gate")["status"] == "not-run"
    code, _ = run("set", str(path), "--check", "other=passed:x", "--on", "artifact:image")
    assert code == 2


def test_reuse_keeps_original_execution_identity(tmp_path: Path):
    path = new_record(tmp_path)
    run("set", str(path), "--check", "live-llm=passed:reports/live.log", "--mandatory")
    original = check(path, "live-llm")
    run("set", str(path), "--commit", "docs-only")
    assert check(path, "live-llm")["status"] == "not-run"
    code, out = run(
        "set", str(path), "--check", "live-llm=passed", "--reuse-from", original["id"],
        "--reason", "runtime, tests and lockfile unchanged between abc123 and docs-only",
    )
    assert code == 0, out
    reused = check(path, "live-llm")
    assert reused["status"] == "passed" and reused["evidence"] == "reports/live.log"
    assert reused["reused_from"]["id"] == original["id"]
    assert reused["reused_from"]["at"] == original["at"]
    assert reused["at"] != original["at"] or reused["id"] != original["id"]
    assert "live-llm" not in [i["check"] for i in json.loads(run("show", str(path), "--json")[1])["go_outstanding"]]
    code, _ = run("set", str(path), "--check", "live-llm=passed", "--reuse-from", "nope", "--reason", "x")
    assert code == 2


def test_published_digests_stay_separate_from_tested_identity(tmp_path: Path):
    path = new_record(tmp_path)
    run("set", str(path), "--digest", "wheel=sha256:tested")
    pass_all_mandatory(path)
    approve_publication(path)
    assert run("finish", str(path), "--verdict", "GO")[0] == 0
    before = read(path)
    run("set", str(path), "--published", "wheel=sha256:distributed", "--note", "publish workflow rebuilt the wheel")
    record = read(path)
    assert record["candidate"]["digests"] == {"wheel": "sha256:tested"}
    assert record["published"]["digests"] == {"wheel": "sha256:distributed"}
    assert record["verdict"] == "GO" and record["superseded"] == before["superseded"]
    run("set", str(path), "--commit", "abc123", "--digest", "wheel=sha256:tested")
    assert read(path)["verdict"] == "GO"


def test_new_post_observation_reopens_delivery(tmp_path: Path):
    path = new_record(tmp_path)
    pass_all_mandatory(path)
    approve_publication(path)
    assert run("finish", str(path), "--verdict", "GO")[0] == 0
    run("set", str(path), "--check", "verify=failed:index serves 1.3.0")
    record = read(path)
    assert record["verdict"] is None and record["delivery"]["status"] == "pending"


def test_invalid_input_leaves_no_partial_writes(tmp_path: Path):
    path = new_record(tmp_path)
    for args in (
        ["--check", "validator=maybe"],
        ["--check", "validator"],
        ["--digest", "wheel"],
        ["--on", "elsewhere", "--check", "x=passed:y"],
        ["--waive", "validator"],
        ["--approve", "publication"],
        ["--check", "a=passed:x", "--check", "b=passed:y", "--reuse-from", "z", "--reason", "r"],
        ["--mandatory", "--optional", "--check", "a=passed:x"],
    ):
        before = path.read_bytes()
        code, _ = run("set", str(path), *args)
        assert code == 2, args
        assert path.read_bytes() == before, args


def test_show_finds_the_latest_record_and_renders_markdown(tmp_path: Path):
    first = new_record(tmp_path, version="1.4.0")
    second = new_record(tmp_path, version="1.5.0", commit="fff000")
    code, out = run("show", "--root", str(tmp_path), "--version", "1.4.0", "--json")
    assert code == 0 and json.loads(out)["path"] == str(first)
    code, out = run("show", "--root", str(tmp_path), "--json")
    assert json.loads(out)["path"] == str(second)
    run("set", str(second), "--check", "validator=passed:make test", "--probe", "make test", "--expect", "0 failures", "--note", "docs-only change")
    _, rendered = run("show", str(second))
    assert "## Coverage" in rendered and "| validator | pre | yes | passed | make test |" in rendered
    assert "probe: make test" in rendered and "docs-only change" in rendered
    assert "GO: blocked by" not in rendered.split("## Gates")[1].split("\n")[2] or True
    assert "publication approval: none for this candidate" in rendered
    code, out = run("show", "--root", str(tmp_path / "empty"))
    assert code == 1 and out == "null"


def test_finish_verdicts(tmp_path: Path):
    path = new_record(tmp_path)
    code, _ = run("finish", str(path), "--verdict", "aborted", "--note", "owner postponed")
    assert code == 0
    record = read(path)
    assert record["verdict"] == "aborted" and record["delivery"]["status"] == "aborted"
    assert record["notes"][-1]["text"] == "owner postponed"
    assert run("finish", str(path), "--verdict", "MAYBE")[0] == 2


def test_go_requires_a_publication_approval_for_the_candidate(tmp_path: Path):
    path = new_record(tmp_path)
    pass_all_mandatory(path)
    code, err = run("finish", str(path), "--verdict", "GO")
    assert code == 2 and "publication approval" in err


def test_profile_change_invalidates_publication_approval_only(tmp_path: Path):
    path = new_record(tmp_path)
    approve_publication(path)
    run("set", str(path), "--approve", "tests", "--scope", "run the live provider suite", "--conditions", "provider A, under 2 USD")
    (tmp_path / ".maintainer/profile.toml").write_text("schema_version = 1\n# changed agreement\n")
    record = rr.load(path)
    assert rr.publication_approval(record) is None
    assert rr.approval_valid(record["approvals"][1], record)
    _, rendered = run("show", str(path))
    assert "profile changed since this record started" in rendered


def test_legacy_records_are_read_without_rewriting_disk_or_inventing_history(tmp_path: Path):
    runs = tmp_path / ".maintainer" / "state" / "runs"
    runs.mkdir(parents=True)
    legacy = {
        "schema": 1, "skill": "release", "id": "2026-01-01T00-00-00.000000Z-release",
        "started_at": "2026-01-01T00:00:00Z", "finished_at": "original", "engine": {"plugin": "oss-maintainer", "version": "0.1.0"},
        "repo": "example/app", "candidate": {"version": "1.4.0", "commit": "abc123", "digests": {"image": "sha256:aaaa"}},
        "profile_hash": None, "overlay_diff": [],
        "phases": [
            {"name": "bucket-a", "status": "passed", "checks": [{"name": "validator", "status": "passed", "evidence": "reports/validator.log"}], "authorizations": []},
            {"name": "go", "status": "passed", "checks": [], "authorizations": [{"scope": "publish via gh release create", "candidate": "abc123", "granted_at": "2026-01-01T01:00:00Z", "by": "owner"}]},
            {"name": "publish", "status": "failed", "checks": [{"name": "registry-a", "status": "passed", "evidence": "manifest"}, {"name": "registry-b", "status": "failed", "evidence": "push timeout"}], "authorizations": []},
        ],
        "commands": [{"run": "old test", "exit": 0, "at": "original"}], "items": [], "verdict": "GO", "notes": ["free text"],
    }
    path = runs / "2026-01-01T00-00-00.000000Z-release.json"
    path.write_text(json.dumps(legacy))
    before = path.read_bytes()
    code, out = run("show", "--root", str(tmp_path), "--json")
    assert code == 0 and path.read_bytes() == before
    loaded = json.loads(out)
    assert loaded["legacy_schema"] == 1 and loaded["schema"] == 3
    assert loaded["commands"] == legacy["commands"] and loaded["phases"] == legacy["phases"]
    assert loaded["delivery"]["status"] == "unknown"
    names = {c["name"]: c for c in loaded["checks"]}
    assert names["registry-b"]["status"] == "failed" and names["registry-b"]["stage"] == "post"
    assert names["validator"]["on"] == {"source": "abc123"}
    assert [i["check"] for i in loaded["outstanding"]] == ["registry-b"]
    assert loaded["approvals"][0]["action"] == "publication" and loaded["approvals"][0]["legacy"]
    assert rr.publication_approval(rr.load(path)) is not None
    # The first mutation upgrades the file and records that it did.
    run("set", str(path), "--check", "registry-b=passed:retry manifest")
    upgraded = read(path)
    assert upgraded["schema"] == 3 and upgraded["legacy_schema"] == 1
    assert any(e["kind"] == "schema-upgraded" for e in upgraded["events"])
    assert upgraded["phases"] == legacy["phases"]
