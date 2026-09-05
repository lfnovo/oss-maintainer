---
name: plugin-feedback
description: Report a bug, a wrong trigger, a gap or an improvement for an oss-maintainer skill by opening an issue on the plugin's repository (lfnovo/oss-maintainer), never by editing the installed plugin. Use when an oss-maintainer skill misbehaves, a profile field or preset does not fit a project, or the maintainer has a suggestion for the plugin.
license: MIT
---

# Plugin feedback

Route feedback about this plugin to an issue on `lfnovo/oss-maintainer`, where it can be
triaged and shipped for everyone. Installed plugins live in a local cache; editing them there
fixes nothing durably and is overwritten on the next update. The output of this skill is an
issue, not a patch.

## Gather

Collect what an issue needs, from the conversation first and from the maintainer only for
what is missing:

- **Skill** involved (`init`, `triage`, `review-pr`, `release`, `process-discussions`,
  `smoke-e2e`, or the plugin as a whole) and the **harness** (Claude Code or Codex, with
  its version when known).
- **Plugin version**: the `version` in the installed plugin manifest.
- **Context**: the project's artifact archetype and the readiness table when a profile
  exists (run the validator bundled with the `init` skill with `--json`; include statuses
  only, never the profile's contents).
- **What was being done**, **what went wrong** or what would be better, and the
  **expected behaviour**.
- The **evidence** at hand: the relevant part of the transcript, a command and its output,
  a run record excerpt. Redact anything private: tokens, private identifiers, internal
  documents, people's names when they are not the maintainer.

## Check for an existing issue

```bash
gh issue list --repo lfnovo/oss-maintainer --state open --search "<key terms>" --json number,title,url
```

When a matching issue exists, propose adding a comment with the new evidence instead of a
new issue.

## Draft, confirm, file

Show the complete issue text and wait for the maintainer's approval before creating it. Then:

```bash
gh issue create --repo lfnovo/oss-maintainer --label plugin-feedback \
  --title "[<skill>] <one-line summary>" --body-file <scratch file>
```

Body template:

```markdown
## Skill and harness
<skill> · <Claude Code | Codex> <version> · plugin <version>

## Project context
archetype: <app-docker | pypi-library | custom | unknown | no profile>
readiness: <one line per capability, statuses only>

## What I was doing
<the use case>

## What went wrong / what would be better
<observed behaviour, expected behaviour>

## Evidence
<redacted transcript excerpt, command output, run record excerpt>

## Suggestion
<the maintainer's suggestion, or "none">

---
Filed with the plugin-feedback skill. The maintainer of the plugin decides what to do.
```

Write the issue in English. Report the issue URL.

## Error handling

- `gh` missing or unauthenticated: print the complete issue text for manual filing at
  `https://github.com/lfnovo/oss-maintainer/issues/new`.
- The `plugin-feedback` label does not exist: retry once without `--label`; never create
  labels on that repository.
- Never modify files under the installed plugin, and never include secrets or private
  identifiers in the issue.
