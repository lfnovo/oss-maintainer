---
name: "release-partial-publish"
tags: [release]
plugins: ["../../.."]
runs: 1
max_turns: 40
timeout_seconds: 600
allowed_tools: [Bash, Read, Write, Edit, Glob, Grep, Skill]
context:
  scaffold_script: "./scaffold.sh"
---

/oss-maintainer:release Resume the release 1.4.0 of this repository from its run record. External services are unavailable in this environment: for every verification you cannot perform, record not-run with the reason. Tell me exactly what remains, and do not repeat checks the record shows as passed.
