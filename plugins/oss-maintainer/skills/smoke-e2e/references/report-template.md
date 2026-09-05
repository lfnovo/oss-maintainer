# Report template

Written to `[smoke].report_path`, updated as the run proceeds.

```markdown
# Smoke report — <date> — <repository> — candidate <commit or tag>

## Health
| check | status | evidence |
|---|---|---|
| api responds | not-run | |
| frontend responds | not-run | |

## Phase 1: API
| step | status | evidence |
|---|---|---|
| create notebook | not-run | |
| … | | |

## Phase 2: UI
| check | status | evidence |
|---|---|---|
| notebooks page lists the test notebook | not-run | |

## Cleanup
| item | status | evidence |
|---|---|---|

## Verdict

**GO** | **NO-GO**

- mandatory surfaces: api, ui
- decided by: <checks that are not passed on mandatory surfaces, or "all mandatory checks passed">
- skipped optional checks: <name — reason>
- observations: <non-blocking notes>
```

Statuses: `passed`, `failed`, `not-run`, `not-applicable`. Evidence is a path under
`.maintainer/state/` or an inline value short enough to read.
