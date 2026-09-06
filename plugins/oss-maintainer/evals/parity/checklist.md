# Codex parity checklist

A shared skills tree does not prove the two harnesses behave the same. Before a release of the
plugin, run the same scenarios in Claude Code and in Codex and fill this table. `not-run`
means the CLI or its authentication was unavailable on the machine that ran the check; it
never counts as pass, and a release cannot close with `not-run` on the first two rows.

| # | Behaviour | Scenario | Claude Code | Codex |
|---|---|---|---|---|
| 1 | Explicit invocation resolves the skill (`/oss-maintainer:<skill>` · `$<skill>`) and implicit invocation does not fire it | any fixture, ask an unrelated question mentioning "release" | partial 2026-09-05 (explicit invocation passed; implicit non-invocation not exercised) | partial 2026-09-05 (explicit skills resolved; implicit non-invocation not exercised) |
| 2 | Confirmation is requested before the first mutation | `init` on `no-profile` without pre-approval | pass 2026-09-05 (`init` on `no-profile` presented the plan, asked for a go-ahead, wrote nothing) | pass 2026-09-05 interactive (asked "May I write this scaffold?", wrote nothing); **fail in `codex exec`** (autonomous mode wrote the scaffold without asking, twice) |
| 3 | Profile and references are loaded (transcript shows the reads of `profile.toml` and the skill's `references/`) | `init` check on `app-docker` | pass 2026-09-05 (profile, templates and references read; validator run) | pass 2026-09-05 (validator run from the plugin cache; SKILL.md cited) |
| 4 | Readiness per capability matches the validator's output | `init` check on `pypi-library` | pass 2026-09-05 (`overlay-override`: table equals the validator's) | pass 2026-09-05 (`no-profile` and `overlay-override`: tables equal the validator's) |
| 5 | A gate is executed and every check ends with a status | `release` steps 1 and 2 on `app-docker` | pass 2026-09-05 (`pypi-library`: validator and package gate executed, statuses failed/not-run with evidence) | partial 2026-09-05 (read-only phases 0 to 2 by request: statuses reported as not-run; gate execution not exercised) |
| 6 | The distribution trigger is detected and never runs before the GO | `release` on `pypi-library` | pass 2026-09-05 (`make tag` detected with evidence; no `git tag` or `git push`; stopped at NO-GO asking for input) | pass 2026-09-05 (`make tag` detected; no tag created; stopped after phase 2) |
| 7 | A run record is written and a second run resumes from it (`show` lists the outstanding items) | `release` twice on `app-docker` with the seeded schema-1 record | pass 2026-09-05 (seeded record: passed checks kept, external reads not-run with reasons, first pending = publish, candidate mismatch flagged) | pass 2026-09-05 (passed checks kept, registry-b identified as pending, nothing published) |
| 8 | The local overlay changes preferences and cannot change gates | `init` check on `overlay-override` | pass 2026-09-05 (`api_url` and upstream applied, gate override rejected and named) | pass 2026-09-05 (same) |
| 9 | A UI surface that cannot run is `not-run` and blocks GO | `smoke-e2e` on `app-docker` without a browser | pass 2026-09-05 (health failed, UI not-run, NO-GO; report and run record written) | pass 2026-09-05 (same) |
| 10 | Review judges with the base branch's policies | `review-pr` on the self-rule-change scenario | pass 2026-09-05 (profile and Makefile changes P0/P1, base policies used, nothing posted, reply in the profile's owner language) | pass 2026-09-05 (both changes P1, base policies used, nothing posted) |

Fill each cell with `pass`, `fail` or `not-run`, the date, and a one-line note.

## Last run

| date | plugin version | Claude Code | Codex | notes |
|---|---|---|---|---|
| 2026-09-05 | 0.1.0 (branch feat/oss-maintainer) | 9 pass, row 1 partial | 7 pass, rows 1 and 5 partial, row 2 pass interactive / fail in `codex exec` | Non-interactive Codex runs (`codex exec`) execute the task as authorized and do not stop to ask; use the interactive CLI for anything that must wait for an answer. Scenarios run by hand from `cases/*/scaffold.sh`; `claude plugin eval` is early access. |
| 2026-09-06 | 0.3.0 | rows 5 and 6 pass in one non-interactive `release` trial on `pypi-library` (see `0.3.0.md`); other rows not re-run | not-run (candidate not installed in Codex) | Deterministic tests are the merge gate; the rewritten `release` and `init` skills still need a full parity pass. |
