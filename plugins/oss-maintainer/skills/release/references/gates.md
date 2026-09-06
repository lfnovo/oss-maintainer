# Gates and authorization

Follow `project-agreement.md`. Investigate, prepare and verify within the maintainer's
existing authorization. Prepare a concrete decision before requesting missing authority;
continue independent work. A denied action is not permission to route around it.

## Scope by action

| Kind | Binding and conditions | When another decision is needed |
|---|---|---|
| Merge | repository/run or explicitly limited session; qualifying PRs, required checks and review | stated conditions fail, scope/session expires, or integration can publish |
| Tests | selected plan, providers/resources, permitted executions and budget | plan/resources change, repeat exceeds count/cost, or permission expires |
| Notes | exact approved text and relevant factual context | text or relevant facts change |
| Publication | complete candidate identity and exact distribution action | commit, version, tested artifact identity or trigger changes |

Use `run_record.py authorize --kind ...` and record conditions, resources and stated limits.
Publication remains the default kind for compatibility. `permissions` reports mechanically
valid grants; it cannot judge natural-language conditions. Before using a grant, verify the
actual action, current project policy, resources and conditions. For bounded grants reserve
usage with `consume` before execution, choosing a documented unit (runs or budget units).
A failed attempt still consumes its reserved allowance; never silently refund a paid test.
Record arbitrary monetary limits in conditions as well as integer budget units when useful.
A grant with no numeric limit is not proof of unlimited paid use: apply its written scope.

`ask-once-per-session` retains its literal lifetime. For continuing work, the maintainer may
instead give an `ask-once-per-run` grant. Do not convert an old session approval into a run
approval. Legacy untyped grants remain candidate-bound and cannot prove merge/test authority.
The harness may independently require permission; the plugin cannot suppress those prompts.

## Work that can proceed

Within the authorized scope, run local tests/builds, prepare changes through the agreed
contribution process, inspect CI and write local evidence. Paid services, owner data and
external messages need the actual scope authorized. A general request to investigate or run
local tests is not permission to spend money or speak for the project. Reviewed batches can
be approved together where project policy allows them.

## Re-test policy

Run the canonical validator after fixes. Run other mandatory checks as required by the
project, and selected additional probes when their dependencies change. Source checks bind
to a commit; artifact checks bind to identified bytes. Adding artifact metadata does not
invalidate unrelated source checks. A changed source commit invalidates source evidence;
rebuilding bytes invalidates evidence for the old artifact. The final artifact gate covers
the exact candidate. Missing dependency information requires conservative revalidation.

## Publication GO

GO requires every mandatory pre-publication check passed with evidence, required manual work
signed off, no open release regression, and alerts resolved or accepted under project policy.
A required unrun check remains NO-GO. Risk acceptance records a decision, never a fabricated
pass. A local preference cannot waive shared requirements.

GO precedes the first action that can distribute, including a publishing merge or direct
push. Separately authorized RC staging uses an immutable prerelease reference, not the final
version or a rolling channel. Source tests do not substitute for the artifact gate. Never
reuse a published version or promote a channel without its scoped authorization.

Post-publication registry checks are required delivery work, not prerequisites to the
publication they verify. Completion is separate from GO and from optional retrospective work;
follow `run-record.md`. Creating feedback issues requires authorization of the actual text.
