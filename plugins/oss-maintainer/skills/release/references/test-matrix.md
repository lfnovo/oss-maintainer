# Coverage table — change → risk → check

Instantiate against the real release diff, starting from the repository's own matrix in
`.maintainer/release/test-matrix.md`. The unit of planning is the **risk**, not the feature:
for each change ask *what can this break, and for whom?* Every project has an inverse
question too, and the profile's matrix names it: for security hardening, *does the protection
break legitimate use?*; for a provider abstraction, *does it hold interface parity?*; for a
content pipeline, *does it preserve uniformity across input paths?*

A change to shared machinery (a base class, routing, configuration loading, a build script)
widens the sweep: one baseline check per consumer of that machinery, not only the feature that
motivated the change.

## The table

One table, produced in step 1 with commands and selectors discovered in the repository, shown
with the one proposal, updated as results land and shown again at the GO. Its rows are the
checks in the run record.

| Check | Change / risk | Real probe | Observable success | Prerequisites | Who / paid scope | Stage | Mandatory |
|---|---|---|---|---|---|---|---|
| Name used in the record | Who can be affected and why this check is sufficient | Existing target plus verified selector, or concrete manual steps | What proves it worked, and where the evidence lands | Credentials, browsers, services (names only, never values) | Agent or owner; budget when applicable | pre-GO or post-publish | yes / no |

Rules for filling it:

- **Observable success, not a passing exit code.** A suite that tolerates a provider error
  does not prove a summary was generated. An extra that installs does not prove inference
  runs. A server that answers `initialize` does not prove a tool executed. Name the artifact
  or output that proves the path ran.
- **Not a CI gate does not mean not relevant.** The project may exclude its live suites from
  the default validator; a release that changed a provider still exercises that provider,
  with real credentials, at least once.
- Select the narrowest supported command for localized changes; widen for shared code with a
  stated dependency rationale. Do not invent flags or assume every provider test is required.
  If selectors do not exist, explain the smallest available suite and its cost.
- A path with no credentials, no device or no budget is a row marked `not-run`, reported as
  unverified this release. It is never implied as covered.
- Post-publication rows (install from the index, pull from the registry, release page) are
  required to finish the release and can never be prerequisites to the GO.

## Preflight

Before running the table, confirm what it needs: runtimes and browsers installed, credentials
present, services reachable. Presence is not capability: when an account can be out of
credits or quota, run one small authorized probe. Resolve or record what is missing now, so
the GO is not where it surfaces.

## Sources of checks

| Check | Source |
|---|---|
| The canonical validator, mandatory project checks and selected additional commands | profile |
| The archetype gate, built from the candidate commit | archetype reference |
| The smoke journey, when the repository has one | `smoke-e2e` skill |
| Dependency audit | security alerts, `npm audit`, `pip-audit` or the project's equivalent |
| Targeted probes for this release's risks | below, plus the repository's probe library |
| The owner's manual checks with real credentials | this release's diff and the credentials the owner has |

Checklist design rule: before writing an error-path item ("X unconfigured should show an
error"), verify in the code that it *is* an error; defaults and fallbacks often make it a
non-event.

### Probe classes

Adapt the endpoints and values to the repository; the classes recur:

- Limits: an input just under and just over each cap → accepted / clean rejection.
- Allowlisted parameters: every valid value plus one invalid, for the whole surface, not one
  sample (one sibling value failing while the others pass is a classic).
- Error paths return a clean 4xx, never a 500, for oversized arrays, unknown providers,
  malformed headers.
- Streaming endpoints stream progressively (first byte far earlier than the total time).
- Self-hosted legitimacy: local and private addresses keep working where the product promises
  them, while link-local and metadata addresses are rejected.
- Anything an LLM or a UI writes through: verify the full path end to end, in a real client,
  not only at the API.
- Deprecations: confirm the deprecated path still *works*, not only that the warning fires.

### Owner's manual checks

- Real credentials: connection tests for the providers whose code changed, one baseline per
  modality that did not.
- One end-to-end run of the expensive path (a paid API, a generated artifact, a real device).
- A visual or usability tour of every user-facing change.
- The prepared candidate on a fresh local environment or separately approved RC stack.

Hand these over early, with expected outcomes, tailored to what the release touched and to
the credentials the owner actually has, so the owner is never the bottleneck at the end.

## Automation worth building

Standing candidates: end-to-end scenarios for this release's features, CI-ification of any
probe that proved valuable twice, anything the owner keeps verifying by hand. Decide with the
owner in the step 1 proposal: build it now when it compounds for future releases and costs
less than the manual verification it replaces; otherwise verify manually this once and note
it in the repository's matrix for next time.
