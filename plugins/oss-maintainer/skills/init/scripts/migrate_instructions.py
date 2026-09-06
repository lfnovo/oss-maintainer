#!/usr/bin/env python3
"""Preview a content-preserving CLAUDE.md → sibling AGENTS.md migration.

Write the JSON preview to a scratch file; after review, use --apply-plan FILE. Application
checks every old and proposed content hash before writing. Divergent canonical content is a
conflict by default; --merge-existing explicitly proposes retaining both complete bodies.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

SKIP = {".git", ".venv", "node_modules", ".cache", "dist", "build"}


def digest(text: str | None) -> str | None:
    return None if text is None else hashlib.sha256(text.encode()).hexdigest()


def preview(root: Path, merge_existing: bool = False) -> dict:
    changes = {}
    conflicts = []
    migrated = []

    def change(path: Path, text: str):
        if path.is_symlink():
            conflicts.append(
                f"{path.relative_to(root)}: symlink requires manual migration"
            )
            return
        old = path.read_text() if path.exists() else None
        if old != text:
            changes[str(path.relative_to(root))] = {
                "before": digest(old),
                "after": digest(text),
                "content": text,
            }

    files = sorted(
        p
        for p in root.rglob("*")
        if p.is_file() and not SKIP.intersection(p.relative_to(root).parts)
    )
    for source in files:
        if source.name != "CLAUDE.md":
            continue
        canonical = source.with_name("AGENTS.md")
        if source.is_symlink() or canonical.is_symlink():
            conflicts.append(
                f"{source.relative_to(root)}: symlink requires manual migration"
            )
            continue
        body = source.read_text()
        existing = canonical.read_text() if canonical.exists() else ""
        if body.strip() == "@AGENTS.md":
            if not canonical.exists():
                conflicts.append(
                    f"{source.relative_to(root)}: dangling @AGENTS.md import"
                )
            elif re.search(r"(?m)^\s*@(?:\./)?(?:AGENTS|CLAUDE)\.md\s*$", existing):
                conflicts.append(
                    f"{canonical.relative_to(root)}: instruction import cycle"
                )
            continue
        if re.search(
            r"(?m)^\s*@(?:\./)?(?:AGENTS|CLAUDE)\.md\s*$", body + "\n" + existing
        ):
            conflicts.append(
                f"{source.relative_to(root)}: resolve instruction import before migration"
            )
            continue
        if existing.strip() and existing.strip() != body.strip():
            if not merge_existing:
                conflicts.append(
                    f"{canonical.relative_to(root)}: divergent content; review a --merge-existing preview or resolve manually"
                )
                continue
            merged = (
                existing.rstrip()
                + "\n\n<!-- Preserved instructions from sibling CLAUDE.md -->\n\n"
                + body
            )
        else:
            merged = existing if existing.strip() else body
        change(canonical, merged)
        change(source, "@AGENTS.md\n")
        migrated.append(str(source.relative_to(root)))

    # Sibling destinations preserve the base directory of all relative links. Update only
    # references to sources actually migrated, never blanket-rename unrelated prose.
    for path in sorted(set(files) | {root / name for name in changes}):
        if path.suffix not in {".md", ".toml"} or path.name == "CLAUDE.md":
            continue
        key = str(path.relative_to(root))
        text = changes[key]["content"] if key in changes else path.read_text()

        def replace(match):
            target = match.group(1)
            if "://" in target:
                return match.group(0)
            candidate = (path.parent / target.split("#")[0]).resolve()
            if path.suffix == ".toml" or match.group(0).startswith("`"):
                candidate = (root / target.split("#")[0]).resolve()
            try:
                relative = str(candidate.relative_to(root))
            except ValueError:
                return match.group(0)
            if relative not in migrated:
                return match.group(0)
            return match.group(0).replace(
                target, target.replace("CLAUDE.md", "AGENTS.md")
            )

        text = re.sub(r"\]\(([^)]+)\)", replace, text)
        text = re.sub(r'["\']([^"\'\n]*CLAUDE\.md(?:#[^"\'\n]*)?)["\']', replace, text)
        text = re.sub(r"`([^`\n]*CLAUDE\.md)`", replace, text)
        # Do not introduce a canonical file importing itself.
        if path.name == "AGENTS.md" and re.search(
            r"(?m)^\s*@(?:\./)?AGENTS\.md\s*$", text
        ):
            conflicts.append(f"{key}: self import")
        change(path, text)
    # Detect standard Markdown instruction imports across directories, including cycles
    # that become visible only after the pointer files are replaced.
    graph = {}
    for path in sorted(set(files) | {root / name for name in changes}):
        if path.name not in {"AGENTS.md", "CLAUDE.md"} or path.is_symlink():
            continue
        key = str(path.relative_to(root))
        text = changes[key]["content"] if key in changes else path.read_text()
        graph[path.resolve()] = [
            (path.parent / target).resolve()
            for target in re.findall(r"(?m)^\s*@([^\s]+\.md)\s*$", text)
        ]
    visited, active = set(), set()

    def visit(node):
        if node in active:
            conflicts.append(f"{node.relative_to(root)}: instruction import cycle")
            return
        if node in visited or node not in graph:
            return
        active.add(node)
        for child in graph[node]:
            visit(child)
        active.remove(node)
        visited.add(node)

    for node in graph:
        visit(node)
    return {
        "root": str(root),
        "merge_existing": merge_existing,
        "changes": changes,
        "conflicts": conflicts,
    }


def apply(root: Path, plan: dict) -> None:
    expected = preview(root, plan.get("merge_existing", False))
    if expected != plan:
        raise ValueError("plan is stale or modified; regenerate and review the preview")
    if plan["conflicts"]:
        raise ValueError("resolve every conflict before applying")
    # All files verified before the first write; plan paths come from the fresh scanner.
    for name, item in plan["changes"].items():
        (root / name).write_text(item["content"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--merge-existing", action="store_true")
    parser.add_argument("--apply-plan", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        if args.apply_plan:
            plan = json.loads(args.apply_plan.read_text())
            apply(root, plan)
            print(f"Applied {len(plan['changes'])} reviewed file changes")
        else:
            print(json.dumps(preview(root, args.merge_existing), indent=2))
    except (OSError, ValueError) as exc:
        parser.exit(2, f"{exc}\n")


if __name__ == "__main__":
    main()
