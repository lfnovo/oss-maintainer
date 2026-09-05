#!/usr/bin/env python3
"""Rebuild .agent-smith/index.json (schema 2.0) from the files on disk.

The filesystem is the source of truth. Accepted compatibility gaps recorded in the existing
index are carried forward when their component still exists; everything else is derived.

Usage: python3 scripts/rebuild_index.py [--check]
  --check   exit 1 when the index on disk differs from the rebuilt one (ignoring lastUpdated)
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / ".agent-smith" / "index.json"
CATALOGS = {
    "claude": ROOT / ".claude-plugin" / "marketplace.json",
    "codex": ROOT / ".agents" / "plugins" / "marketplace.json",
}
AGENT_GAP_REASON = (
    "Codex plugins bundle no custom agents; Codex users run the shared skill directly."
)


def frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    fields: dict[str, str] = {}
    if match:
        for line in match.group(1).splitlines():
            if ":" in line and not line.startswith((" ", "\t")):
                key, _, value = line.partition(":")
                fields[key.strip()] = value.strip().strip('"')
    return fields


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def local_plugins() -> dict[str, dict[str, list[str]]]:
    """Map normalized plugin directory -> {harness: [plugin names]} for local sources only."""
    plugins: dict[str, dict[str, list[str]]] = {}
    for harness, catalog in CATALOGS.items():
        if not catalog.exists():
            continue
        for entry in json.loads(catalog.read_text(encoding="utf-8")).get("plugins", []):
            source = entry.get("source")
            path = source if isinstance(source, str) else source.get("path") if isinstance(source, dict) and source.get("source") == "local" else None
            if not path:
                continue
            key = (ROOT / path).resolve().relative_to(ROOT).as_posix()
            plugins.setdefault(key, {}).setdefault(harness, []).append(entry["name"])
    return plugins


def build() -> dict:
    targets = [h for h, c in CATALOGS.items() if c.exists()]
    components: list[dict] = []
    adapters: list[dict] = []
    gaps: list[dict] = []
    previous = json.loads(INDEX.read_text(encoding="utf-8")) if INDEX.exists() else {}
    previous_gaps = {
        (g["componentId"], g["harness"], g["capability"]): g
        for g in previous.get("gaps", [])
        if g.get("status") in {"accepted", "resolved"}
    }

    def add_gap(component_id: str, harness: str, capability: str, reason: str) -> None:
        kept = previous_gaps.get((component_id, harness, capability))
        gaps.append(kept or {
            "componentId": component_id,
            "harness": harness,
            "capability": capability,
            "reason": reason,
            "status": "unacknowledged",
        })

    plugins = local_plugins()
    for plugin_dir, names in plugins.items():
        plugin_name = sorted({n for ns in names.values() for n in ns})[0]
        base = ROOT / plugin_dir
        for skill_file in sorted((base / "skills").glob("*/SKILL.md")):
            name = skill_file.parent.name
            fields = frontmatter(skill_file)
            component_id = f"skill:{name}"
            components.append({
                "id": component_id,
                "type": "skill",
                "name": name,
                "plugin": plugin_name,
                "canonicalPath": rel(skill_file),
                "description": fields.get("description", ""),
            })
            for harness in targets:
                adapters.append({"componentId": component_id, "harness": harness, "status": "shared", "path": rel(skill_file)})
            policy = skill_file.parent / "agents" / "openai.yaml"
            if fields.get("disable-model-invocation") == "true" or policy.exists():
                policy_id = f"policy:{name}:user-invoked"
                components.append({
                    "id": policy_id,
                    "type": "policy",
                    "name": f"{name} user-invoked only",
                    "plugin": plugin_name,
                    "canonicalPath": rel(skill_file),
                    "description": "The skill runs only on explicit user invocation, never by model auto-selection.",
                })
                if fields.get("disable-model-invocation") == "true":
                    adapters.append({"componentId": policy_id, "harness": "claude", "status": "native", "path": rel(skill_file)})
                elif "claude" in targets:
                    add_gap(policy_id, "claude", "user-invoked-only", "SKILL.md lacks disable-model-invocation: true")
                if policy.exists():
                    adapters.append({"componentId": policy_id, "harness": "codex", "status": "native", "path": rel(policy)})
                elif "codex" in targets:
                    add_gap(policy_id, "codex", "user-invoked-only", "agents/openai.yaml with allow_implicit_invocation: false is missing")
            for script in sorted((skill_file.parent / "scripts").glob("*.py")):
                script_id = f"script:{script.stem.replace('_', '-')}"
                components.append({
                    "id": script_id,
                    "type": "script",
                    "name": script.stem,
                    "plugin": plugin_name,
                    "canonicalPath": rel(script),
                    "description": f"Bundled with the {name} skill.",
                })
                for harness in targets:
                    adapters.append({"componentId": script_id, "harness": harness, "status": "shared", "path": rel(script)})
        for agent_file in sorted((base / "agents").glob("*.md")):
            name = agent_file.stem
            component_id = f"agent:{name}"
            components.append({
                "id": component_id,
                "type": "agent",
                "name": name,
                "plugin": plugin_name,
                "canonicalPath": rel(agent_file),
                "description": frontmatter(agent_file).get("description", ""),
            })
            if "claude" in targets:
                adapters.append({"componentId": component_id, "harness": "claude", "status": "native", "path": rel(agent_file)})
            if "codex" in targets:
                add_gap(component_id, "codex", "plugin-bundled-agent", AGENT_GAP_REASON)

    marketplaces = []
    for harness, catalog in CATALOGS.items():
        if not catalog.exists():
            continue
        entries = []
        for entry in json.loads(catalog.read_text(encoding="utf-8")).get("plugins", []):
            source = entry.get("source")
            local = source if isinstance(source, str) else source.get("path") if isinstance(source, dict) and source.get("source") == "local" else None
            entries.append({
                "name": entry["name"],
                "sourceType": "local" if local else "external",
                "path": (ROOT / local).resolve().relative_to(ROOT).as_posix() if local else None,
                "managed": bool(local),
            })
        marketplaces.append({"harness": harness, "manifestPath": rel(catalog), "plugins": entries})

    skills_root = sorted(plugins)[0] + "/skills" if plugins else "skills"
    return {
        "schemaVersion": "2.0",
        "topology": "marketplace",
        "targets": targets,
        "canonicalPaths": {"skills": skills_root, "index": rel(INDEX)},
        "lastUpdated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "components": components,
        "adapters": adapters,
        "gaps": gaps,
        "marketplaces": marketplaces,
    }


def main(argv: list[str]) -> int:
    index = build()
    if "--check" in argv:
        current = json.loads(INDEX.read_text(encoding="utf-8")) if INDEX.exists() else {}
        current.pop("lastUpdated", None)
        fresh = dict(index)
        fresh.pop("lastUpdated")
        if current != fresh:
            print("index is stale; run scripts/rebuild_index.py", file=sys.stderr)
            return 1
        print("index is current")
        return 0
    INDEX.parent.mkdir(parents=True, exist_ok=True)
    INDEX.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    unacknowledged = [g for g in index["gaps"] if g["status"] == "unacknowledged"]
    print(f"index rebuilt: {len(index['components'])} components, {len(index['adapters'])} adapters, {len(index['gaps'])} gaps ({len(unacknowledged)} unacknowledged)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
