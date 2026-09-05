# Release notes, credits and announcements

Notes are approved before anything irreversible happens (phase 8 precedes the GO). Write them
in `[comms].public_language`. When the platform has a structured notes source
(`[release].notes_source`, such as GitHub's `release.yml` categories with `--generate-notes`),
use it for the skeleton and the contributor list, then edit.

## Notes structure

```
<one-line verdict: what this release is, and how it was validated>

## <lead section for the release's dominant theme, when there is one: security, a packaging fix>
## ✨ New features               (user language, issue references)
## <domain extension section: new providers, new engines and formats, new integrations>
## ⚡ Performance
## 🐛 Notable fixes
## ⚠️ Breaking and behaviour changes
    <numbered; each with its migration or escape hatch: env var, override, doc link>
## 🙏 Thanks
Full details in the CHANGELOG. <install or pull line for the archetype>
```

Tone: honest and specific. Say what the protections do *and* what stays supported. Say what
was not verified rather than implying uniform coverage. When the release fixes a packaging
or upgrade bug, lead with it and name who was affected.

## 🙏 Thanks — collecting contributors

Never skip it, never miss anyone. External contributions are the pipeline that keeps a
project alive; crediting every one of them is part of maintaining it.

1. Commit authors in the release range:
   `git log <last-tag>..<candidate-sha> --pretty='%an <%ae>' | sort | uniq -c | sort -rn`
   Use the prepared candidate SHA even when the final tag does not exist yet. For the
   first release with no previous tag, use `git log <candidate-sha>` (all reachable history).
2. Map every non-obvious name to a handle through their PRs:
   `gh pr list --state merged --limit 1000 --search "merged:>=<previous-tag-date>" --json number,author,mergedAt,title`
   then `gh pr view <n> --json author --jq .author.login`. Filter by merge date on the server
   and keep the limit large: a small limit caps the list *before* the date filter and silently
   drops contributors. Exclude PRs merged before the previous tag that the date filter still
   returns.
3. Include `Co-authored-by` trailers.
4. One bullet per contributor: **@handle** — what they shipped, with references.
5. Close with a collective thank-you to issue reporters and testers. Bots are excluded.

## Announcement skeleton

```
📢 <project> v<X.Y.Z> is out — <hook: why upgrade>

<2 to 3 lines: the headline theme plus feature highlights as a one-line · separated list>

⚡ <performance line, when there is one>
🧪 <one line on how it was tested: fresh install and upgrade on the real artifact>
⚠️ <one line for operators: check the behaviour changes in the notes>

📝 <release URL>
<install or pull line>
```

Consider crediting contributors in the announcement too. The owner posts; deliver the final
text, never post it.

## Attribution

`[comms].agent_attribution` decides whether public text carries an AI-assistance line
(`disclaimer`) or not (`none`). Follow it exactly; some projects require one policy and some
forbid the other.
