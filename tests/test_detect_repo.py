"""Deterministic tests for skills/init/scripts/detect_repo.py against the fixture repositories."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys

from tests.conftest import FIXTURES, PLUGIN

SCRIPT = PLUGIN / "skills" / "init" / "scripts" / "detect_repo.py"


def load_module():
    spec = importlib.util.spec_from_file_location("detect_repo", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


dr = load_module()


def detect(fixture: str) -> dict:
    return dr.detect(FIXTURES / fixture)


def test_pypi_library_tag_target_that_pushes_is_the_trigger():
    result = detect("pypi-library")
    assert result["archetype"]["value"] == "pypi-library"
    assert result["archetype"]["confidence"] == "high"
    trigger = result["distribution_trigger"]
    assert trigger["value"] == "make tag"
    assert trigger["kind"] == "tag-push"
    assert trigger["requires_confirmation"] is True
    assert any("Makefile:" in e and "pushes the tag" in e for e in trigger["evidence"])
    assert any("publish.yml" in e and "tag push" in e for e in trigger["evidence"])
    assert result["makefile_targets"]["tag"]["pushes_tag"] is True
    assert result["makefile_targets"]["tag"]["creates_tag"] is True
    assert result["publish_workflow"] == ".github/workflows/publish.yml"
    assert result["version_files"] == ["pyproject.toml"]
    assert result["changelog"] == "CHANGELOG.md"
    assert result["commands_doc"] == "AGENTS.md"


def test_app_docker_release_event_is_the_trigger():
    result = detect("app-docker")
    assert result["archetype"]["value"] == "app-docker"
    assert result["archetype"]["confidence"] == "high"
    trigger = result["distribution_trigger"]
    assert trigger["value"] == "gh release create"
    assert trigger["kind"] == "release"
    assert result["makefile_targets"]["tag"]["pushes_tag"] is False
    assert result["makefile_targets"]["tag"]["creates_tag"] is True
    assert result["process_doc"] == ".github/RELEASE_PROCESS.md"
    assert result["contributing"] == "CONTRIBUTING.md"
    assert result["has_profile"] is True


def test_npm_package_without_makefile_needs_a_manual_tag_push():
    result = detect("npm-package")
    assert result["archetype"]["value"] == "npm-package"
    trigger = result["distribution_trigger"]
    assert trigger["kind"] == "tag-push"
    assert trigger["value"] == "git push origin v<version>"
    assert result["version_files"] == ["package.json"]
    assert result["makefile_targets"] == {}


def test_plain_repository_has_low_confidence_and_no_trigger():
    result = detect("no-profile")
    assert result["archetype"]["value"] == "pypi-library"
    assert result["archetype"]["confidence"] == "low"
    trigger = result["distribution_trigger"]
    assert trigger["value"] is None
    assert trigger["kind"] == "unknown"
    assert result["has_profile"] is False


def test_custom_runbook_is_detected_when_nothing_else_matches():
    result = detect("overlay-override")
    assert result["archetype"]["value"] == "custom"


def test_release_tool_forces_merge_trigger(tmp_path):
    (tmp_path / "release-please-config.json").write_text("{}")
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"\nversion = "1.0.0"\n')
    result = dr.detect(tmp_path)
    trigger = result["distribution_trigger"]
    assert trigger["kind"] == "merge"
    assert "release-please" in result["release_tools"]
    assert trigger["requires_confirmation"] is True


def test_cli_json_output_round_trips():
    proc = subprocess.run([sys.executable, str(SCRIPT), "--root", str(FIXTURES / "pypi-library"), "--json"], capture_output=True, text=True)
    assert proc.returncode == 0
    assert json.loads(proc.stdout)["distribution_trigger"]["value"] == "make tag"
    text = subprocess.run([sys.executable, str(SCRIPT), "--root", str(FIXTURES / "pypi-library")], capture_output=True, text=True)
    assert "distribution trigger: make tag" in text.stdout
