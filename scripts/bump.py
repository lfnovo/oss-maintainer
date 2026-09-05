#!/usr/bin/env python3
"""Keep the plugin version identical in both plugin manifests and both marketplace catalogs.

Usage:
  python3 scripts/bump.py --check          # exit 1 when the four versions disagree
  python3 scripts/bump.py 0.2.0            # rewrite the four files to the given version
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "plugins" / "oss-maintainer"
FILES = {
    "claude plugin manifest": (PLUGIN / ".claude-plugin" / "plugin.json", ()),
    "codex plugin manifest": (PLUGIN / ".codex-plugin" / "plugin.json", ()),
    "claude marketplace entry": (ROOT / ".claude-plugin" / "marketplace.json", ("plugins", 0)),
    "codex marketplace entry": (ROOT / ".agents" / "plugins" / "marketplace.json", ("plugins", 0)),
}
SEMVER = re.compile(r"^\d+\.\d+\.\d+(-[0-9A-Za-z.-]+)?$")


def _node(data: dict, path: tuple) -> dict:
    for key in path:
        data = data[key]
    return data


def read_versions() -> dict[str, str]:
    return {
        label: _node(json.loads(file.read_text(encoding="utf-8")), path).get("version", "")
        for label, (file, path) in FILES.items()
    }


def write_version(version: str) -> None:
    for file, path in FILES.values():
        data = json.loads(file.read_text(encoding="utf-8"))
        _node(data, path)["version"] = version
        file.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main(argv: list[str]) -> int:
    if len(argv) != 1 or argv[0] in {"-h", "--help"}:
        print(__doc__.strip())
        return 2
    versions = read_versions()
    if argv[0] == "--check":
        distinct = set(versions.values())
        for label, version in versions.items():
            print(f"{version or '<missing>':12} {label}")
        if len(distinct) != 1 or "" in distinct:
            print("versions disagree", file=sys.stderr)
            return 1
        print("versions agree")
        return 0
    version = argv[0]
    if not SEMVER.match(version):
        print(f"not a semantic version: {version}", file=sys.stderr)
        return 2
    write_version(version)
    print(f"version set to {version} in {len(FILES)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
