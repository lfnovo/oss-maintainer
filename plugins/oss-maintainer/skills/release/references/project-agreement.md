# Project agreement

The plugin guarantees honest evidence, scoped authority, traceable delivery identity and
verification of external effects. Repository policies choose how those guarantees are met.

Read declared contribution rules, the human process document and the profile before proposing
work. Separate declared policy, inferred practice and unknowns. The profile binds supported
executable choices; linked documents supply their meaning. A conflict between explicit
choices is unresolved configuration: present the sources, effect and proposed resolution to
the authorized maintainer. Do not execute the conflicting action until resolved. Continue
independent authorized work. Proposed changes cannot authorize themselves.

Defaults apply only when the repository is silent. Identify them as defaults. The smallest
agreement needs the existing canonical validator, delivery process, publication trigger and
required evidence; philosophy and strategy stay in existing documents, referenced as needed.
Local overlays cannot change shared governance or weaken gates.

## Supported choices

- `release.change_delivery = "repository"` (default): discover contribution and process rules;
  use PRs as the stated fallback when no process exists. `pr` explicitly requires PRs;
  `direct` allows scoped direct commits/pushes when project protections and review rules allow.
- `release.versioning = "semver"` (default), or `repository` with a `process_doc` explaining
  the project's convention and compatibility commitments.
- `release.gates.merge_own_prs`: `ask-once-per-session` (legacy default), `ask-once-per-run`,
  `always-ask`, or `never`. A session grant expires with that session unless its actual scope
  explicitly covers resumption. An authorized run grant may survive session boundaries.
- Mandatory gates remain binding; `not_gates` only describes nonblocking signals. A check
  cannot be both mandatory and nonblocking. Policy changes require a new effective agreement.

Direct publication and PR-based publication use the same boundary: if a push or merge can
publish, prepare and validate the candidate first and defer that action until exact-candidate
GO. Never bypass required review, branch protection or a denied action. Explain unsupported
pipelines precisely, particularly when the prospective published identity cannot be verified.

## Examples

A solo library maintainer can choose `change_delivery = "direct"`, a documented versioning
convention, `make test` as validator and a tag push as publication trigger. Prepare the
reviewable commit, run the required checks, retain the authorized test scope and publish only
with the exact candidate and trigger approved. Keep the profile small.

A community can choose `change_delivery = "pr"`, `merge_own_prs = "never"`, independent
review, multiple artifact checks and a publishing merge. Prepare the candidate on a branch,
hand off the PR to the designated reviewer and retain evidence while its dependencies hold.
Approval to publish comes from the project's authorized maintainer after required review.
Neither example assumes a particular review bot or adds a role management system.
