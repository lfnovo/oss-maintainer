# oss-maintainer

Maintenance workflows for open-source maintainers, as a plugin for Claude Code and Codex.

`oss-maintainer` turns a project's own practices into assisted maintenance workflows. It prepares decisions with evidence, executes the actions the maintainer authorizes, and verifies the results, while preserving the policies and tools the community already uses. The plugin is the engine; each repository carries its profile in a `.maintainer/` directory, so the context, criteria and procedures of triage, review, release and community facilitation stop being rebuilt in every session.

## Product philosophy

The maintainer defines the project's direction and commitments. The plugin makes those choices easier to execute, verify and carry forward. Five principles guide its development:

- **The process belongs to the project.** Respect its philosophy, stack, governance and strategy; offer useful defaults where needed.
- **Autonomy operates within a clear agreement.** Carry authorized work through and ask when a new decision is needed.
- **Trust is built on evidence.** Verify premises and delivered results; keep uncertainty and accepted risk visible.
- **Knowledge accumulates in the project.** Preserve canonical decisions and run history so work can continue across sessions.
- **Attention follows risk.** Match investigation, testing and coordination to the impact of the work.

The plugin requires honest evidence and respect for authority, recommends maintenance practices, and lets the repository define its policies. Read [PRINCIPLES.md](PRINCIPLES.md) for that distinction and how it should adapt to different projects. [VISION.md](VISION.md) describes the product's purpose, intended experience and architectural direction; the original market research is in [research/](research/oss-maintainer-landscape.md).

## Status

Version 0.2.0. Skills:

| Skill | Purpose | Invocation |
|---|---|---|
| `init` | Bootstrap, check and upgrade `.maintainer/`; readiness per capability | explicit only |
| `triage` | Classify open issues into the project's outcomes, one confirmed verdict at a time | explicit only |
| `review-pr` | Review a pull request against the project's own rules; the maintainer decides what to post | explicit only |
| `release` | Orchestrate a release behind human gates (`app-docker`, `pypi-library`, `custom` archetypes) | explicit only |
| `process-discussions` | Facilitate the GitHub Discussions queue; every reply approved before posting | explicit only |
| `smoke-e2e` | Run the product journey on a running instance and give a GO / NO-GO verdict | model or explicit |
| `plugin-feedback` | Open an issue on this repository about a skill, never editing the installed plugin | model or explicit |

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

Optional canonical instruction migration is available through `init`: preview root and nested changes, resolve conflicts, then apply the reviewed plan. Ordinary adoption preserves existing instruction structure.

The profile format is documented in [docs/profile-reference.md](docs/profile-reference.md), with the rationale in [VISION.md](VISION.md#a-shared-engine-and-a-repository-owned-profile). Only `profile.toml` is mandatory; skills that only read work without a profile and say which policies they assumed.

## How it works

1. **Profile, not prompts.** `init` reads what the repository already declares (Makefile, workflows, `AGENTS.md`, changelog, package manifests) and proposes `.maintainer/profile.toml` with the archetype, the canonical commands, the gates and, above all, the *distribution trigger*: the first action that can start public distribution. Anything it cannot derive stays `TODO`; anything it derived but you have not confirmed stays `CONFIRM:`.
2. **Invariants in the engine, policies in the profile.** Checking premises against the code, showing evidence, respecting authorization and verifying results in the external system are the shared guarantees. The profile declares supported project choices: triage states, Discussion outcomes, release gates and public language. Release changes can follow the repository process, require PRs or use authorized direct commits; guarantees and project choices are described in [PRINCIPLES.md](PRINCIPLES.md#what-we-require-recommend-and-leave-to-the-repository).
3. **Human gates with scope.** Every check ends as `passed`, `failed`, `not-run` or `not-applicable`; a gate is GO only when every mandatory check passed. A GO names the candidate (commit, digests) and lapses when it changes. The distribution trigger runs only after the GO, never before, even when it is a `make tag` that pushes.
4. **Resumable runs, without ceremony.** Releases and smoke runs write one record under `.maintainer/state/runs/` as the work happens and consult external results on resumption. The record is a result of the work, never a condition for continuing it: four commands (`new`, `set`, `show`, `finish`) cover a release, approvals are kept in the maintainer's words, only the publication approval binds mechanically to the exact candidate, and evidence is reused with a written rationale when its inputs did not change. `show` and `finish` apply one completion rule and name the same outstanding items. Older records remain readable without fabricated history.

A minimal profile for a PyPI library:

```toml
schema_version = 1

[project]
name = "example-lib"
repo = "example/lib"
artifact = "pypi-library"

[commands.validator]
run = "make test lint"

[release]
changelog = "CHANGELOG.md"
version_files = ["pyproject.toml"]
distribution_trigger = "make tag"      # creates and pushes the tag; publish.yml publishes on tag push

[artifacts.pypi]
package = "example-lib"
gate = '''
repo="$(git rev-parse --show-toplevel)" && src="$(mktemp -d)" && check_dir="$(mktemp -d)" &&
git -C "$repo" status --porcelain | sed 's/^/excluded from the build (not in HEAD): /' &&
git -C "$repo" worktree add --detach --quiet "$src" HEAD &&
(
  trap 'git -C "$repo" worktree remove --force "$src"; rm -rf "$check_dir"' EXIT &&
  cd "$src" && uv build && rm -rf "$repo/dist" && cp -R dist "$repo/dist" &&
  wheel="$(cd "$repo" && python3 -I -c 'from pathlib import Path; wheels = list(Path("dist").glob("*.whl")); assert len(wheels) == 1, "expected one wheel"; print(wheels[0].resolve())')" &&
  cd "$check_dir" &&
  uv run --isolated --no-project --with "$wheel" python -I -c 'import example_lib; print(example_lib.__file__)'
)
'''
```

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
PRINCIPLES.md                       product values and repository autonomy
VISION.md                          workflow design and implementation direction
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

## Feedback

Something misbehaved or could be better? Run `/oss-maintainer:plugin-feedback` (Claude Code) or `$plugin-feedback` (Codex): it drafts an issue for this repository with the skill, the harness, the readiness table and redacted evidence, and files it after your approval.

## Boundary with `snl-pm`

`oss-maintainer` covers intake (`triage`), review (`review-pr`), release, community (`process-discussions`) and the smoke gate. The Supernova `snl-pm` plugin keeps design, delivery and the Linear platform. `oss-maintainer` depends on no other plugin.

## License

MIT.
