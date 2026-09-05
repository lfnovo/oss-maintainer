# GraphQL recipes — Discussions

The CLI's Discussions support is partial; use the GraphQL API through `gh api graphql`.
`<owner>`, `<name>` and the category ids come from `[project].repo` and
`[discussions].categories`.

## Category ids (regenerate when a category is recreated)

```bash
gh api graphql -f query='{ repository(owner: "<owner>", name: "<name>") {
  id discussionCategories(first: 20) { nodes { id name } } } }'
```

## Open threads in a category, oldest first

```bash
gh api graphql -f query='
{ repository(owner: "<owner>", name: "<name>") {
    discussions(first: 50, categoryId: "<category id>", orderBy: {field: CREATED_AT, direction: ASC}) {
      nodes { number title createdAt closed author { login } comments { totalCount } } } } }' \
  --jq '.data.repository.discussions.nodes[] | select(.closed == false) | "\(.number) | \(.createdAt[:10]) | \(.author.login) | comments:\(.comments.totalCount) | \(.title)"'
```

## One thread with every comment and reply

```bash
gh api graphql -f query='
{ repository(owner: "<owner>", name: "<name>") {
    discussion(number: <n>) { id title body author { login } createdAt closed
      comments(first: 100) { nodes { id body author { login } createdAt
        replies(first: 50) { nodes { body author { login } createdAt } } } } } } }'
```

## Post a comment (after approval)

```bash
gh api graphql -f query='mutation($id: ID!, $body: String!) {
  addDiscussionComment(input: {discussionId: $id, body: $body}) { comment { url } } }' \
  -f id="<discussion id>" -F body=@<scratch file>
```

## Rename or broaden a thread in place

```bash
gh api graphql -f query='mutation($id: ID!, $title: String!) {
  updateDiscussion(input: {discussionId: $id, title: $title}) { discussion { url } } }' \
  -f id="<discussion id>" -f title="<new title>"
```

## Close with a reason

```bash
gh api graphql -f query='mutation($id: ID!) {
  closeDiscussion(input: {discussionId: $id, reason: RESOLVED}) { discussion { url } } }' -f id="<discussion id>"
```

Reasons: `RESOLVED`, `OUTDATED`, `DUPLICATE`.

## Issues born from a thread

```bash
gh issue create --title "<title>" --label "<ready label>" --body-file <scratch file>
gh issue close <n> --comment "$(cat <scratch file>)"
gh search issues "<terms>" --repo <owner>/<name> --state all --include-prs   # precedents
```

Order matters when linking: create the Issues first, then post the reply with real links.
