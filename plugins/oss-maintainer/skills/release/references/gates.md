# Gates — what needs a human, what does not

When in doubt, ask. A blocked action is feedback, not an obstacle to route around.

## Autonomous, once the run is underway

- Run any test, build, probe or analysis; start and stop the local services the runbook
  declares.
- Create branches and commits; open PRs that follow the repository's conventions.
- Delegate to subagents where the harness supports them: the smoke journey, investigations,
  focused fixes, the changelog audit.
- Build the artifact locally and run its gate against it.
- Watch CI and the repository's reviewers.
- Write the run record, reports and evidence under `.maintainer/state/`.

## Requires an explicit answer in this session

| Action | Why |
|---|---|
| Merging PRs you authored | two-party review; ask once per session when `merge_own_prs = "ask-once-per-session"` and honour the answer |
| Approving the release notes and announcements | public text |
| The distribution trigger (phase 10) | the point of no return; for a tag-push pipeline, the tag push itself |
| RC staging to a registry | separate prerelease reference, candidate digest and explicit staging scope; never a final version or rolling tag |
| Anything that promotes a rolling channel (`latest`) | users receive it immediately |
| Creating issues | external artifacts the owner may not want |
| Mass-labeling issues | bulk modification of shared state |
| Paid or manual bucket C runs (real credentials, real providers) | cost and access |
| Touching the owner's data | only ever on copies; never mount or mutate originals |
| Lint, type or cleanup work beyond the release diff | a separate task with its own PR |
| Changing profile policies during a run | the run's authorizations were given under the current profile |

## Never

- Push to the default branch.
- Publish, push a tag or dispatch a publishing workflow to work around a blocked step.
- Mark a phase complete with a failing or `not-run` mandatory check. GO with known issues is
  worse than a NO-GO that catches problems before users do.
- Reuse or overwrite a published version; bump and re-cut.
- Hand-craft a tag that differs from the version files.
- Skip the artifact gate because the tests passed: source tests do not prove the shipped
  artifact works.
- Accept a local overlay that changes a gate.

## Authorization scope

An authorization names the actions it covers, the candidate it applies to (commit, digests,
approved text) and the conditions that end it: a new commit on the candidate, a rebuilt
artifact, a changed profile policy. When any of those happens, the affected checks return to
`not-run` and the authorization is asked again. "Merge when clean", given once per session,
covers PRs opened during the run; it does not cover the distribution trigger.

## Re-test policy after each fix merge

- Cheap suite (validator and the other declared commands): always.
- Artifact gate and smoke journey: when the fix touches what they cover.
- The owner's manual checks: only for what the fix touched.
- The final artifact gate always runs on the exact candidate that will be distributed.

## GO / NO-GO

A release is GO when every mandatory pre-publication check is `passed`, pre-publication
bucket C is signed off, no release
regression is open, security alerts are resolved or explicitly accepted, and the candidate
has not changed since the checks ran. Every other state is NO-GO with a stated reason.

Registry-dependent checks run after publication and do not feed its prerequisite GO. A
publishing merge follows `candidate-and-publication.md`, including merges in the fix loop.
