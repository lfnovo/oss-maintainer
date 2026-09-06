# oss-maintainer — Vision

`oss-maintainer` helps open-source maintainers turn their project's own practices into assisted maintenance workflows. It prepares decisions with evidence, carries authorized work through to a verified result and preserves the knowledge needed to continue across sessions.

The maintainer defines direction and commitments. The plugin makes those choices easier to execute consistently as the project, its community and its tooling evolve.

The [product principles](PRINCIPLES.md) define the values behind this vision. The [README](README.md) describes available capabilities and usage; the [profile reference](docs/profile-reference.md) documents supported configuration.

## The problem we solve

Maintaining an open-source project requires repeatedly connecting context to action: understanding a report, assessing a contribution, deciding what is ready to ship, answering a community question and checking whether the result works for users. The difficult part often sits between tools. A command can publish a package, but deciding whether it should be published requires knowledge of the project's commitments, risks and evidence.

Much of that knowledge lives in a maintainer's memory, scattered conversations or local scripts. Each new session reconstructs decisions and procedures. As contributors, agents and repositories multiply, practices drift and the maintainer becomes the person who must explain, coordinate and verify everything again.

We want to reduce that repeated work while preserving the judgment and identity that make each project its own.

## Who we serve

Our primary user is the maintainer accountable for a project's direction, quality and relationship with its community. This includes a solo author with limited time and a group of maintainers with distinct responsibilities. Contributors and users benefit when reports receive grounded responses, contributions are assessed consistently and published changes meet the project's stated commitments.

A repository should gain value without first adopting a large maintenance framework. A project seeking help with review should not need to configure publication infrastructure. A mature community should be able to express its existing governance without having to adopt the conventions of the repositories where this plugin originated.

## The experience we want

The plugin should work like a collaborator who knows the repository, prepares decisions carefully and follows through. A maintainer brings an objective; the plugin discovers relevant context, identifies the effective policy and establishes what evidence and authorization the work requires.

It then performs the work within that agreement. When a decision is needed, it presents a concrete proposal with its evidence, consequences and remaining uncertainty. It retains valid authorization, continues independent work and verifies the effects of the actions it takes.

At a handoff or session boundary, the project retains an understandable record: what happened, what was verified, what was authorized and what remains. The next session resumes from those facts. Completion is explicit, and optional follow-up learning can continue after the delivery obligations are fulfilled.

## One maintenance context across workflows

The product connects recurring maintenance activities through shared project context:

- **Intake:** establish whether a report's premise holds, identify related work and apply the project's criteria for what deserves action.
- **Review:** assess a contribution against the project's rules, intended behavior and evidence, and prepare findings the maintainer can evaluate.
- **Delivery and publication:** establish readiness, coordinate appropriate checks, act within publication authority and verify the result users receive.
- **Community facilitation:** understand the needs behind a discussion, connect them to decisions and existing work, and prepare responses consistent with the project's public voice.
- **Product verification:** exercise the relevant user journey and report which surfaces worked, failed or remain unverified.

These workflows should share decisions and evidence where they apply. A finding from review can inform delivery risk; a community discussion can explain why a proposal is outside the project's strategy; a verified result can support a response to a user. Reuse must preserve the context and limits of the original evidence.

## The project owns its process

The plugin has an opinion about trustworthy maintenance: claims need evidence, actions need authority, results need verification and work needs continuity. The project chooses its goals and how to govern the work that serves them.

We therefore distinguish required guarantees, recommended practices and repository policies, as defined in [PRINCIPLES.md](PRINCIPLES.md#what-we-require-recommend-and-leave-to-the-repository). Defaults help a maintainer get started. They remain visible choices, with reasons and tradeoffs. Existing conventions can be questioned through a concrete proposal when they conflict with the project's goals; changing them remains a project decision.

Adaptation includes philosophy, stack, size, maturity and strategy. Stability and experimentation call for different proposals. A library and a running service require different evidence. A solo maintainer and a distributed team need different coordination. Projects pursuing adoption, reduced maintenance or a planned sunset should receive recommendations that serve those directions.

## Architecture that supports the vision

### A shared engine and a repository-owned profile

The engine supplies reusable methods for discovery, reasoning, verification and continuity. A profile under `.maintainer/` expresses the supported settings and references that connect those methods to a particular repository. Readiness is assessed per capability so missing configuration blocks only the work that depends on it.

The profile references canonical commands, contribution rules, decision records and human process documents. Each fact has one home. Qualitative philosophy and strategy remain readable project documents; the profile should not become a schema for every aspect of a community's identity.

Local preferences may adapt an environment or a person's interaction style. They must not silently weaken shared requirements or expand authority. Conflicting sources and unsupported policies require an explicit explanation and a feasible proposal.

### Existing tools execute; the agent coordinates and judges

Build tools, scripts, CI workflows and hosting or registry APIs remain the executors of deterministic operations. The plugin contributes the judgment around them: understanding the objective, checking premises, choosing proportionate validation, interpreting evidence and confirming the outcome.

This lets projects retain tools they trust. The plugin should discover and compose with existing automation, and propose new automation when observed repetition or risk justifies the investment.

### Evidence, authority and completion have separate records

Evidence records what was executed or observed, the result and the conditions under which it remains applicable. Authorizations record covered actions, limits and invalidation conditions. Delivery state records which obligations have been fulfilled and which remain outstanding.

Keeping these distinct prevents a passing check from being treated as permission, a still-valid authorization from being discarded because unrelated metadata changed, or a retrospective from keeping completed work open. Historical execution facts remain intact when later observations revalidate or supersede them.

External effects are confirmed in the system where they occur. When tested and distributed artifacts differ, that boundary is stated and the distributed artifact is verified. A required check that did not run remains unverified; a permitted exception records a decision without rewriting the result.

### A portable core with native integration

The maintenance method should remain consistent across supported agent environments. Shared skills carry the core behavior; native adapters handle invocation, discovery and execution differences. Portability is demonstrated through equivalent behavior, including authorization, evidence handling and resumption.

Repository and community content provide context for the task. A proposed change cannot grant itself authority: review uses the established policy against which that change is being evaluated.

## Product boundaries

The plugin focuses on maintenance judgment and coordination. Feature design and implementation, general project management and organization-wide planning belong to complementary workflows. Maintenance may identify work for those workflows and hand it off with evidence and a clear decision.

Existing review tools, changelog generators and publication systems remain useful components. The plugin integrates their outputs and verifies relevant claims. It does not require a particular vendor, impose a new role system or turn permission to investigate into authority to speak for the project.

## What success looks like

Maintainers spend less time restating context, repeating valid checks and answering questions whose decisions already hold. They can see why an action is proposed, which project commitment it serves and what evidence supports it. Contributors encounter consistent criteria and useful responses. Work survives interruptions, and delivery ends with an accurate account of the result.

The product should improve through use in repositories with different needs. Repeated friction can justify a better default, a supported policy or a simpler workflow. New configuration and process steps earn their place by helping maintainers make decisions, fulfill commitments or reduce future work. A safeguard that is right on its own can still be wrong in aggregate: the experience is measured on a whole release, by how many decisions the maintainer had to make and how many commands served only the process.
