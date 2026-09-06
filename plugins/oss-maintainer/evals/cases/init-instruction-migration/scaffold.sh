#!/usr/bin/env bash
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -R "$here/../../fixtures/no-profile/." .
mkdir -p module
printf '%s\n' '# Root Claude rules' 'Run make test.' > CLAUDE.md
printf '%s\n' '# Module rules' 'Preserve module contracts.' > module/CLAUDE.md
git init -q -b main
git -c user.name=fixture -c user.email=fixture@example.com add -A
git -c user.name=fixture -c user.email=fixture@example.com commit -q -m fixture
