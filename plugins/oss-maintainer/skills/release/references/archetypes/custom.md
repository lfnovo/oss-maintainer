# Archetype `custom` — the repository's own runbook

The project ships something the built-in archetypes do not describe, and
`.maintainer/release/runbook.md` states the exact commands for building, gating, publishing
and verifying it.

The steps, the gates, the check vocabulary and the ordering rule apply unchanged:

- The runbook's gate section is the artifact gate; it must produce a recorded identity
  (a digest, a checksum, a manifest) for what was tested.
- `[release].distribution_trigger` is still the first action that can start distribution and
  still runs only in step 5 after the GO.
- Post-publish verification uses the runbook's verification section and compares identities.

When the runbook lacks a gate or a verification section, `release` is incomplete for this
repository: propose the missing section instead of improvising commands.

`npm-package` is a placeholder in schema v1 and follows this archetype until a real repository
gives it its own reference.
