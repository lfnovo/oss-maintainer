"""Behavioral contracts for evidence, scoped permissions and actual delivery closure."""

import json
from tests.test_run_record import run, new_record, complete_delivery


def read(path):
    return json.loads(path.read_text())


def check(path, phase="bucket-a"):
    return next(p for p in read(path)["phases"] if p["name"] == phase)["checks"][0]


def grant(path, kind="tests", **kw):
    args = [
        "authorize",
        str(path),
        "--kind",
        kind,
        "--scope",
        "reviewed work",
        "--conditions",
        "only the reviewed scope and resources",
    ]
    for key, value in kw.items():
        args += ["--" + key.replace("_", "-"), str(value)]
    code, out = run(*args)
    assert code == 0
    return out


def test_source_evidence_survives_enrichment_and_artifact_tracks_bytes(tmp_path):
    path = new_record(tmp_path)
    run(
        "update",
        str(path),
        "--phase",
        "bucket-a",
        "--status",
        "passed",
        "--check",
        "validator=passed:log",
        "--depends-on",
        "source",
    )
    before = check(path)
    run(
        "update",
        str(path),
        "--phase",
        "artifact-gate",
        "--status",
        "passed",
        "--digest",
        "wheel=sha256:a",
        "--depends-on",
        "artifact:wheel",
        "--check",
        "package-gate=passed:wheel.log",
    )
    assert check(path) == before
    run("digest", str(path), "--name", "wheel", "--value", "sha256:b")
    assert check(path) == before
    assert check(path, "artifact-gate")["status"] == "not-run"
    run("candidate", str(path), "--commit", "changed")
    assert check(path)["status"] == "not-run"


def test_unknown_artifact_rejected_atomically(tmp_path):
    path = new_record(tmp_path)
    before = path.read_bytes()
    code, _ = run(
        "update",
        str(path),
        "--phase",
        "artifact-gate",
        "--status",
        "passed",
        "--depends-on",
        "artifact:unknown",
        "--check",
        "package-gate=passed:log",
    )
    assert code == 2 and path.read_bytes() == before


def test_invalid_commands_leave_no_partial_writes(tmp_path):
    path = new_record(tmp_path)
    for spec in ["make test", "make test=oops", "=0", "make test="]:
        before = path.read_bytes()
        code, _ = run(
            "update",
            str(path),
            "--phase",
            "bucket-a",
            "--status",
            "passed",
            "--command",
            spec,
        )
        assert code == 2 and path.read_bytes() == before


def test_multiple_commands_and_revalidation_keep_execution_history(tmp_path):
    path = new_record(tmp_path)
    code, _ = run(
        "update",
        str(path),
        "--phase",
        "bucket-a",
        "--status",
        "passed",
        "--depends-on",
        "source",
        "--check",
        "validator=passed:log",
        "--command",
        "env MODE=ci make test=0",
        "--command",
        "make lint=1",
        "--executed-at",
        "2026-01-01T10:00:00Z",
    )
    assert code == 0
    commands = read(path)["commands"]
    assert [c["run"] for c in commands] == ["env MODE=ci make test", "make lint"]
    assert len({c["id"] for c in commands}) == 2
    evidence = check(path)
    run("digest", str(path), "--name", "wheel", "--value", "sha256:a")
    code, _ = run(
        "revalidate",
        str(path),
        "--phase",
        "bucket-a",
        "--evidence-id",
        evidence["id"],
        "--reason",
        "source unchanged",
    )
    assert code == 0 and read(path)["commands"] == commands and check(path) == evidence
    assert read(path)["events"][-1]["kind"] == "evidence-revalidated"
    run("candidate", str(path), "--commit", "new")
    code, _ = run(
        "revalidate",
        str(path),
        "--phase",
        "bucket-a",
        "--evidence-id",
        evidence["id"],
        "--reason",
        "wishful reuse",
    )
    assert code == 2


def test_action_grants_survive_candidate_change_but_publication_does_not(tmp_path):
    path = new_record(tmp_path)
    tests = grant(path, limit=2)
    merge = grant(path, "merge")
    notes = grant(path, "notes", subject="sha256:text-and-facts")
    run(
        "authorize",
        str(path),
        "--scope",
        "publish via make tag",
        "--candidate",
        "abc123",
    )
    run("digest", str(path), "--name", "wheel", "--value", "sha256:a")
    _, out = run("permissions", str(path))
    approvals = {a["id"]: a for a in json.loads(out)}
    assert all(approvals[i]["valid"] for i in [tests, merge, notes])
    assert not next(a for a in approvals.values() if a["kind"] == "publication")[
        "valid"
    ]
    run("candidate", str(path), "--commit", "new")
    _, out = run("permissions", str(path))
    approvals = {a["id"]: a for a in json.loads(out)}
    assert (
        approvals[tests]["valid"]
        and approvals[merge]["valid"]
        and not approvals[notes]["valid"]
    )
    assert (
        run(
            "consume",
            str(path),
            "--authorization",
            tests,
            "--units",
            "2",
            "--reason",
            "reserve paid work",
        )[0]
        == 0
    )
    before = path.read_bytes()
    assert (
        run("consume", str(path), "--authorization", tests, "--reason", "repeat")[0]
        == 2
    )
    assert path.read_bytes() == before


def test_policy_change_invalidates_grants(tmp_path):
    path = new_record(tmp_path)
    grant(path)
    (tmp_path / ".maintainer/profile.toml").write_text(
        "schema_version = 1\n# changed agreement\n"
    )
    _, out = run("permissions", str(path))
    assert not json.loads(out)[0]["valid"]


def test_delivery_cannot_finish_empty_but_retro_can_remain_pending(tmp_path):
    path = new_record(tmp_path)
    assert run("finish", str(path), "--verdict", "GO")[0] == 2
    assert read(path)["finished_at"] is None
    assert complete_delivery(path)[0] == 0
    before = read(path)
    assert before["delivery"]["status"] == "completed"
    assert before["delivery"]["retrospective"] == "pending"
    run(
        "update",
        str(path),
        "--phase",
        "retro",
        "--status",
        "passed",
        "--check",
        "learning=passed:diary",
    )
    assert read(path)["finished_at"] == before["finished_at"]
    assert read(path)["delivery"]["status"] == "completed"


def test_delivery_requires_verification_even_with_custom_phases(tmp_path):
    code, out = run(
        "new",
        "--root",
        str(tmp_path),
        "--version",
        "1",
        "--commit",
        "abc",
        "--required-phase",
        "matrix",
    )
    from pathlib import Path

    path = Path(out)
    assert {"publish", "verify", "cleanup", "announce", "matrix"} <= set(
        read(path)["delivery"]["required_phases"]
    )
    run(
        "update",
        str(path),
        "--phase",
        "publish",
        "--status",
        "passed",
        "--check",
        "published=passed:registry",
    )
    assert run("finish", str(path), "--verdict", "GO")[0] == 2


def test_legacy_read_does_not_invent_provenance_or_rewrite_disk(tmp_path):
    path = new_record(tmp_path)
    record = read(path)
    record["schema"] = 1
    record.pop("delivery")
    record.pop("events")
    record["commands"] = [{"run": "old test", "exit": 0, "at": "original"}]
    record["finished_at"] = "original"
    record["verdict"] = "GO"
    path.write_text(json.dumps(record))
    before = path.read_bytes()
    _, out = run("latest", "--root", str(tmp_path))
    loaded = json.loads(out)
    assert path.read_bytes() == before
    assert loaded["commands"] == record["commands"]
    assert loaded["delivery"]["status"] == "unknown"
    assert loaded["legacy_schema"] == 1


def test_expiry_and_required_observations_are_enforced(tmp_path):
    path = new_record(tmp_path)
    code, _ = run(
        "authorize",
        str(path),
        "--kind",
        "tests",
        "--scope",
        "probe",
        "--conditions",
        "provider A only",
        "--expires-at",
        "2000-01-01T00:00:00Z",
    )
    assert code == 2
    approval_id = grant(path, expires_at="2999-01-01T00:00:00Z")
    record = read(path)
    approval = next(
        a
        for p in record["phases"]
        for a in p["authorizations"]
        if a["id"] == approval_id
    )
    approval["expires_at"] = "2000-01-01T00:00:00Z"
    path.write_text(json.dumps(record))
    assert (
        run(
            "consume", str(path), "--authorization", approval_id, "--reason", "late use"
        )[0]
        == 2
    )
    assert complete_delivery(path)[0] == 0
    run(
        "update",
        str(path),
        "--phase",
        "verify",
        "--status",
        "failed",
        "--check",
        "verify=failed:registry-missing",
    )
    assert read(path)["delivery"]["status"] == "pending"
    assert run("finish", str(path), "--verdict", "GO")[0] == 2
