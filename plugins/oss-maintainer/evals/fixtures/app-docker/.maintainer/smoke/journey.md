# Smoke journey

## Phase 1: API

### Step: create notebook
request: POST /api/notebooks {"name": "Smoke"}
expect: 200, body.id present
save: notebook_id

## UI
- /notebooks lists "Smoke"
