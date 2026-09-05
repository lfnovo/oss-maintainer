#!/usr/bin/env bash
# Seeds the eval workspace with the app-docker fixture as a git repository.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -R "$here/../../fixtures/app-docker/." .
git init -q -b main
git -c user.name=fixture -c user.email=fixture@example.com add -A
git -c user.name=fixture -c user.email=fixture@example.com commit -q -m "fixture"
mkdir -p .maintainer/state/runs
cat > .maintainer/state/runs/2026-01-01T00-00-00.000000Z-release.json <<'JSON'
{"schema": 1, "skill": "release", "id": "2026-01-01T00-00-00.000000Z-release", "started_at": "2026-01-01T00:00:00Z", "finished_at": null,
 "engine": {"plugin": "oss-maintainer", "version": "0.1.0", "resolution": "local"}, "repo": "example/app",
 "candidate": {"version": "1.4.0", "commit": "abc123", "digests": {"example/app:1.4.0": "sha256:aaaa"}},
 "profile_hash": null, "overlay_diff": [],
 "phases": [
   {"name": "scope", "status": "passed", "checks": [], "authorizations": []},
   {"name": "version", "status": "passed", "checks": [], "authorizations": []},
   {"name": "matrix", "status": "passed", "checks": [], "authorizations": []},
   {"name": "bucket-a", "status": "passed", "checks": [{"name": "validator", "status": "passed", "evidence": "reports/validator.log"}], "authorizations": []},
   {"name": "artifact-gate", "status": "passed", "checks": [{"name": "image-gate", "status": "passed", "evidence": "reports/gate.log"}], "authorizations": []},
   {"name": "bucket-c", "status": "passed", "checks": [], "authorizations": []},
   {"name": "cut", "status": "passed", "checks": [], "authorizations": []},
   {"name": "notes", "status": "passed", "checks": [{"name": "notes-approved", "status": "passed", "evidence": "notes.md"}], "authorizations": []},
   {"name": "go", "status": "passed", "checks": [], "authorizations": [{"scope": "publish via gh release create", "candidate": "abc123", "granted_at": "2026-01-01T01:00:00Z", "by": "owner"}]},
   {"name": "publish", "status": "failed", "checks": [{"name": "registry-a", "status": "passed", "evidence": "manifest digest sha256:aaaa"}, {"name": "registry-b", "status": "failed", "evidence": "push timeout"}], "authorizations": []}
 ],
 "commands": [], "items": [], "verdict": null, "notes": []}
JSON
