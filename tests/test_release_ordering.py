"""The GO precedes the distribution trigger, in the record's rules and in the skill text."""

from __future__ import annotations

import re
import subprocess

from tests.conftest import PLUGIN
from tests.test_run_record import approve_publication, new_record, rr, run

SKILL = PLUGIN / "skills" / "release" / "SKILL.md"


def test_pre_checks_gate_go_and_post_checks_gate_delivery(tmp_path):
    path = new_record(tmp_path)
    run("set", str(path), "--check", "validator=passed:log")
    record = rr.load(path)
    assert rr.outstanding(record, "pre") == []
    assert [i["check"] for i in rr.outstanding(record)] == ["publish", "verify"]
    approve_publication(path)
    assert run("finish", str(path), "--verdict", "GO")[0] == 2


def test_skill_text_states_the_ordering_rule():
    text = SKILL.read_text(encoding="utf-8")
    assert "runs in step 5 and nowhere else" in text
    assert "never in step 3" in text
    headings = re.findall(r"^### (\d) ", text, re.M)
    assert headings == ["1", "2", "3", "4", "5", "6"]
    assert text.index("### 3 Cut") < text.index("### 4 GO") < text.index("### 5 Publish") < text.index("### 6 Verify")


def test_fresh_version_credits_use_candidate_without_future_tag(tmp_path):
    notes = (PLUGIN / "skills/release/references/notes-and-credits.md").read_text()
    recipe = re.search(r"`(git log <last-tag>.*?sort -rn)`", notes).group(1)
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)

    def git(*args):
        return subprocess.check_output(
            ["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.com", *args], cwd=tmp_path, text=True
        ).strip()

    git("commit", "--allow-empty", "-m", "baseline")
    git("tag", "v1.0.0")
    git("commit", "--allow-empty", "-m", "new version candidate")
    candidate = git("rev-parse", "HEAD")
    command = recipe.replace("<last-tag>", "v1.0.0").replace("<candidate-sha>", candidate)
    result = subprocess.run(["bash", "-o", "pipefail", "-c", command], cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0 and "Fixture" in result.stdout
    assert git("tag", "--list") == "v1.0.0"
