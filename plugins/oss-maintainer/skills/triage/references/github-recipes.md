# GitHub recipes — triage

`gh` must be authenticated (`gh auth status`). Label names come from `[labels]` in the profile.

## Labels for the assignable states

```bash
gh label list --limit 200 --json name --jq '.[].name'
gh label create <ready label> --description "Fully specified; a developer can pick it up" --color "0E8A16"
gh label create <needs-design label> --description "Needs design or specification work before implementation" --color "FBCA04"
```

Creation that fails because the label exists: ignore and continue.

## The queue

```bash
gh issue list --state open --limit 200 --json number,title,labels,createdAt \
  --jq 'sort_by(.createdAt) | .[] | {number, title, labels: [.labels[].name]}'
```

Needs triage: no pipeline-state label, or the intake label.

## Read an issue with full context

```bash
gh issue view <n> --comments
gh pr list --search "linked:<n>" --state all --json number,title,state
```

Capture title, body, labels, comments, linked PRs, referenced issues, assignee.

## Apply a state

```bash
gh issue edit <n> --add-label "<new state>" --remove-label "<previous state>"
```

`gh` fails when removing a label the issue does not carry: include `--remove-label` only for
labels seen in the read. Always remove the intake label in the same edit.

## Close with an open door

```bash
gh issue close <n> --comment "<reason; canonical link for duplicates or superseded; 'reopen if X changes'>"
```

## Rewrite (promotion to ready with a full specification)

```bash
gh issue edit <n> --title "<new title>" --body-file <drafted body> --add-label "<ready label>" --remove-label "<previous state>"
```

Write bodies to a scratch file first; avoid shell escaping in `--body`.
