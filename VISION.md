# oss-maintainer — Vision

**Status:** draft for discussion, revision 2 (2026-09-05, after the first review round)
**Scope:** a Claude Code + Codex plugin for maintainers of open-source projects: issue triage, PR review, release orchestration, community facilitation and a smoke gate, driven by a per-repository profile.

## What it is

`oss-maintainer` turns a project's own practices into assisted maintenance workflows. It prepares decisions with evidence, executes the actions the maintainer authorizes, and verifies the results, while preserving the policies and tools the community already uses.

For a maintainer the promise is continuity. The context, the criteria and the procedures of triage, review, release and community facilitation stop being rebuilt in every session: they live in the repository as a profile, the plugin supplies the method, and every run leaves a record the next one can resume from.

Six skills, one shared tree for Claude Code and Codex: `triage`, `review-pr`, `release`, `process-discussions`, `smoke-e2e` and `init`.

This document says where the plugin comes from, what each skill does, what a repository carries to use it, and what changes in the repositories we maintain today. Background: the inventory of skills across our `oss/` repositories and the market research in `research/oss-maintainer-landscape.md`.

---

## 1. Where it comes from

| Skill | Born in | What it encodes |
|---|---|---|
| `release` | open-notebook (v1.11.0 onwards), then adapted by hand for esperanto and content-core | Changelog audit, risk-based test matrix, artifact gate, fix loop via PRs, cut, publication behind an explicit GO, notes with credits, retro |
| `process-discussions` | open-notebook (calibrated on 2026-08-16, 09-02, 09-05) | Queue map, decomposition of ideas into needs, verification of claims in code, outcome vocabulary, reply structure, one-decision-at-a-time approval |
| `smoke-e2e` | open-notebook | Full happy path via API plus UI verification, evidence, GO / NO-GO verdict |
| `triage` | Supernova issue pipeline (`snl-pm`), used on open-notebook and esperanto | Classify open issues into close / needs-design / ready after checking their premises against the code; confirm every verdict before writing |
| `review-pr` | Supernova issue pipeline (`snl-pm`) | Full review of a PR against the project's own rules, existing AI reviews treated as hypotheses, P0 / P1 / P2 findings, the maintainer decides what to post |

Two problems motivate the plugin. The first is visible from inside: the skills are copies. The release skill exists three times with 20% to 34% shared lines, two of the copies are not versioned (they live only in one machine's gitignored `.claude/`), and each retro improves one copy while the others drift. The second is the one any maintainer feels: without a home for the project's criteria and procedures, every session rebuilds them from scratch, and the quality of a triage or a release depends on what the person remembered to say that day.

The market research is a snapshot, not a proof of absence. It found no solution that combines an integrated method for these workflows with the project's own policies, decisions backed by evidence and verification of results. Release orchestration with human gates appears only as in-repo skills of a few projects (OpenAI Agents SDK, Apache OpenDAL, GitVersion); Discussions facilitation has two products that reply and none that qualifies, decomposes, verifies or graduates; smoke tests as a release gate have no reusable form. That combination is the differentiation, and it must stay valid when a competitor appears. The saturated areas (changelog and semver generation, PR review products, issue triage by Action) are not where this plugin competes.

`triage` and `review-pr` come from the Supernova issue pipeline and join in a generic form: GitHub only (no Linear adapter), any AI reviewer already on a PR treated as input rather than a named dependency, content in English, interaction language taken from the profile.

The closest precedent is the `open-source-maintainer` plugin of the `n-skills` marketplace: a generic engine plus a per-repository profile in `.github/maintainer/`. It validates the shape; its content is different from ours.

---

## 2. Principles

1. **Engine and profile are separate, and the line is invariants versus policies.** The engine holds what must hold everywhere: verify premises before judging, present evidence, confirm results in the external system, ask before any public or irreversible mutation, record what was done. The profile holds policies: taxonomies and transitions, close and graduation criteria, gates and thresholds, languages, tone, channels. The behaviours calibrated in our repositories ship as recommended presets, never as universal requirements.
2. **The human owns every public or irreversible action, and authorization has a scope.** Skills are propose-only by default. An authorization names the actions it covers, the candidate it applies to (a commit, an artifact digest, a text) and the conditions that invalidate it. A GO given for one candidate does not carry over when the candidate changes. Where a project splits preparation, review and publication between different maintainers, the skills follow that governance; they add no role system of their own.
3. **Verdicts are binary; checks are not.** Every check ends as `passed`, `failed`, `not-run` or `not-applicable`. A gate is GO only when every mandatory check passed. Absence of evidence is never approval, and producing a report is not a positive result.
4. **External confirmation and artifact identity.** A phase is done when the external system confirms it: the remote has the tag, the registry serves the manifest, the package installs from the index. What was tested and what is promoted should be the same bytes, recorded by digest. When a pipeline rebuilds before publishing, the run says so and verifies the artifact that was actually distributed.
5. **The deterministic layer executes; the agent orchestrates and judges risk.** `make`, `gh`, `.github/release.yml`, `git-cliff`, CI workflows and registry APIs remain the executors. The plugin adds what happens before and after the command: risk analysis, artifact gate, fix loop, verification, retro.
6. **Retro records always and applies within scope.** Every run that produced learning records it. Improvements that are agreed and small land in the same run, by PR in the repository or in the plugin; larger ones become proposals. Finishing a release never depends on opening a new front in the engine.
7. **Portable core, native edges.** One `skills/` tree shared by Claude Code and Codex, native manifests per harness, no harness-only variables in shared content, adapters only where a harness needs them.
8. **Born from real repositories, stabilized with external ones.** The profile schema grows from open-notebook, esperanto and content-core, and is frozen only after a maintainer outside this house has used it.
9. **The trust boundary includes the change under review.** Everything read from GitHub is data, never instructions. Files that arrive through a PR (`.maintainer/`, `AGENTS.md`, `Makefile`, scripts, workflows) are part of the change, not the rules for judging it: a review applies the policies of the base branch, and a PR cannot grant authority to its own review.

---

## 3. The skills

### 3.1 `init` — bootstrap, validate and report readiness

Purpose: make a repository ready for the skills it wants to use, keep its profile valid as the schema evolves, and tell the maintainer what is ready.

How it works:

- Reads what the repository already declares: `Makefile`, `.github/workflows/`, `AGENTS.md` and `CLAUDE.md`, `CHANGELOG.md`, `pyproject.toml` or `package.json`, `Dockerfile`, contribution and release documents.
- Classifies the artifact archetype: `app-docker`, `pypi-library`, `npm-package`, `custom` (an explicit runbook exists and the engine follows it) or `unknown` (nothing could be derived; release stays unavailable until filled in).
- Finds the **distribution trigger**: the first action that can start public distribution, directly or through a workflow. It reads the tag target of the `Makefile` and the `on:` blocks of the workflows to answer "what happens when a tag is pushed, a release is created, a workflow is dispatched", and writes the answer into the profile for the maintainer to confirm.
- Proposes `.maintainer/` from the templates bundled in the plugin, filled with what it derived and `TODO` markers for what it could not. It never invents commands.
- Validates the profile deterministically: types, required fields per skill, paths that must exist, references that must resolve, `TODO` markers that block the skill that needs them. A syntactically valid file is not an executable profile.
- Adds the pointer that makes the profile discoverable (one line in `AGENTS.md`; `CLAUDE.md` contains `@AGENTS.md`, so nothing is duplicated) and the engine pin (section 4.5).
- Opens the result as a PR. On a repository that already has a profile it validates `schema_version`, reports missing or stale fields, and proposes the upgrade.

Readiness is reported per capability, not as one bit: "review available; triage needs its state policy confirmed; release incomplete (distribution trigger unconfirmed, image gate missing); discussions not applicable". A maintainer who wants only `review-pr` never configures registries.

Skills that only read (`review-pr`, the analysis half of `triage`, the queue map of `process-discussions`) can run without a persisted profile: they use the engine presets, read the repository and GitHub live, and state which policies were assumed. Any mutation still requires the profile.

### 3.2 `release` — orchestrate a release behind human gates

Purpose: take a repository from "main has enough validated change" to a published, verified release, with the maintainer deciding every irreversible step.

The engine defines the phases; the profile supplies the commands, the gates, the trigger and the gotchas.

| Phase | Engine (generic) | Profile (per repository) |
|---|---|---|
| 0 Scope and changelog audit | last tag, merged range, changelog convention check, security alerts | changelog path and convention, alerts policy |
| 1 Version decision | SemVer classification of the aggregate diff, proposed to the owner | what counts as a consumer surface (public exports, CLI flags, MCP tools, config keys) |
| 2 Test matrix | risk-based template with three buckets: **A** automated now, **B** automatable with investment, **C** manual by the owner. Bucket B is decided with the owner: build it now when it compounds for future releases and costs less than the manual check it replaces, otherwise verify manually this once and record it for next time. Only A and C feed the gates; B feeds A or C | probe library, standing bucket-C items, credentials the owner has |
| 3 Bucket A | run the canonical validator and the other declared commands | command references (section 4.3), "not a gate" list |
| 4 Artifact gate | the archetype's gate; records the digest of what was tested | gate command, registries, variants, platforms |
| 5 Bucket C handoff | concrete checklist delivered early, in parallel | provider list, manual tour items |
| 6 Fix loop | reproduce, root-cause, focused PR with regression test, CI, merge per policy; re-test policy | merge authorization policy, contribution conventions |
| 7 Prepare the cut | bump, date the changelog, lock file, cut PR merged; artifact gate re-run on the merged commit, which becomes **the candidate** | version files, lock command |
| 8 Notes and credits | release notes drafted from the structured source, contributor credits collected by command, approved by the owner **before** publication | notes source, credit conventions |
| 9 GO | explicit authorization for this candidate, with its scope recorded (actions, digest, expiry conditions) | who may give it, when the project splits roles |
| 10 Publish | the distribution trigger runs here and only here. For a tag-triggered pipeline the tag is created and pushed in this phase, never in phase 7 | distribution trigger, publish workflow, latest promotion |
| 11 Post-publish verification | verify from the registry, never from the local build; compare digests; when the pipeline rebuilt, state the limit of the evidence and verify the distributed artifact | manifests, install command, release page |
| 12 Announce | deliver the approved texts to the owner's channels; confirm what was posted | channels and skeletons |
| 13 Cleanup | stacks down, temp data removed, clean working tree | stack commands |
| 14 Retro | record learning; apply what is agreed and small; propose the rest | |

GO criteria are nominal and numeric: every mandatory check `passed`, bucket C signed off by the owner, zero open release regressions, alerts resolved or explicitly accepted. A `not-run` mandatory check is a NO-GO with a reason, not a warning.

The ordering rule that matters most: **the GO precedes the first action that can start distribution, including indirectly.** In esperanto and content-core, `make tag` creates the tag and pushes it, and the tag push runs the publish workflow to PyPI. A cut that "tags" in phase 7 would publish before the gate and before the GO. `init` finds that trigger by reading the `Makefile` and the workflows, and the phases above place it after the GO. In content-core the publish workflow also rebuilds the wheel after its packaging job, so the local gate and the published artifact are different builds; phase 11 verifies the published one and the run record says the local gate ran on another build.

Artifact archetypes known in v1: `app-docker` (open-notebook) and `pypi-library` (esperanto, content-core). `npm-package` is a template placeholder until a real repository needs it; `custom` follows the repository's runbook with the same gates.

#### Run record and resumption

Every run writes a small record under `.maintainer/state/runs/`: candidate commit and digests, engine version and how it was resolved, the effective profile with any overlay differences, commands executed, the status of every check, evidence paths, authorizations with their scope. A new run starts by reading the last record **and** the external systems (tags, releases, registries, CI), recognises what already happened, and repeats only what is missing. A relevant change (a new commit on the candidate, a changed profile policy, a rebuilt artifact) invalidates the affected gates and their authorizations. Publication across several registries is never assumed atomic: each target is verified on its own, and a run that published a package but failed an image resumes at the image.

### 3.3 `process-discussions` — facilitate the community queue

Purpose: turn a GitHub Discussions queue into qualified, routed, honest replies and, when the project's policy says so, into Issues. The maintainer approves every text before it is posted.

Engine (invariants):

- Queue map first: cohorts, authors with several entries, theme clusters, processing state of every open thread, graduated Issues that closed since the last run.
- Per thread: fetch everything, decompose into distinct needs, search precedents, verify claims in the code, check alignment against the public decision records the profile names.
- Reply structure and honesty rules; evidence marked as verified or opinion; side actions before the reply; scoreboard at session close.
- Approval before posting. Default: one decision at a time. The maintainer may authorize a concrete set of decisions at once when every proposal, text and effect is visible; that is not auto-posting and not a blanket approval.
- Supervision ladder: draft-only is the only mode in v1.

Profile (policies, shipped as presets from the open-notebook practice):

- Outcome vocabulary (`exploring`, `incubating`, `accepted → graduated`, `parked until champion`, `combine`, `answer`, `bug`).
- Graduation rule. Preset: pull, an Issue is born when someone will build. A project that records accepted proposals or bugs without a committed builder sets its own rule.
- Close rules. Preset: close on `answer` and when graduated work lands. A project that keeps Discussions open after delivery sets its own.
- Repository, categories with the command that regenerates their ids, public anchors, never-cite list, canonical-thread precedents, style calibrations, upstream checkouts, label mapping.
- Public language from `[comms]`, not English by construction.

### 3.4 `smoke-e2e` — run the product journey and give a verdict

Purpose: prove that a running instance works end to end before a release, with evidence.

Engine: health checks, journey execution with polling and timeouts, evidence collection (response bodies, screenshots, query results), UI verification through a browser, cleanup of everything created, report file, binary verdict with the status of every check.

The profile declares which surfaces are mandatory. When the browser is unavailable, UI checks are `not-run`; if UI is mandatory the verdict is NO-GO. An HTTP status check may run as partial evidence and is reported as such; it never satisfies a UI check silently.

Profile: `smoke/journey.md` (endpoints, payload conventions, fixtures, pages to verify, known quirks), service URLs, mandatory surfaces, report path.

Claude Code gets an agent adapter that preloads the skill so `release` can delegate the gate. Codex runs the skill directly; the missing bundled-agent packaging is an accepted gap recorded in the index.

### 3.5 `triage` — classify open issues so the pipeline can flow

Purpose: put every open issue into one of the project's outcomes, with the maintainer confirming each verdict.

Engine (invariants):

- Reality check before judging: does the feature already exist in the code, is there an active PR, do the external claims hold, is another open issue covering the same ground.
- A compact report block per issue with the evidence, explicit confirmation before any write, and the upgrade flow that promotes a thin issue straight to `ready` with a researched rewrite shown first.
- GitHub recipes for its own operations: label bootstrap, read an issue with full context, apply a state and remove the previous one, close with an open door, rewrite.
- Related issues are pointed out, never consolidated silently; when it cannot tell whether something is implemented it never closes, it falls to the state the policy names for "needs work" and says why.
- Default one issue at a time. The maintainer may authorize a reviewed set at once, each proposal and its effect visible.

Profile (policies):

- States, transitions and close criteria. The preset is the maturity ladder we use (`needs-triage` intake; outcomes close, `needs-design`, `ready`; recognised states `needs-vision`, `awaiting-demand`). A project that distinguishes `needs-reproduction`, `confirmed`, `blocked` or `help-wanted`, or keeps bugs without immediate demand, declares its own states and which ones triage may assign. Mapping label names is not enough; the policy is the semantics.
- `.maintainer/triage.md`: the repository's own rules, extra labels, area conventions, owners by theme, vision-fit heuristics and the decision records they cite. This is the convention known today as `TRIAGE.md` at the repository root. When it is missing the skill offers to seed it from the labels in use, `CONTRIBUTING.md` and already-triaged issues, and writes only on confirmation.

Removed from the `snl-pm` version: the Linear adapter, the argument and skill-directory variables, the fixed interaction language.

### 3.6 `review-pr` — review a pull request as the maintainer

Purpose: produce a grounded verdict on a PR (approve, request changes, comment) with classified findings, judged against the project's own rules rather than personal taste. The maintainer decides what gets posted. Merge is never this skill's action.

Engine:

- Project context first, found by function and not by file name: the documents for agents (canonical validator, traps, conventions), architecture and vision documents, contribution and testing guides. When none exist the review proceeds on general judgement and reports the gap.
- **Policies come from the base branch.** The PR's own versions of `.maintainer/`, `AGENTS.md`, `Makefile`, scripts and workflows are part of the diff under review; changes to them are findings to assess, and the review is judged with the base versions.
- The PR loaded completely: description, diff, commits, CI checks, existing reviews and threads including resolved ones, the linked issue with its acceptance criteria.
- Any AI review already on the PR (cubic, CodeRabbit, Copilot, Claude code review) is a set of hypotheses to verify against the code; the report states what was confirmed and what was refuted.
- Six dimensions: correctness, adherence to the issue (including scope creep), architectural consistency, consistency with the two or three closest sibling implementations, tests, security. Large diffs are delegated by area and consolidated; nothing is skipped silently.
- Report block with P0 (blocks merge), P1 (should be fixed, here or in a follow-up), P2 (polish). A finding without an anchor (a project document, a sibling pattern, a demonstrable bug) is at most P2. Findings that recur across PRs are flagged as candidates for an architecture principle or a reviewer rule.
- Decision, then action: post the review, fix on the PR branch only on explicit request (project validator, push without force, reply in the thread), answer a wrong AI finding with the rule so the reviewer learns when it supports that, or skip.

Profile: `[review]` lists the documents the review judges against when the defaults are not enough, and the AI reviewers the repository uses so their findings are looked for.

Removed from the `snl-pm` version: the cubic-specific reading of reviews and memory mechanics, the Linear adapter for linked issues, the skill-directory variables.

### 3.7 Explicitly out of scope for v1

The design and delivery steps of the issue pipeline (`design`, `develop` and `project-management` stay in `snl-pm`), a Linear adapter (GitHub only), replacing automated PR reviewers (they are inputs to `review-pr`), changelog and version generation engines (compose with `git-cliff`, `release-please` or the repo's own convention), a hosted GitHub App, auto-posting anywhere, Cursor manifests, a role system.

---

## 4. Repository setup: `.maintainer/`

### 4.1 Layout

```
.maintainer/
├── README.md              # what this directory is, for humans; distinct from MAINTAINERS
├── profile.toml           # machine-readable profile, carries schema_version
├── PROFILE.md             # scope (own / do not own), tone, what must never be cited
├── gotchas.md             # fragile areas and known issues, fed by retros
├── triage.md              # repository-specific triage rules (today's TRIAGE.md convention)
├── release/
│   ├── runbook.md         # exact commands of this repository for cut, publish, verify, cleanup
│   └── test-matrix.md     # the A/B/C matrix instantiated for this repository
├── smoke/
│   └── journey.md         # the product journey the smoke skill executes
├── decisions.md           # append-only log of release and Discussions decisions
├── profile.local.toml     # gitignored: local preferences (section 4.4)
└── state/                 # gitignored: runs/, reports, hashes
```

Only `profile.toml` is mandatory. `smoke/` exists only for applications; `triage.md` only where the repository has rules beyond the preset. `decisions.md` is optional in v1 and is discussed in section 8.

### 4.2 `profile.toml`

Illustrative, derived from open-notebook. Field names are proposals until `init` has run against the three real repositories and one external one.

```toml
schema_version = 1
# Every path is relative to the repository root, including paths into .maintainer/.

[project]
name = "open-notebook"
repo = "lfnovo/open-notebook"
artifact = "app-docker"                     # app-docker | pypi-library | npm-package | custom | unknown
commands_doc = "AGENTS.md"                  # where the canonical commands are documented

[commands.validator]                        # invoking a canonical target is a reference; copying its body is duplication
run = "make test lint typecheck"
cwd = "."
timeout = "20m"

[commands.frontend]
run = "npm run lint && npm run test && npm run build"
cwd = "frontend"
timeout = "15m"

[contributing]
conventions = "docs/7-DEVELOPMENT/contributing.md"   # PR, branch and commit conventions the skills follow

[release]
process_doc = ".github/RELEASE_PROCESS.md"
changelog = "CHANGELOG.md"
version_files = ["pyproject.toml"]
distribution_trigger = "gh release create"  # first action that can start public distribution; confirmed by init
publish_workflow = "build-and-release.yml"
latest_promotion = "publication promotes v1-latest"
notes_source = ".github/release.yml"

[release.gates]
mandatory = ["validator", "frontend", "image-gate", "bucket-c", "notes-approved"]
optional = ["security-alerts"]              # reported with a status, never silently skipped
alerts_policy = "highs resolved or explicitly accepted"
merge_own_prs = "ask-once-per-session"

[artifacts.docker]
registries = ["lfnovo/open_notebook", "ghcr.io/lfnovo/open-notebook"]
variants = ["", "-single"]
platforms = ["amd64", "arm64"]
dev_tag = "v1-dev"
gate = "make release-test TAG=<ver> OLD_TAG=<prev>"
identity = "manifest-digest"                # what is recorded and compared per registry and variant

[labels]                                    # canonical -> real
needs_triage = "needs-triage"
needs_design = "needs-design"
needs_vision = "needs-vision"
awaiting_demand = "awaiting-demand"
ready = "ready"
released = "released"
bug = "bug"

[triage]
preset = "maturity-ladder"                  # states, transitions and close criteria shipped by the engine
assignable = ["close", "needs-design", "ready"]
extra_states = { needs-info = "waiting for the reporter; recognised, never assigned by triage" }
rules = ".maintainer/triage.md"
batch_approval = "allowed"                  # a reviewed set may be authorized at once; default is one at a time

[review]
docs = ["AGENTS.md", "VISION.md", "docs/7-DEVELOPMENT/architecture.md", "docs/7-DEVELOPMENT/decisions/"]
reviewers = ["cubic"]                       # AI reviewers whose findings are treated as hypotheses

[discussions]
categories = { ideas = "DIC_kwDONDsQ184CjkD_", feedback = "DIC_kwDONDsQ184DBrfp" }
regenerate = "gh api graphql ... discussionCategories"
public_anchors = ["VISION.md", "docs/7-DEVELOPMENT/decisions/"]
never_cite = [".tmp-context/", "maintainer/"]
graduation = "pull"                         # preset; a project may declare its own rule
close_on = ["answer", "graduated-work-landed"]

[smoke]
api_url = "http://localhost:5055"
frontend_url = "http://localhost:3000"
mandatory_surfaces = ["api", "ui"]          # a mandatory surface that cannot run blocks GO
report_path = ".maintainer/state/smoke-report.md"

[comms]
owner_language = "pt-BR"
public_language = "en"
agent_attribution = "none"                  # none | disclaimer

[channels]
announce = ["discord"]                      # texts delivered to the owner, never posted by the skill

[upstreams]
esperanto = "../esperanto/esperanto"
content-core = "../content-core"
```

The same file for esperanto is shorter: `artifact = "pypi-library"`, `distribution_trigger = "make tag"` (it pushes the tag, and the tag push publishes), an `[artifacts.pypi]` table with the clean-room install command and the `pytest -m release` ritual as the bucket-C gate, `[labels]`, `[triage]` and `[review]`, no `[smoke]`, no `[discussions]`.

### 4.3 What lives where

| Kind of knowledge | Lives in | Read by |
|---|---|---|
| Phases, invariants, verdict rules, templates, presets | plugin `skills/` | every repo |
| Canonical build, test and lint commands | `AGENTS.md`, `Makefile` | profile references them |
| The human release process | `.github/RELEASE_PROCESS.md` or equivalent | profile points to it |
| Commands, gates, trigger, registries, ids, anchors, gotchas of this repo | `.maintainer/` | skills |
| Repository-specific triage rules and vision-fit heuristics | `.maintainer/triage.md` | `triage` |
| Documents a review judges against | where they already live, listed in `profile.toml [review]` | `review-pr` |
| Local preferences | `.maintainer/profile.local.toml` (gitignored) | skills, within the allowed tables |
| Run records and reports | `.maintainer/state/` (gitignored) | skills, on resumption |

Rule against drift: a fact has exactly one home. Invoking a canonical target (`make test`, `npm run build`) in the profile is a reference; copying what the target does is duplication. The retro updates the home of each fact, not the copies.

Path convention: every path in `profile.toml` is relative to the repository root, including paths into `.maintainer/`. Commands declare their own `cwd` and `timeout`.

### 4.4 Local overlay

`profile.local.toml` exists for what differs between machines and people, not for policy. It may set local preferences: service URLs, upstream checkout paths, `owner_language`, private channel ids, credential pointers. It may not set gates, mandatory checks, publication criteria, authorization policy, state policies or public language. The engine merges the overlay only into the allowed tables, reports and ignores anything else, and prints the effective profile with the overlay differences at the start of every run and into the run record. A local file never weakens a shared policy silently.

### 4.5 Discovery and pinning

No harness discovers `.maintainer/` on its own, and installing a plugin is not the same as pinning it. Three things make the setup work:

- **Discovery.** One pointer line in `AGENTS.md` ("Maintainer profile lives in `.maintainer/`; do not run release, triage or discussions workflows without it"); `CLAUDE.md` contains `@AGENTS.md`. In Claude Code, `.claude/settings.json` declares the marketplace in `extraKnownMarketplaces` and enables the plugin in `enabledPlugins`. Neither carries a version.
- **Pinning.** In Claude Code the version comes from the marketplace source `ref` (a tag of the plugin repository, published per release; marketplace sources accept `ref` but not `sha`) and from the `version` field of the catalog entry, which fixes the cached copy until it changes. The run record stores the plugin version and how it was resolved, so a run is reproducible even when the pin is loose. Codex: a marketplace entry in `.agents/plugins/marketplace.json` pointing at the plugin's git source is the intended mechanism; it is unverified against the current Codex plugin loader and stays marked as pending until tested.
- **Schema.** `profile.toml` carries `schema_version`; the engine refuses unknown versions and `init` proposes the upgrade.

Hygiene: `.gitattributes` gets `.maintainer/ export-ignore` in projects that publish tarballs (this does not affect `git push`), and `.maintainer/README.md` explains the directory to contributors who stumble on it. Nested profiles for monorepos are not designed until a real case appears.

---

## 5. The plugin repository

```
oss-maintainer/                      # marketplace: oss-maintainer
├── .claude-plugin/marketplace.json  # Claude catalog
├── .agents/plugins/marketplace.json # Codex catalog
├── .agent-smith/index.json          # component graph, adapters, accepted gaps
├── VISION.md                        # this document
├── research/                        # landscape research (input to this vision)
├── evals/                           # scenarios and fixtures (section 5.1)
└── plugins/oss-maintainer/
    ├── .claude-plugin/plugin.json
    ├── .codex-plugin/plugin.json    # skills: ./skills/
    ├── skills/
    │   ├── init/                    # SKILL.md + templates/ for .maintainer/ + validation script
    │   ├── triage/                  # SKILL.md + references/ (ladder preset, GitHub recipes)
    │   ├── review-pr/               # SKILL.md + references/ (GitHub recipes)
    │   ├── release/                 # SKILL.md + references/ (gates, matrix, notes templates)
    │   ├── process-discussions/     # SKILL.md + references/
    │   └── smoke-e2e/               # SKILL.md
    └── agents/smoke-e2e.md          # Claude subagent adapter
```

Invocation: `/oss-maintainer:triage`, `/oss-maintainer:review-pr`, `/oss-maintainer:release`, `/oss-maintainer:process-discussions`, `/oss-maintainer:smoke-e2e`, `/oss-maintainer:init` in Claude Code; by name in Codex. Every skill that changes public state (`triage`, `review-pr`, `release`, `process-discussions`) is user-invoked only, with no model auto-invocation; `smoke-e2e` may be delegated by `release`.

Each skill carries its own GitHub recipes under `references/`. The validator forbids a skill referencing files outside its directory, so the small overlap between `triage` and `review-pr` recipes is accepted over a shared file (open question in section 8).

Versioning: the plugin follows SemVer; the profile schema has its own integer `schema_version`. A plugin minor may add optional profile fields; a schema bump is a plugin major. Each release of the plugin tags the repository so marketplaces can pin by `ref`.

### 5.1 Validation

Structural: `claude plugin validate`, the agent-smith validator, and an install from GitHub in both CLIs.

Behavioural parity: a shared skills tree does not prove the two harnesses behave the same. Before a release of the plugin, the same scenarios run in Claude Code and Codex and must show the same invocation, the same confirmation before mutations, the same profile and reference loading, the same gate execution and the same resumption. Scenarios live in `evals/` as fixtures (small fake repositories with a `Makefile`, workflows and a profile) and local evaluations:

- profile incomplete: the skill reports readiness per capability and stops before any mutation;
- a `Makefile` whose tag target pushes, and a workflow that publishes on tag push: `init` detects the trigger and `release` never tags before the GO;
- partial publication: one registry succeeded and another failed; the next run verifies each target and resumes at the failed one;
- UI unavailable with UI mandatory: `not-run` and NO-GO;
- a PR that alters `.maintainer/`, `AGENTS.md` or a workflow: `review-pr` judges with the base policies and flags the change;
- a local overlay that tries to change a gate: reported and ignored.

---

## 6. How this changes what we have today

### 6.1 `open-notebook-mgmt` (this repository)

- Rename to `lfnovo/oss-maintainer`; plugin `on-maintainer` becomes `oss-maintainer`. The old marketplace registration in both CLIs is replaced.
- The skills lose everything that is Open Notebook: ports and startup order, `make` targets, registries and variants, the CI workflow name and its inputs, the `v1-latest` promotion rule, the GraphQL category ids, the public anchors and the never-cite list, the Discord skeleton, the 400-line product journey. Section 4.7 of the research maps each item to its profile field.
- `smoke-e2e` keeps the protocol and loses the journey. `release` keeps the phases and loses the runbook. `process-discussions` keeps the method and loses the ids, anchors and policies, which become presets.
- `init`, its templates, the profile validation and the `evals/` scenarios are new.

### 6.2 `open-notebook`

The pending cleanup branch changes nature. Instead of only removing `.agents/skills`, `.claude/skills`, `.claude/agents` and `.codex/agents`, the PR also adds `.maintainer/` (profile, `release/runbook.md`, `release/test-matrix.md`, `smoke/journey.md`, `gotchas.md` seeded from the current Known Gotchas), the pointer line in `AGENTS.md`, the marketplace declaration, and the `.gitignore` entries for the local overlay and state. `.github/RELEASE_PROCESS.md` stays as the human process document the profile points to. The operator notes in the gitignored `TRIAGE.local.md` become `.maintainer/triage.md`, versioned, pointing at the public taxonomy in `docs/7-DEVELOPMENT/maintainer-guide.md`. Transparency is preserved: the community keeps seeing the release profile and the Discussions configuration in the repository.

### 6.3 `esperanto` and `content-core`

Their release skills exist only as gitignored local copies. The first `init` run on each repository turns that knowledge into a versioned `.maintainer/` (archetype `pypi-library`; esperanto's `pytest -m release` ritual and content-core's three-surface packaging gate become their `release/runbook.md`). In both, `init` will record `make tag` as the distribution trigger, because the target pushes the tag and the tag push publishes to PyPI. content-core's `version_files` also lists its own plugin manifests, which must equal the package version, and its profile notes that the publish workflow rebuilds the wheel after the packaging job. After the profiles land, the local `.claude/skills/release` copies are deleted, together with esperanto's local `triage` (superseded by this plugin's `triage`), `design` and `develop` (superseded by `snl-pm`) and `archon`.

### 6.4 Other libraries

ai-prompter, podcast-creator, surreal-commands, surreal-basics, surreal-mcp, langgraph-checkpoint-surrealdb and omni-storage share the same mechanics (`make tag` from `pyproject.toml`, tag push publishes to PyPI). `init` bootstraps each one when its next release is due. No rush and no pre-emptive profiles.

### 6.5 Neighbouring plugins

- `snl-pm` is the origin of `triage` and `review-pr`. `oss-maintainer` carries their generic form; `snl-pm` keeps `design`, `develop`, `project-management`, the GitHub and Linear conventions and, for now, its own Supernova-flavoured `triage` and `review-pr` with the Linear and cubic adapters. Rule to contain drift: `oss-maintainer` is the upstream of the generic method, changes land there first and are ported to `snl-pm`. A plugin dependency would express this in Claude Code but has no Codex equivalent, so it is not used. The boundary, written in both READMEs: `oss-maintainer` covers intake, review, release, community and smoke; `snl-pm` covers design, delivery and the Linear platform.
- `oss-maintainer` depends on no other plugin. The PRs it opens follow the repository's own contribution conventions (`[contributing].conventions`, or `CONTRIBUTING.md` found by function) and fall back to a conservative default (conventional commit message, linked issue, description with what and why) when none exist. Our repositories point their profiles at the conventions `snl-development` documents; an external maintainer never installs it.
- The `harny` plugin also has a skill named `release`; it is the release manager of harness runs, a different concept. Namespaces keep them apart.
- `agent-smith` remains the tool that keeps this repository's Claude and Codex representations in sync. `.maintainer/` is project data, not an agent-smith component.

---

## 7. Sequence

1. Rename the repository and the plugin. Extract one complete flow first: `init` plus `release`, validated on both archetypes we have (`app-docker` on open-notebook, `pypi-library` on esperanto or content-core), with the run record, the trigger detection and the scenarios of section 5.1. Reinstall in both CLIs.
2. Open the open-notebook PR (`.maintainer/`, pointer, marketplace declaration, removals) and the `init` PRs on esperanto and content-core. Delete the local copies once merged.
3. Add `triage`, `review-pr`, `process-discussions` and `smoke-e2e` incrementally, each with its profile section, its presets and its scenarios.
4. Pilot with at least one maintainer outside this house. Exit criterion: they configure and complete a useful workflow without editing the engine, without installing any Supernova plugin, and without explanations beyond the documentation.
5. Stabilize `schema_version = 1` after the pilot. Publish the README for other maintainers, install instructions and the boundary with `snl-pm`.

---

## 8. Open questions

- **Profile format.** TOML for machine fields plus Markdown for prose (proposed) versus Markdown with frontmatter everywhere. TOML validates; Markdown reads. The first `init` run should settle it.
- **Location.** `.maintainer/` (tool-neutral, literal precedents) versus `.github/maintainer/` (direct structural precedent, GitHub-bound, already crowded). Proposal: `.maintainer/`.
- **Trigger detection beyond `Makefile` and workflows.** Projects using `release-please`, `semantic-release` or a merge-triggered pipeline start distribution on a PR merge. `init` needs heuristics for those, or a required manual confirmation when it cannot tell.
- **Batch approval defaults.** Allowed per profile for `triage`; for `process-discussions` the current owner preference is one decision at a time. Whether the default differs per skill or per profile is open.
- **`smoke-e2e` as a skill or as a release phase.** Keeping it a skill lets it run outside releases and gives Claude a subagent. Proposal: keep the skill.
- **`decisions.md` in the repository.** Useful memory for future runs; adds a file contributors may not understand. Proposal: optional in v1, seeded by the retro.
- **Private identifiers.** Discord channel ids and similar go to `profile.local.toml`; Discussion category ids are public and stay in `profile.toml` with their regeneration command.
- **Codex pinning.** The repo-level marketplace entry pointing at a git source is unverified.
- **Running in CI later.** `claude-code-action` accepts `plugins` and `plugin_marketplaces`, which would allow a scheduled queue map for Discussions. Out of scope for v1; the design should not prevent it.
- **Agent attribution in public text.** The current policy is none. The profile carries the switch because other projects require a disclaimer.
- **The `snl-pm` copies of `triage` and `review-pr`.** Keep the Supernova variants (Linear, cubic) next to the generic ones, or drop them once `oss-maintainer` gains a Linear adapter? Proposal: keep both with `oss-maintainer` as upstream until that adapter exists.
- **Shared GitHub recipes.** Per-skill `references/` with a little duplication, or a `github-mechanics` skill the others load by name? Proposal: per skill; revisit if the recipes grow.
