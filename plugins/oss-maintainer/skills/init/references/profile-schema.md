# Profile schema v1 — `.maintainer/profile.toml`

The single specification of the per-repository profile read by every `oss-maintainer`
skill. `scripts/validate_profile.py` enforces it; this file explains it.

## Contents

- [Conventions](#conventions)
- [Tables and fields](#tables-and-fields)
- [Capabilities and what they require](#capabilities-and-what-they-require)
- [Local overlay](#local-overlay)
- [Companion files](#companion-files)

## Conventions

- `schema_version = 1` at the root. The engine refuses other values; `init` proposes upgrades.
- **Every path is relative to the repository root**, including paths into `.maintainer/`
  (write `.maintainer/triage.md`, never `triage.md`). Absolute paths are errors.
- **Markers.** A string value equal to or starting with `TODO` means "not known yet" and
  blocks the capability that needs the field. A value starting with `CONFIRM:` carries a
  detected proposal (for example `distribution_trigger = "CONFIRM: make tag"`); skills use
  the value after the colon only for analysis and ask for confirmation before any mutation.
- **References, not copies.** Invoking a canonical target (`make test`, `npm run build`) in
  `[commands.*]` is a reference. Copying what the target does is duplication; keep the
  implementation in the `Makefile` or `AGENTS.md`, and point to it with `commands_doc`.
- **Policies live here; preferences live in the overlay.** Gates, states, close criteria,
  graduation rules and public language are shared policy. URLs, local checkouts and the
  interaction language are preferences (see [Local overlay](#local-overlay)).
- Unknown tables and fields are warnings, never errors, so a profile can carry data for
  tools other than this plugin.

## Tables and fields

| Table.field | Type | Required by | Preset / default | Validation |
|---|---|---|---|---|
| `schema_version` | int | all | 1 | must be 1 |
| `[project].name` | str | all | | non-empty |
| `[project].repo` | str | all | | `owner/name` |
| `[project].artifact` | enum | release | `unknown` | `app-docker`, `pypi-library`, `npm-package`, `custom`, `unknown`; `unknown` leaves release incomplete |
| `[project].commands_doc` | path | init (informational) | `AGENTS.md` when present | exists |
| `[commands.<name>].run` | str | release (`validator` required) | | non-empty |
| `[commands.<name>].cwd` | path | | `.` | directory exists |
| `[commands.<name>].timeout` | duration | | `10m` | `^\d+[smh]$` |
| `[contributing].conventions` | path | PR-opening flows | `CONTRIBUTING.md` when present, else engine fallback | exists when set |
| `[release].process_doc` | path | release (optional) | | exists when set |
| `[release].changelog` | path | release | `CHANGELOG.md` | exists |
| `[release].version_files` | paths | release | | non-empty, every file exists |
| `[release].lock_command` | str | release (optional) | | |
| `[release].distribution_trigger` | str | release | | non-empty, no `TODO`; the first action that can start public distribution, confirmed by the maintainer |
| `[release].publish_workflow` | path | release (optional) | | exists when set |
| `[release].latest_promotion` | str | release (optional) | | free text: how the rolling channel moves |
| `[release].notes_source` | path | release (optional) | | exists when set |
| `[release].consumer_surfaces` | list | release (optional) | | what a breaking change can break: public exports, CLI flags, MCP tools, config keys |
| `[release.gates].mandatory` | list | release | `["validator"]` | each name is a `[commands.*]` key or one of `image-gate`, `package-gate`, `bucket-c`, `notes-approved`, `security-alerts` |
| `[release.gates].optional` | list | release | `[]` | same resolution; reported with a status, never skipped silently |
| `[release.gates].not_gates` | list | release (optional) | `[]` | checks that produce signal but never block |
| `[release.gates].alerts_policy` | str | release (optional) | | free text |
| `[release.gates].merge_own_prs` | enum | release | `ask-once-per-session` | `ask-once-per-session`, `always-ask`, `never` |
| `[artifacts.docker].registries` | list | release if `app-docker` | | non-empty |
| `[artifacts.docker].variants` | list | | `[""]` | image name suffixes |
| `[artifacts.docker].platforms` | list | | | expected architectures |
| `[artifacts.docker].dev_tag` | str | | | rolling tag testers use |
| `[artifacts.docker].gate` | str | release if `app-docker` | | the fresh + upgrade image gate command |
| `[artifacts.docker].identity` | str | | `manifest-digest` | what is recorded and compared per registry and variant |
| `[artifacts.pypi].package` | str | release if `pypi-library` | | distribution name on the index |
| `[artifacts.pypi].gate` | str | release if `pypi-library` | | build + clean-room install command |
| `[artifacts.pypi].surfaces` | list | | `["library"]` | `library`, `cli`, `mcp` |
| `[artifacts.pypi].extras` | list | | `[]` | extras that must still resolve |
| `[artifacts.pypi].install_check` | str | | | import or command that proves a bare install works |
| `[artifacts.pypi].identity` | str | | `sha256` | of the wheel and sdist |
| `[artifacts.npm].package` | str | release if `npm-package` | | placeholder archetype in v1 |
| `[labels].needs_triage` … `[labels].bug` | str | triage, release | same names as the keys | canonical → real label names; existence checked live |
| `[triage].preset` | str | triage | `maturity-ladder` | |
| `[triage].assignable` | list | triage | `["close", "needs-design", "ready"]` | subset of the preset states plus `extra_states` |
| `[triage].extra_states` | table | triage | `{}` | name → meaning, for states the preset lacks |
| `[triage].rules` | path | triage | `.maintainer/triage.md` | exists when set |
| `[triage].batch_approval` | enum | triage | `one-at-a-time` | `one-at-a-time`, `allowed` |
| `[review].docs` | paths | review-pr (optional) | found by function | each exists |
| `[review].reviewers` | list | review-pr (optional) | `[]` | AI reviewers whose findings are read as hypotheses |
| `[discussions].categories` | table | process-discussions | | name → GraphQL id, non-empty; absent table means the capability does not apply |
| `[discussions].regenerate` | str | process-discussions (optional) | | command that lists category ids again |
| `[discussions].public_anchors` | paths | process-discussions (optional) | | documents replies may cite |
| `[discussions].never_cite` | list | process-discussions (optional) | | paths or names that must never appear in public text |
| `[discussions].graduation` | enum | process-discussions | `pull` | `pull` (an Issue is born when someone will build), `push` |
| `[discussions].close_on` | list | process-discussions | `["answer", "graduated-work-landed"]` | subset of `answer`, `graduated-work-landed`, `never` |
| `[smoke].api_url` | str | smoke-e2e | | absent `[smoke]` table means the capability does not apply |
| `[smoke].frontend_url` | str | smoke-e2e (optional) | | |
| `[smoke].journey` | path | smoke-e2e | `.maintainer/smoke/journey.md` | exists |
| `[smoke].mandatory_surfaces` | list | smoke-e2e | `["api"]` | subset of `api`, `ui`, `db`; a mandatory surface that cannot run blocks GO |
| `[smoke].report_path` | path | smoke-e2e | `.maintainer/state/smoke-report.md` | |
| `[smoke].poll_interval`, `[smoke].step_timeout` | duration | smoke-e2e (optional) | `5s`, `5m` | |
| `[comms].owner_language` | str | all | `en` | language of the interaction |
| `[comms].public_language` | str | all | `en` | language of everything posted publicly |
| `[comms].agent_attribution` | enum | all | `none` | `none`, `disclaimer` |
| `[channels].announce` | list | release (optional) | `[]` | where the owner posts announcements; texts are delivered, never posted |
| `[upstreams].<name>` | path | optional | `{}` | local checkouts of libraries the project depends on; a missing path is a warning |

## Capabilities and what they require

| Capability | Required | Status when the profile is missing |
|---|---|---|
| `init` | `schema_version`, `[project].name`, `[project].repo` | incomplete |
| `release` | `[project].artifact` ≠ `unknown`, `[commands.validator]`, `[release].changelog`, `[release].version_files`, `[release].distribution_trigger`, the archetype table | incomplete |
| `triage` | nothing (presets); `[triage].rules` must exist when set | ready, read-only mode |
| `review-pr` | nothing | ready, read-only mode |
| `process-discussions` | `[discussions].categories` | incomplete; not applicable when the table is absent |
| `smoke-e2e` | `[smoke].api_url`, `[smoke].journey` | incomplete; not applicable when the table is absent |

Statuses: `ready`, `needs-confirmation` (a `CONFIRM:` value is pending), `incomplete`
(something required is missing, invalid or `TODO`), `not-applicable`.

## Local overlay

`.maintainer/profile.local.toml` is gitignored and exists for what differs between machines
and people. The engine merges it only into these fields and tables:

- `[smoke].api_url`, `[smoke].frontend_url`
- `[comms].owner_language`
- `[project].commands_doc`
- `[upstreams]` (whole table)
- `[channels]` (whole table)

Anything else in the overlay is reported and ignored: a local file never weakens a shared
policy silently. The effective profile, with the overlay differences, is printed at the start
of every run and stored in the run record.

## Companion files

| File | Purpose | Read by |
|---|---|---|
| `.maintainer/README.md` | what the directory is, for humans; distinct from a `MAINTAINERS` list | people |
| `.maintainer/PROFILE.md` | scope (own / do not own), tone, what must never be cited | every skill that writes public text |
| `.maintainer/gotchas.md` | fragile areas and known issues, fed by retros | release, review-pr |
| `.maintainer/triage.md` | repository-specific triage rules beyond the preset | triage |
| `.maintainer/release/runbook.md` | exact commands for cut, publish, verify, cleanup | release |
| `.maintainer/release/test-matrix.md` | the A/B/C matrix instantiated for this repository | release |
| `.maintainer/smoke/journey.md` | the product journey the smoke skill executes | smoke-e2e |
| `.maintainer/decisions.md` | append-only log of release and Discussions decisions (optional) | release, process-discussions |
| `.maintainer/state/` | gitignored run records and reports | every skill, on resumption |
