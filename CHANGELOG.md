# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
