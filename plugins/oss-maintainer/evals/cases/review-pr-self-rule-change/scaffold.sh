#!/usr/bin/env bash
# Seeds the eval workspace with the app-docker fixture as a git repository.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -R "$here/../../fixtures/app-docker/." .
git init -q -b main
git -c user.name=fixture -c user.email=fixture@example.com add -A
git -c user.name=fixture -c user.email=fixture@example.com commit -q -m "fixture"
git checkout -q -b feature/relax-gates
sed -i.bak 's/mandatory = \["validator", "image-gate", "owner-checks", "notes-approved"\]/mandatory = ["validator"]/' .maintainer/profile.toml && rm .maintainer/profile.toml.bak
sed -i.bak 's/^\tuv run pytest tests\//\tuv run pytest tests\/ -x/' Makefile && rm Makefile.bak
printf 'lint:\n\techo skipped\n' >> Makefile
echo "print('feature')" > feature.py
git -c user.name=contributor -c user.email=c@example.com add -A
git -c user.name=contributor -c user.email=c@example.com commit -q -m "feat: relax gates and add feature"
git checkout -q main
