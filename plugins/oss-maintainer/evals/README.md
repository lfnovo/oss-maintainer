# Evals

Scenario material for the `oss-maintainer` plugin.

- `fixtures/`: small fake repositories (no `.git`; tests copy them to a temp dir and run
  `git init` when a scenario needs a repository). Shared by the deterministic tests under
  the repository root `tests/` and by the eval cases.
- `cases/<case>/case.yaml`: `claude plugin eval` cases. Each case seeds a fixture through its
  `scaffold.sh` and grades the transcript (see `README` in each case). Run from the repository
  root:

  ```bash
  claude plugin eval plugins/oss-maintainer --scaffold \
    --allow-tools 'Bash(git *)' 'Bash(python3 *)' --runs 2 --threshold 0.8 \
    --max-cost-usd 5 --no-publish
  ```

  The command is early access; when unavailable, record `not-run` and rely on the
  deterministic tests plus the manual dry runs in `parity/checklist.md`.
- `parity/`: the Codex parity checklist and its runner.
- `results/`: gitignored output of eval runs.

No case ever calls the live GitHub API: fixtures use local bare repositories, or the step is
recorded as `not-run`.

## Status of the eval layers (2026-09-05)

- `claude plugin eval`: early access, not enabled on the maintainer's account; every case is `not-run`. The cases are kept current so they run as soon as the feature is available.
- Deterministic tests (`tests/`): the merge gate.
- Codex parity: run `parity/run-codex.sh`; results in `parity/checklist.md`.

## 0.1.1 regression coverage

The new `release-merge-publish-trigger`, `release-docker-rc-authorization` and
`release-fresh-version-pre-go` cases cover #2, #3 and #11. Their scaffolds were executed
locally. Native `claude plugin eval` remains early-access/unavailable; direct Claude CLI
attempts on 2026-09-05 returned the account session limit (HTTP 429) before inference, so
these behavioral runs are **not-run**, not passed. The deterministic tests execute the
candidate-SHA credit recipe without a future tag and cover validator failures, candidate
invalidation, independent GraphQL pagination and isolated wheel/index import recipes.

## 0.2.0 validation

See [parity/0.2.0.md](parity/0.2.0.md) for the direct CLI scenarios, deterministic coverage
and explicitly unverified dimensions. New cases cover scoped agreements, evidence continuity
and optional instruction migration.

## 0.3.0 validation

See [parity/0.3.0.md](parity/0.3.0.md). The release cases follow the six steps and the four
record commands; `release-partial-publish` keeps its schema-1 seed on purpose as the
legacy-read scenario. The acceptance the issue asks for, a normal release and a release with
one late documentation change conducted with the simplified guidance, happens on the next real
release of a downstream repository and is recorded there.
