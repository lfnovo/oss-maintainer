# oss-maintainer

Maintenance workflows for open-source maintainers, as a plugin for Claude Code and Codex.

`oss-maintainer` turns a project's own practices into assisted maintenance workflows. It prepares decisions with evidence, executes the actions the maintainer authorizes, and verifies the results, while preserving the policies and tools the community already uses. The plugin is the engine; each repository carries its profile in a `.maintainer/` directory, so the context, criteria and procedures of triage, review, release and community facilitation stop being rebuilt in every session.

The design is documented in [VISION.md](VISION.md); the market research that informed it is in [research/](research/oss-maintainer-landscape.md).

## Status

Version 0.1.0. Skills:

| Skill | Purpose | Invocation |
|---|---|---|
| `init` | Bootstrap, check and upgrade `.maintainer/`; readiness per capability | explicit only |
| `triage` | Classify open issues into the project's outcomes, one confirmed verdict at a time | explicit only |
| `review-pr` | Review a pull request against the project's own rules; the maintainer decides what to post | explicit only |
| `release` | Orchestrate a release behind human gates (`app-docker`, `pypi-library`, `custom` archetypes) | explicit only |
| `process-discussions` | Facilitate the GitHub Discussions queue; every reply approved before posting | explicit only |
| `smoke-e2e` | Run the product journey on a running instance and give a GO / NO-GO verdict | model or explicit |

"Explicit only" means the model never auto-selects the skill: `disable-model-invocation` in
Claude Code and `policy.allow_implicit_invocation: false` in Codex. `smoke-e2e` also ships as a
Claude Code subagent so `release` can delegate the gate; Codex runs the skill directly.

## Install

Claude Code:

```
/plugin marketplace add lfnovo/oss-maintainer
/plugin install oss-maintainer@oss-maintainer
```

Codex:

```bash
codex plugin marketplace add lfnovo/oss-maintainer
codex plugin add oss-maintainer@oss-maintainer
```

Skills are invoked as `/oss-maintainer:<skill>` in Claude Code and as `$<skill>` in Codex. Every skill that changes public state runs only on explicit invocation.

## Using it in a repository

Run `init` inside a checkout. It reads the `Makefile`, the workflows, `AGENTS.md`, the changelog and the package manifests, proposes a `.maintainer/` profile with `TODO` markers for what it could not derive, and reports which capabilities are ready. Skills that only read (for example `review-pr`) work without a profile; anything that mutates public state requires one.

The profile format is documented in [docs/profile-reference.md](docs/profile-reference.md) (rationale in VISION.md section 4). Only `profile.toml` is mandatory; skills that only read work without a profile and say which policies they assumed.

## Layout

```
.claude-plugin/marketplace.json     Claude Code catalog
.agents/plugins/marketplace.json    Codex catalog
.agent-smith/index.json             component graph, adapters, accepted gaps
plugins/oss-maintainer/
  .claude-plugin/plugin.json        Claude manifest
  .codex-plugin/plugin.json         Codex manifest (skills: ./skills/)
  skills/<name>/SKILL.md            canonical skills, shared by both harnesses
  agents/smoke-e2e.md               Claude subagent adapter
  evals/                            fixtures, eval cases, Codex parity checklist and runner
docs/profile-reference.md           generated profile documentation
scripts/bump.py                     the only way the version changes (four files)
scripts/rebuild_index.py            regenerates the agent-smith index from disk
scripts/render_docs.py              regenerates docs/profile-reference.md
tests/                              deterministic tests (pytest, Python 3.11+)
```

## Maintaining

- Edit skills under `plugins/oss-maintainer/skills/` only; there are no copies to keep in sync.
- Bump the version with `python3 scripts/bump.py <version>`; CI fails when the four version fields disagree.
- Rebuild the index with `python3 scripts/rebuild_index.py` after adding or removing components.
- Validate: `python3 -m pytest`, `claude plugin validate .`, and the agent-smith validator (`validate_repository.py .`). Scenario evals: `claude plugin eval plugins/oss-maintainer --scaffold` (early access); Codex parity: `plugins/oss-maintainer/evals/parity/run-codex.sh`.
- Releases are tagged `oss-maintainer--v<version>` with `claude plugin tag --push`, so marketplaces can pin by `ref`.

## Boundary with `snl-pm`

`oss-maintainer` covers intake (`triage`), review (`review-pr`), release, community (`process-discussions`) and the smoke gate. The Supernova `snl-pm` plugin keeps design, delivery and the Linear platform. `oss-maintainer` depends on no other plugin.

## License

MIT.
