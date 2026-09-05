# Recipes — generic commands for the phases

Repository-specific commands live in `.maintainer/release/runbook.md`. These are the parts
that are the same everywhere, parameterised by the profile.

## Scope (phase 0)

```bash
git fetch --tags --quiet
last=$(git tag --sort=-creatordate | grep -E '^v?[0-9]' | head -1)      # or --sort=-v:refname
git log "$last"..origin/<default-branch> --oneline
gh release list --limit 5
gh api "repos/<owner>/<repo>/dependabot/alerts?state=open" --jq 'map({severity: .security_advisory.severity, package: .dependency.package.name})'
```

## Changelog heading (phase 7)

Turn `## [Unreleased]` into `## [X.Y.Z] - YYYY-MM-DD` and open a fresh `## [Unreleased]`
above it. Keep the project's heading style (Keep a Changelog sections, bare `(#NN)`
references). If the repository resolves changelog conflicts with a `merge=union` attribute,
check the attribute is still there after a rebase.

## Version files (phase 7)

Bump every path in `[release].version_files` to the same string and verify:

```bash
grep -n '"version"\|^version' <each version file>
```

For plugin manifests that must equal the package version, edit them in place; never
round-trip JSON through a formatter that reorders keys.

## Watch a workflow (phases 10 and 11)

```bash
gh run list --workflow=<file> --limit 1 --json databaseId,status,conclusion
gh run watch <run-id> --exit-status
```

## Label shipped issues (phase 12, after the owner's OK)

Changelog references mix issue and PR numbers; label only actual closed issues:

```bash
for n in <numbers>; do
  state=$(gh api "repos/<owner>/<repo>/issues/$n" --jq 'if .pull_request then "pr" else .state end')
  [ "$state" = "closed" ] && gh issue edit "$n" --add-label "<released label>"
done
```

## Post-publish retry (phase 11)

Registries and indexes propagate with a lag of a minute or so. Retry a verification three
times with a short wait before calling it `failed`; record the attempt count as evidence.

## Working tree after suites (phases 3 and 13)

```bash
git status --short          # must be empty; suites that write next to fixtures leave traces
```

## Digests (phases 4, 7 and 11)

```bash
sha256sum dist/*                                                   # packages
docker manifest inspect <registry>/<image>:<tag> | jq -r '.manifests[].digest'   # images
```
