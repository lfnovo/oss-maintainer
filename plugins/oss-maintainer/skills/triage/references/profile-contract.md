# Profile contract — `triage`

| Field | Use | Without it |
|---|---|---|
| `[labels]` | canonical state → real label name | the canonical names |
| `[triage].preset` | `maturity-ladder` or `custom` (rules and explicit assignable states required) | `maturity-ladder` |
| `[triage].assignable` | outcomes triage may assign | close, `needs-design`, `ready` |
| `[triage].extra_states` | project-specific states and meanings | none |
| `[triage].rules` | repository triage rules | `.maintainer/triage.md` when present; offered when missing |
| `[triage].batch_approval` | whether a reviewed set may be authorized at once | one at a time |
| `[comms]` | languages | interact in the user's language, publish in English |
| `[review].docs` and the rules file | documents that decide vision fit | general judgement, stated as such |

Without a profile the skill runs in read-only mode: proposals with the preset, assumed
policies listed at the start of the reply, no label change and no comment.
