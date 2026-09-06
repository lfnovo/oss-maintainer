"""Behavioral contracts: approvals are recorded in plain language and only publication binds mechanically."""

from tests.test_run_record import approve_publication, new_record, pass_all_mandatory, read, rr, run


def test_action_approvals_survive_candidate_changes_but_publication_does_not(tmp_path):
    path = new_record(tmp_path)
    run("set", str(path), "--approve", "tests", "--scope", "run the reviewed live plan", "--conditions", "provider A; at most 2 USD")
    run("set", str(path), "--approve", "merge", "--scope", "merge qualifying fixes during this run", "--conditions", "CI green and reviewed")
    approve_publication(path)
    run("set", str(path), "--commit", "new")
    record = rr.load(path)
    by_action = {a["action"]: a for a in record["approvals"]}
    assert rr.approval_valid(by_action["tests"], record)
    assert rr.approval_valid(by_action["merge"], record)
    assert by_action["publication"]["revoked"] is True
    assert "publication" in [e["kind"] and by_action["publication"]["id"] == e.get("approval_id") and "publication" for e in record["events"] if e["kind"] == "approval-revoked"]


def test_no_execution_counting_is_required(tmp_path):
    """A test approval is used by doing the work; the record never demands a reservation."""
    path = new_record(tmp_path)
    run("set", str(path), "--approve", "tests", "--scope", "run the live suite as often as needed this run")
    for attempt in range(3):
        code, _ = run("set", str(path), "--check", f"live-suite=passed:attempt {attempt}", "--mandatory")
        assert code == 0
    record = rr.load(path)
    assert record["approvals"][0].get("used") is None
    assert len([e for e in record["events"] if e["kind"] == "check-superseded"]) == 2


def test_delivery_cannot_finish_empty_and_optional_checks_never_block(tmp_path):
    path = new_record(tmp_path)
    assert run("finish", str(path), "--verdict", "GO")[0] == 2
    assert read(path)["finished_at"] is None
    pass_all_mandatory(path)
    approve_publication(path)
    run("set", str(path), "--check", "announce=not-applicable:owner asked for no announcement")
    run("set", str(path), "--check", "cleanup=not-run")
    assert run("finish", str(path), "--verdict", "GO")[0] == 0
    assert read(path)["delivery"]["status"] == "completed"
    # A note after completion is retrospective work; it does not reopen delivery.
    run("set", str(path), "--note", "retro: the wheel gate should also list the sdist")
    assert read(path)["delivery"]["status"] == "completed"


def test_custom_mandatory_checks_join_the_contract(tmp_path):
    (tmp_path / ".maintainer").mkdir()
    (tmp_path / ".maintainer/profile.toml").write_text("schema_version = 1\n")
    code, out = run("new", "--root", str(tmp_path), "--version", "1", "--commit", "abc", "--mandatory", "owner-checks", "--mandatory", "release-page:post")
    assert code == 0
    from pathlib import Path

    path = Path(out)
    checks = {c["name"]: c for c in read(path)["checks"]}
    assert checks["owner-checks"]["stage"] == "pre" and checks["release-page"]["stage"] == "post"
    pass_all_mandatory(path)
    approve_publication(path)
    code, err = run("finish", str(path), "--verdict", "GO")
    assert code == 2 and "owner-checks" in err and "release-page" in err
