"""The canonical phase order guarantees the GO precedes the distribution trigger."""

from __future__ import annotations

import importlib.util

from tests.conftest import PLUGIN

SCRIPT = PLUGIN / "skills" / "release" / "scripts" / "run_record.py"
SKILL = PLUGIN / "skills" / "release" / "SKILL.md"


def load_module():
    spec = importlib.util.spec_from_file_location("run_record", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rr = load_module()


def test_trigger_phase_comes_after_go_and_after_notes():
    order = rr.PHASES
    assert order.index(rr.TRIGGER_PHASE) > order.index(rr.GO_PHASE)
    assert order.index("notes") < order.index(rr.GO_PHASE)
    assert order.index("artifact-gate") < order.index(rr.GO_PHASE)
    assert order.index("cut") < order.index("notes")
    assert order.index("verify") > order.index(rr.TRIGGER_PHASE)


def test_skill_text_states_the_ordering_rule():
    text = SKILL.read_text(encoding="utf-8")
    assert "runs in phase 10 and nowhere else" in text
    assert "never in phase 7" in text
    assert "### 9 GO" in text and "### 10 Publish" in text
    assert text.index("### 8 Notes and credits") < text.index("### 9 GO") < text.index("### 10 Publish")
