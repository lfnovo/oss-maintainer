#!/usr/bin/env bash
# Seeds the eval workspace with the app-docker fixture as a git repository.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -R "$here/../../fixtures/app-docker/." .
git init -q -b main
git -c user.name=fixture -c user.email=fixture@example.com add -A
git -c user.name=fixture -c user.email=fixture@example.com commit -q -m "fixture"

