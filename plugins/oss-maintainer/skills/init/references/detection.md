# Detection rules

How `scripts/detect_repo.py` derives the archetype and the distribution trigger, and how to
read its output. Every value it prints is a proposal: the maintainer confirms it before it
becomes policy, so the profile receives it as `CONFIRM: <value>` until confirmed.

## Artifact archetype

Rules are tried in this order; the first match wins.

| Archetype | Evidence |
|---|---|
| `app-docker` | `Dockerfile` present, plus a workflow that pushes an image, or `docker-*` Makefile targets, or a compose file. When the repository also publishes to PyPI, the image wins because it is what users run. |
| `pypi-library` | `pyproject.toml` with a `[project]` table, plus a workflow or Makefile target that runs `uv publish`, `twine upload` or `pypa/gh-action-pypi-publish`. |
| `npm-package` | `package.json` with `publishConfig`, or a workflow running `npm publish`. Placeholder archetype in v1. |
| `custom` | none of the above, but `.maintainer/release/runbook.md` exists: the engine follows the runbook with the same gates and vocabulary. |
| `pypi-library` (low confidence) | `pyproject.toml` with `[project]` and no publishing mechanism found. |
| `unknown` | nothing found. `release` stays incomplete until the maintainer sets the archetype. |

## Distribution trigger

The distribution trigger is the first action that can start public distribution, directly or
through a workflow. The `release` skill runs it only after the GO. Detection order:

1. A release tool configuration (`release-please-config.json`, `.releaserc*`, `.changeset/`)
   means distribution starts when its release PR merges. Always requires confirmation; the
   engine cannot see that PR's semantics.
2. A publishing workflow triggered on `push: tags` becomes the trigger. When a Makefile target
   both creates and pushes the tag, the trigger is `make <target>` and the evidence quotes the
   line; otherwise it is the manual `git push origin v<version>`.
3. A publishing workflow triggered on `release` means `gh release create`.
4. A publishing workflow with only `workflow_dispatch` means `gh workflow run <file>`.
5. A publishing workflow on `push` to a branch means merging to that branch publishes.
6. A Makefile target that publishes directly (`docker push`, `uv publish`, `npm publish`).
7. A Makefile target that pushes a tag without any workflow listening (low confidence).

A workflow "publishes" when its body contains a publishing step: `uv publish`,
`twine upload`, `pypa/gh-action-pypi-publish`, `npm publish`, `docker push`,
`docker/build-push-action`, `cargo publish`, `gh release create`, `goreleaser`.

## Other fields

- `version_files`: `pyproject.toml`, `package.json`, `Cargo.toml` and plugin manifests that
  carry a `version`. All must move together in a cut.
- `changelog`: `CHANGELOG.md`, `CHANGES.md` or `HISTORY.md`.
- `commands_doc`: `AGENTS.md`, else `CLAUDE.md`.
- `contributing`: `CONTRIBUTING.md`, `.github/CONTRIBUTING.md` or `docs/**/contributing.md`.
- `process_doc`: `.github/RELEASE_PROCESS.md`, `RELEASING.md`, `RELEASE.md` or
  `docs/**/release*.md`.

## Reading the output

`confidence` is `high` when a publishing workflow with matching steps exists, `medium` when
only the Makefile or a compose file supports the conclusion, `low` otherwise. Low confidence
never becomes a profile value without an explicit answer from the maintainer.

The scanner is regex-based and reads workflow files without a YAML parser. Unusual layouts
(anchors, reusable workflows called with `uses:`) may hide a publishing step; when the output
disagrees with what the maintainer knows, the maintainer is right and the profile records the
truth.
