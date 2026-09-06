# Run record and resumption

Use `scripts/run_record.py` to keep JSON records under `.maintainer/state/runs/`. Record
schema 2 separates evidence dependencies, action permissions, delivery and retrospective
state. Profile schema remains 1. Reading schema-1 records does not write them; the next
mutation adds the new fields while preserving historical values and `legacy_schema: 1`.
Unknown schemas are rejected. An old GO is not inferred to prove completed delivery.

## Start with the delivery contract

`new` defaults release obligations to publish, verify, announcement disposition and cleanup.
Add all project mandatory checks with repeated `--required-check`; add extra delivery phases
with `--required-phase`. For non-release runs explicitly name their required phases. Required
checks must pass with evidence. Optional checks remain visible without blocking completion.

```bash
python3 scripts/run_record.py new --root <root> --skill release --version 1.4.0 --commit <sha> \
    --repo owner/name --required-check validator --required-check package-gate
```

The profile hash records the shared profile and overlay bytes conservatively. On resumption,
compare the profile hash and read the linked policies before relying on prior decisions. A
changed policy requires a new run/agreement; keep the old record and externally confirmed
publication history. A new record never authorizes repeating successful distribution.

## Evidence and commands

Every check has an ID, status, evidence reference, dependency snapshot and linked execution
IDs. Choose `--depends-on source`, `--depends-on artifact:NAME`, or `candidate` (the conservative
default). Repeat dependencies when the result depends on more than one. A missing artifact
identity is rejected. Register identity and gate result atomically:

```bash
python3 scripts/run_record.py update <record> --phase bucket-a --status passed \
    --depends-on source --check validator=passed:reports/tests.log \
    --command 'make test=0' --cwd . --log reports/tests.log
python3 scripts/run_record.py update <record> --phase artifact-gate --status passed \
    --digest wheel=sha256:<tested> --depends-on artifact:wheel \
    --check package-gate=passed:reports/wheel.log --command 'make package-check=0'
```

`--command 'COMMAND=INTEGER_EXIT_STATUS'` splits at the last equals sign, so commands may
contain equals signs. Repeat the option to record multiple executions. Invalid entries fail
before any record is saved. Supply `--executed-at <ISO timestamp with timezone>` only when the
actual execution time is known; otherwise it stays null. `at`/`recorded_at` are recording
times, not proof of when an old command ran. Execution IDs and original records are preserved.

Use `revalidate <record> --phase <phase> --evidence-id <id> --reason <reason>` for a later
observation that an existing result still applies. It adds an event without manufacturing a
new execution or editing its timestamp. It refuses changed dependencies. Re-run affected
checks instead; replaced checks remain in the event history.

`candidate --commit <sha> [--version V]` invalidates affected dependencies; changing source
identity clears the old candidate's digests. `digest --name NAME --value DIGEST` enriches or
replaces tested identity. Same-identity updates do nothing. `digest --published` records a
registry observation separately. Never bind an artifact check to bytes it did not test.

## Authorizations

```bash
python3 scripts/run_record.py authorize <record> --kind tests --phase matrix \
    --scope 'execute the reviewed plan once' --conditions 'provider A; maximum 2 USD' \
    --resource provider-a --limit 1
python3 scripts/run_record.py authorize <record> --kind merge --phase fix-loop \
    --scope 'merge qualifying fixes during this run' --conditions 'required CI and independent review passed'
python3 scripts/run_record.py authorize <record> --kind notes --phase notes \
    --scope 'approved notes' --subject sha256:<text-and-facts> --conditions 'exact text and facts unchanged'
python3 scripts/run_record.py authorize <record> --kind publication --candidate <sha> \
    --scope 'publish this candidate via make tag'
python3 scripts/run_record.py permissions <record>
python3 scripts/run_record.py consume <record> --authorization <id> --units 1 --reason 'reserve reviewed test execution'
```

Optional `--expires-at` and numeric `--limit` bound validity. Verify written conditions and
actual resources before consuming. Merge/test grants survive unrelated candidate changes
within the same agreement. Notes bind to approved text and source/version context; publication
binds to complete identity. Legacy grants retain conservative full-candidate semantics.
Publication authority never follows from ordinary merge or test permission.

## Resume and close

Read `latest --root <root> --skill release --version V` and external systems first. Reconcile
what is published, which registries serve it and what remains unverified. Report missing
bookkeeping separately from missing execution. `pending` lists outstanding phases/checks;
optional retrospective work may remain pending after delivery is completed.

Record each required phase with checks and evidence. `publish` and `verify` must pass;
`announce` and `cleanup` may be not-applicable only with a recorded reason as evidence (for
example, no channels requested or no resources created). Never silently skip required work.

```bash
python3 scripts/run_record.py update <record> --phase announce --status not-applicable \
    --check disposition=not-applicable:'owner requested no announcement'
python3 scripts/run_record.py finish <record> --verdict GO
```

`finish --verdict GO` means delivery completed, not permission to publish. It refuses missing
required obligations. `NO-GO` ends a blocked attempt; `aborted` records cancellation. Publish
approval is recorded with `authorize`. Complete delivery before the optional retro; retro
updates do not reopen publication. A completed run retains its delivery outcome while its
retrospective remains pending. Do not infer missing checks, execution times or approval from
old records; reconcile them with actual external evidence.
