# Readiness report

`init` ends every run, and every other skill starts, with a readiness report per capability.
It is produced by `scripts/validate_profile.py` (`--json` for machines, plain text for people).

## Format

```
capability             status               details
init                   ready
release                needs-confirmation   confirm release.distribution_trigger
triage                 ready                assumed triage: maturity-ladder preset, one-at-a-time approval
review-pr              ready                assumed review.docs: found by function
process-discussions    not-applicable
smoke-e2e              incomplete           missing smoke.api_url; TODO smoke.journey
```

## Statuses

| Status | Meaning | What a skill does |
|---|---|---|
| `ready` | every required field is present and valid | proceeds |
| `needs-confirmation` | a `CONFIRM:` value is pending | uses the proposal for analysis, asks before any mutation that depends on it |
| `incomplete` | a required field is missing, invalid or `TODO` | proceeds with analysis, stops before the mutation that needs the field, names it |
| `not-applicable` | the capability's table is absent by design (`[smoke]`, `[discussions]`) | says so and stops |

Details are prefixed: `missing`, `TODO`, `confirm`, `assumed` (a preset in use), `warning`.

## Without a profile

Skills that only read (`review-pr`, the analysis half of `triage`, the queue map of
`process-discussions`) run in **read-only mode**: engine presets, live reads of the
repository and GitHub, and an explicit list of assumed policies at the start of the reply.
Any mutation requires the profile; the skill says "run `init` to scaffold `.maintainer/`"
and stops before it.

## Exit codes of the validator

`0` every requested capability is ready or not applicable; `1` at least one is incomplete or
needs confirmation, or the profile has errors; `2` the profile is missing or cannot be parsed.
