#!/usr/bin/env python3
"""Detect what a repository already declares about building, versioning and publishing.

Reads the Makefile, the GitHub workflows, package manifests and the usual documents, and
prints a JSON proposal for the `.maintainer/profile.toml` fields that can be derived:
artifact archetype, distribution trigger, version files, changelog, command docs.

Every value is a candidate for the maintainer to confirm. The script never guesses a
command that is not written somewhere in the repository.

Usage: detect_repo.py [--root PATH] [--json]   (text output when --json is omitted)
Requires Python 3.11+. Standard library only; workflow files are scanned with regular
expressions, not a YAML parser.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

if sys.version_info < (3, 11):  # pragma: no cover
    sys.stderr.write("detect_repo.py needs Python 3.11 or newer.\n")
    sys.exit(2)

PUBLISH_STEP = re.compile(
    r"uv publish|twine upload|pypa/gh-action-pypi-publish|npm publish|pnpm publish|yarn publish|"
    r"docker push|docker/build-push-action|cargo publish|gh release create|goreleaser",
    re.I,
)
DOCKER_PUBLISH = re.compile(r"docker push|docker/build-push-action", re.I)
PYPI_PUBLISH = re.compile(r"uv publish|twine upload|pypa/gh-action-pypi-publish", re.I)
NPM_PUBLISH = re.compile(r"npm publish|pnpm publish|yarn publish", re.I)
TAG_PUSH = re.compile(r"git push\b.*(tag|refs/tags|v\$\$?\w*version|\$\(?version|v\d)", re.I)
TARGET = re.compile(r"^([A-Za-z0-9_./-]+)\s*:(?!=)")


def repo_root(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).resolve()
    try:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True)
        return Path(out.stdout.strip()).resolve()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return Path.cwd().resolve()


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def first_existing(root: Path, candidates: list[str]) -> str | None:
    for candidate in candidates:
        matches = sorted(root.glob(candidate))
        for match in matches:
            if match.is_file():
                return match.relative_to(root).as_posix()
    return None


def makefile_targets(root: Path) -> dict[str, dict]:
    targets: dict[str, dict] = {}
    text = read(root / "Makefile")
    current: str | None = None
    for number, line in enumerate(text.splitlines(), 1):
        match = TARGET.match(line)
        if match and not line.startswith(("\t", " ")):
            current = match.group(1)
            if current.startswith("."):
                current = None
                continue
            targets[current] = {"line": number, "recipe": [], "pushes_tag": False, "publishes": False, "creates_tag": False}
            continue
        if current and line.startswith("\t"):
            recipe = line.strip()
            targets[current]["recipe"].append(recipe)
            if TAG_PUSH.search(recipe):
                targets[current]["pushes_tag"] = True
            if re.search(r"\bgit tag\b", recipe):
                targets[current]["creates_tag"] = True
            if PUBLISH_STEP.search(recipe):
                targets[current]["publishes"] = True
    return targets


def workflow_triggers(text: str) -> dict:
    """Extract the `on:` block shape with regexes: tags, release, dispatch, push branches."""
    triggers = {"push_tags": False, "push_branches": [], "release": False, "workflow_dispatch": False, "pull_request": False}
    on_match = re.search(r"^on:\s*(.*?)(?=^\S)", text, re.S | re.M)
    if on_match:
        block = on_match.group(0)
    else:
        start = text.find("\non:")
        block = text[start + 1:] if start >= 0 else (text if text.startswith("on:") else "")
    if re.search(r"^on:\s*\[([^\]]*)\]", text, re.M):
        inline = re.search(r"^on:\s*\[([^\]]*)\]", text, re.M).group(1)
        triggers["push_branches"] = ["*"] if "push" in inline else []
        triggers["workflow_dispatch"] = "workflow_dispatch" in inline
        triggers["pull_request"] = "pull_request" in inline
        return triggers
    push = re.search(r"^\s+push:\s*\n((?:\s{4,}.*\n?)*)", block, re.M)
    if push:
        body = push.group(1)
        triggers["push_tags"] = bool(re.search(r"^\s+tags:", body, re.M))
        branches = re.search(r"^\s+branches:\s*(\[.*?\]|\n(?:\s+-\s+.*\n?)+)", body, re.M)
        if branches:
            triggers["push_branches"] = re.findall(r"[\w./*-]+", branches.group(1).replace("branches", ""))
    triggers["release"] = bool(re.search(r"^\s+release:", block, re.M))
    triggers["workflow_dispatch"] = bool(re.search(r"^\s+workflow_dispatch:?", block, re.M))
    triggers["pull_request"] = bool(re.search(r"^\s+pull_request:?", block, re.M))
    return triggers


def publishing_evidence(text: str) -> tuple[str, list[str]]:
    """Exclude build-only Docker steps; regex detection never proves dynamic conditions."""
    uncertain = []
    step = re.compile(r"^(?P<indent> +)-\s+(?:[A-Za-z_-]+):[^\n]*(?:\n(?:(?P=indent) +[^\n]*|[ \t]*))*", re.M)

    def inspect(match):
        block = match.group(0)
        if "docker/build-push-action" not in block:
            return block
        push = re.search(r"^\s+push:\s*([^\n#]*)(?:#.*)?$", block, re.M)
        inline = re.search(r"^\s+with:\s*\S", block, re.M)
        if push is None and inline:
            uncertain.append("inline or indirect Docker inputs require inspection")
            return block
        value = push.group(1).strip().strip("\"'").lower() if push else "false"
        if value == "false":
            return block.replace("docker/build-push-action", "build-only-action")
        if value != "true":
            uncertain.append("Docker push depends on an expression")
        return block

    cleaned = step.sub(inspect, text)
    if re.search(r"^\s+(?:-\s+)?if:", cleaned, re.M):
        uncertain.append("workflow/job/step conditions require inspection")
    if re.search(r"^\s+uses:\s*(?:\./\.github/workflows/|[^\n]+/\.github/workflows/)", text, re.M):
        uncertain.append("reusable workflow requires inspection")
    return cleaned, uncertain


def workflows(root: Path) -> list[dict]:
    found = []
    for path in sorted((root / ".github" / "workflows").glob("*.y*ml")):
        text = read(path)
        publishing_text, uncertainty = publishing_evidence(text)
        steps = [m.group(0) for m in PUBLISH_STEP.finditer(publishing_text)]
        found.append({
            "file": path.relative_to(root).as_posix(),
            "triggers": workflow_triggers(text),
            "publishes": bool(steps),
            "publish_steps": sorted(set(s.lower() for s in steps)),
            "uncertainty": uncertainty,
            "docker": bool(DOCKER_PUBLISH.search(publishing_text)),
            "pypi": bool(PYPI_PUBLISH.search(publishing_text)),
            "npm": bool(NPM_PUBLISH.search(publishing_text)),
        })
    return found


def release_tools(root: Path) -> list[str]:
    tools = []
    if any((root / f).exists() for f in ("release-please-config.json", ".release-please-manifest.json")):
        tools.append("release-please")
    if any(root.glob(".releaserc*")) or any(root.glob("release.config.*")):
        tools.append("semantic-release")
    if (root / ".changeset").is_dir():
        tools.append("changesets")
    return tools


def detect_archetype(root: Path, targets: dict, flows: list[dict]) -> dict:
    evidence = []
    has_dockerfile = (root / "Dockerfile").exists()
    compose = first_existing(root, ["docker-compose.y*ml", "compose.y*ml"])
    pyproject = read(root / "pyproject.toml")
    has_pyproject = bool(re.search(r"^\[project\]", pyproject, re.M))
    package_json = read(root / "package.json")
    docker_flow = [f["file"] for f in flows if f["docker"]]
    pypi_flow = [f["file"] for f in flows if f["pypi"]]
    npm_flow = [f["file"] for f in flows if f["npm"]]
    docker_targets = [t for t in targets if t.startswith("docker")]
    if has_dockerfile and (docker_flow or docker_targets or compose):
        evidence.append("Dockerfile present")
        evidence += [f"{f}: pushes an image" for f in docker_flow]
        evidence += [f"Makefile target {t}" for t in docker_targets]
        if compose:
            evidence.append(f"{compose} present")
        if has_pyproject and pypi_flow:
            evidence.append("pyproject.toml also publishes to PyPI; app-docker chosen because an image is shipped")
        return {"value": "app-docker", "confidence": "high" if docker_flow else "medium", "evidence": evidence}
    if has_pyproject and (pypi_flow or any(PYPI_PUBLISH.search(" ".join(t["recipe"])) for t in targets.values())):
        evidence.append("pyproject.toml with [project]")
        evidence += [f"{f}: publishes to PyPI" for f in pypi_flow]
        return {"value": "pypi-library", "confidence": "high", "evidence": evidence}
    if package_json and ("publishConfig" in package_json or npm_flow):
        evidence.append("package.json present")
        evidence += [f"{f}: npm publish" for f in npm_flow]
        return {"value": "npm-package", "confidence": "high" if npm_flow else "medium", "evidence": evidence}
    if (root / ".maintainer" / "release" / "runbook.md").exists():
        return {"value": "custom", "confidence": "medium", "evidence": [".maintainer/release/runbook.md present"]}
    if has_pyproject:
        return {"value": "pypi-library", "confidence": "low", "evidence": ["pyproject.toml with [project] but no publish workflow found"]}
    return {"value": "unknown", "confidence": "low", "evidence": ["no Dockerfile, publishing workflow or package manifest found"]}


def select_trigger(root: Path, targets: dict, flows: list[dict], tools: list[str]) -> dict:
    evidence = []
    publishing = [f for f in flows if f["publishes"]]
    tag_pushing = {name: t for name, t in targets.items() if t["pushes_tag"]}
    if tools:
        evidence += [f"{tool} configuration present: publishing starts when its release PR merges" for tool in tools]
        return {"value": f"merge of the release PR ({', '.join(tools)})", "kind": "merge", "confidence": "medium",
                "evidence": evidence, "requires_confirmation": True}
    for flow in publishing:
        trig = flow["triggers"]
        if trig["push_tags"]:
            evidence.append(f"{flow['file']}: runs on tag push and {', '.join(flow['publish_steps'])}")
            if tag_pushing:
                name, target = next(iter(tag_pushing.items()))
                evidence.append(f"Makefile:{target['line']} target {name} creates and pushes the tag")
                return {"value": f"make {name}", "kind": "tag-push", "confidence": "high", "evidence": evidence,
                        "requires_confirmation": True, "publish_workflow": flow["file"]}
            return {"value": "git push origin v<version>", "kind": "tag-push", "confidence": "high", "evidence": evidence,
                    "requires_confirmation": True, "publish_workflow": flow["file"]}
        if trig["release"]:
            evidence.append(f"{flow['file']}: runs on release and {', '.join(flow['publish_steps'])}")
            return {"value": "gh release create", "kind": "release", "confidence": "high", "evidence": evidence,
                    "requires_confirmation": True, "publish_workflow": flow["file"]}
    for flow in publishing:
        trig = flow["triggers"]
        if trig["workflow_dispatch"]:
            evidence.append(f"{flow['file']}: publishes on workflow_dispatch")
            return {"value": f"gh workflow run {Path(flow['file']).name}", "kind": "workflow-dispatch", "confidence": "medium",
                    "evidence": evidence, "requires_confirmation": True, "publish_workflow": flow["file"]}
        if trig["push_branches"]:
            evidence.append(f"{flow['file']}: publishes on push to {', '.join(trig['push_branches'])}")
            return {"value": f"merge to {trig['push_branches'][0]}", "kind": "merge", "confidence": "medium",
                    "evidence": evidence, "requires_confirmation": True, "publish_workflow": flow["file"]}
    for name, target in targets.items():
        if target["publishes"]:
            evidence.append(f"Makefile:{target['line']} target {name} publishes directly")
            return {"value": f"make {name}", "kind": "direct", "confidence": "medium", "evidence": evidence,
                    "requires_confirmation": True}
    if tag_pushing:
        name, target = next(iter(tag_pushing.items()))
        evidence.append(f"Makefile:{target['line']} target {name} pushes a tag, but no workflow publishes on it")
        return {"value": f"make {name}", "kind": "tag-push", "confidence": "low", "evidence": evidence,
                "requires_confirmation": True}
    return {"value": None, "kind": "unknown", "confidence": "low",
            "evidence": ["no publishing workflow, release tool or publishing Makefile target found"],
            "requires_confirmation": True}


def detect_trigger(root: Path, targets: dict, flows: list[dict], tools: list[str]) -> dict:
    result = select_trigger(root, targets, flows, tools)
    result.setdefault("publish_workflow", None)
    publishing = [flow for flow in flows if flow["publishes"]]
    uncertainty = [f"{flow['file']}: {reason}" for flow in flows for reason in flow["uncertainty"]]
    if len(publishing) > 1:
        uncertainty.append("multiple publishing workflows: " + ", ".join(flow["file"] for flow in publishing))
        result.update(value=None, kind="unknown", publish_workflow=None)
    if uncertainty:
        result["confidence"] = "low"
        result["evidence"].extend(uncertainty)
    return result


def version_files(root: Path) -> list[str]:
    files = []
    if re.search(r"^version\s*=", read(root / "pyproject.toml"), re.M):
        files.append("pyproject.toml")
    if re.search(r'"version"\s*:', read(root / "package.json")):
        files.append("package.json")
    if re.search(r"^version\s*=", read(root / "Cargo.toml"), re.M):
        files.append("Cargo.toml")
    for manifest in (".claude-plugin/plugin.json", ".codex-plugin/plugin.json"):
        if re.search(r'"version"\s*:', read(root / manifest)):
            files.append(manifest)
    return files


def detect(root: Path) -> dict:
    targets = makefile_targets(root)
    flows = workflows(root)
    tools = release_tools(root)
    trigger = detect_trigger(root, targets, flows, tools)
    return {
        "root": str(root),
        "archetype": detect_archetype(root, targets, flows),
        "distribution_trigger": trigger,
        "version_files": version_files(root),
        "changelog": first_existing(root, ["CHANGELOG.md", "CHANGES.md", "HISTORY.md"]),
        "commands_doc": first_existing(root, ["AGENTS.md", "CLAUDE.md"]),
        "contributing": first_existing(root, ["CONTRIBUTING.md", "docs/**/contributing.md", ".github/CONTRIBUTING.md"]),
        "process_doc": first_existing(root, [".github/RELEASE_PROCESS.md", "RELEASING.md", "RELEASE.md", "docs/**/release*.md"]),
        "publish_workflow": trigger["publish_workflow"],
        "release_tools": tools,
        "makefile_targets": {
            name: {"line": t["line"], "pushes_tag": t["pushes_tag"], "creates_tag": t["creates_tag"], "publishes": t["publishes"]}
            for name, t in targets.items()
        },
        "workflows": flows,
        "has_profile": (root / ".maintainer" / "profile.toml").exists(),
    }


def render_text(result: dict) -> str:
    arch = result["archetype"]
    trig = result["distribution_trigger"]
    lines = [
        f"root: {result['root']}",
        f"archetype: {arch['value']} ({arch['confidence']})",
        *[f"  - {e}" for e in arch["evidence"]],
        f"distribution trigger: {trig['value']} [{trig['kind']}, {trig['confidence']}, confirm with the maintainer]",
        *[f"  - {e}" for e in trig["evidence"]],
        f"version files: {', '.join(result['version_files']) or 'none found'}",
        f"changelog: {result['changelog']}",
        f"commands doc: {result['commands_doc']}",
        f"contributing: {result['contributing']}",
        f"process doc: {result['process_doc']}",
        f"publish workflow: {result['publish_workflow']}",
        f"existing profile: {'yes' if result['has_profile'] else 'no'}",
    ]
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    result = detect(repo_root(args.root))
    print(json.dumps(result, indent=2, ensure_ascii=False) if args.json else render_text(result))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
