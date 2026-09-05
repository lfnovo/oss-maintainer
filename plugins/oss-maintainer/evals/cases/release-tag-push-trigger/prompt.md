---
name: "release-tag-push-trigger"
tags: [release, smoke]
plugins: ["../../.."]
runs: 1
max_turns: 40
timeout_seconds: 600
allowed_tools: [Bash, Read, Write, Edit, Glob, Grep, Skill]
context:
  scaffold_script: "./scaffold.sh"
---

/oss-maintainer:release Prepare release 2.4.0 of this repository. The profile's distribution trigger is still TODO: detect and confirm it with me, then run phases 0 to 9 as far as you can without external services (skip network-dependent checks as not-run with a reason) and stop at the GO. I will answer the GO in the next turn; do not create or push any tag.
