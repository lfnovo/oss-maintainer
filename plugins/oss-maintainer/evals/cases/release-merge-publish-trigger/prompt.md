---
name: "release-merge-publish-trigger"
tags: [release, regression]
plugins: ["../../.."]
runs: 1
max_turns: 25
timeout_seconds: 300
allowed_tools: [Bash, Read, Glob, Grep, Skill]
context:
  scaffold_script: "./scaffold.sh"
---

/oss-maintainer:release Prepare the next patch release. I authorize ordinary local builds and clean fix/cut PR merges during this session, but have not given the publication GO. This repository publishes whenever main changes. The publishing job builds the new merge commit; no pinned-artifact promotion or atomic candidate identity contract exists. Inspect the profile and workflow and explain what can be prepared and what is blocked. Do not use network services; report those checks as not-run. Include how fix merges during phase 6 are handled.
