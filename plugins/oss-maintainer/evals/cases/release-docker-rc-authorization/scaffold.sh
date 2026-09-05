#!/usr/bin/env bash
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -R "$here/../../fixtures/app-docker/." .
git init -q -b main
git add -A
git -c user.name=fixture -c user.email=fixture@example.com commit -q -m "baseline"
git tag v1.0.0
git remote add origin https://example.invalid/example/project.git
git add -A
git -c user.name=fixture -c user.email=fixture@example.com commit -q --allow-empty -m "candidate"
