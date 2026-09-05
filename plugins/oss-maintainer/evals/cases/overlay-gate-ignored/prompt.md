---
name: "overlay-gate-ignored"
tags: [init, smoke]
plugins: ["../../.."]
runs: 1
max_turns: 20
timeout_seconds: 600
allowed_tools: [Bash, Read, Glob, Grep, Skill]
context:
  scaffold_script: "./scaffold.sh"
---

/oss-maintainer:init Check this repository's maintainer profile and show me the effective profile, including what the local overlay changed and what it tried to change but could not. Do not modify any file.
