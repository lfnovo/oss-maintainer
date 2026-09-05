# Codex parity checklist

A shared skills tree does not prove the two harnesses behave the same. Before a release of the
plugin, run the same scenarios in Claude Code and in Codex and fill this table. `not-run`
means the CLI or its authentication was unavailable on the machine that ran the check; it
never counts as pass, and a release cannot close with `not-run` on the first two rows.

| # | Behaviour | Scenario | Claude Code | Codex |
|---|---|---|---|---|
| 1 | Explicit invocation resolves the skill (`/oss-maintainer:<skill>` · `$<skill>`) and implicit invocation does not fire it | any fixture, ask an unrelated question mentioning "release" | pass 2026-09-05 (`/oss-maintainer:<skill>` in every run; implicit invocation not exercised) | pass 2026-09-05 (`$init`, `$release`, `$smoke-e2e`, `$review-pr` resolved; implicit invocation not exercised) |
| 2 | Confirmation is requested before the first mutation | `init` on `no-profile` without pre-approval | pass 2026-09-05 (`init` on `no-profile` presented the plan, asked for a go-ahead, wrote nothing) | pass 2026-09-05 interactive (asked "May I write this scaffold?", wrote nothing); **fail in `codex exec`** (autonomous mode wrote the scaffold without asking, twice) |
| 3 | Profile and references are loaded (transcript shows the reads of `profile.toml` and the skill's `references/`) | `init` check on `app-docker` | pass 2026-09-05 (profile, templates and references read; validator run) | pass 2026-09-05 (validator run from the plugin cache; SKILL.md cited) |
| 4 | Readiness per capability matches the validator's output | `init` check on `pypi-library` | pass 2026-09-05 (`overlay-override`: table equals the validator's) | pass 2026-09-05 (`no-profile` and `overlay-override`: tables equal the validator's) |
| 5 | A gate is executed and every check ends with a status | `release` phases 0 to 3 on `app-docker` | pass 2026-09-05 (`pypi-library`: validator and package gate executed, statuses failed/not-run with evidence) | partial 2026-09-05 (read-only phases 0 to 2 by request: statuses reported as not-run; gate execution not exercised) |
| 6 | The distribution trigger is detected and never runs before the GO | `release` on `pypi-library` | pass 2026-09-05 (`make tag` detected with evidence; no `git tag` or `git push`; stopped at NO-GO asking for input) | pass 2026-09-05 (`make tag` detected; no tag created; stopped after phase 2) |
| 7 | A run record is written and a second run resumes from it | `release` twice on `app-docker` with the seeded record | pass 2026-09-05 (seeded record: passed checks kept, external reads not-run with reasons, first pending = publish, candidate mismatch flagged) | pass 2026-09-05 (passed checks kept, registry-b identified as pending, nothing published) |
| 8 | The local overlay changes preferences and cannot change gates | `init` check on `overlay-override` | pass 2026-09-05 (`api_url` and upstream applied, gate override rejected and named) | pass 2026-09-05 (same) |
| 9 | A UI surface that cannot run is `not-run` and blocks GO | `smoke-e2e` on `app-docker` without a browser | pass 2026-09-05 (health failed, UI not-run, NO-GO; report and run record written) | pass 2026-09-05 (same) |
| 10 | Review judges with the base branch's policies | `review-pr` on the self-rule-change scenario | pass 2026-09-05 (profile and Makefile changes P0/P1, base policies used, nothing posted, reply in the profile's owner language) | pass 2026-09-05 (both changes P1, base policies used, nothing posted) |

Fill each cell with `pass`, `fail` or `not-run`, the date, and a one-line note.

## Last run

| date | plugin version | Claude Code | Codex | notes |
|---|---|---|---|---|
| 2026-09-05 | 0.1.0 (branch feat/oss-maintainer) | 10 pass | 8 pass, 1 partial (row 5), row 2 pass interactive / fail in `codex exec` | Non-interactive Codex runs (`codex exec`) execute the task as authorized and do not stop to ask; use the interactive CLI for anything that must wait for an answer. Scenarios run by hand from `cases/*/scaffold.sh`; `claude plugin eval` is early access. |
