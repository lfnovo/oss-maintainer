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


def write_workflow(root, name, content):
    directory = root / '.github/workflows'
    directory.mkdir(parents=True, exist_ok=True)
    (directory / name).write_text(content)


def test_build_only_workflow_is_not_selected_for_release(tmp_path):
    (tmp_path / 'Dockerfile').write_text('FROM scratch\n')
    write_workflow(tmp_path, 'build.yml', '''on:
  pull_request:
jobs:
  build:
    steps:
      - uses: docker/build-push-action@v6
        with:
          push: false
''')
    write_workflow(tmp_path, 'publish.yml', '''on:
  release:
    types: [published]
jobs:
  publish:
    steps:
      - run: docker push example/audit:1.0.0
''')
    result = dr.detect(tmp_path)
    assert result['publish_workflow'] == '.github/workflows/publish.yml'
    assert result['distribution_trigger']['publish_workflow'] == result['publish_workflow']
    assert result['distribution_trigger']['kind'] == 'release'
    assert result['workflows'][0]['publishes'] is False


def test_docker_push_flag_is_scoped_to_each_step(tmp_path):
    write_workflow(tmp_path, 'publish.yml', '''on:
  release:
jobs:
  publish:
    steps:
      - name: Build only
        uses: docker/build-push-action@v6
        with:
          push: false
      - uses: docker/build-push-action@v6
        with:
          push: true
''')
    assert dr.detect(tmp_path)['distribution_trigger']['kind'] == 'release'


def test_docker_action_defaults_to_build_only(tmp_path):
    write_workflow(tmp_path, 'build.yml', 'on: [pull_request]\njobs:\n  build:\n    steps:\n      - uses: docker/build-push-action@v6\n')
    result = dr.detect(tmp_path)
    assert result['workflows'][0]['publishes'] is False
    assert result['publish_workflow'] is None


def test_conditions_are_not_high_confidence(tmp_path):
    write_workflow(tmp_path, 'publish.yml', '''on:
  release:
jobs:
  publish:
    if: github.repository_owner == 'example'
    steps:
      - run: docker push example/image:1.0.0
''')
    result = dr.detect(tmp_path)
    assert result['distribution_trigger']['confidence'] == 'low'
    assert any('conditions' in e for e in result['distribution_trigger']['evidence'])


def test_multiple_publish_paths_require_selection(tmp_path):
    for name in ('a.yml', 'b.yml'):
        write_workflow(tmp_path, name, 'on:\n  release:\njobs:\n  publish:\n    steps:\n      - run: docker push example/image:1.0.0\n')
    result = dr.detect(tmp_path)
    assert result['publish_workflow'] is None
    assert result['distribution_trigger']['value'] is None
    assert result['distribution_trigger']['confidence'] == 'low'


def test_reusable_workflow_reports_uncertainty(tmp_path):
    write_workflow(tmp_path, 'release.yml', 'on:\n  release:\njobs:\n  publish:\n    uses: example/project/.github/workflows/publish.yml@main\n')
    result = dr.detect(tmp_path)
    assert result['publish_workflow'] is None
    assert any('reusable workflow' in e for e in result['distribution_trigger']['evidence'])


def test_condition_as_first_step_key_is_not_missed(tmp_path):
    write_workflow(tmp_path, 'build.yml', '''on:
  release:
jobs:
  build:
    steps:
      - if: github.event_name == 'release'
        uses: docker/build-push-action@v6
        with:
          push: false
''')
    result = dr.detect(tmp_path)
    assert result['workflows'][0]['publishes'] is False
    assert result['distribution_trigger']['confidence'] == 'low'
    assert any('conditions' in e for e in result['distribution_trigger']['evidence'])


def test_inline_inputs_are_uncertain_instead_of_assumed_build_only(tmp_path):
    write_workflow(tmp_path, 'publish.yml', '''on:
  release:
jobs:
  build:
    steps:
      - uses: docker/build-push-action@v6
        with: {push: true}
''')
    result = dr.detect(tmp_path)
    assert result['workflows'][0]['publishes'] is True
    assert result['distribution_trigger']['confidence'] == 'low'
    assert any('inline' in e for e in result['distribution_trigger']['evidence'])
