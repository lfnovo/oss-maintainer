---
name: "release-fresh-version-pre-go"
tags: [release, regression]
plugins: ["../../.."]
runs: 1
max_turns: 25
timeout_seconds: 300
allowed_tools: [Bash, Read, Glob, Grep, Skill]
context:
  scaffold_script: "./scaffold.sh"
---

/oss-maintainer:release Prepare notes, credits and the pre-GO test matrix for version 2.4.0 using the current candidate SHA. No 2.4.0 tag or artifact exists. Use the baseline tag already present. Do not publish or use network services; unavailable checks remain not-run. Demonstrate the contributor range locally and distinguish pre-publication manual checks from the later registry verification. Stop before GO.
