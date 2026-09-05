#!/usr/bin/env python3
"""Validate a repository's `.maintainer/profile.toml` and report readiness per capability.

Usage:
  validate_profile.py [--root PATH] [--capability NAME|all] [--json]

  --root        repository root (default: the git top-level of the cwd, else the cwd)
  --capability  one of init, release, triage, review-pr, process-discussions, smoke-e2e, all
  --json        machine-readable output

Exit codes: 0 every requested capability is ready or not applicable; 1 at least one is
incomplete or needs confirmation, or the profile has errors; 2 the profile is missing or
cannot be parsed.

Requires Python 3.11+ (tomllib). Standard library only.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

if sys.version_info < (3, 11):  # pragma: no cover
    sys.stderr.write("validate_profile.py needs Python 3.11 or newer (tomllib).\n")
    sys.exit(2)

import tomllib

SCHEMA_VERSION = 1
CAPABILITIES = ["init", "release", "triage", "review-pr", "process-discussions", "smoke-e2e"]
ARCHETYPES = {"app-docker", "pypi-library", "npm-package", "custom", "unknown"}
KNOWN_TABLES = {
    "project", "commands", "contributing", "release", "artifacts", "labels", "triage",
    "review", "discussions", "smoke", "comms", "channels", "upstreams",
}
OVERLAY_ALLOWED = {
    ("smoke", "api_url"), ("smoke", "frontend_url"), ("comms", "owner_language"),
    ("project", "commands_doc"),
}
OVERLAY_ALLOWED_TABLES = {"upstreams", "channels"}
LADDER_STATES = {"needs-triage", "needs-vision", "needs-design", "awaiting-demand", "ready", "close"}
BUILTIN_GATES = {"image-gate", "package-gate", "bucket-c", "notes-approved", "security-alerts"}
TIMEOUT = re.compile(r"^\d+[smh]$")
REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


class Report:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.capabilities: dict[str, dict] = {}
        self.overlay = {"applied": [], "rejected": []}

    def capability(self, name: str) -> dict:
        return self.capabilities.setdefault(
            name, {"status": "ready", "missing": [], "todos": [], "confirm": [], "warnings": [], "assumed": []}
        )


def repo_root(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).resolve()
    try:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True)
        return Path(out.stdout.strip()).resolve()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return Path.cwd().resolve()


def load_toml(path: Path) -> tuple[dict | None, str | None]:
    try:
        with path.open("rb") as handle:
            return tomllib.load(handle), None
    except (tomllib.TOMLDecodeError, OSError) as exc:
        return None, str(exc)


def leaves(value, prefix: str) -> list[str]:
    """Dotted paths of every leaf below a nested table, for precise overlay reports."""
    if not isinstance(value, dict) or not value:
        return [prefix]
    paths: list[str] = []
    for key, item in value.items():
        paths.extend(leaves(item, f"{prefix}.{key}"))
    return paths


def merge_overlay(profile: dict, overlay: dict, report: Report) -> None:
    for table, value in overlay.items():
        if table in OVERLAY_ALLOWED_TABLES and isinstance(value, dict):
            profile.setdefault(table, {}).update(value)
            report.overlay["applied"].extend(f"{table}.{k}" for k in value)
            continue
        if not isinstance(value, dict):
            report.overlay["rejected"].append(table)
            continue
        for key, item in value.items():
            if (table, key) in OVERLAY_ALLOWED:
                profile.setdefault(table, {})[key] = item
                report.overlay["applied"].append(f"{table}.{key}")
            else:
                report.overlay["rejected"].extend(leaves(item, f"{table}.{key}"))


def marker(value) -> str | None:
    if isinstance(value, str):
        if value.strip().upper().startswith("TODO"):
            return "todo"
        if value.strip().upper().startswith("CONFIRM:"):
            return "confirm"
    return None


def check_field(cap: dict, table: dict, dotted: str, kind: str, required: bool, root: Path,
                enum: set | None = None) -> object:
    """Validate one field; record problems on the capability; return the value or None."""
    key = dotted.split(".")[-1]
    value = table.get(key)
    if value is None:
        if required:
            cap["missing"].append(dotted)
        return None
    flag = marker(value)
    if flag == "todo":
        cap["todos"].append(dotted)
        return None
    if flag == "confirm":
        cap["confirm"].append(dotted)
        value = value.split(":", 1)[1].strip()
    if kind == "str" and not isinstance(value, str):
        cap["missing"].append(f"{dotted} (expected string)")
        return None
    if kind == "list" and not (isinstance(value, list) and all(isinstance(v, str) for v in value)):
        cap["missing"].append(f"{dotted} (expected list of strings)")
        return None
    if kind == "table" and not isinstance(value, dict):
        cap["missing"].append(f"{dotted} (expected table)")
        return None
    if kind in {"path", "paths"}:
        paths = [value] if kind == "path" else value
        if not isinstance(paths, list) or not all(isinstance(p, str) for p in paths):
            cap["missing"].append(f"{dotted} (expected path or list of paths)")
            return None
        for item in paths:
            if Path(item).is_absolute():
                cap["missing"].append(f"{dotted}: absolute path not allowed ({item})")
            elif not (root / item).exists():
                cap["missing"].append(f"{dotted}: path does not exist ({item})")
    if enum is not None and value not in enum:
        cap["missing"].append(f"{dotted}: expected one of {sorted(enum)}")
        return None
    return value


def validate_commands(profile: dict, cap: dict, root: Path) -> dict:
    commands = profile.get("commands", {})
    if not isinstance(commands, dict):
        cap["missing"].append("commands (expected table of tables)")
        return {}
    for name, spec in commands.items():
        if not isinstance(spec, dict):
            cap["missing"].append(f"commands.{name} (expected table with run, cwd, timeout)")
            continue
        check_field(cap, spec, f"commands.{name}.run", "str", True, root)
        cwd = spec.get("cwd", ".")
        if not isinstance(cwd, str) or Path(cwd).is_absolute() or not (root / cwd).is_dir():
            cap["missing"].append(f"commands.{name}.cwd: directory does not exist ({cwd})")
        timeout = spec.get("timeout", "10m")
        if not isinstance(timeout, str) or not TIMEOUT.match(timeout):
            cap["missing"].append(f"commands.{name}.timeout: expected <number>[smh] ({timeout})")
    return commands


def validate_init(profile: dict, report: Report, root: Path) -> None:
    cap = report.capability("init")
    project = profile.get("project", {})
    check_field(cap, project, "project.name", "str", True, root)
    repo = check_field(cap, project, "project.repo", "str", True, root)
    if isinstance(repo, str) and not REPO.match(repo):
        cap["missing"].append("project.repo: expected owner/name")
    if "commands_doc" in project:
        check_field(cap, project, "project.commands_doc", "path", False, root)
    comms = profile.get("comms", {})
    if comms.get("agent_attribution", "none") not in {"none", "disclaimer"}:
        cap["missing"].append("comms.agent_attribution: expected none or disclaimer")


def validate_release(profile: dict, report: Report, root: Path) -> None:
    cap = report.capability("release")
    project = profile.get("project", {})
    artifact = check_field(cap, project, "project.artifact", "str", True, root, ARCHETYPES)
    if artifact == "unknown":
        cap["missing"].append("project.artifact is unknown; set the archetype before releasing")
    commands = validate_commands(profile, cap, root)
    if "validator" not in commands:
        cap["missing"].append("commands.validator")
    release = profile.get("release", {})
    check_field(cap, release, "release.changelog", "path", True, root)
    files = check_field(cap, release, "release.version_files", "paths", True, root)
    if isinstance(files, list) and not files:
        cap["missing"].append("release.version_files must not be empty")
    check_field(cap, release, "release.distribution_trigger", "str", True, root)
    for optional in ("process_doc", "publish_workflow", "notes_source"):
        if optional in release:
            check_field(cap, release, f"release.{optional}", "path", False, root)
    gates = release.get("gates", {})
    mandatory = gates.get("mandatory", ["validator"])
    optional_gates = gates.get("optional", [])
    known = set(commands) | BUILTIN_GATES
    for group, names in (("mandatory", mandatory), ("optional", optional_gates)):
        if not isinstance(names, list):
            cap["missing"].append(f"release.gates.{group} (expected list)")
            continue
        for name in names:
            if name not in known:
                cap["missing"].append(f"release.gates.{group}: unknown gate {name}")
    if gates.get("merge_own_prs", "ask-once-per-session") not in {"ask-once-per-session", "always-ask", "never"}:
        cap["missing"].append("release.gates.merge_own_prs: expected ask-once-per-session, always-ask or never")
    artifacts = profile.get("artifacts", {})
    if artifact == "app-docker":
        docker = artifacts.get("docker", {})
        registries = check_field(cap, docker, "artifacts.docker.registries", "list", True, root)
        if isinstance(registries, list) and not registries:
            cap["missing"].append("artifacts.docker.registries must not be empty")
        check_field(cap, docker, "artifacts.docker.gate", "str", True, root)
    elif artifact == "pypi-library":
        pypi = artifacts.get("pypi", {})
        check_field(cap, pypi, "artifacts.pypi.package", "str", True, root)
        check_field(cap, pypi, "artifacts.pypi.gate", "str", True, root)
    elif artifact == "npm-package":
        npm = artifacts.get("npm", {})
        check_field(cap, npm, "artifacts.npm.package", "str", True, root)
        cap["warnings"].append("npm-package archetype is a placeholder in schema v1")
    elif artifact == "custom":
        if not (root / ".maintainer" / "release" / "runbook.md").exists():
            cap["missing"].append("custom archetype requires .maintainer/release/runbook.md")


def validate_triage(profile: dict, report: Report, root: Path) -> None:
    cap = report.capability("triage")
    if "labels" not in profile:
        cap["assumed"].append("labels: preset names")
    triage = profile.get("triage", {})
    if not triage:
        cap["assumed"].append("triage: maturity-ladder preset, one-at-a-time approval")
        return
    extra = triage.get("extra_states", {})
    if not isinstance(extra, dict):
        cap["missing"].append("triage.extra_states (expected table)")
        extra = {}
    assignable = check_field(cap, triage, "triage.assignable", "list", False, root)
    if isinstance(assignable, list):
        for state in assignable:
            if state not in LADDER_STATES | set(extra):
                cap["missing"].append(f"triage.assignable: unknown state {state}")
    if "rules" in triage:
        check_field(cap, triage, "triage.rules", "path", False, root)
    if triage.get("batch_approval", "one-at-a-time") not in {"one-at-a-time", "allowed"}:
        cap["missing"].append("triage.batch_approval: expected one-at-a-time or allowed")


def validate_review(profile: dict, report: Report, root: Path) -> None:
    cap = report.capability("review-pr")
    review = profile.get("review", {})
    if "docs" in review:
        check_field(cap, review, "review.docs", "paths", False, root)
    else:
        cap["assumed"].append("review.docs: found by function (agent docs, architecture, contributing)")
    if "reviewers" in review:
        check_field(cap, review, "review.reviewers", "list", False, root)


def validate_discussions(profile: dict, report: Report, root: Path) -> None:
    cap = report.capability("process-discussions")
    discussions = profile.get("discussions")
    if discussions is None:
        cap["status"] = "not-applicable"
        return
    categories = check_field(cap, discussions, "discussions.categories", "table", True, root)
    if isinstance(categories, dict) and (not categories or not all(isinstance(v, str) for v in categories.values())):
        cap["missing"].append("discussions.categories must map names to ids")
    if "public_anchors" in discussions:
        check_field(cap, discussions, "discussions.public_anchors", "paths", False, root)
    if discussions.get("graduation", "pull") not in {"pull", "push"}:
        cap["missing"].append("discussions.graduation: expected pull or push")
    close_on = discussions.get("close_on", ["answer", "graduated-work-landed"])
    if not isinstance(close_on, list) or not set(close_on) <= {"answer", "graduated-work-landed", "never"}:
        cap["missing"].append("discussions.close_on: expected a list of answer, graduated-work-landed, never")


def validate_smoke(profile: dict, report: Report, root: Path) -> None:
    cap = report.capability("smoke-e2e")
    smoke = profile.get("smoke")
    if smoke is None:
        cap["status"] = "not-applicable"
        return
    check_field(cap, smoke, "smoke.api_url", "str", True, root)
    journey = smoke.get("journey", ".maintainer/smoke/journey.md")
    if Path(journey).is_absolute() or not (root / journey).exists():
        cap["missing"].append(f"smoke.journey: path does not exist ({journey})")
    surfaces = smoke.get("mandatory_surfaces", ["api"])
    if not isinstance(surfaces, list) or not set(surfaces) <= {"api", "ui", "db"}:
        cap["missing"].append("smoke.mandatory_surfaces: expected a list of api, ui, db")


VALIDATORS = {
    "init": validate_init,
    "release": validate_release,
    "triage": validate_triage,
    "review-pr": validate_review,
    "process-discussions": validate_discussions,
    "smoke-e2e": validate_smoke,
}


def finalize(report: Report) -> None:
    for cap in report.capabilities.values():
        if cap["status"] == "not-applicable":
            continue
        if cap["missing"] or cap["todos"]:
            cap["status"] = "incomplete"
        elif cap["confirm"]:
            cap["status"] = "needs-confirmation"
        else:
            cap["status"] = "ready"


def no_profile_report(report: Report, requested: list[str]) -> None:
    read_only = {"review-pr", "triage"}
    for name in requested:
        cap = report.capability(name)
        if name in read_only:
            cap["assumed"].append("no profile: read-only mode with engine presets")
        else:
            cap["missing"].append(".maintainer/profile.toml")
    finalize(report)


def validate(root: Path, requested: list[str]) -> tuple[Report, dict | None, int]:
    report = Report(root)
    profile_path = root / ".maintainer" / "profile.toml"
    if not profile_path.exists():
        report.errors.append(f"profile missing: {profile_path.relative_to(root)}")
        no_profile_report(report, requested)
        return report, None, 2
    profile, error = load_toml(profile_path)
    if profile is None:
        report.errors.append(f"profile cannot be parsed: {error}")
        return report, None, 2
    overlay_path = root / ".maintainer" / "profile.local.toml"
    if overlay_path.exists():
        overlay, error = load_toml(overlay_path)
        if overlay is None:
            report.warnings.append(f"overlay ignored, cannot be parsed: {error}")
        else:
            merge_overlay(profile, overlay, report)
    version = profile.get("schema_version")
    if version != SCHEMA_VERSION:
        report.errors.append(f"schema_version must be {SCHEMA_VERSION} (found {version!r})")
    for table in profile:
        if table != "schema_version" and table not in KNOWN_TABLES:
            report.warnings.append(f"unknown table [{table}] ignored")
    for name in requested:
        VALIDATORS[name](profile, report, root)
    finalize(report)
    blocking = report.errors or any(
        cap["status"] in {"incomplete", "needs-confirmation"} for cap in report.capabilities.values()
    )
    return report, profile, 1 if blocking else 0


def render_text(report: Report, profile: dict | None) -> str:
    lines = [f"profile root: {report.root}"]
    lines.append("")
    lines.append(f"{'capability':22} {'status':20} details")
    for name, cap in report.capabilities.items():
        details = []
        details += [f"missing {m}" for m in cap["missing"]]
        details += [f"TODO {t}" for t in cap["todos"]]
        details += [f"confirm {c}" for c in cap["confirm"]]
        details += [f"assumed {a}" for a in cap["assumed"]]
        details += [f"warning {w}" for w in cap["warnings"]]
        lines.append(f"{name:22} {cap['status']:20} {'; '.join(details)}")
    if report.overlay["applied"] or report.overlay["rejected"]:
        lines.append("")
        lines.append(f"overlay applied: {', '.join(report.overlay['applied']) or 'none'}")
        lines.append(f"overlay rejected (policy fields cannot be overridden locally): {', '.join(report.overlay['rejected']) or 'none'}")
    for error in report.errors:
        lines.append(f"error: {error}")
    for warning in report.warnings:
        lines.append(f"warning: {warning}")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root")
    parser.add_argument("--capability", default="all", choices=CAPABILITIES + ["all"])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    root = repo_root(args.root)
    requested = CAPABILITIES if args.capability == "all" else [args.capability]
    report, profile, code = validate(root, requested)
    if args.json:
        payload = {
            "schema_version": SCHEMA_VERSION,
            "root": str(root),
            "profile": None if profile is None else str((root / ".maintainer" / "profile.toml").relative_to(root)),
            "effective_profile": profile,
            "capabilities": report.capabilities,
            "overlay": report.overlay,
            "errors": report.errors,
            "warnings": report.warnings,
            "exit_code": code,
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(render_text(report, profile))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
