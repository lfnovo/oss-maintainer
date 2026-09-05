# Decision format — one decision at a time

After the queue map, decisions are presented sequentially, numbered ("Decision 2 of 4") so
the maintainer knows the size of the session. Each one, in the maintainer's language:

1. **Id and title** of the thread.
2. **Summary**: what the thread is, how it was decomposed, its current status.
3. **Last movement**: who did what and when; what changed since the last run (a graduated
   Issue closing, an upstream release, an author answering). Check for the maintainer's own
   replies before drafting: they may have answered from another session.
4. **Proposal or question**: the outcome, the complete draft reply, and every side action the
   package includes (Issues to open, renames, closures); or the concrete question when the call
   is the maintainer's. Options are labelled (a), (b), (c) with a recommendation.

On approval, execute the package in order (side actions first, reply last), report the URLs,
then present the next decision. A redirect ("incubating instead", "close as answer") replaces
the proposal; a decline skips the thread and records why.

## Batch variant

When `[triage].batch_approval = "allowed"`, the maintainer may authorize several decisions at
once. Every decision is still presented in full before the batch; the authorization names the
decision numbers it covers; anything not named waits.
