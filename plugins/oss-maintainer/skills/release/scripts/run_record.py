#!/usr/bin/env python3
"""Create, update and read run records under `.maintainer/state/runs/`.

A run record makes a release (or a smoke run) resumable and auditable: candidate, checks with
their status and evidence, authorizations with their scope, commands, verdict.

Usage:
  run_record.py new --root R --skill release --version V [--commit SHA] [--engine-version X]
  run_record.py update RECORD --phase NAME [--status S] [--check name=status[:evidence]]...
  run_record.py authorize RECORD --scope TEXT --candidate SHA [--by WHO]
  run_record.py candidate RECORD --commit SHA [--version V]     # invalidates affected dependencies
  run_record.py digest RECORD --name REF --value DIGEST [--published]
  run_record.py latest --root R --skill release [--version V]
  run_record.py pending RECORD
  run_record.py finish RECORD --verdict GO|NO-GO|aborted [--note TEXT]

Requires Python 3.11+. Standard library only.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import uuid
import re
import tomllib
import sys
from datetime import datetime, timezone
from pathlib import Path

if sys.version_info < (3, 11):  # pragma: no cover
    sys.stderr.write("run_record.py needs Python 3.11 or newer.\n")
    sys.exit(2)

PHASES = [
    "scope",
    "version",
    "matrix",
    "bucket-a",
    "artifact-gate",
    "bucket-c",
    "fix-loop",
    "cut",
    "notes",
    "go",
    "publish",
    "verify",
    "announce",
    "cleanup",
    "retro",
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
    record = json.loads(path.read_text(encoding="utf-8"))
    if record.get("schema") not in {1, 2}:
        raise ValueError("unsupported run-record schema")
    # Reading does not rewrite history. The next mutation persists the additive migration.
    if record["schema"] == 1:
        record["schema"] = 2
        record["legacy_schema"] = 1
    record.setdefault("events", [])
    record.setdefault(
        "delivery",
        {
            "status": "unknown" if record.get("finished_at") else "pending",
            "required_phases": ["publish", "verify", "announce", "cleanup"],
            "required_checks": [],
            "retrospective": "pending",
        },
    )
    return record


def save(path: Path, record: dict) -> None:
    path.write_text(
        json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


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
    record["phases"].sort(
        key=lambda p: PHASES.index(p["name"]) if p["name"] in PHASES else len(PHASES)
    )
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
    required_phases = list(
        dict.fromkeys(
            (
                ["publish", "verify", "announce", "cleanup"]
                if args.skill == "release"
                else []
            )
            + (args.required_phase or [])
        )
    )
    required_checks = (["validator"] if args.skill == "release" else []) + list(
        args.required_check or []
    )
    profile_path = root / ".maintainer" / "profile.toml"
    if args.skill == "release" and profile_path.exists():
        profile = tomllib.loads(profile_path.read_text())
        required_checks += (
            profile.get("release", {}).get("gates", {}).get("mandatory", ["validator"])
        )
    record = {
        "schema": 2,
        "skill": args.skill,
        "id": path.stem,
        "started_at": now(),
        "finished_at": None,
        "engine": {
            "plugin": "oss-maintainer",
            "version": args.engine_version,
            "resolution": args.resolution,
        },
        "repo": args.repo,
        "candidate": {"version": args.version, "commit": args.commit, "digests": {}},
        "published": {"digests": {}},
        "superseded": [],
        "profile_hash": profile_hash(root),
        "root": str(root),
        "overlay_diff": [],
        "phases": [],
        "commands": [],
        "items": [],
        "verdict": None,
        "notes": [],
        "events": [],
        "delivery": {
            "status": "pending",
            "required_phases": required_phases,
            "required_checks": list(dict.fromkeys(required_checks)),
            "retrospective": "pending",
        },
    }
    save(path, record)
    print(path)
    return 0


def event(record: dict, kind: str, **fields) -> dict:
    item = {"id": uuid.uuid4().hex, "kind": kind, "recorded_at": now(), **fields}
    record.setdefault("events", []).append(item)
    return item


def dependencies(record: dict, specs: list[str] | None) -> dict:
    candidate = record["candidate"]
    result = {}
    for spec in specs or ["candidate"]:
        if spec == "source":
            if not candidate.get("commit"):
                raise ValueError("source evidence requires a commit")
            result[spec] = candidate["commit"]
        elif spec == "candidate":
            result[spec] = deepcopy(candidate)
        elif spec.startswith("artifact:"):
            name = spec.split(":", 1)[1]
            if not candidate["digests"].get(name):
                raise ValueError(f"record the tested artifact identity first: {name}")
            result[spec] = candidate["digests"][name]
        else:
            raise ValueError(f"unknown dependency: {spec}")
    return result


def matches(deps: dict, candidate: dict) -> bool:
    for name, value in deps.items():
        actual = (
            candidate
            if name == "candidate"
            else candidate.get("commit")
            if name == "source"
            else candidate.get("digests", {}).get(name.split(":", 1)[1])
        )
        if actual != value:
            return False
    return True


def command_records(args) -> list[dict]:
    commands = []
    for spec in args.command or []:
        run, sep, status = spec.rpartition("=")
        if not sep or not run.strip() or not re.fullmatch(r"-?\d+", status):
            raise ValueError(
                "--command requires nonempty COMMAND=INTEGER_EXIT_STATUS; repeat for multiple commands"
            )
        commands.append(
            {
                "id": uuid.uuid4().hex,
                "run": run,
                "exit": int(status),
                "at": now(),
                "recorded_at": now(),
                "executed_at": args.executed_at,
                "cwd": args.cwd,
                "log": args.log,
            }
        )
    if args.executed_at:
        timestamp(args.executed_at)
    if args.executed_at and not commands:
        raise ValueError("--executed-at requires --command")
    return commands


def timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include a timezone")
    return parsed


def cmd_update(args) -> int:
    path = Path(args.record)
    record = load(path)
    commands = command_records(args)  # validate before any disk mutation
    if args.digest:
        candidate = deepcopy(record["candidate"])
        for spec in args.digest:
            name, sep, value = spec.partition("=")
            if not sep or not name.strip() or not value.strip():
                raise ValueError("--digest requires NAME=DIGEST")
            candidate["digests"][name] = value
        invalidate_candidate(
            record, candidate, "artifact identity registered with evidence"
        )
    deps = dependencies(record, args.depends_on)
    entry = phase(record, args.phase)
    if args.status:
        entry["status"] = args.status
    for spec in args.check or []:
        name, _, rest = spec.partition("=")
        status, _, evidence = rest.partition(":")
        if not name.strip() or status not in STATUSES:
            raise ValueError(f"invalid check: {spec}")
        previous = [c for c in entry["checks"] if c["name"] == name]
        if previous:
            event(
                record,
                "check-superseded",
                phase=args.phase,
                check=deepcopy(previous[0]),
            )
        entry["checks"] = [c for c in entry["checks"] if c["name"] != name]
        check = {
            "id": uuid.uuid4().hex,
            "name": name,
            "status": status,
            "evidence": evidence or None,
            "at": now(),
            "dependencies": deps,
            "execution_ids": [c["id"] for c in commands],
        }
        entry["checks"].append(check)
        event(record, "check-recorded", phase=args.phase, check=deepcopy(check))
    record["commands"].extend(commands)
    if args.phase != "retro" and record.get("finished_at"):
        event(
            record,
            "delivery-reopened",
            reason="new delivery observation",
            phase=args.phase,
        )
        record["finished_at"] = None
        record["verdict"] = None
        record["delivery"]["status"] = "pending"
    if args.phase == "retro" and args.status:
        record["delivery"]["retrospective"] = args.status
    save(path, record)
    print(f"{args.phase}: {entry['status']}")
    return 0


def cmd_revalidate(args) -> int:
    path = Path(args.record)
    record = load(path)
    entry = phase(record, args.phase)
    check = next((c for c in entry["checks"] if c.get("id") == args.evidence_id), None)
    if not check or not check.get("dependencies"):
        raise ValueError(
            "revalidation requires an existing identified check with explicit dependencies"
        )
    if not matches(check["dependencies"], record["candidate"]) or check.get(
        "invalidated_by"
    ):
        raise ValueError(
            "evidence dependencies changed; execute the affected check again"
        )
    event(
        record,
        "evidence-revalidated",
        evidence_id=check["id"],
        reason=args.reason,
        identity=deepcopy(record["candidate"]),
    )
    save(path, record)
    print(check["id"])
    return 0


def cmd_authorize(args) -> int:
    path = Path(args.record)
    record = load(path)
    if not args.scope.strip():
        raise ValueError("authorization scope must not be empty")
    kind = args.kind
    if kind == "publication" and (
        not args.candidate or args.candidate != record["candidate"]["commit"]
    ):
        print(
            "publication authorization must name the current candidate", file=sys.stderr
        )
        return 1
    if record.get("root") and profile_hash(Path(record["root"])) != record.get(
        "profile_hash"
    ):
        raise ValueError(
            "profile changed; start a new agreement/run before authorizing"
        )
    if kind != "publication" and not args.conditions:
        raise ValueError("action-scoped approval requires explicit --conditions")
    if kind == "notes" and not args.subject:
        raise ValueError(
            "notes approval requires --subject (hash of approved text and factual context)"
        )
    if args.limit is not None and args.limit < 1:
        raise ValueError("authorization limit must be positive")
    if args.expires_at:
        if timestamp(args.expires_at) <= datetime.now(timezone.utc):
            raise ValueError("authorization already expired")
    approval = {
        "id": uuid.uuid4().hex,
        "kind": kind,
        "scope": args.scope,
        "conditions": args.conditions,
        "resources": args.resource or [],
        "subject": args.subject,
        "limit": args.limit,
        "used": 0,
        "expires_at": args.expires_at,
        "repo": record.get("repo"),
        "run_id": record["id"],
        "profile_hash": record.get("profile_hash"),
        "granted_at": now(),
        "by": args.by,
    }
    if kind in {"publication", "notes"}:
        approval.update(
            candidate=record["candidate"]["commit"],
            identity=deepcopy(record["candidate"]),
        )
    phase(record, args.phase)["authorizations"].append(approval)
    event(record, "authorization-granted", authorization=deepcopy(approval))
    save(path, record)
    print(approval["id"])
    return 0


def approval_valid(approval: dict, record: dict) -> bool:
    if approval.get("revoked"):
        return False
    if record.get("root") and profile_hash(Path(record["root"])) != record.get(
        "profile_hash"
    ):
        return False
    if approval.get("expires_at") and timestamp(approval["expires_at"]) <= datetime.now(
        timezone.utc
    ):
        return False
    if (
        approval.get("limit") is not None
        and approval.get("used", 0) >= approval["limit"]
    ):
        return False
    if approval.get("kind") == "notes":
        return bool(
            approval.get("subject")
            and approval.get("identity")
            and all(
                approval["identity"].get(k) == record["candidate"].get(k)
                for k in ("commit", "version")
            )
        )
    if approval.get("kind") in {"merge", "tests"}:
        return approval.get("run_id") == record["id"] and approval.get(
            "profile_hash"
        ) == record.get("profile_hash")
    return bool(
        approval.get("identity") and approval["identity"] == record["candidate"]
    )


def cmd_permissions(args) -> int:
    record = load(Path(args.record))
    print(
        json.dumps(
            [
                {**a, "valid": approval_valid(a, record)}
                for p in record["phases"]
                for a in p["authorizations"]
            ],
            indent=2,
        )
    )
    return 0


def cmd_consume(args) -> int:
    path = Path(args.record)
    record = load(path)
    approval = next(
        (
            a
            for p in record["phases"]
            for a in p["authorizations"]
            if a.get("id") == args.authorization
        ),
        None,
    )
    if not approval or not approval_valid(approval, record):
        raise ValueError("approval missing, expired, revoked or no longer applicable")
    if args.units < 1 or (
        approval.get("limit") is not None
        and approval.get("used", 0) + args.units > approval["limit"]
    ):
        raise ValueError("execution exceeds authorized limit")
    approval["used"] = approval.get("used", 0) + args.units
    event(
        record,
        "authorization-consumed",
        authorization_id=approval["id"],
        units=args.units,
        reason=args.reason,
    )
    save(path, record)
    print(approval["used"])
    return 0


def invalidate_candidate(record: dict, candidate: dict, reason: str) -> int:
    """Supersede candidate-bound evidence without losing its original status or identity."""
    if candidate == record["candidate"]:
        return 0
    record.setdefault("superseded", []).append(
        {
            "at": now(),
            "reason": reason,
            **deepcopy(
                {
                    key: record.get(key)
                    for key in (
                        "candidate",
                        "phases",
                        "published",
                        "verdict",
                        "finished_at",
                    )
                }
            ),
        }
    )
    previous = record["candidate"]
    record["candidate"] = candidate
    record["verdict"] = None
    record["finished_at"] = None
    record["delivery"]["status"] = "pending"
    record["published"] = {"digests": {}}
    reset = 0
    for entry in record["phases"]:
        for approval in entry["authorizations"]:
            # Old permissions have no proven action scope; remain conservative.
            if approval.get("kind") not in {"merge", "tests"}:
                if approval.get("kind") != "notes" or not approval_valid(
                    approval, record
                ):
                    approval["revoked"] = True
        affected = False
        for check in entry["checks"]:
            deps = check.get("dependencies", {"candidate": previous})
            if not matches(deps, candidate):
                check["status"] = "not-run"
                check["invalidated_by"] = candidate["commit"]
                affected = True
                reset += 1
        if affected or (
            not entry["checks"] and entry["name"] not in {"scope", "version", "matrix"}
        ):
            entry["status"] = "not-run"
    event(
        record,
        "candidate-changed",
        reason=reason,
        previous=deepcopy(previous),
        identity=deepcopy(candidate),
    )
    record["notes"].append(f"{now()} {reason}; {reset} checks reset")
    return reset


def cmd_candidate(args) -> int:
    path = Path(args.record)
    record = load(path)
    candidate = deepcopy(record["candidate"])
    candidate["commit"] = args.commit
    if args.version:
        candidate["version"] = args.version
    if candidate != record["candidate"]:
        candidate["digests"] = {}
    reset = invalidate_candidate(
        record,
        candidate,
        f"candidate changed to {args.commit} / {candidate['version']}",
    )
    save(path, record)
    print(f"candidate {args.commit}; {reset} checks reset to not-run")
    return 0


def cmd_digest(args) -> int:
    path = Path(args.record)
    record = load(path)
    if not args.name.strip() or not args.value.strip():
        raise ValueError("digest name and value must not be empty")
    if args.published:
        record.setdefault("published", {"digests": {}})["digests"][args.name] = (
            args.value
        )
    else:
        candidate = deepcopy(record["candidate"])
        candidate["digests"][args.name] = args.value
        invalidate_candidate(
            record, candidate, f"candidate digest changed: {args.name}"
        )
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
        checks = [
            c
            for c in entry["checks"]
            if c["status"] not in {"passed", "not-applicable"}
        ]
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
        raise ValueError(f"invalid verdict {args.verdict}")
    if args.verdict == "GO":
        required = record["delivery"]["required_phases"]
        if not required:
            raise ValueError(
                "completion requires an explicit delivery contract (--required-phase on new)"
            )
        phases = {p["name"]: p for p in record["phases"]}
        missing = []
        for name in required:
            p = phases.get(name, {})
            allowed = (
                {"passed", "not-applicable"}
                if name in {"announce", "cleanup"}
                else {"passed"}
            )
            if (
                p.get("status") not in allowed
                or not p.get("checks")
                or any(
                    c["status"] not in allowed or not c.get("evidence")
                    for c in p.get("checks", [])
                )
            ):
                missing.append(name)
        for name in record["delivery"]["required_checks"]:
            if not any(
                c["name"] == name and c["status"] == "passed" and c.get("evidence")
                for p in phases.values()
                for c in p["checks"]
            ):
                missing.append(name)
        if missing:
            raise ValueError("delivery incomplete: " + ", ".join(missing))
        record["delivery"]["status"] = "completed"
    else:
        record["delivery"]["status"] = (
            "aborted" if args.verdict == "aborted" else "blocked"
        )
    record["verdict"] = args.verdict
    record["finished_at"] = now()
    if args.note:
        record["notes"].append(args.note)
    event(
        record,
        "run-finished",
        verdict=args.verdict,
        delivery=record["delivery"]["status"],
    )
    save(path, record)
    print(f"{record['id']}: {args.verdict}")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="command", required=True)

    new = sub.add_parser("new")
    new.add_argument("--root", required=True)
    new.add_argument("--skill", default="release")
    new.add_argument("--version", required=True)
    new.add_argument("--commit")
    new.add_argument("--repo")
    new.add_argument("--engine-version")
    new.add_argument("--resolution")
    new.add_argument("--required-phase", action="append", choices=PHASES)
    new.add_argument("--required-check", action="append")
    new.set_defaults(func=cmd_new)

    update = sub.add_parser("update")
    update.add_argument("record")
    update.add_argument("--phase", required=True, choices=PHASES)
    update.add_argument("--status", choices=sorted(STATUSES))
    update.add_argument("--check", action="append")
    update.add_argument("--command", action="append")
    update.add_argument("--executed-at")
    update.add_argument("--cwd", default=".")
    update.add_argument("--log")
    update.add_argument(
        "--depends-on", action="append", help="source, candidate or artifact:NAME"
    )
    update.add_argument(
        "--digest", action="append", help="atomic artifact identity and gate result"
    )
    update.set_defaults(func=cmd_update)

    authorize = sub.add_parser("authorize")
    authorize.add_argument("record")
    authorize.add_argument("--scope", required=True)
    authorize.add_argument("--candidate")
    authorize.add_argument(
        "--kind",
        choices=["publication", "merge", "tests", "notes"],
        default="publication",
    )
    authorize.add_argument("--conditions")
    authorize.add_argument("--resource", action="append")
    authorize.add_argument("--limit", type=int)
    authorize.add_argument("--subject")
    authorize.add_argument("--expires-at")
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
    digest.add_argument(
        "--published",
        action="store_true",
        help="record an observed distributed digest without changing the candidate",
    )
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

    reuse = sub.add_parser("revalidate")
    reuse.add_argument("record")
    reuse.add_argument("--phase", required=True, choices=PHASES)
    reuse.add_argument("--evidence-id", required=True)
    reuse.add_argument("--reason", required=True)
    reuse.set_defaults(func=cmd_revalidate)

    permissions = sub.add_parser("permissions")
    permissions.add_argument("record")
    permissions.set_defaults(func=cmd_permissions)

    consume = sub.add_parser("consume")
    consume.add_argument("record")
    consume.add_argument("--authorization", required=True)
    consume.add_argument("--units", type=int, default=1)
    consume.add_argument("--reason", required=True)
    consume.set_defaults(func=cmd_consume)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
