# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2026-09-05

### Fixed
- Keep publishing merges, including release fix merges, behind candidate-scoped GO; require
  a verifiable pre-merge identity or report the workflow unsupported (#2).
- Reconcile Docker publication with the release gates: explicit RC staging approval,
  separate immutable prerelease references, and no reuse of distributed final versions (#3).
- Isolate PyPI wheel and registry smokes from the source checkout and inherited Python path (#4).
- Reject unresolved nested markers, empty required fields, missing shared identity and invalid
  consumed label/contribution settings in capability readiness reports (#5).
- Return structured diagnostics for invalid TOML field/container types, including temporal
  values in JSON output, instead of crashing the profile validator (#6).
- Bind release approvals to version, commit and digests; supersede old evidence and clear
  terminal status on candidate changes, keeping published observations separate (#7).
- Derive the workflow to watch from the selected publication trigger, exclude build-only
  Docker steps, and expose ambiguous/conditional workflow detection (#8).
- Paginate Discussion queues, comments and nested replies independently; report interrupted
  reads as incomplete before making facilitation decisions (#9).
- Remove the unsupported `--state all` argument from precedent searches (#10).
- Separate pre-GO manual checks from post-publication verification and collect credits from
  the candidate SHA without depending on a future release tag (#11).

## [0.1.0] - 2026-09-05

### Added
- First release of the `oss-maintainer` plugin for Claude Code and Codex: a generic engine
  for maintainers of open-source projects, driven by a per-repository `.maintainer/` profile.
  Skills: `init` (bootstrap and validate the profile), `triage`, `review-pr`, `release`
  (orchestration behind human gates, `app-docker` and `pypi-library` archetypes),
  `process-discussions`, `smoke-e2e` and `plugin-feedback` (files an issue on this repository);
  a Claude subagent adapter for `smoke-e2e`.
- Profile schema v1, deterministic profile validator and repository detection scripts,
  fixture repositories, scenario tests and eval cases.

### Changed
- Renamed from `open-notebook-mgmt` / `on-maintainer`: the Open Notebook specifics that lived
  inside the skills now belong to that repository's `.maintainer/` profile.
