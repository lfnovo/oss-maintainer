---
name: "init-no-profile"
tags: [init, smoke]
plugins: ["../../.."]
runs: 1
max_turns: 40
timeout_seconds: 600
allowed_tools: [Bash, Read, Write, Edit, Glob, Grep, Skill]
context:
  scaffold_script: "./scaffold.sh"
---

/oss-maintainer:init Scaffold the maintainer profile for this repository. This is a disposable fixture: I pre-approve every file you propose under .maintainer/, the AGENTS.md pointer line and the .gitignore entries, so write them without waiting, using detected values as CONFIRM: proposals. Do not open a PR. End by printing the readiness table.
