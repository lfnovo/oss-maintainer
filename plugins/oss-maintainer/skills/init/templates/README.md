# .maintainer

Maintainer profile read by the [oss-maintainer](https://github.com/lfnovo/oss-maintainer)
plugin for Claude Code and Codex. It holds what the maintenance workflows of this repository
need and cannot derive: commands to run, gates, the distribution trigger, identifiers, and
the lessons learned. It is not a list of people; see `MAINTAINERS` or `GOVERNANCE.md` for that.

| File | Purpose |
|---|---|
| `profile.toml` | machine-readable profile (schema v1) |
| `PROFILE.md` | scope, tone, what must never be cited in public |
| `gotchas.md` | fragile areas and known issues, fed by release retros |
| `triage.md` | triage rules specific to this repository |
| `release/runbook.md`, `release/test-matrix.md` | exact release commands and the risk matrix |
| `smoke/journey.md` | the product journey the smoke test executes (applications only) |
| `decisions.md` | append-only log of release and Discussions decisions (optional) |
| `profile.local.toml` | gitignored local preferences (URLs, checkouts, interaction language) |
| `state/` | gitignored run records and reports |

Commands documented in `AGENTS.md` or the `Makefile` are referenced from here, never copied.
