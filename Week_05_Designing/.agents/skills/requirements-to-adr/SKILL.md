---
name: requirements-to-adr
description: Analyze software requirements, compare concrete architectural proposals, and develop an architecture decision record through actual user review. Use for requirements-led architecture discussions, selection, and ADR creation or revision.
---

# Requirements to ADR

Use the caller's project inputs, output locations, language preferences, required proposal count, deliverables and review checkpoints. Support the requested phase without selecting a preferred architectural style in advance or beginning application implementation.

## Establish the record before analysis

- Read applicable repository instructions and the supplied assignment or project brief. Resolve inputs against the actual repository; report missing material rather than substituting invented requirements.
- Before substantive analysis or drafting, create or continue the caller's discussion notes. If no location is supplied, establish one in the authorized output area and state the choice. Obtain materially missing scope or language preferences while continuing independent work where possible.
- Record actual user questions, assistant explanations, feedback, changes and explicit decisions as they occur. Summaries suffice. Keep unanswered questions unanswered; a request to continue or select an architecture is not evidence of understanding-check answers.
- Separate notes for analysis and ADR review when requested. Preserve historical entries; append later decisions rather than rewriting earlier uncertainty as agreement.

## Establish requirements and their authority

Read both numbered requirements and descriptive prose. Preserve source identifiers; assign stable identifiers to otherwise unnumbered capabilities or constraints. Build compact traceability from every requirement to proposed responsibility/ownership, including actors and access scope. Do not silently omit prose-only capabilities.

Keep these categories explicit throughout discussion and ADR writing:

| Category | Treatment |
| --- | --- |
| Source requirement | Cite the supplied source; preserve what it actually requires. |
| Working assumption | Identify its origin and provisional status; use it consistently across alternatives. |
| Correctness/security safeguard | Explain why the design needs it; do not present it as optional or as source wording. |
| Proposed product policy | State the suggested behavior and that confirmation is pending. |
| Open question/integration choice | Explain architectural impact without silently choosing an answer. |
| Explicit user decision | Record what was selected or accepted, and the scope/exclusions of that acceptance. |

Do not invent workload measurements, performance targets, budget figures, team capabilities or measured cost rankings. Do not infer a provider or implementation technology from a capability's name. Identify uncertainties that could change a boundary or recommendation; avoid turning every unknown into a blocking question.

## Compare concrete proposals fairly

Use the requested number of proposals and pacing. Explain each in plain language, showing what is genuinely different in deployment units, communication, state ownership, transaction boundaries, operating responsibilities and scaling. Architectural labels can overlap; compare concrete designs rather than treating labels as exclusive categories.

For each proposal:

- Justify a minimal coherent decomposition. Distinguish modules, processes, services and provider-managed resources; distinguish logical data ownership from physical database deployment.
- Map the complete requirements inventory to responsibilities. Keep functionality, working assumptions and unresolved choices consistent across options; identify any intentional difference rather than hiding it.
- Walk through the same representative user journey. Mark synchronous calls, deferred work, each durable commit, what success means to the user, and the visible outcome of failures or lost acknowledgements.
- Explain the difficult implementation trade-offs relevant to that system: identity versus authorization, private-data access, concurrent writes, duplicate commands, time interpretation, slow dependencies, retries, recovery and operational maintenance. Tailor depth to the actual requirements.
- Introduce infrastructure patterns only for a demonstrated boundary. A database transaction does not include a separate scheduler, broker or external provider. Where a dual-write gap exists, explain durable intent, idempotent processing and reconciliation, including their limits.
- For cancellable background effects, use a short state table when useful. Distinguish reservation from final authorization and external acceptance, locate the authoritative concurrency check, and separate logical invalidation from physical cleanup. Derive cancellation semantics from requirements or label them as proposed policies. Do not promise recall or exactly-once external effects without an established end-to-end contract.
- Discuss positive and negative consequences, failure coupling, operation/maintenance effort, qualitative cost drivers and evidence for change. Verify concrete product claims against official documentation; label illustrative stacks and keep their assessment specific to the actual proposal.

Use small diagrams where helpful. Show deployment/version boundaries, execution roles, public module interfaces, required external actors and persistence ownership. Label network, local, persistence and asynchronous interactions; clarify when repeated boxes are the same code in different processes. Do not imply unspecified integrations.

Honor requested pauses. Ask understanding checks if requested or useful, without manufacturing answers. Recommend using the stated drivers, disclose disadvantages and uncertainty, and distinguish an assistant recommendation from the user's choice. Record the actual selection when supplied.

## Draft and review the ADR

Use the caller's ADR convention and paths. Unless already explicitly accepted, keep the document Proposed during review, even when the architectural direction has been selected.

Keep the ADR focused on context/scope and sources; decision drivers; the selected or proposed direction and its boundaries/ownership; complete traceability; concrete alternatives and rejection rationale; safeguards, proposed policies and open choices; consequences; and reconsideration criteria. Link detailed notes instead of copying algorithms. A compact status table can prevent mixing obligations with product proposals; keep each fact in one authoritative location.

Make reconsideration actionable: **observable evidence or newly confirmed requirement → limitation revealed → response to investigate**. Consider optimization, hosting changes or limited extraction where appropriate; do not automatically prescribe complete migration or invent thresholds.

Review the first draft for authority/status confusion, incomplete coverage, ambiguous diagram arrows, unclear ownership, inconsistent terminology, repeated explanations and unjustified guarantees. Then revise in response to actual user feedback, recording what changed and why. Do not invent review rounds or approval. Preserve requested immutable revision snapshots and keep each new snapshot identical to its canonical revision.

Acceptance applies only to the scope the user states. On explicit document acceptance, update status and review wording; keep explicitly proposed policies and unresolved choices open unless separately resolved. Record the actual acceptance and preserve the requested final snapshot and discussion history.

## Verify and finish the authorized phase

- Resolve relative links from the canonical document's real directory and check the targets exist. Check full traceability, status consistency and snapshot equality; verify older snapshots remain unchanged when preservation is requested.
- If a diagram renderer is available, render and inspect the output. Otherwise report source inspection only; do not claim rendered layout or parser validation from text checks.
- Report which checks actually ran, their outcomes and remaining limitations. Structural validation does not establish behavioral effectiveness or measured architectural quality.
- For a requested fresh-session replay, preserve the reference run and use distinct outputs. Follow the caller's rules on prior-answer access; a clean evaluation must not quietly reuse earlier decisions. Do not simulate user exchanges or claim improvement before a real replay and evidence-based comparison.
- Stop at the caller's phase boundary. Architecture/ADR work alone does not authorize implementation, deployment or a later evaluation phase.
