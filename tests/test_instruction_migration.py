import importlib.util
import pytest
from tests.conftest import PLUGIN

spec = importlib.util.spec_from_file_location(
    "migration", PLUGIN / "skills/init/scripts/migrate_instructions.py"
)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def test_nested_migration_preserves_scope_content_and_references(tmp_path):
    (tmp_path / "pkg").mkdir()
    (tmp_path / ".maintainer").mkdir()
    root = "# Root rules\n\nRun make test.\n"
    nested = "# Module rules\n\nSee [guide](guide.md).\n"
    (tmp_path / "CLAUDE.md").write_text(root)
    (tmp_path / "pkg/CLAUDE.md").write_text(nested)
    (tmp_path / ".maintainer/profile.toml").write_text(
        'commands_doc = "CLAUDE.md"\ndocs = ["pkg/CLAUDE.md"]\n'
    )
    (tmp_path / ".maintainer/runbook.md").write_text("[rules](../CLAUDE.md)\n")
    plan = m.preview(tmp_path)
    assert not plan["conflicts"] and not (tmp_path / "AGENTS.md").exists()
    m.apply(tmp_path, plan)
    assert (tmp_path / "AGENTS.md").read_text() == root
    assert (tmp_path / "pkg/AGENTS.md").read_text() == nested
    assert (tmp_path / "CLAUDE.md").read_text() == "@AGENTS.md\n"
    assert (tmp_path / "pkg/CLAUDE.md").read_text() == "@AGENTS.md\n"
    assert "CLAUDE.md" not in (tmp_path / ".maintainer/profile.toml").read_text()
    assert "../AGENTS.md" in (tmp_path / ".maintainer/runbook.md").read_text()
    assert m.preview(tmp_path)["changes"] == {}


def test_conflicts_need_explicit_preserving_merge_and_fresh_plan(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("Claude rules\n")
    (tmp_path / "AGENTS.md").write_text("Agent rules\n")
    plan = m.preview(tmp_path)
    assert plan["conflicts"]
    with pytest.raises(ValueError):
        m.apply(tmp_path, plan)
    plan = m.preview(tmp_path, True)
    (tmp_path / "CLAUDE.md").write_text("Changed rules\n")
    with pytest.raises(ValueError):
        m.apply(tmp_path, plan)
    assert (tmp_path / "AGENTS.md").read_text() == "Agent rules\n"
    plan = m.preview(tmp_path, True)
    m.apply(tmp_path, plan)
    assert all(
        s in (tmp_path / "AGENTS.md").read_text()
        for s in ["Agent rules", "Changed rules"]
    )


def test_cycles_dangling_imports_and_symlinks_refused(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("@AGENTS.md\n")
    assert m.preview(tmp_path)["conflicts"]
    (tmp_path / "AGENTS.md").write_text("@CLAUDE.md\n")
    # Already imported canonical content must be inspected too.
    assert m.preview(tmp_path)["conflicts"]


def test_symlink_source_is_not_replaced(tmp_path):
    target = tmp_path / "instructions.md"
    target.write_text("Preserve me.\n")
    (tmp_path / "CLAUDE.md").symlink_to(target)
    plan = m.preview(tmp_path)
    assert plan["conflicts"]
    with pytest.raises(ValueError):
        m.apply(tmp_path, plan)
    assert (tmp_path / "CLAUDE.md").is_symlink()
    assert target.read_text() == "Preserve me.\n"
