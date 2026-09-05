# Codex parity checklist

A shared skills tree does not prove the two harnesses behave the same. Before a release of the
plugin, run the same scenarios in Claude Code and in Codex and fill this table. `not-run`
means the CLI or its authentication was unavailable on the machine that ran the check; it
never counts as pass, and a release cannot close with `not-run` on the first two rows.

| # | Behaviour | Scenario | Claude Code | Codex |
|---|---|---|---|---|
| 1 | Explicit invocation resolves the skill (`/oss-maintainer:<skill>` · `$<skill>`) and implicit invocation does not fire it | any fixture, ask an unrelated question mentioning "release" | | |
| 2 | Confirmation is requested before the first mutation | `init` on `no-profile` without pre-approval | | |
| 3 | Profile and references are loaded (transcript shows the reads of `profile.toml` and the skill's `references/`) | `init` check on `app-docker` | | |
| 4 | Readiness per capability matches the validator's output | `init` check on `pypi-library` | | |
| 5 | A gate is executed and every check ends with a status | `release` phases 0 to 3 on `app-docker` | | |
| 6 | The distribution trigger is detected and never runs before the GO | `release` on `pypi-library` | | |
| 7 | A run record is written and a second run resumes from it | `release` twice on `app-docker` with the seeded record | | |
| 8 | The local overlay changes preferences and cannot change gates | `init` check on `overlay-override` | | |
| 9 | A UI surface that cannot run is `not-run` and blocks GO | `smoke-e2e` on `app-docker` without a browser | | |
| 10 | Review judges with the base branch's policies | `review-pr` on the self-rule-change scenario | | |

Fill each cell with `pass`, `fail` or `not-run`, the date, and a one-line note.

## Last run

| date | plugin version | Claude Code | Codex | notes |
|---|---|---|---|---|
| | | | | |
