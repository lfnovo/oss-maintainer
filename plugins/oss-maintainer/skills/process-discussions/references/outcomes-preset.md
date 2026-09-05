# Outcome vocabulary — preset

The qualification stage of a community contribution flow: discovery happens in Discussions,
delivery in Issues. Projects may rename outcomes or change the graduation and close rules
through the profile; the reply always states the outcome textually.

| Outcome | When | The reply must include |
|---|---|---|
| **exploring** | a real, aligned problem; open solution space | sharpening questions that actually shape the design |
| **incubating** | direction decided, *timing* open (waits on vision fit, capacity or a champion) | the settled spec, what it waits on, "this Discussion stays the home" |
| **accepted → graduated** | someone will build it now: a builder plus a closed spec | the Issue(s) opened immediately, linked |
| **parked until champion** | valid but needs a community owner (packaging channels, integrations) | the explicit return condition and how to volunteer |
| **combine** | duplicate or facet of an existing theme | the link to the canonical home |
| **answer** | already exists or documented | the answer, plus where the docs fell short |
| **bug** | reproducible defect | graduated straight to a bug Issue |

## Graduation (`[discussions].graduation`)

- `pull` (preset): an Issue is born when someone is going to build it, never because the idea
  became clear. `ready` is a promise of execution; filling it with well-discussed items and no
  builder recreates a stale backlog. A discussed-but-unscheduled idea is **incubating** and the
  Discussion remains its home. Exceptions that graduate immediately: verified bugs, and small
  items the maintainer will do next.
- `push`: accepted proposals become Issues even without a committed builder. The reply says
  so and the Issue carries no execution promise.

## Closing (`[discussions].close_on`)

- `answer`: when the need has a better home (an existing Issue, upstream, "not planned"), post
  the reply and close as resolved; an open thread with a final answer clutters the queue.
  Anyone can reopen with a new argument.
- `graduated-work-landed`: a thread whose needs all shipped or were routed elsewhere is done
  when the last fix merges to the default branch. The closing reply names the merged PRs, says
  the change ships with the next release and points testers at the development artifact
  (`[artifacts.docker].dev_tag` for applications).
- `never`: threads stay open after delivery; the reply still reports the status.

## Canonical threads

- Threshold: **three or more signals** on one theme broaden an existing thread in place
  (rename it; keep the history). At two signals, a linked pair is enough.
- Consolidating old Issues into a canonical thread: close **solution proposals** with an
  explanatory comment (they become evidence); keep **execution umbrellas** open; respect
  pointers from decision records.
- Referencing Issues in a reply creates backlinks on their timelines: free visibility, no mass
  edits.
