# Gates and authorization

Follow `project-agreement.md`. Investigate, prepare and verify within the maintainer's
existing authorization. Prepare a concrete decision before requesting missing authority;
continue independent work. A denied action is not permission to route around it.

## Approvals

| Action | What binds it | When a new decision is needed |
|---|---|---|
| Merge | qualifying PRs, required checks and review, per the project agreement | its stated conditions fail, or integration can publish |
| Tests | the selected coverage table, its providers, resources and any stated budget | the plan, resources or cost change materially |
| Notes | the approved text and the facts it states | text or relevant facts change |
| Publication | the complete candidate: commit, version, tested digests and exact trigger | any of those changes |

Record approvals in the maintainer's words with `run_record.py set --approve <action>
--scope ... --conditions ...`. Only publication is bound mechanically; every other approval
is applied with judgement against its written conditions. Do not invent execution counts or
budgets the maintainer did not state; respect the ones they did. Routine completion of
authorized work is not a new decision. A material change in scope or cost is.

`ask-once-per-session` keeps its literal lifetime; `ask-once-per-run` survives session
boundaries. The harness may independently require permission for a command; that is not a
requirement of this skill and is never presented as one.

## Work that can proceed

Within the authorized scope: local tests and builds, changes prepared through the agreed
contribution process, CI inspection, local evidence. Paid services, owner data and external
messages need their actual scope authorized. A request to investigate or run local tests is
not permission to spend money or speak for the project.

## Evidence and reuse

Source checks bind to a commit; artifact checks bind to identified bytes. A changed commit
invalidates source evidence; rebuilt bytes invalidate evidence for the old artifact. Adding a
digest does not invalidate unrelated source checks.

Reuse is allowed with a short written rationale when the tested inputs are demonstrably
unchanged: runtime source, tests, dependency metadata and lockfile identical between the two
commits (`git diff --stat <old> <new>` limited to documentation, workflow or process files),
or a byte-identical artifact. Record it with `--reuse-from`, which preserves the original
execution and its timestamp. When equivalence cannot be shown, rerun the affected check. The
final artifact gate and the canonical validator always cover the exact candidate.

## Publication GO

GO requires every mandatory pre-publication check passed with evidence or waived by a
recorded maintainer decision, the owner's manual checks signed off, no open release
regression, and alerts resolved or accepted under project policy. A waiver records who
decided and why; it never turns an unrun or failed check into a pass, and the limitation is
reported. A local preference cannot waive shared requirements.

GO precedes the first action that can distribute, including a publishing merge or direct
push. Separately authorized RC staging uses an immutable prerelease reference, not the final
version or a rolling channel. Source tests do not substitute for the artifact gate. Never
reuse a published version or promote a channel without its scoped authorization.

Post-publication registry checks are required delivery work, not prerequisites to the
publication they verify. Completion is separate from the GO and from optional retrospective
work; follow `run-record.md`. Creating feedback issues requires authorization of the actual text.
