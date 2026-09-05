---
type: llm
target: files
criteria: "In .maintainer/profile.toml, every command or value that the fixture repository does not state (the distribution trigger, the package gate, the repository slug) is marked TODO or CONFIRM:, and no invented command appears. The validator command references the Makefile targets (make test, make lint) rather than copying their bodies."
---

The skill never invents commands.
