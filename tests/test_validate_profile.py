"""Deterministic tests for skills/init/scripts/validate_profile.py against the fixture repositories."""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tests.conftest import FIXTURES, PLUGIN

SCRIPT = PLUGIN / "skills" / "init" / "scripts" / "validate_profile.py"


def load_module():
    spec = importlib.util.spec_from_file_location("validate_profile", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


vp = load_module()


def run(fixture: str, *args: str) -> tuple[int, dict]:
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--root",
            str(FIXTURES / fixture),
            "--json",
            *args,
        ],
        capture_output=True,
        text=True,
    )
    return proc.returncode, json.loads(proc.stdout)


def test_complete_profile_is_ready_everywhere():
    code, payload = run("app-docker")
    statuses = {name: cap["status"] for name, cap in payload["capabilities"].items()}
    assert statuses == {name: "ready" for name in vp.CAPABILITIES}, statuses
    assert code == 0
    assert payload["errors"] == []


def test_todo_trigger_blocks_release_and_absent_tables_are_not_applicable():
    code, payload = run("pypi-library")
    caps = payload["capabilities"]
    assert caps["release"]["status"] == "incomplete"
    assert "release.distribution_trigger" in caps["release"]["todos"]
    assert caps["smoke-e2e"]["status"] == "not-applicable"
    assert caps["process-discussions"]["status"] == "not-applicable"
    assert caps["triage"]["status"] == "ready"
    assert any("preset" in a for a in caps["triage"]["assumed"])
    assert caps["review-pr"]["status"] == "ready"
    assert code == 1


def test_missing_profile_reports_read_only_capabilities():
    code, payload = run("no-profile")
    assert code == 2
    assert payload["profile"] is None
    caps = payload["capabilities"]
    assert caps["review-pr"]["status"] == "ready"
    assert caps["triage"]["status"] == "ready"
    assert caps["release"]["status"] == "incomplete"
    assert ".maintainer/profile.toml" in caps["release"]["missing"]


def test_overlay_applies_preferences_and_rejects_policy():
    code, payload = run("overlay-override")
    overlay = payload["overlay"]
    assert "smoke.api_url" in overlay["applied"]
    assert "upstreams.example-lib" in overlay["applied"]
    assert "release.gates.mandatory" in overlay["rejected"]
    effective = payload["effective_profile"]
    assert effective["smoke"]["api_url"] == "http://localhost:9999"
    assert effective["release"]["gates"]["mandatory"] == ["validator", "notes-approved"]
    assert payload["capabilities"]["release"]["status"] == "ready"
    assert any("example-lib" in w for w in payload["capabilities"]["init"]["warnings"])
    assert code == 0


def test_single_capability_selection():
    code, payload = run("pypi-library", "--capability", "review-pr")
    assert list(payload["capabilities"]) == ["review-pr"]
    assert code == 0


@pytest.fixture
def scratch(tmp_path: Path) -> Path:
    shutil.copytree(FIXTURES / "app-docker", tmp_path / "repo")
    return tmp_path / "repo"


def rewrite(root: Path, old: str, new: str) -> None:
    profile = root / ".maintainer" / "profile.toml"
    text = profile.read_text()
    assert old in text
    profile.write_text(text.replace(old, new))


def test_unknown_schema_version_is_an_error(scratch: Path):
    rewrite(scratch, "schema_version = 1", "schema_version = 7")
    report, _, code = vp.validate(scratch, vp.CAPABILITIES)
    assert code == 1
    assert any("schema_version" in e for e in report.errors)


def test_confirm_marker_needs_confirmation(scratch: Path):
    rewrite(
        scratch,
        'distribution_trigger = "gh release create"',
        'distribution_trigger = "CONFIRM: gh release create"',
    )
    report, _, code = vp.validate(scratch, ["release"])
    cap = report.capabilities["release"]
    assert cap["status"] == "needs-confirmation"
    assert cap["confirm"] == ["release.distribution_trigger"]
    assert code == 1


def test_absolute_and_missing_paths_are_rejected(scratch: Path):
    rewrite(scratch, 'changelog = "CHANGELOG.md"', 'changelog = "/etc/CHANGELOG.md"')
    rewrite(
        scratch,
        'version_files = ["pyproject.toml"]',
        'version_files = ["pyproject.toml", "missing.toml"]',
    )
    report, _, _ = vp.validate(scratch, ["release"])
    missing = report.capabilities["release"]["missing"]
    assert any("absolute path" in m for m in missing)
    assert any("missing.toml" in m for m in missing)


def test_unknown_gate_and_bad_timeout_are_reported(scratch: Path):
    rewrite(
        scratch,
        'mandatory = ["validator", "image-gate", "owner-checks", "notes-approved"]',
        'mandatory = ["validator", "typo-gate"]',
    )
    rewrite(scratch, 'timeout = "20m"', 'timeout = "twenty"')
    report, _, _ = vp.validate(scratch, ["release"])
    missing = report.capabilities["release"]["missing"]
    assert any("typo-gate" in m for m in missing)
    assert any("timeout" in m for m in missing)


def test_unknown_archetype_value_is_rejected(scratch: Path):
    rewrite(scratch, 'artifact = "app-docker"', 'artifact = "app-kubernetes"')
    report, _, _ = vp.validate(scratch, ["release"])
    assert any(
        "project.artifact" in m for m in report.capabilities["release"]["missing"]
    )


def test_unparsable_profile_exits_2(scratch: Path):
    (scratch / ".maintainer" / "profile.toml").write_text(
        "schema_version = [unclosed\n"
    )
    report, profile, code = vp.validate(scratch, vp.CAPABILITIES)
    assert code == 2 and profile is None
    assert any("parsed" in e for e in report.errors)


def test_text_output_lists_every_capability():
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(FIXTURES / "app-docker")],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    for name in vp.CAPABILITIES:
        assert name in proc.stdout


def toml_value(value):
    if isinstance(value, dict):
        return (
            "{ "
            + ", ".join(f"{json.dumps(k)} = {toml_value(v)}" for k, v in value.items())
            + " }"
        )
    if isinstance(value, list):
        return "[" + ", ".join(toml_value(v) for v in value) + "]"
    return json.dumps(value)


def set_profile_value(root, dotted, value):
    profile_path = root / ".maintainer/profile.toml"
    profile, error = vp.load_toml(profile_path)
    assert error is None
    table = profile
    parts = dotted.split(".")
    for key in parts[:-1]:
        table = table[key]
    table[parts[-1]] = value
    profile_path.write_text(
        "\n".join(f"{key} = {toml_value(val)}" for key, val in profile.items()) + "\n"
    )


@pytest.mark.parametrize(
    "dotted,value,capability,expected,path",
    [
        (
            "artifacts.docker.registries",
            ["TODO registry/image"],
            "release",
            "incomplete",
            "artifacts.docker.registries[0]",
        ),
        (
            "discussions.categories",
            {"ideas": "CONFIRM: DIC_example"},
            "process-discussions",
            "needs-confirmation",
            "discussions.categories.ideas",
        ),
        (
            "labels.ready",
            "TODO choose existing label",
            "triage",
            "incomplete",
            "labels.ready",
        ),
        (
            "labels.ready",
            "TODO choose existing label",
            "init",
            "incomplete",
            "labels.ready",
        ),
        (
            "contributing.conventions",
            "missing-contributing.md",
            "review-pr",
            "incomplete",
            "contributing.conventions",
        ),
        (
            "contributing.conventions",
            "missing-contributing.md",
            "triage",
            "incomplete",
            "contributing.conventions",
        ),
        (
            "contributing.conventions",
            "missing-contributing.md",
            "init",
            "incomplete",
            "contributing.conventions",
        ),
        ("project.name", "", "release", "incomplete", "project.name"),
        (
            "commands.validator.run",
            "  ",
            "release",
            "incomplete",
            "commands.validator.run",
        ),
        (
            "release.distribution_trigger",
            "",
            "release",
            "incomplete",
            "release.distribution_trigger",
        ),
        ("artifacts.docker.gate", "", "release", "incomplete", "artifacts.docker.gate"),
        (
            "discussions.categories",
            {"ideas": " "},
            "process-discussions",
            "incomplete",
            "discussions.categories.ideas",
        ),
        (
            "release.version_files",
            ["CONFIRM: pyproject.toml"],
            "release",
            "needs-confirmation",
            "release.version_files[0]",
        ),
    ],
)
def test_unusable_consumed_fields_block(
    scratch, dotted, value, capability, expected, path
):
    set_profile_value(scratch, dotted, value)
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--root",
            str(scratch),
            "--capability",
            capability,
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 1, proc.stderr
    cap = json.loads(proc.stdout)["capabilities"][capability]
    assert cap["status"] == expected
    assert any(
        path in item for group in ("missing", "todos", "confirm") for item in cap[group]
    )


@pytest.mark.parametrize(
    "dotted,value",
    [
        ("project", "not-a-table"),
        ("comms", []),
        ("release", 1),
        ("release.gates", "bad"),
        ("artifacts", []),
        ("artifacts.docker", False),
        ("commands", "bad"),
        ("commands.validator", []),
        ("release.gates.mandatory", [{}]),
        ("release.gates.merge_own_prs", []),
        ("comms.agent_attribution", {}),
        ("smoke", 1),
        ("smoke.journey", {}),
        ("smoke.mandatory_surfaces", [{}]),
        ("discussions", False),
        ("discussions.close_on", [{}]),
        ("discussions.graduation", []),
        ("triage", True),
        ("triage.batch_approval", {}),
        ("review", 2),
        ("labels", 2),
        ("contributing", []),
    ],
)
@pytest.mark.parametrize("json_mode", [True, False])
def test_wrong_structural_types_return_diagnostics(scratch, dotted, value, json_mode):
    set_profile_value(scratch, dotted, value)
    args = [sys.executable, str(SCRIPT), "--root", str(scratch)] + (
        ["--json"] if json_mode else []
    )
    proc = subprocess.run(args, capture_output=True, text=True)
    assert proc.returncode == 1, proc.stderr
    assert not proc.stderr
    assert dotted in proc.stdout
    if json_mode:
        assert any(
            cap["status"] == "incomplete"
            for cap in json.loads(proc.stdout)["capabilities"].values()
        )


def test_single_capability_requires_shared_identity(scratch):
    (scratch / ".maintainer/profile.toml").write_text(
        "schema_version = 1\n[review]\nreviewers = []\n"
    )
    report, _, code = vp.validate(scratch, ["triage"])
    assert code == 1
    assert report.capabilities["triage"]["status"] == "incomplete"
    assert "project.repo" in report.capabilities["triage"]["missing"]


def test_unrelated_optional_fields_do_not_block_read_only(scratch):
    set_profile_value(scratch, "artifacts.docker.registries", ["TODO"])
    report, _, code = vp.validate(scratch, ["review-pr"])
    assert code == 0 and report.capabilities["review-pr"]["status"] == "ready"


def test_overlay_on_wrong_base_table_is_reported(scratch):
    set_profile_value(scratch, "smoke", "bad")
    (scratch / ".maintainer/profile.local.toml").write_text(
        '[smoke]\napi_url = "http://localhost"\n'
    )
    report, _, code = vp.validate(scratch, ["smoke-e2e"])
    assert code == 1
    assert any("smoke" in error for error in report.errors)


@pytest.mark.parametrize(
    "dotted,capability",
    [
        ("release.lock_command", "release"),
        ("release.latest_promotion", "release"),
        ("discussions.regenerate", "process-discussions"),
        ("triage.extra_states.needs-info", "triage"),
    ],
)
def test_optional_consumed_values_also_require_confirmation(
    scratch, dotted, capability
):
    set_profile_value(scratch, dotted, "CONFIRM: configure this value")
    report, _, code = vp.validate(scratch, [capability])
    assert code == 1
    assert report.capabilities[capability]["status"] == "needs-confirmation"
    assert dotted in report.capabilities[capability]["confirm"]


@pytest.mark.parametrize("literal", ["2026-01-01", "12:00:00", "2026-01-01T12:00:00Z"])
def test_temporal_toml_types_keep_json_parseable(scratch, literal):
    rewrite(scratch, 'name = "example-app"', f"name = {literal}")
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(scratch), "--json"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 1 and not proc.stderr
    data = json.loads(proc.stdout)
    assert "project.name (expected string)" in data["capabilities"]["init"]["missing"]


def test_pypi_optional_install_check_is_not_executable_until_confirmed(tmp_path):
    root = tmp_path / "repo"
    shutil.copytree(FIXTURES / "pypi-library", root)
    set_profile_value(root, "release.distribution_trigger", "make tag")
    set_profile_value(root, "artifacts.pypi.install_check", "TODO choose import")
    report, _, code = vp.validate(root, ["release"])
    assert code == 1
    assert "artifacts.pypi.install_check" in report.capabilities["release"]["todos"]


def test_project_delivery_policies_and_gate_conflicts():
    root = FIXTURES / "app-docker"
    import tomllib

    profile = tomllib.loads((root / ".maintainer/profile.toml").read_text())
    for choice in ["repository", "pr", "direct"]:
        profile["release"]["change_delivery"] = choice
        profile["release"]["gates"]["merge_own_prs"] = "ask-once-per-run"
        report = vp.Report(root)
        vp.validate_release(profile, report, root)
        assert not report.capabilities["release"]["missing"]
    profile["release"]["change_delivery"] = "bypass-protection"
    report = vp.Report(root)
    vp.validate_release(profile, report, root)
    assert any(
        "change_delivery" in s for s in report.capabilities["release"]["missing"]
    )
    profile["release"]["change_delivery"] = "direct"
    profile["release"]["gates"]["not_gates"] = ["validator"]
    report = vp.Report(root)
    vp.validate_release(profile, report, root)
    assert any(
        "cannot be not_gates" in s for s in report.capabilities["release"]["missing"]
    )


def test_custom_triage_requires_executable_policy_and_independent_batch_choices(
    tmp_path,
):
    profile = {"triage": {"preset": "made-up"}}
    report = vp.Report(tmp_path)
    vp.validate_triage(profile, report, tmp_path)
    assert any("preset" in s for s in report.capabilities["triage"]["missing"])
    (tmp_path / "rules.md").write_text(
        "confirmed: a verified report; blocked: needs reproduction"
    )
    profile = {
        "triage": {
            "preset": "custom",
            "rules": "rules.md",
            "assignable": ["confirmed"],
            "extra_states": {"confirmed": "verified report"},
        },
        "review": {"batch_approval": "allowed"},
        "discussions": {
            "categories": {"ideas": "D_fixture"},
            "batch_approval": "allowed",
        },
    }
    report = vp.Report(tmp_path)
    for validate in [vp.validate_triage, vp.validate_review, vp.validate_discussions]:
        validate(profile, report, tmp_path)
    assert all(not cap["missing"] for cap in report.capabilities.values())
