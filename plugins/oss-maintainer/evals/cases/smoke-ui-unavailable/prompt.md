---
name: "smoke-ui-unavailable"
tags: [smoke-e2e, smoke]
plugins: ["../../.."]
runs: 1
max_turns: 40
timeout_seconds: 600
allowed_tools: [Bash, Read, Write, Glob, Grep, Skill]
context:
  scaffold_script: "./scaffold.sh"
---

/oss-maintainer:smoke-e2e Run the smoke journey of this repository. No instance is running and no browser tool is available in this environment: record every check you cannot perform with the right status and give the verdict the profile's mandatory surfaces require.
