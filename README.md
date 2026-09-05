# open-notebook-mgmt

Plugin marketplace with maintainer tooling for
[Open Notebook](https://github.com/lfnovo/open-notebook). Skills are written
once and shared by Claude Code and Codex; each harness gets its own native
manifest.

## Plugins

### `on-maintainer`

| Component | Type | What it does |
|---|---|---|
| `release` | skill | Orchestrates a release: changelog audit, risk-based A/B/C test matrix, Docker image gate (fresh + upgrade), fix loop via PRs, cut, publication with credits, retro. Human gates in `references/gates.md`. |
| `process-discussions` | skill | Facilitates the GitHub Discussions queue: queue map, decomposition into needs, claim verification in code, outcome proposal, draft replies, graduation to Issues — one decision at a time, owner approves every post. |
| `smoke-e2e` | skill | Full end-to-end happy path (notebook → sources → chat → ask → transform → podcast → search → cleanup) via API, then UI verification with Playwright. Ends with GO / NO-GO. |
| `smoke-e2e` | agent (Claude only) | Subagent that preloads the `smoke-e2e` skill so the release flow can delegate the gate. Codex has no plugin-bundled agents; run the skill directly there. |

All three skills assume the working directory is a checkout of
`lfnovo/open-notebook` (they call `make`, `gh`, `uv`, `npm` and read
`.github/RELEASE_PROCESS.md` from that repo).

## Install

Claude Code:

```
/plugin marketplace add lfnovo/open-notebook-mgmt
/plugin install on-maintainer@open-notebook-mgmt
```

Codex:

```bash
codex plugin marketplace add lfnovo/open-notebook-mgmt
codex plugin add on-maintainer@open-notebook-mgmt
```

Skills are then available as `/on-maintainer:release`,
`/on-maintainer:process-discussions` and `/on-maintainer:smoke-e2e` in Claude
Code, and by name in Codex.

## Layout

```
.claude-plugin/marketplace.json     Claude Code catalog
.agents/plugins/marketplace.json    Codex catalog
.agent-smith/index.json             component graph, adapters, accepted gaps
plugins/on-maintainer/
  .claude-plugin/plugin.json        Claude manifest
  .codex-plugin/plugin.json         Codex manifest (skills: ./skills/)
  skills/<name>/SKILL.md            canonical skills (shared)
  agents/smoke-e2e.md               Claude subagent adapter
```

## Maintaining

Edit skills under `plugins/on-maintainer/skills/` only; there are no copies
to keep in sync. Bump `version` in both plugin manifests and both catalogs
together. Validate with the agent-smith plugin:

```bash
python3 <agent-smith>/scripts/validate_repository.py .
claude plugin validate .
```
