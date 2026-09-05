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
  deterministic tests plus the manual dry runs described in `VISION.md` section 5.1.
- `parity/`: the Codex parity checklist and its runner.
- `results/`: gitignored output of eval runs.

No case ever calls the live GitHub API: fixtures use local bare repositories, or the step is
recorded as `not-run`.
