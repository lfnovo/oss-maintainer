# Profile contract — `review-pr`

Read-only mode is the normal mode: this skill needs no profile to review.

| Field | Use | Without it |
|---|---|---|
| `[review].docs` | documents the review judges against, when the defaults are not enough | found by function: agent docs, architecture and vision documents, contribution and testing guides |
| `[review].reviewers` | AI reviewers whose findings are looked for on the PR | any AI review present on the PR |
| `[contributing].conventions` | what a PR is expected to look like | `CONTRIBUTING.md`, else general judgement |
| `[comms]` | languages | interact in the user's language, publish in English |
| `[commands.validator]` | the validator to run when fixing on the PR branch | the project's documented commands |

Posting a review, fixing on the branch and replying to a reviewer are mutations: they always
wait for the maintainer's decision, profile or not.

`[review].batch_approval` is `one-at-a-time` by default; `allowed` permits approval of a
concrete reviewed set with every proposed text and effect visible.
