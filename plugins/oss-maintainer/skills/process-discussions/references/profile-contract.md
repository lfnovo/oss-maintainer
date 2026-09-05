# Profile contract — `process-discussions`

| Field | Use | Without it |
|---|---|---|
| `[project].repo` | the repository | ask the maintainer (read-only mode) |
| `[discussions].categories` | which categories form the queue; ids for GraphQL | capability not applicable |
| `[discussions].regenerate` | command to refresh the ids | the recipe in `references/graphql-recipes.md` |
| `[discussions].public_anchors` | documents replies may cite | nothing citable beyond public issues and PRs |
| `[discussions].never_cite` | what must never appear in public text | the `.maintainer/PROFILE.md` list |
| `[discussions].graduation`, `[discussions].close_on` | policies | `pull`; close on `answer` and when graduated work lands |
| `[labels].ready`, `[labels].bug` | labels for graduated Issues | `ready`, `bug` |
| `[triage].batch_approval` | whether a reviewed set may be authorized at once | one at a time |
| `[upstreams]` | local checkouts to verify claims about libraries | verification limited to this repository |
| `[artifacts.docker].dev_tag` | where to point testers when a fix merged | "the next release" |
| `[comms]` | languages, attribution | interact in the user's language, publish in English |

Companion file: `.maintainer/PROFILE.md` (scope, tone, never cite). Session summaries go to
`.maintainer/state/runs/`.
