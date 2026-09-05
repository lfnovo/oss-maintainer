#!/usr/bin/env bash
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -R "$here/../../fixtures/app-docker/." .
git init -q -b main
git add -A
git -c user.name=fixture -c user.email=fixture@example.com commit -q -m "baseline"
git tag v1.0.0
git remote add origin https://example.invalid/example/project.git
python3 - <<'PYCODE'
from pathlib import Path
p = Path('.maintainer/profile.toml')
p.write_text(p.read_text().replace('distribution_trigger = "gh release create"', 'distribution_trigger = "merge to main"'))
Path('.github/workflows/build-and-release.yml').write_text('on:\n  push:\n    branches: [main]\njobs:\n  publish:\n    steps:\n      - uses: actions/checkout@v4\n      - run: docker build -t example/image:1.0.1 . && docker push example/image:1.0.1\n')
PYCODE
git add -A
git -c user.name=fixture -c user.email=fixture@example.com commit -q --allow-empty -m "candidate"
