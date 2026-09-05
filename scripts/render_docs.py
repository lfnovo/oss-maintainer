#!/usr/bin/env python3
"""Regenerate docs/profile-reference.md from the schema and readiness references of the init skill."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REFS = ROOT / "plugins" / "oss-maintainer" / "skills" / "init" / "references"
OUT = ROOT / "docs" / "profile-reference.md"


def main() -> int:
    schema = (REFS / "profile-schema.md").read_text(encoding="utf-8").split("\n", 1)[1]
    readiness = (REFS / "readiness.md").read_text(encoding="utf-8").split("\n", 1)[1]
    doc = (
        "# Profile reference\n\n"
        "Generated from the plugin's schema reference (`plugins/oss-maintainer/skills/init/references/profile-schema.md`) "
        "and readiness reference. Edit those files, then run `python3 scripts/render_docs.py`.\n\n"
        + schema.replace("`scripts/validate_profile.py`", "`skills/init/scripts/validate_profile.py`")
        + "\n\n---\n\n# Readiness report\n\n"
        + readiness
    )
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(doc, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
