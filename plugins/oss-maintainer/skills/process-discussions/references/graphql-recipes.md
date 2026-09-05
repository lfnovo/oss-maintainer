# GraphQL recipes — Discussions

The CLI's Discussions support is partial; use the GraphQL API through `gh api graphql`.
`<owner>`, `<name>` and the category ids come from `[project].repo` and
`[discussions].categories`.

## Category ids (regenerate when a category is recreated)

```bash
gh api graphql -f query='{ repository(owner: "<owner>", name: "<name>") {
  id discussionCategories(first: 20) { nodes { id name } } } }'
```

## Complete queue and thread reads

Use the bundled reader (paths relative to the skill directory):

```bash
python3 scripts/read_discussions.py queue --repo <owner>/<name> --category '<category id>'
python3 scripts/read_discussions.py thread --repo <owner>/<name> --number <n>
```

The reader follows every category page before filtering closed threads, and paginates
comments and each reply connection independently. JSON includes `complete: true` only when
all requested pages were read. A rate limit, request failure or invalid cursor exits 1 with
`complete: false`, the error and any partial context collected. Report the interruption and
resume the read before making a final decision; partial output is not an empty queue or a
complete thread. Read every configured category to complete the queue map.

The query shapes and cursor handling are in `scripts/read_discussions.py`; the API contract
is [GitHub GraphQL pagination](https://docs.github.com/en/graphql/guides/using-pagination-in-the-graphql-api).

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
gh search issues "<terms>" --repo <owner>/<name> --include-prs   # precedents
```

Order matters when linking: create the Issues first, then post the reply with real links.

For `gh search issues`, omit `--state` to search both open and closed items. Unlike
`gh issue list` and `gh pr list`, the search subcommand accepts only `open` or `closed`.
