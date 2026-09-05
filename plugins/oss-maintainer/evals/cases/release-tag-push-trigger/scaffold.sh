#!/usr/bin/env bash
# Seeds the eval workspace with the pypi-library fixture as a git repository.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -R "$here/../../fixtures/pypi-library/." .
git init -q -b main
git -c user.name=fixture -c user.email=fixture@example.com add -A
git -c user.name=fixture -c user.email=fixture@example.com commit -q -m "fixture"
git remote add origin https://example.invalid/example/lib.git
