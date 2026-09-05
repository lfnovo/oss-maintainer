# Preset `maturity-ladder` — states, transitions, criteria

The default state policy of `triage`. A repository adopts it as is, extends it with
`[triage].extra_states`, or replaces it by declaring its own states and `[triage].assignable`
in the profile. Label names are mapped through `[labels]`; the semantics below are what the
policy is about.

## States

The state says how specified an item is, not its priority or urgency:

| State | Meaning |
|---|---|
| `needs-triage` | intake; applied by templates or by hand; triage always removes it |
| `needs-vision` | needs a product-vision decision before technical design; recognised, not assigned by triage |
| `needs-design` | a real request with open architectural questions; design resolves them and promotes to `ready` |
| `ready` | fully specified; a developer picks it up without changes |
| `awaiting-demand` | a valid idea with no concrete demand yet; parked outside the flow; recognised, not assigned by triage |
| closed | no demand, superseded, duplicate, or already implemented |

Assignable by triage, by default: close, `needs-design`, `ready`. Downstream states
(`doing`, `review`, `done`) belong to delivery and are outside this skill.

## Criteria

**Close** when any of:

- already implemented (verified in the code);
- speculative, with no concrete user request; close with an open door ("reopen if you need it
  and we will prioritise");
- superseded by a newer, broader or better specified issue;
- duplicate (link the canonical issue).

**`ready`** when all of:

- a clear problem statement;
- implementation pointers (reference files, patterns to follow);
- acceptance criteria, explicit or obvious from context;
- every architectural decision resolved;
- for new components or integrations: external interface, identifiers, authentication and
  contract formats specified.

**`needs-design`** when any of:

- open architectural questions in the body or the comments;
- scope too broad (several unrelated features in one issue);
- competing implementation approaches without a decision;
- unresolved cross-component consistency questions;
- vague references to external capabilities without concrete detail.

When it cannot be told whether the feature exists: never close; assign `needs-design` and say
what could not be determined.

## Transitions

`needs-triage` → close | `needs-design` | `ready`. Triage never moves an item backwards from a
downstream state unless the maintainer explicitly asks for that issue.

## Extending the preset

Projects commonly add `needs-reproduction`, `needs-info`, `confirmed`, `blocked` or
`help-wanted`, or keep bugs open without immediate demand. Declare each as
`[triage].extra_states = { name = "meaning" }`, list the ones triage may assign in
`[triage].assignable`, and describe their criteria in `.maintainer/triage.md`. The invariants
(check the premises, show evidence, confirm before writing) do not change.
