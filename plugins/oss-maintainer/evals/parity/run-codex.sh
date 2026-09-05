#!/usr/bin/env bash
# Runs the parity scenarios in Codex non-interactively when `codex exec` can load the plugin.
# Usage: evals/parity/run-codex.sh [fixture-name]   (default: all)
# Each scenario prints the transcript tail; fill evals/parity/checklist.md by hand from it.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fixtures="$here/../fixtures"
work="${TMPDIR:-/tmp}/oss-maintainer-parity"
rm -rf "$work"; mkdir -p "$work"

if ! command -v codex >/dev/null 2>&1; then
  echo "codex CLI not found: every Codex cell is not-run" >&2
  exit 3
fi
if ! codex plugin list 2>&1 | grep -E "oss-maintainer@oss-maintainer" | grep -qi "installed"; then
  echo "oss-maintainer is not installed in Codex: every Codex cell is not-run" >&2
  exit 3
fi

run() {
  local fixture="$1" prompt="$2" dir="$work/$1-$RANDOM"
  cp -R "$fixtures/$fixture/." "$dir"
  ( cd "$dir" && git init -q -b main && git -c user.name=f -c user.email=f@e add -A && git -c user.name=f -c user.email=f@e commit -q -m fixture )
  echo "=== $fixture: $prompt"
  ( cd "$dir" && codex exec --skip-git-repo-check "$prompt" 2>&1 | tail -40 ) || echo "(codex exec exited with $?)"
}

selected="${1:-all}"
[[ "$selected" == all || "$selected" == no-profile ]] && run no-profile '$init Check this repository and report readiness per capability. Do not write anything.'
[[ "$selected" == all || "$selected" == pypi-library ]] && run pypi-library '$release Prepare release 2.4.0: detect the distribution trigger, run phases 0 to 2 in read-only mode, and stop. Do not create or push a tag.'
[[ "$selected" == all || "$selected" == overlay-override ]] && run overlay-override '$init Show the effective profile and what the local overlay changed or tried to change. Do not modify files.'
[[ "$selected" == all || "$selected" == app-docker ]] && run app-docker '$smoke-e2e No instance is running and no browser is available: report every check with the right status and the verdict.'
echo "Fill $here/checklist.md from the transcripts above."
