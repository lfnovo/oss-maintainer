# Journey format — `.maintainer/smoke/journey.md`

A journey is a Markdown file the `smoke-e2e` skill executes. It belongs to the repository:
endpoints, payload conventions, fixtures, pages and quirks are the product's, not the engine's.

```markdown
# Smoke journey

## Conventions
- Base URL for API calls: <api_url>/api ; JSON unless a step says multipart.
- Ids look like `notebook:xxxx`.

## Health
- GET <api_url>/docs → 200
- GET <frontend_url> → 200
- GET <api_url>/api/models/defaults → a default chat model is configured

## Phase 1: API

### Step: create notebook
request: POST /api/notebooks {"name": "Smoke Test", "description": "safe to delete"}
expect: 200; body.id present
save: notebook_id

### Step: add text source
request: POST /api/sources (multipart) type=text, notebooks=["<notebook_id>"], content="…", async_processing=true
expect: 200; body.id present
save: source_id

### Step: wait for processing
request: GET /api/sources/<source_id>/status
expect: status == completed
timeout: 5m

## Phase 2: UI
- <frontend_url>/notebooks lists "Smoke Test"
- <frontend_url>/notebooks/<notebook_id> shows the source; console has no errors

## Cleanup
- DELETE /api/notebooks/<notebook_id>?delete_exclusive_sources=true → 200; GET returns 404 afterwards

## Quirks
- Processing can take minutes after heavy operations; the dev server may slow down.
- The retry endpoint is known to fail with X; use Y instead.
```

Rules:

- `request`, `expect`, `save` and `timeout` are the step fields; `timeout` defaults to
  `[smoke].step_timeout`.
- `expect` is a checkable statement: a status code, a field present, a value, a count.
- Values saved by earlier steps are referenced as `<name>`.
- UI lines are page URL plus what must be visible or must not appear.
- Phases may be skipped by the caller ("API only"); mandatory surfaces still decide the
  verdict.
- Fixtures the journey needs (a PDF, an image) live in the repository at a path the journey
  names; when absent, the step is `not-run` with that reason.
