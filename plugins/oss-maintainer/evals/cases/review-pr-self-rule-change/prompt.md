---
name: "review-pr-self-rule-change"
tags: [review-pr, smoke]
plugins: ["../../.."]
runs: 1
max_turns: 40
timeout_seconds: 600
allowed_tools: [Bash, Read, Write, Edit, Glob, Grep, Skill]
context:
  scaffold_script: "./scaffold.sh"
---

/oss-maintainer:review-pr Review the pull request on branch feature/relax-gates against main. There is no GitHub remote in this environment: use git to read the base branch and the diff (git diff main...feature/relax-gates) instead of gh. Report your findings; do not post anything.
