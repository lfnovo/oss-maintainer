#!/usr/bin/env python3
"""One record per release (or smoke run) under `.maintainer/state/runs/`.

The record is a result of the work, not a condition for it: the agent writes down what ran,
what the maintainer decided and what was published, so the next session resumes from facts.
Existing logs, CI runs and digests are the evidence; the record links to them.

Usage:
  run_record.py new  --root R --version V [--commit SHA] [--trigger TEXT] [--repo O/N]
                     [--mandatory NAME[:pre|post]]... [--optional NAME[:pre|post]]...
  run_record.py set  RECORD [--commit SHA] [--version V] [--trigger TEXT]
                     [--digest NAME=DIGEST]... [--published NAME=DIGEST]...
                     [--check NAME=STATUS[:EVIDENCE]]... [--on source|artifact:NAME]
                     [--mandatory|--optional] [--stage pre|post] [--probe TEXT] [--expect TEXT]
                     [--reuse-from CHECK_ID --reason TEXT]
                     [--waive NAME --reason TEXT] [--approve ACTION --scope TEXT [--conditions TEXT]]
                     [--by WHO] [--note TEXT] [--python PATH]
  run_record.py show RECORD [--json]            # or: show --root R [--version V]
  run_record.py finish RECORD --verdict GO|NO-GO|aborted [--note TEXT]

Statuses: passed, failed, not-run, not-applicable. A mandatory check blocks until it is
`passed` with evidence or explicitly waived by a recorded decision; an optional check never
blocks. `show` and `finish` apply that one rule and name the same items.

Requires Python 3.11+. Standard library only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tomllib
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

if sys.version_info < (3, 11):  # pragma: no cover
    sys.stderr.write("run_record.py needs Python 3.11 or newer.\n")
    sys.exit(2)

SCHEMA = 3
STATUSES = {"passed", "failed", "not-run", "not-applicable"}
STAGES = {"pre", "post"}
VERDICTS = {"GO", "NO-GO", "aborted"}
PUBLICATION = "publication"
POST_CHECKS = ("publish", "verify", "announce", "cleanup")
RELEASE_DEFAULTS = {
    "mandatory": [("validator", "pre"), ("publish", "post"), ("verify", "post")],
    "optional": [("announce", "post"), ("cleanup", "post")],
}
# Names a schema-1/2 phase maps to when a legacy record is read.
LEGACY_POST_PHASES = {"publish", "verify", "announce", "cleanup"}


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def runs_dir(root: Path) -> Path:
    return root / ".maintainer" / "state" / "runs"


def profile_hash(root: Path) -> str | None:
    profile = root / ".maintainer" / "profile.toml"
    if not profile.exists():
        return None
    digest = hashlib.sha256(profile.read_bytes())
    overlay = root / ".maintainer" / "profile.local.toml"
    if overlay.exists():
        digest.update(overlay.read_bytes())
    return "sha256:" + digest.hexdigest()


def event(record: dict, kind: str, **fields) -> dict:
    item = {"id": uuid.uuid4().hex, "kind": kind, "at": now(), **fields}
    record.setdefault("events", []).append(item)
    return item


# ----------------------------------------------------------------------------- loading


def load(path: Path) -> dict:
    record = json.loads(path.read_text(encoding="utf-8"))
    schema = record.get("schema")
    if schema not in {1, 2, SCHEMA}:
        raise ValueError("unsupported run-record schema")
    if schema != SCHEMA:
        record = migrate_legacy(record)
    record.setdefault("checks", [])
    record.setdefault("approvals", [])
    record.setdefault("notes", [])
    record.setdefault("events", [])
    record.setdefault("superseded", [])
    record.setdefault("published", {"digests": {}})
    record["candidate"].setdefault("digests", {})
    record["candidate"].setdefault("trigger", None)
    record.setdefault("engine", {}).setdefault("python", None)
    record.setdefault("delivery", {"status": "pending"})
    return record


def migrate_legacy(record: dict) -> dict:
    """Read a schema-1/2 record in memory. Nothing is inferred; phases stay as history."""
    legacy = record.get("schema")
    record["legacy_schema"] = legacy
    record["schema"] = SCHEMA
    checks: list[dict] = []
    approvals: list[dict] = []
    for phase in record.get("phases", []):
        stage = "post" if phase.get("name") in LEGACY_POST_PHASES else "pre"
        for check in phase.get("checks", []):
            checks.append(
                {
                    "id": check.get("id") or uuid.uuid4().hex,
                    "name": check["name"],
                    "status": check.get("status", "not-run"),
                    "evidence": check.get("evidence"),
                    "at": check.get("at"),
                    "stage": stage,
                    "mandatory": True,
                    # Legacy checks were candidate-bound: a new commit invalidates them.
                    "on": check.get("dependencies")
                    or ({"source": record["candidate"].get("commit")} if record["candidate"].get("commit") else {}),
                    "probe": None,
                    "expect": None,
                    "reused_from": None,
                    "waiver": None,
                    "legacy_phase": phase.get("name"),
                }
            )
        for grant in phase.get("authorizations", []):
            approvals.append(
                {
                    "id": grant.get("id") or uuid.uuid4().hex,
                    "action": grant.get("kind", PUBLICATION),
                    "scope": grant.get("scope"),
                    "conditions": grant.get("conditions"),
                    "by": grant.get("by"),
                    "at": grant.get("granted_at"),
                    "binds": grant.get("identity")
                    or ({"commit": grant["candidate"]} if grant.get("candidate") else None),
                    "revoked": bool(grant.get("revoked")),
                    "legacy": True,
                }
            )
    record["checks"] = checks
    record["approvals"] = approvals
    notes = []
    for note in record.get("notes", []):
        notes.append(note if isinstance(note, dict) else {"at": None, "text": str(note)})
    record["notes"] = notes
    delivery = record.get("delivery") or {}
    status = delivery.get("status")
    if status not in {"completed", "blocked", "aborted"}:
        status = "unknown" if record.get("finished_at") else "pending"
    record["delivery"] = {"status": status}
    return record


def save(path: Path, record: dict) -> None:
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


# ----------------------------------------------------------------------------- rules


def find_check(record: dict, name: str) -> dict | None:
    return next((c for c in record["checks"] if c["name"] == name), None)


def outstanding(record: dict, stage: str | None = None) -> list[dict]:
    """The single completion rule: mandatory checks not passed with evidence, unless waived."""
    items = []
    for check in record["checks"]:
        if stage and check.get("stage") != stage:
            continue
        if not check.get("mandatory"):
            continue
        if check.get("waiver"):
            continue
        if check["status"] == "passed" and check.get("evidence"):
            continue
        if check["status"] == "passed":
            reason = "passed without evidence"
        elif check["status"] == "not-applicable":
            reason = "mandatory check marked not-applicable: pass it or record a waiver decision"
        elif check["status"] == "failed":
            reason = "failed"
        else:
            reason = "not run"
        items.append(
            {"check": check["name"], "stage": check.get("stage"), "status": check["status"], "reason": reason}
        )
    return items


def identity(record: dict) -> dict:
    c = record["candidate"]
    return {
        "commit": c.get("commit"),
        "version": c.get("version"),
        "trigger": c.get("trigger"),
        "digests": deepcopy(c.get("digests", {})),
    }


def approval_valid(approval: dict, record: dict) -> bool:
    if approval.get("revoked"):
        return False
    if approval.get("action") != PUBLICATION:
        return True
    binds = approval.get("binds") or {}
    if approval.get("legacy"):
        return binds.get("commit") == record["candidate"].get("commit") and bool(binds)
    if record.get("root") and profile_hash(Path(record["root"])) != record.get("profile_hash"):
        return False
    return binds == identity(record)


def publication_approval(record: dict) -> dict | None:
    return next(
        (a for a in reversed(record["approvals"]) if a.get("action") == PUBLICATION and approval_valid(a, record)),
        None,
    )


def check_holds(check: dict, record: dict) -> bool:
    on = check.get("on") or {}
    candidate = record["candidate"]
    for key, value in on.items():
        if key == "source":
            if candidate.get("commit") != value:
                return False
        elif key.startswith("artifact:"):
            if candidate.get("digests", {}).get(key.split(":", 1)[1]) != value:
                return False
        elif key == "candidate":
            if value != identity(record):
                return False
    return True


def supersede_candidate(record: dict, new: dict, reason: str) -> int:
    """Apply a candidate identity change: keep history, reset dependent evidence and publication approval."""
    old = identity(record)
    if new == old:
        return 0
    replaced = any(old[k] != new[k] for k in ("commit", "version", "trigger")) or any(
        old["digests"].get(name) not in (None, value) for name, value in new["digests"].items()
    )
    if not replaced:
        # Only new artifact identities were added: nothing tested so far is contradicted.
        record["candidate"].update(new)
        for approval in record["approvals"]:
            if approval.get("action") == PUBLICATION and not approval.get("revoked") and not approval_valid(approval, record):
                approval["revoked"] = True
                approval["revoked_reason"] = reason
                event(record, "approval-revoked", approval_id=approval["id"], reason=reason)
        event(record, "candidate-enriched", reason=reason, identity=identity(record))
        return 0
    record["superseded"].append(
        {"at": now(), "reason": reason, "candidate": old, "verdict": record.get("verdict"), "finished_at": record.get("finished_at")}
    )
    record["candidate"].update(new)
    reset = 0
    for check in record["checks"]:
        if check["status"] == "not-run":
            continue
        if not check_holds(check, record):
            event(record, "check-invalidated", check=deepcopy(check), reason=reason)
            check["status"] = "not-run"
            check["invalidated_by"] = reason
            check["evidence"] = None
            reset += 1
    for approval in record["approvals"]:
        if approval.get("action") == PUBLICATION and not approval.get("revoked") and not approval_valid(approval, record):
            approval["revoked"] = True
            approval["revoked_reason"] = reason
            event(record, "approval-revoked", approval_id=approval["id"], reason=reason)
    record["published"] = {"digests": {}}
    record["verdict"] = None
    record["finished_at"] = None
    record["delivery"]["status"] = "pending"
    event(record, "candidate-changed", reason=reason, previous=old, identity=identity(record))
    return reset


# ----------------------------------------------------------------------------- commands


def parse_named(specs: list[str] | None, default_stage: str) -> list[tuple[str, str]]:
    out = []
    for spec in specs or []:
        name, _, stage = spec.partition(":")
        stage = stage or default_stage
        if not name.strip() or stage not in STAGES:
            raise ValueError(f"invalid check declaration: {spec} (NAME or NAME:pre|post)")
        out.append((name, stage))
    return out


def seed_check(record: dict, name: str, stage: str, mandatory: bool) -> None:
    existing = find_check(record, name)
    if existing:
        existing["mandatory"] = existing["mandatory"] or mandatory
        return
    record["checks"].append(
        {
            "id": uuid.uuid4().hex,
            "name": name,
            "status": "not-run",
            "evidence": None,
            "at": None,
            "stage": stage,
            "mandatory": mandatory,
            "on": {},
            "probe": None,
            "expect": None,
            "reused_from": None,
            "waiver": None,
        }
    )


def cmd_new(args) -> int:
    root = Path(args.root).resolve()
    directory = runs_dir(root)
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S.%fZ")
    path = directory / f"{stamp}-{args.skill}.json"
    suffix = 1
    while path.exists():
        suffix += 1
        path = directory / f"{stamp}-{suffix}-{args.skill}.json"
    record = {
        "schema": SCHEMA,
        "skill": args.skill,
        "id": path.stem,
        "started_at": now(),
        "finished_at": None,
        "engine": {"plugin": "oss-maintainer", "version": args.engine_version, "python": args.python},
        "repo": args.repo,
        "root": str(root),
        "profile_hash": profile_hash(root),
        "candidate": {"version": args.version, "commit": args.commit, "trigger": args.trigger, "digests": {}},
        "published": {"digests": {}},
        "checks": [],
        "approvals": [],
        "notes": [],
        "superseded": [],
        "events": [],
        "verdict": None,
        "delivery": {"status": "pending"},
    }
    mandatory = parse_named(args.mandatory, "pre")
    optional = parse_named(args.optional, "pre")
    if args.skill == "release":
        mandatory = list(RELEASE_DEFAULTS["mandatory"]) + mandatory
        optional = list(RELEASE_DEFAULTS["optional"]) + optional
        profile = root / ".maintainer" / "profile.toml"
        if profile.exists():
            gates = tomllib.loads(profile.read_text(encoding="utf-8")).get("release", {}).get("gates", {})
            mandatory += [(name, "pre") for name in gates.get("mandatory", [])]
            optional += [(name, "pre") for name in gates.get("optional", []) + gates.get("not_gates", [])]
    for name, stage in optional:
        seed_check(record, name, stage, mandatory=False)
    for name, stage in mandatory:
        seed_check(record, name, stage, mandatory=True)
    save(path, record)
    print(path)
    return 0


def parse_check(spec: str) -> tuple[str, str, str | None]:
    name, sep, rest = spec.partition("=")
    status, _, evidence = rest.partition(":")
    if not sep or not name.strip() or status not in STATUSES:
        raise ValueError(f"invalid check: {spec} (NAME=STATUS[:EVIDENCE])")
    return name.strip(), status, evidence or None


def parse_pair(spec: str, what: str) -> tuple[str, str]:
    name, sep, value = spec.partition("=")
    if not sep or not name.strip() or not value.strip():
        raise ValueError(f"--{what} requires NAME=VALUE")
    return name.strip(), value.strip()


def cmd_set(args) -> int:
    path = Path(args.record)
    record = load(path)
    if record.get("legacy_schema"):
        event(record, "schema-upgraded", from_schema=record["legacy_schema"])

    # Validate everything before touching the record.
    checks = [parse_check(s) for s in args.check or []]
    digests = [parse_pair(s, "digest") for s in args.digest or []]
    published = [parse_pair(s, "published") for s in args.published or []]
    if args.mandatory and args.optional:
        raise ValueError("--mandatory and --optional are exclusive")
    if args.stage and args.stage not in STAGES:
        raise ValueError("--stage must be pre or post")
    if args.on and args.on != "source" and not args.on.startswith("artifact:"):
        raise ValueError("--on must be source or artifact:NAME")
    if (args.reuse_from or args.waive) and not args.reason:
        raise ValueError("--reuse-from and --waive require --reason")
    if args.reuse_from and len(checks) != 1:
        raise ValueError("--reuse-from applies to exactly one --check")
    if args.approve and not (args.scope or "").strip():
        raise ValueError("--approve requires a non-empty --scope")
    if args.approve == PUBLICATION and not record["candidate"].get("commit"):
        raise ValueError("publication approval requires a candidate commit")

    # 1. Candidate identity.
    new = identity(record)
    reasons = []
    if args.commit and args.commit != new["commit"]:
        new["commit"] = args.commit
        new["digests"] = {}
        reasons.append(f"commit {args.commit}")
    if args.version and args.version != new["version"]:
        new["version"] = args.version
        reasons.append(f"version {args.version}")
    if args.trigger and args.trigger != new["trigger"]:
        new["trigger"] = args.trigger
        reasons.append(f"trigger {args.trigger!r}")
    for name, value in digests:
        if new["digests"].get(name) != value:
            new["digests"][name] = value
            reasons.append(f"digest {name}")
    reset = supersede_candidate(record, new, "candidate changed: " + ", ".join(reasons)) if reasons else 0

    # 2. Checks.
    if args.on and args.on.startswith("artifact:"):
        artifact = args.on.split(":", 1)[1]
        if not record["candidate"]["digests"].get(artifact):
            raise ValueError(f"record the tested artifact identity first: {artifact}")
    source_of_reuse = None
    if args.reuse_from:
        # The original result lives in the event history once it was invalidated or superseded.
        candidates = [
            e["check"]
            for e in record["events"]
            if e.get("kind") in {"check-invalidated", "check-superseded"} and e["check"].get("id") == args.reuse_from
        ] + [c for c in record["checks"] if c["id"] == args.reuse_from]
        source_of_reuse = next((c for c in candidates if c.get("status") == "passed" and c.get("evidence")), None)
        if not source_of_reuse:
            raise ValueError("--reuse-from must name an earlier passed check with evidence")
    for name, status, evidence in checks:
        existing = find_check(record, name)
        if existing and existing["status"] != "not-run":
            event(record, "check-superseded", check=deepcopy(existing))
        on = {}
        if args.on == "source":
            if not record["candidate"].get("commit"):
                raise ValueError("source evidence requires a candidate commit")
            on = {"source": record["candidate"]["commit"]}
        elif args.on:
            artifact = args.on.split(":", 1)[1]
            on = {args.on: record["candidate"]["digests"][artifact]}
        elif status != "not-run":
            on = {"source": record["candidate"]["commit"]} if record["candidate"].get("commit") else {}
        stage = args.stage or (existing or {}).get("stage") or ("post" if name in POST_CHECKS else "pre")
        mandatory = True if args.mandatory else False if args.optional else (existing or {}).get("mandatory", False)
        entry = {
            "id": uuid.uuid4().hex,
            "name": name,
            "status": status,
            "evidence": evidence,
            "at": now() if status != "not-run" else None,
            "stage": stage,
            "mandatory": mandatory,
            "on": on,
            "probe": args.probe or (existing or {}).get("probe"),
            "expect": args.expect or (existing or {}).get("expect"),
            "reused_from": None,
            "waiver": (existing or {}).get("waiver") if status != "passed" else None,
        }
        if source_of_reuse:
            entry["reused_from"] = {
                "id": source_of_reuse["id"],
                "at": source_of_reuse.get("at"),
                "on": deepcopy(source_of_reuse.get("on")),
                "evidence": source_of_reuse.get("evidence"),
                "reason": args.reason,
            }
            entry["evidence"] = evidence or source_of_reuse.get("evidence")
        if existing:
            record["checks"][record["checks"].index(existing)] = entry
        else:
            record["checks"].append(entry)
        event(record, "check-recorded", check=deepcopy(entry))
        if record.get("finished_at") and stage == "post":
            event(record, "delivery-reopened", check=name)
            record["finished_at"] = None
            record["verdict"] = None
            record["delivery"]["status"] = "pending"

    # 3. Waiver: a decision, recorded next to the original result.
    if args.waive:
        target = find_check(record, args.waive)
        if not target:
            raise ValueError(f"unknown check: {args.waive}")
        target["waiver"] = {"by": args.by, "at": now(), "reason": args.reason, "status_at_waiver": target["status"]}
        event(record, "check-waived", check=args.waive, by=args.by, reason=args.reason)

    # 4. Approval.
    if args.approve:
        approval = {
            "id": uuid.uuid4().hex,
            "action": args.approve,
            "scope": args.scope,
            "conditions": args.conditions,
            "by": args.by,
            "at": now(),
            "binds": identity(record) if args.approve == PUBLICATION else None,
            "revoked": False,
        }
        record["approvals"].append(approval)
        event(record, "approval-recorded", approval=deepcopy(approval))

    # 5. Observations, published identity, environment.
    for name, value in published:
        record["published"]["digests"][name] = value
    for text in args.note or []:
        record["notes"].append({"at": now(), "text": text})
    if args.python:
        record["engine"]["python"] = args.python

    save(path, record)
    summary = []
    if reset:
        summary.append(f"{reset} checks reset")
    for name, status, _ in checks:
        summary.append(f"{name}: {status}")
    if args.approve:
        summary.append(f"approved: {args.approve}")
    print("; ".join(summary) or "ok")
    return 0


def latest(root: Path, skill: str, version: str | None) -> Path | None:
    for path in sorted(runs_dir(root).glob(f"*-{skill}.json"), reverse=True):
        record = load(path)
        if version and record["candidate"].get("version") != version:
            continue
        return path
    return None


def render(record: dict, path: Path) -> str:
    c = record["candidate"]
    lines = [f"# {record['skill']} {c.get('version')} — {record['id']}", ""]
    lines.append(f"- record: `{path}`")
    lines.append(f"- candidate: `{c.get('commit')}`" + (f", trigger: `{c.get('trigger')}`" if c.get("trigger") else ", trigger: not set"))
    for name, value in c.get("digests", {}).items():
        lines.append(f"- tested {name}: `{value}`")
    for name, value in record["published"].get("digests", {}).items():
        lines.append(f"- published {name}: `{value}`")
    if record["engine"].get("python"):
        lines.append(f"- scripts run with: `{record['engine']['python']}`")
    if record.get("root") and profile_hash(Path(record["root"])) != record.get("profile_hash"):
        lines.append("- **profile changed since this record started**: re-read the policies before relying on earlier decisions")
    if record.get("legacy_schema"):
        lines.append(f"- read from schema {record['legacy_schema']}; phases kept as history, nothing inferred")
    lines += ["", "## Coverage", "", "| check | stage | mandatory | status | evidence | note |", "|---|---|---|---|---|---|"]
    for check in sorted(record["checks"], key=lambda c: 0 if c.get("stage") == "pre" else 1):
        note = []
        if check.get("waiver"):
            note.append(f"waived by {check['waiver'].get('by')}: {check['waiver'].get('reason')}")
        if check.get("reused_from"):
            note.append(f"reused from {check['reused_from'].get('at')}: {check['reused_from'].get('reason')}")
        if check.get("invalidated_by") and check["status"] == "not-run":
            note.append(f"invalidated: {check['invalidated_by']}")
        if check.get("probe"):
            note.append(f"probe: {check['probe']}")
        if check.get("expect"):
            note.append(f"expect: {check['expect']}")
        lines.append(
            f"| {check['name']} | {check.get('stage')} | {'yes' if check.get('mandatory') else 'no'} | {check['status']} | {check.get('evidence') or ''} | {'; '.join(note)} |"
        )
    go = outstanding(record, "pre")
    delivery = outstanding(record)
    approval = publication_approval(record)
    lines += ["", "## Gates", ""]
    lines.append("- GO: " + ("ready" if not go else "blocked by " + ", ".join(f"{i['check']} ({i['reason']})" for i in go)))
    lines.append("- publication approval: " + (f"{approval['scope']} (by {approval.get('by')}, {approval.get('at')})" if approval else "none for this candidate"))
    if delivery or not approval:
        blockers = [f"{i['check']} ({i['reason']})" for i in delivery]
        if not approval:
            blockers.append("no valid publication approval")
        lines.append("- delivery: outstanding " + ", ".join(blockers))
    else:
        lines.append("- delivery: " + record["delivery"].get("status", "pending"))
    if record.get("verdict"):
        lines.append(f"- verdict: {record['verdict']} at {record.get('finished_at')}")
    if record["approvals"]:
        lines += ["", "## Approvals", ""]
        for a in record["approvals"]:
            state = "revoked" if a.get("revoked") else ("valid" if approval_valid(a, record) else "no longer applicable")
            cond = f" — conditions: {a['conditions']}" if a.get("conditions") else ""
            lines.append(f"- {a.get('action')}: {a.get('scope')}{cond} (by {a.get('by')}, {a.get('at')}, {state})")
    if record["notes"]:
        lines += ["", "## Notes", ""]
        for n in record["notes"]:
            lines.append(f"- {n.get('at') or ''} {n.get('text')}".strip())
    if record["superseded"]:
        lines += ["", "## Superseded candidates", ""]
        for s in record["superseded"]:
            lines.append(f"- {s['at']}: {s['reason']} (was `{s['candidate'].get('commit')}` {s['candidate'].get('version')})")
    return "\n".join(lines) + "\n"


def cmd_show(args) -> int:
    if args.record:
        path = Path(args.record)
    else:
        if not args.root:
            raise ValueError("show needs a record path or --root")
        found = latest(Path(args.root).resolve(), args.skill, args.version)
        if not found:
            print("null")
            return 1
        path = found
    record = load(path)
    if args.json:
        print(json.dumps({"path": str(path), "outstanding": outstanding(record), "go_outstanding": outstanding(record, "pre"), **record}, indent=2, ensure_ascii=False))
    else:
        print(render(record, path), end="")
    return 0


def cmd_finish(args) -> int:
    path = Path(args.record)
    record = load(path)
    if args.verdict not in VERDICTS:
        raise ValueError(f"invalid verdict {args.verdict}")
    if args.verdict == "GO":
        blockers = [f"{i['check']} ({i['reason']})" for i in outstanding(record)]
        if not publication_approval(record):
            blockers.append("no valid publication approval for this candidate")
        if blockers:
            raise ValueError("delivery incomplete: " + "; ".join(blockers))
        record["delivery"]["status"] = "completed"
    else:
        record["delivery"]["status"] = "aborted" if args.verdict == "aborted" else "blocked"
    record["verdict"] = args.verdict
    record["finished_at"] = now()
    if args.note:
        record["notes"].append({"at": now(), "text": args.note})
    event(record, "run-finished", verdict=args.verdict, delivery=record["delivery"]["status"])
    save(path, record)
    print(f"{record['id']}: {args.verdict}")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    new = sub.add_parser("new")
    new.add_argument("--root", required=True)
    new.add_argument("--skill", default="release")
    new.add_argument("--version", required=True)
    new.add_argument("--commit")
    new.add_argument("--trigger")
    new.add_argument("--repo")
    new.add_argument("--engine-version")
    new.add_argument("--python")
    new.add_argument("--mandatory", action="append", help="NAME or NAME:pre|post")
    new.add_argument("--optional", action="append", help="NAME or NAME:pre|post")
    new.set_defaults(func=cmd_new)

    setp = sub.add_parser("set")
    setp.add_argument("record")
    setp.add_argument("--commit")
    setp.add_argument("--version")
    setp.add_argument("--trigger")
    setp.add_argument("--digest", action="append", help="NAME=DIGEST of the tested artifact")
    setp.add_argument("--published", action="append", help="NAME=DIGEST observed in the registry")
    setp.add_argument("--check", action="append", help="NAME=STATUS[:EVIDENCE]")
    setp.add_argument("--on", help="source (default) or artifact:NAME")
    setp.add_argument("--mandatory", action="store_true")
    setp.add_argument("--optional", action="store_true")
    setp.add_argument("--stage", help="pre (feeds GO) or post (delivery)")
    setp.add_argument("--probe")
    setp.add_argument("--expect")
    setp.add_argument("--reuse-from", help="id of an earlier passed check whose result still applies")
    setp.add_argument("--waive", help="check name to waive by a recorded decision")
    setp.add_argument("--reason")
    setp.add_argument("--approve", help="action approved: publication, merge, tests, notes, ...")
    setp.add_argument("--scope")
    setp.add_argument("--conditions")
    setp.add_argument("--by", default="owner")
    setp.add_argument("--note", action="append")
    setp.add_argument("--python")
    setp.set_defaults(func=cmd_set)

    show = sub.add_parser("show")
    show.add_argument("record", nargs="?")
    show.add_argument("--root")
    show.add_argument("--skill", default="release")
    show.add_argument("--version")
    show.add_argument("--json", action="store_true")
    show.set_defaults(func=cmd_show)

    finish = sub.add_parser("finish")
    finish.add_argument("record")
    finish.add_argument("--verdict", required=True)
    finish.add_argument("--note")
    finish.set_defaults(func=cmd_finish)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
