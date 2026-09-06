# Test matrix template — change → risk → bucket

Instantiate against the real release diff, starting from the repository's own matrix in
`.maintainer/release/test-matrix.md`. The unit of planning is the **risk**, not the feature:
for each change ask *what can this break, and for whom?* Every project has an inverse
question too, and the profile's matrix names it: for security hardening, *does the protection
break legitimate use?*; for a provider abstraction, *does it hold interface parity?*; for a
content pipeline, *does it preserve uniformity across input paths?*

A change to shared machinery (a base class, routing, configuration loading, a build script)
widens the sweep: one baseline check per consumer of that machinery, not only the feature that
motivated the change.

## Executable plan

Before execution, produce a compact table using commands/selectors discovered in the repository.
Do not invent flags or infer that every provider test is required. Preserve mandatory project
gates and the canonical validator independently of the additional risk-selected probes.

| Change / shared component | Risk and coverage | Exact command or manual steps | Expected result / evidence | Resources (no secret values) | Executor / paid scope and limit | Before or after publication | Gate / unavailable disposition |
|---|---|---|---|---|---|---|---|
| Affected surface | Who can be affected and why this check is sufficient | Existing target plus verified selector, or concrete steps | Observable pass/fail and evidence location | Environment, service and credential names only | Agent or owner; budget/count when applicable | Pre-GO or post-publish | Mandatory, optional; blocked or explicitly unverified |

Select a narrow supported command for localized changes. Shared code widens coverage only
with a stated dependency rationale. If selectors do not exist, explain the smallest available
suite and its cost; propose a supported alternative instead of silently running a broad paid
suite. Present the actual paid/manual scope for approval once, unless a valid grant already
covers it. Repeats consume the authorized allowance; an exhausted budget is a new decision.
Unavailable mandatory checks block the relevant gate; optional gaps remain visible.

## Bucket A — selected automated checks

| Check | Source |
|---|---|
| The canonical validator, mandatory project checks and selected additional commands | profile |
| The archetype gate | archetype reference |
| The smoke journey, when the repository has one | `smoke-e2e` skill |
| Dependency audit | security alerts, `npm audit`, `pip-audit` or the project's equivalent |
| Targeted probes for this release's risks | below, plus the repository's probe library |

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
  not only at the API (a field dropped on one side and ignored on the other is only visible
  end to end).
- Deprecations: confirm the deprecated path still *works*, not only that the warning fires.

## Bucket B — automatable with investment

Standing candidates: end-to-end scenarios for this release's features, CI-ification of any
probe that proved valuable twice, anything the owner keeps verifying by hand.

Decision rule, applied with the owner per item: build it now when it compounds for future
releases and costs less than the manual verification it replaces; otherwise verify manually
this once and note it in the repository's matrix for next time. Bucket B never feeds a gate
directly: what gets built joins A, what does not joins C.

## Bucket C — pre-publication manual checks, started early

- Real credentials: connection tests for the providers whose code changed, one baseline per
  modality that did not.
- One end-to-end run of the expensive path (a paid API, a generated artifact, a real device).
- A visual or usability tour of every user-facing change.
- The prepared candidate on a fresh local environment or separately approved RC stack.

Deliver this as a concrete checklist with expected outcomes, tailored to what the release
touched and to the credentials the owner actually has. A provider or path with no
credentials is recorded as **unverified this release**, never implied as covered. Start it
in parallel with bucket A so the owner is never the bottleneck at the end.

## Post-publication verification — phase 11

- Install/pull the distributed artifact in a fresh environment and repeat its surface smokes.
- Verify registry identity and the release page against the approved candidate and notes.

These checks start `not-run` until publication. Report them separately; they are required to
finish the release, but cannot be prerequisites to the publication they verify. Do not mark
them passed or waive them just to obtain the pre-publication GO.
