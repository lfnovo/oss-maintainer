# Candidate identity and publication ordering

A preparation action is safe to run before the final GO only if it cannot distribute the
final version. Classify its actual workflow effect, including fix merges and pushes to a
branch that publishes. A general approval to merge clean PRs does not approve distribution.

## When merging publishes

Keep the cut PR and any fixes unmerged until phase 10. In phases 3–8, test on a candidate
branch that cannot publish on push, approve the notes against that candidate SHA, and record:

- the pinned PR head and base SHAs, merge method and intended target branch;
- the exact source commit the publishing job will check out;
- the tested artifact digests and whether the job promotes them or rebuilds from source.

The publishing contract must make the identity verifiable **before** the merge. For example,
a pipeline may consume the pinned, tested PR-head commit or promote an immutable artifact
built from it. Inspect the workflow to prove that mapping; testing a PR head does not prove
a future merge/squash/rebase commit. A workflow that insists on a new, not-yet-known merge
SHA as its build source is unsupported until a non-publishing preparation/staging path is
configured. Report that limitation and stop; never merge first to learn what will publish.

At phase 9 the GO names that source commit, digests, PR head/base, merge method and the exact
publishing merge. Re-read the PR and base before acting and use the platform's expected-head
precondition where available. The repository must also enforce the approved base/preconditions
atomically (or the pipeline must consume only the pinned candidate, independently of base
changes). If the platform/workflow cannot enforce the required identity, stop as unsupported.
Any changed identity invalidates checks and GO; prepare and approve the new candidate first.

This rule also applies in the fix loop: accumulate fixes on the non-publishing candidate
branch. If the project has no way to stage and test those fixes without distribution, stop
and ask for a workflow change, not broader ordinary merge approval.

## Candidate changes and observed artifacts

`run_record.py candidate` and candidate `digest` updates supersede old evidence, clear the
terminal verdict/timestamp and revoke approvals. Digests must be recorded before the gate
results and approval that cover them. Repeating the same identity is a no-op. Approvals
bind to the full candidate (version, commit and digests); `superseded` preserves prior results.
A registry observation belongs in `digest --published`; it cannot retroactively approve a
rebuild or rewrite what the pre-publication gate tested.

## Fresh versions

Pre-publication work uses the existing baseline and candidate SHA, never a future final tag
or a not-yet-published artifact. Notes and credits use `<last-tag>..<candidate-sha>`; for the
repository's first release, use the candidate's full reachable history. Manual bucket C
checks run on the prepared candidate. Registry installation, fresh pulls and release-page
verification run only in phase 11, after their objects exist.
