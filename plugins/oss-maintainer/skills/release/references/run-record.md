# Run record and resumption

`scripts/run_record.py` keeps one JSON record per release under `.maintainer/state/runs/`
and renders it as a one-page Markdown summary. The record is written as the work happens; it
never has to be satisfied before the work continues. Four commands cover a whole release.

## Create it when the version is decided

```bash
python3 scripts/run_record.py new --root <root> --version 1.4.0 --commit <sha> \
    --trigger 'make tag' --repo owner/name --python "$(command -v python3.12)"
```

`new` seeds the delivery contract: `validator` and every `[release.gates].mandatory` check as
mandatory pre-publication checks, `publish` and `verify` as mandatory post-publication checks,
`announce` and `cleanup` as optional, `[release.gates].not_gates` as optional signals. Add
project-specific obligations with `--mandatory NAME[:post]`. A mandatory check blocks the GO
(stage `pre`) or delivery (stage `post`) until it is `passed` with evidence or waived by a
recorded decision; an optional check never blocks.

## Write things down as they happen

```bash
# a selected probe, added from the coverage table before it runs
python3 scripts/run_record.py set <record> --check live-llm=not-run --mandatory \
    --probe 'make test-live PROVIDER=a' --expect 'a summary is generated for the fixture'
# a result, with its evidence (a log, a CI run, a report)
python3 scripts/run_record.py set <record> --check validator=passed:reports/tests.log
# an artifact identity and the check that tested those bytes, atomically
python3 scripts/run_record.py set <record> --digest wheel=sha256:<tested> \
    --check package-gate=passed:reports/wheel.log --on artifact:wheel
# a decision or observation in plain language
python3 scripts/run_record.py set <record> --note 'provider B has no credentials: unverified this release'
# an approval, in the maintainer's words
python3 scripts/run_record.py set <record> --approve tests \
    --scope 'run the live suite for providers A and C' --conditions 'at most 5 USD'
# the GO
python3 scripts/run_record.py set <record> --approve publication \
    --scope 'publish 1.4.0 at <sha> with make tag'
```

Several of those flags combine in one call. Checks default to source evidence (bound to the
candidate commit); `--on artifact:NAME` binds a check to the recorded digest of that artifact
instead. A check recorded again supersedes the previous result, which stays in the event
history.

Only publication approval binds mechanically: to commit, version, trigger and tested digests.
Every other approval is text the agent applies with judgement, and it survives candidate
changes; escalate when its written conditions no longer hold. No approval requires counting
executions or reserving units. The maintainer's numeric limits, when given, go in
`--conditions` and are respected as written.

## Candidate changes and reuse

```bash
python3 scripts/run_record.py set <record> --commit <new-sha>        # resets dependent checks
python3 scripts/run_record.py set <record> --check live-llm=passed \
    --reuse-from <check-id> --reason 'runtime, tests, pyproject and lockfile identical; docs and workflow only'
```

Changing the commit clears the tested digests and resets every check bound to the old source;
changing a digest resets the checks bound to that artifact; either revokes the publication
approval. Reuse records a new entry pointing to the original check, its evidence and its
timestamp, with the rationale; it never rewrites the original execution. If the relevant
dependencies did change, rerun the check.

A waiver records a maintainer decision next to the original result, which is preserved and
reported as a limitation:

```bash
python3 scripts/run_record.py set <record> --waive lint --reason 'pre-existing findings, tracked in #12' --by owner
```

## Resume and close

```bash
python3 scripts/run_record.py show --root <root>          # latest record, Markdown
python3 scripts/run_record.py show <record> --json        # raw, with the outstanding items
python3 scripts/run_record.py set <record> --published wheel=sha256:<observed>
python3 scripts/run_record.py finish <record> --verdict GO
```

On resumption read `show` and the external systems first; reconcile what is published, which
registries serve it and what remains unverified. `show` lists what blocks the GO and what
blocks delivery; `finish --verdict GO` refuses with the same items. A profile change since
the record started is flagged in `show` and invalidates the publication approval only.

`finish --verdict GO` means delivery completed: every mandatory check passed or waived, and a
publication approval covered this candidate. `NO-GO` ends a blocked attempt; `aborted`
records cancellation. Retrospective notes after completion do not reopen delivery; a new
post-publication observation (a failed registry check) does.

Records of schema 1 and 2 are read without rewriting the file; their phases stay as history
and their checks and approvals are mapped conservatively. The first `set` upgrades the file
and records that it did.
