# oss-maintainer — Product principles

`oss-maintainer` helps open-source maintainers turn their project's choices into work that can be executed, verified and continued across sessions. The maintainer sets direction and commitments; the plugin gathers context, prepares decisions and carries authorized work through to a confirmed result. Success means less repeated explanation, fewer unnecessary interruptions and more confidence in what was delivered.

These principles guide product and implementation decisions. [VISION.md](VISION.md) describes the product's purpose, intended experience and architectural direction; the [README](README.md) describes available capabilities and usage.

## Five principles

### 1. The process belongs to the project

Each repository owns its philosophy, tools, conventions, quality criteria and governance. The plugin discovers those choices, makes them explicit where needed and helps the community apply them consistently. It offers useful, simple defaults when the project has no established practice, identifies them as recommendations and explains their tradeoffs. Our own repositories provide experience and presets; their way of working is one valid starting point, not a requirement for other maintainers.

### 2. Autonomy operates within a clear agreement

The plugin investigates, prepares, executes and verifies within the scope the maintainer has authorized. The maintainer retains authority over consequential decisions, publication and the project's public voice. Authorization has a purpose, covered actions, limits and invalidation conditions; it remains valid while those conditions hold. The plugin prepares concrete, reviewable decisions before asking and continues independent authorized work while a decision is pending. A new question should represent a new decision, an unresolved ambiguity or a material change in scope.

### 3. Trust is built on evidence

Recommendations and verdicts must be grounded in the code, the community's context and verifiable results. The plugin checks an issue's premise before judging it, records what actually ran and verifies what was actually delivered. It distinguishes facts, hypotheses, failed checks, missing evidence and explicitly accepted risks. Evidence has dependencies: a source check proves something about a source revision; an artifact check proves something about particular bytes. Preserve evidence while those dependencies hold, and repeat the affected checks when they change. Accepting a risk never turns an unrun or failed check into a pass.

### 4. Knowledge accumulates in the project

Decisions, criteria, procedures and useful learnings should survive a conversation, an agent or a change of maintainer. Each fact has a canonical home in the repository; profiles reference existing documents and commands instead of duplicating them. Run records preserve execution history, evidence, decisions and outstanding obligations so the next session can resume from reality. The record is a result of the work, never a condition for continuing it: the plugin writes down what it did and what the maintainer decided, and it does not stop to prove already completed work to a ledger. Existing logs, CI runs and artifact digests are the evidence; the record links to them. Delivery has an explicit completion state. Learning can continue after delivery, and optional retrospective work must not keep an otherwise completed release open.

### 5. Attention follows risk

Maintainer time and attention are scarce. Investigation, tests, review and coordination should be proportional to the affected users, surfaces, uncertainty and cost of failure. The plugin starts with the relevant scope, broadens when shared dependencies or evidence justify it, and turns testing recommendations into executable plans. Adoption should be useful with a small amount of configuration and grow with the project's needs. Every additional step should help resolve a decision, verify an obligation or reduce future maintenance work. Ceremony is judged by its total cost, not one safeguard at a time: when an experienced maintainer feels they are working for the plugin instead of with it, the plugin is wrong, even if every individual step has a justification. Publication is the one gate that always asks; everything about how work is recorded, approved and organized is a recommendation the project can replace.

## What we require, recommend and leave to the repository

| Layer | Product position | Examples |
|---|---|---|
| **Required guarantees** | The plugin must preserve truth, authority, provenance and clear delivery outcomes in every workflow. | Never claim an unrun check passed; expand an authorization silently; apply evidence to an artifact it did not verify; or call an incomplete delivery complete. Confirm public effects in the system where they occur. |
| **Recommended practices** | Offer explainable defaults that a maintainer can adopt or replace with a practice that preserves the guarantees. Missing policy does not make a default mandatory. | Reviewable changes, tests proportional to risk, artifact verification, identifiable publication, useful release notes and recorded decisions. |
| **Repository policies** | The project defines its commitments and how work is governed. The plugin follows the agreed policy and reports unsupported choices explicitly. | Required checks, approvers, review tools, PRs versus direct commits, release cadence, versioning and compatibility, supported platforms, test budget, issue closure and public tone. |

A solo maintainer using direct commits and manual publication and a larger community using protected branches, independent review and staged releases are both valid product design cases. Both need an authorized action, evidence appropriate to their commitments and confirmation of the result. The plugin should support different workflows through explicit agreements that preserve these guarantees.

Required project gates remain binding under the effective agreement. If a maintainer authorized by the project's governance changes a requirement or accepts a permitted exception, record who decided, why and under which conditions. Preserve the original check result and report the resulting limitation. A local preference cannot silently weaken a shared requirement.

## Adapting to different repositories

| Dimension | How the plugin should adapt |
|---|---|
| **Philosophy** | Read the project's stated values and precedents. Judge a proposal against its preference for stability, experimentation, simplicity or extensibility, and explain tensions using that context. |
| **Stack** | Discover existing commands, tooling and deliverable surfaces: library, CLI, service, image or plugin. Reuse canonical executors and verify the artifact users consume. |
| **Size** | Match coordination to the people and components involved. A solo maintainer needs little ceremony; multiple owners may need explicit handoffs and separate approval responsibilities. |
| **Maturity** | Work with the evidence and infrastructure available, expose gaps honestly and propose incremental improvements. An immature release capability should not prevent useful read-only review. |
| **Strategy** | Use the project's current direction to prioritize: adoption, stability, reduced maintenance, new capabilities or a planned sunset imply different recommendations. Record uncertainty rather than infer a roadmap from issue volume. |

These dimensions inform judgment; they are not a scoring system or a fixed ladder every repository must climb. When a convention appears costly or conflicts with the project's stated goal, explain the concrete consequence and propose an alternative. The maintainer decides whether to change it.

## How the plugin makes this practical

1. **Discover before prescribing.** Read established instructions, contribution and release documents, workflows, canonical commands and relevant decisions. Distinguish declared policy, inferred practice and unknowns. A change under review cannot authorize itself or replace the base branch's review rules.
2. **Build the smallest useful agreement.** Configure only what the selected capabilities need. Put executable settings in the supported profile schema and link to the existing documents that express philosophy and strategy. Do not turn every qualitative preference into a new configuration field or require a documentation migration to get started.
3. **Resolve consequential ambiguity with a proposal.** Show conflicting sources or missing information, the practical consequence and a recommended resolution. Label defaults. Ask when the answer affects authority, correctness or a project commitment; continue useful independent work when possible.
4. **Execute and verify within that agreement.** Keep approvals valid within their actual scope. For each selected test, identify the risk, command or manual action, expected evidence, required resources, responsible actor and whether it runs before or after publication. Explain any unsupported policy or unavailable check precisely, along with a feasible alternative; never silently substitute another process.
5. **Retain what was learned.** Record approved policy adjustments in their canonical home and execution facts in the run history, without secrets. Propose improvements in response to observed friction. A retrospective may suggest a plugin issue or a repository change; it does not itself authorize posting or starting another project.

## Keep evidence, authority and completion separate

These are three different questions: **What do we know? What may we do? What remains to be delivered?** A test passing does not authorize publication. Permission for one action does not imply permission for another. New information should invalidate evidence or authorization only when it changes the conditions on which they depend. Revalidating an old observation creates a new event; it must not rewrite the original execution as if it just happened.

Authorization permits scoped action; completion follows fulfillment and verification of the agreed delivery obligations. An optional retrospective can remain pending after that point. Keeping these states distinct lets the plugin act autonomously without losing either continuity or the maintainer's control.
