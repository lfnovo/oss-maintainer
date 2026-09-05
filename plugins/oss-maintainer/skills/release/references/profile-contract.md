# Profile contract — `release`

| Field | Use | Without it |
|---|---|---|
| `[project].artifact` | selects the archetype reference and gate | release incomplete |
| `[commands.validator]` and other `[commands.*]` | bucket A | release incomplete |
| `[release].changelog`, `[release].version_files` | phases 0 and 7 | release incomplete |
| `[release].distribution_trigger` | phase 10; must not be `TODO` or unconfirmed | release incomplete |
| `[release].process_doc`, `[release].notes_source`, `[release].publish_workflow`, `[release].lock_command`, `[release].consumer_surfaces`, `[release].latest_promotion` | context, notes, watching, cut, version decision | defaults and general judgement |
| `[release.gates]` | mandatory and optional checks, merge policy, alerts policy | `mandatory = ["validator"]`, ask once per session |
| `[artifacts.docker]` or `[artifacts.pypi]` | the archetype gate and verification | release incomplete for that archetype |
| `[contributing].conventions` | every PR the skill opens | `CONTRIBUTING.md`, else the engine fallback |
| `[labels].released` | phase 12 | `released` |
| `[channels].announce` | phase 12 | nothing to deliver |
| `[comms]` | languages, attribution | English, no attribution line |

Companion files: `.maintainer/release/runbook.md` (exact commands), `.maintainer/release/test-matrix.md`
(the instantiated matrix), `.maintainer/gotchas.md` (lessons), `.maintainer/state/runs/`
(records).

Without a profile the skill can audit the changelog, propose a version and draft a matrix in
read-only mode; every mutation waits for `init`.
