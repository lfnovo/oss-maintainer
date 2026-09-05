# Profile contract — `smoke-e2e`

| Field | Use | Without it |
|---|---|---|
| `[smoke].api_url` | base URL of the API | capability not applicable when the whole table is absent |
| `[smoke].frontend_url` | base URL of the UI | UI checks not applicable |
| `[smoke].journey` | the journey file | `.maintainer/smoke/journey.md`; missing file: stop |
| `[smoke].mandatory_surfaces` | which surfaces decide the verdict | `["api"]` |
| `[smoke].report_path` | where the report is written | `.maintainer/state/smoke-report.md` |
| `[smoke].poll_interval`, `[smoke].step_timeout` | polling | `5s`, `5m` |

The local overlay may change `api_url` and `frontend_url`; it cannot change the mandatory
surfaces or the journey.
