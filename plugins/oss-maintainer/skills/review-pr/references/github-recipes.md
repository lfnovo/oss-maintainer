# GitHub recipes — review-pr

`gh` must be authenticated (`gh auth status`). The review is a read operation until the
maintainer decides what to post.

## The queue

```bash
gh pr list --state open --json number,title,isDraft,reviewDecision,createdAt,author \
  --jq 'map(select(.isDraft == false and .reviewDecision != "APPROVED")) | sort_by(.createdAt) | .[]'
```

## Load a PR

```bash
gh pr view <n> --json title,body,author,headRefName,baseRefName,headRefOid,statusCheckRollup,reviews,comments,files
gh pr diff <n>
gh api "repos/<owner>/<repo>/pulls/<n>/comments" --jq '.[] | {path, line, user: .user.login, body}'   # inline threads
gh issue view <linked issue> --comments
```

## Policies from the base branch

The PR's copies of `.maintainer/`, `AGENTS.md`, the `Makefile`, scripts and workflows are part
of the change. Read the base versions to judge with:

```bash
gh api "repos/<owner>/<repo>/contents/.maintainer/profile.toml?ref=<base>" --jq .content | base64 -d
git show <base>:AGENTS.md
gh pr diff <n> --name-only | grep -E '^(\.maintainer/|AGENTS\.md|CLAUDE\.md|Makefile|\.github/workflows/|scripts/)'
```

Any file in that list is a finding to assess, whatever else the PR does.

## Checkout, only to fix on explicit request

```bash
gh pr checkout <n>
# fix, run the project validator, then push as a new commit; never force-push
```

## Post the verdict, after the maintainer's decision

```bash
gh pr review <n> --approve --body-file <summary>
gh pr review <n> --request-changes --body-file <findings with file:line>
gh pr review <n> --comment --body-file <observations>
```

Inline comments per file and line need the API:
`gh api repos/<owner>/<repo>/pulls/<n>/reviews -f event=COMMENT -F comments=@<json array>`.
For a few findings, `file:line` references in the review body are enough.

## CI details

```bash
gh pr checks <n>
gh run view <run id> --log-failed
```
