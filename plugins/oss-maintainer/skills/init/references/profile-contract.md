# Profile contract — `init`

`init` creates and maintains the profile, so it needs nothing from it to start.

| Mode | Precondition | Reads |
|---|---|---|
| `scaffold` | no `.maintainer/profile.toml` | the repository (see `detection.md`) |
| `check` | profile present | the profile, the overlay, the companion files |
| `upgrade` | profile with an older `schema_version` | the profile; proposes the diff |

Presets and templates it ships: `templates/` (one profile per archetype plus the companion
files) and `references/profile-schema.md` (the schema).
