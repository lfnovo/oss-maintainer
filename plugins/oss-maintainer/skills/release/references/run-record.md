# Run record and resumption

Every run writes a JSON record under `.maintainer/state/runs/` (gitignored), created and
updated with `scripts/run_record.py`. The record is what makes a release resumable and
auditable: what was checked, on which candidate, with what evidence, under which
authorizations.

## Record

```json
{
  "schema": 1,
  "skill": "release",
  "id": "2026-09-05T14-02-11Z-release",
  "started_at": "2026-09-05T14:02:11Z",
  "finished_at": null,
  "engine": {"plugin": "oss-maintainer", "version": "0.1.0", "resolution": "marketplace ref oss-maintainer--v0.1.0"},
  "repo": "owner/name",
  "candidate": {"version": "1.4.0", "commit": "abc123", "digests": {"registry/image:1.4.0": "sha256:..."}},
  "profile_hash": "sha256 of the effective profile",
  "overlay_diff": ["smoke.api_url"],
  "phases": [
    {"name": "artifact-gate", "status": "passed", "checks": [
      {"name": "image-gate", "status": "passed", "evidence": ".maintainer/state/reports/image-gate.log"}
    ], "authorizations": []}
  ],
  "commands": [{"run": "make test", "cwd": ".", "exit": 0, "log": ".maintainer/state/reports/validator.log"}],
  "items": [],
  "verdict": null,
  "notes": []
}
```

Phase names, in order: `scope`, `version`, `matrix`, `bucket-a`, `artifact-gate`,
`bucket-c`, `fix-loop`, `cut`, `notes`, `go`, `publish`, `verify`, `announce`, `cleanup`,
`retro`. Check statuses: `passed`, `failed`, `not-run`, `not-applicable`. Verdicts: `GO`,
`NO-GO`, `aborted`.

An authorization is `{"scope": "publish via make tag", "candidate": "abc123", "granted_at": "...", "by": "owner"}`.
It is valid only while the candidate in the record equals the one it names.

## Commands

```bash
python3 scripts/run_record.py new --root <root> --skill release --version 1.4.0 --commit abc123
python3 scripts/run_record.py update <record> --phase artifact-gate --status passed \
    --check image-gate=passed:.maintainer/state/reports/image-gate.log
python3 scripts/run_record.py authorize <record> --scope "publish via make tag" --candidate abc123
python3 scripts/run_record.py candidate <record> --commit def456        # invalidates checks and authorizations
python3 scripts/run_record.py latest --root <root> --skill release [--version 1.4.0]
python3 scripts/run_record.py pending <record>                            # phases and checks not yet passed
python3 scripts/run_record.py finish <record> --verdict GO
```

## Resumption

1. `latest` for the same repository and version. No record: start at phase 0.
2. Read the external systems before trusting the record: does the tag exist on the remote, is
   the release published, which registries already serve the version, did the publish workflow
   finish. Each answer marks the corresponding check `passed` with the external evidence.
3. `pending` lists what remains. Continue from the first pending phase; repeat only what the
   re-test policy requires.
4. Publication across several registries is never assumed atomic. A run that published the
   package but failed the image resumes at the image, with the package verified and left alone.
5. A relevant change since the record (a new commit on the candidate, a rebuilt artifact, a
   changed profile policy) invalidates the affected checks and their authorizations:
   `candidate --commit <new>` resets them, and the GO is asked again.

Even a run that stops before phase 0 writes a record with `verdict: aborted` and the reason,
so the next session knows what happened.
