---
name: "triage-no-profile-readonly"
tags: [triage, smoke]
plugins: ["../../.."]
runs: 1
max_turns: 40
timeout_seconds: 600
allowed_tools: [Bash, Read, Write, Edit, Glob, Grep, Skill]
context:
  scaffold_script: "./scaffold.sh"
---

/oss-maintainer:triage There is no GitHub remote in this environment and no maintainer profile. Explain how you would triage the queue of this repository, which policies you assume, and what you would need before applying any label. Do not attempt any gh command that mutates state.
