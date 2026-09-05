"""Structural invariants of the plugin repository that no other validator covers."""

from __future__ import annotations

import json
import re
from pathlib import Path

USER_INVOKED_ONLY = {"init", "triage", "review-pr", "release", "process-discussions"}


def _frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert match, f"{path} has no frontmatter"
    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line and not line.startswith((" ", "\t")):
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip()
    return fields


def test_manifests_and_catalogs_agree(root: Path, plugin: Path) -> None:
    claude = json.loads((plugin / ".claude-plugin" / "plugin.json").read_text())
    codex = json.loads((plugin / ".codex-plugin" / "plugin.json").read_text())
    claude_catalog = json.loads((root / ".claude-plugin" / "marketplace.json").read_text())
    codex_catalog = json.loads((root / ".agents" / "plugins" / "marketplace.json").read_text())
    entries = [claude, codex, claude_catalog["plugins"][0], codex_catalog["plugins"][0]]
    assert {e["name"] for e in entries} == {"oss-maintainer"}
    assert len({e["version"] for e in entries}) == 1
    assert codex["skills"] == "./skills/"


def test_skill_names_match_directories(plugin: Path) -> None:
    for skill_file in sorted((plugin / "skills").glob("*/SKILL.md")):
        fields = _frontmatter(skill_file)
        assert fields["name"] == skill_file.parent.name
        assert fields["description"], f"{skill_file} has an empty description"
        assert len(skill_file.read_text().splitlines()) <= 500


def test_user_invoked_skills_carry_both_adapters(plugin: Path) -> None:
    for skill_file in sorted((plugin / "skills").glob("*/SKILL.md")):
        name = skill_file.parent.name
        fields = _frontmatter(skill_file)
        claude_flag = fields.get("disable-model-invocation") == "true"
        codex_policy = skill_file.parent / "agents" / "openai.yaml"
        codex_flag = codex_policy.exists() and "allow_implicit_invocation: false" in codex_policy.read_text()
        assert claude_flag == codex_flag, f"{name}: invocation policy differs between Claude and Codex"
        if name in USER_INVOKED_ONLY and (skill_file.parent / "agents").exists():
            assert claude_flag and codex_flag, f"{name} must be user-invoked only in both harnesses"


def test_no_vendor_variables_in_shared_content(plugin: Path) -> None:
    banned = re.compile(r"\$\{CLAUDE_[A-Z_]+\}|\$ARGUMENTS|\bTaskCreate\b|\bTaskUpdate\b")
    offenders = []
    for path in sorted((plugin / "skills").rglob("*.md")):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if banned.search(line):
                offenders.append(f"{path.relative_to(plugin)}:{number}: {line.strip()}")
    assert not offenders, "vendor-specific variables in shared content:\n" + "\n".join(offenders)
