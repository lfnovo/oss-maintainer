#!/usr/bin/env python3
"""Create, update and read run records under `.maintainer/state/runs/`.

A run record makes a release (or a smoke run) resumable and auditable: candidate, checks with
their status and evidence, authorizations with their scope, commands, verdict.

Usage:
  run_record.py new --root R --skill release --version V [--commit SHA] [--engine-version X]
  run_record.py update RECORD --phase NAME [--status S] [--check name=status[:evidence]]...
  run_record.py authorize RECORD --scope TEXT --candidate SHA [--by WHO]
  run_record.py candidate RECORD --commit SHA [--version V]     # resets checks and authorizations
  run_record.py digest RECORD --name REF --value DIGEST
  run_record.py latest --root R --skill release [--version V]
  run_record.py pending RECORD
  run_record.py finish RECORD --verdict GO|NO-GO|aborted [--note TEXT]

Requires Python 3.11+. Standard library only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

if sys.version_info < (3, 11):  # pragma: no cover
    sys.stderr.write("run_record.py needs Python 3.11 or newer.\n")
    sys.exit(2)

PHASES = [
    "scope", "version", "matrix", "bucket-a", "artifact-gate", "bucket-c", "fix-loop",
    "cut", "notes", "go", "publish", "verify", "announce", "cleanup", "retro",
]
TRIGGER_PHASE = "publish"
GO_PHASE = "go"
STATUSES = {"passed", "failed", "not-run", "not-applicable"}
VERDICTS = {"GO", "NO-GO", "aborted"}


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def runs_dir(root: Path) -> Path:
    return root / ".maintainer" / "state" / "runs"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, record: dict) -> None:
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def profile_hash(root: Path) -> str | None:
    profile = root / ".maintainer" / "profile.toml"
    if not profile.exists():
        return None
    digest = hashlib.sha256(profile.read_bytes())
    overlay = root / ".maintainer" / "profile.local.toml"
    if overlay.exists():
        digest.update(overlay.read_bytes())
    return "sha256:" + digest.hexdigest()


def phase(record: dict, name: str) -> dict:
    for entry in record["phases"]:
        if entry["name"] == name:
            return entry
    entry = {"name": name, "status": "not-run", "checks": [], "authorizations": []}
    record["phases"].append(entry)
    record["phases"].sort(key=lambda p: PHASES.index(p["name"]) if p["name"] in PHASES else len(PHASES))
    return entry


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
        "schema": 1,
        "skill": args.skill,
        "id": path.stem,
        "started_at": now(),
        "finished_at": None,
        "engine": {"plugin": "oss-maintainer", "version": args.engine_version, "resolution": args.resolution},
        "repo": args.repo,
        "candidate": {"version": args.version, "commit": args.commit, "digests": {}},
        "profile_hash": profile_hash(root),
        "overlay_diff": [],
        "phases": [],
        "commands": [],
        "items": [],
        "verdict": None,
        "notes": [],
    }
    save(path, record)
    print(path)
    return 0


def cmd_update(args) -> int:
    path = Path(args.record)
    record = load(path)
    entry = phase(record, args.phase)
    if args.status:
        if args.status not in STATUSES:
            print(f"invalid status {args.status}", file=sys.stderr)
            return 2
        entry["status"] = args.status
    for spec in args.check or []:
        name, _, rest = spec.partition("=")
        status, _, evidence = rest.partition(":")
        if status not in STATUSES:
            print(f"invalid check status in {spec}", file=sys.stderr)
            return 2
        entry["checks"] = [c for c in entry["checks"] if c["name"] != name]
        entry["checks"].append({"name": name, "status": status, "evidence": evidence or None, "at": now()})
    if args.command:
        run, _, exit_code = args.command.rpartition("=")
        record["commands"].append({"run": run, "exit": int(exit_code) if exit_code.lstrip("-").isdigit() else None, "at": now()})
    save(path, record)
    print(f"{args.phase}: {entry['status']}; checks: " + ", ".join(f"{c['name']}={c['status']}" for c in entry["checks"]))
    return 0


def cmd_authorize(args) -> int:
    path = Path(args.record)
    record = load(path)
    if record["candidate"]["commit"] and args.candidate != record["candidate"]["commit"]:
        print(f"authorization names candidate {args.candidate} but the record's candidate is {record['candidate']['commit']}", file=sys.stderr)
        return 1
    entry = phase(record, args.phase)
    entry["authorizations"].append({"scope": args.scope, "candidate": args.candidate, "granted_at": now(), "by": args.by})
    save(path, record)
    print(f"authorized: {args.scope} for {args.candidate}")
    return 0


def cmd_candidate(args) -> int:
    path = Path(args.record)
    record = load(path)
    previous = record["candidate"]["commit"]
    record["candidate"]["commit"] = args.commit
    if args.version:
        record["candidate"]["version"] = args.version
    record["candidate"]["digests"] = {}
    reset = 0
    for entry in record["phases"]:
        if entry["name"] in {"scope", "version", "matrix"}:
            continue
        for check in entry["checks"]:
            if check["status"] == "passed":
                check["status"] = "not-run"
                check["invalidated_by"] = args.commit
                reset += 1
        if entry["status"] == "passed":
            entry["status"] = "not-run"
        entry["authorizations"] = [dict(a, revoked=True) for a in entry["authorizations"]]
    record["notes"].append(f"{now()} candidate changed {previous} -> {args.commit}; {reset} checks reset")
    save(path, record)
    print(f"candidate {args.commit}; {reset} checks reset to not-run; authorizations revoked")
    return 0


def cmd_digest(args) -> int:
    path = Path(args.record)
    record = load(path)
    record["candidate"]["digests"][args.name] = args.value
    save(path, record)
    print(f"{args.name}: {args.value}")
    return 0


def cmd_latest(args) -> int:
    root = Path(args.root).resolve()
    candidates = sorted(runs_dir(root).glob(f"*-{args.skill}.json"), reverse=True)
    for path in candidates:
        record = load(path)
        if args.version and record["candidate"].get("version") != args.version:
            continue
        print(json.dumps({"path": str(path), **record}, indent=2, ensure_ascii=False))
        return 0
    print("null")
    return 1


def pending(record: dict) -> list[dict]:
    seen = {p["name"]: p for p in record["phases"]}
    out = []
    for name in PHASES:
        entry = seen.get(name)
        if entry is None:
            out.append({"phase": name, "status": "not-run", "checks": []})
            continue
        checks = [c for c in entry["checks"] if c["status"] not in {"passed", "not-applicable"}]
        if entry["status"] not in {"passed", "not-applicable"} or checks:
            out.append({"phase": name, "status": entry["status"], "checks": checks})
    return out


def cmd_pending(args) -> int:
    record = load(Path(args.record))
    print(json.dumps(pending(record), indent=2, ensure_ascii=False))
    return 0


def cmd_finish(args) -> int:
    path = Path(args.record)
    record = load(path)
    if args.verdict not in VERDICTS:
        print(f"invalid verdict {args.verdict}", file=sys.stderr)
        return 2
    record["verdict"] = args.verdict
    record["finished_at"] = now()
    if args.note:
        record["notes"].append(args.note)
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
    new.add_argument("--repo")
    new.add_argument("--engine-version")
    new.add_argument("--resolution")
    new.set_defaults(func=cmd_new)

    update = sub.add_parser("update")
    update.add_argument("record")
    update.add_argument("--phase", required=True, choices=PHASES)
    update.add_argument("--status", choices=sorted(STATUSES))
    update.add_argument("--check", action="append")
    update.add_argument("--command")
    update.set_defaults(func=cmd_update)

    authorize = sub.add_parser("authorize")
    authorize.add_argument("record")
    authorize.add_argument("--scope", required=True)
    authorize.add_argument("--candidate", required=True)
    authorize.add_argument("--phase", default=GO_PHASE, choices=PHASES)
    authorize.add_argument("--by", default="owner")
    authorize.set_defaults(func=cmd_authorize)

    candidate = sub.add_parser("candidate")
    candidate.add_argument("record")
    candidate.add_argument("--commit", required=True)
    candidate.add_argument("--version")
    candidate.set_defaults(func=cmd_candidate)

    digest = sub.add_parser("digest")
    digest.add_argument("record")
    digest.add_argument("--name", required=True)
    digest.add_argument("--value", required=True)
    digest.set_defaults(func=cmd_digest)

    latest = sub.add_parser("latest")
    latest.add_argument("--root", required=True)
    latest.add_argument("--skill", default="release")
    latest.add_argument("--version")
    latest.set_defaults(func=cmd_latest)

    pend = sub.add_parser("pending")
    pend.add_argument("record")
    pend.set_defaults(func=cmd_pending)

    finish = sub.add_parser("finish")
    finish.add_argument("record")
    finish.add_argument("--verdict", required=True)
    finish.add_argument("--note")
    finish.set_defaults(func=cmd_finish)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
