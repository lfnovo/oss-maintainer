# Release runbook

The sequence and the policy of a release of this repository, in one place. The plugin's
`release` skill supplies the steps and the gates; `profile.toml` holds the executable
references (`[commands.validator]`, `[artifacts.*].gate`, `[release].distribution_trigger`);
this file holds what those fields cannot express: order, environment, manual steps, and the
reasons behind them. Other documents link here instead of repeating it.

## Validate

- Canonical validator and mandatory checks: `[commands.validator]` and `[release.gates].mandatory`.
- Artifact gate: `[artifacts.*].gate`, built from the candidate commit.
- Environment or credentials the checks need (names only, never values):
  - TODO

## Owner's manual checks

- TODO what the owner verifies by hand with real credentials, and what proves it worked

## Cut

- TODO anything beyond bumping `[release].version_files`, dating the changelog and running
  `[release].lock_command`: a review requirement, a branch, a release PR template

## Publish, only after the GO

- Trigger: `[release].distribution_trigger`; workflow: `[release].publish_workflow`.
- TODO what to watch and what "done" looks like on the platform

## Verify from the registry

- TODO the install or pull that proves users receive the published artifact

## Cleanup

- TODO
