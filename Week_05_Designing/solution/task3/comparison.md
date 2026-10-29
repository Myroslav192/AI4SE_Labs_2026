# RecipeCove — baseline versus skill-assisted replay

## Basis and limits

The evidence is the preserved [baseline Task 1](../baseline/task1_discussion.md) and [Task 2](../baseline/task2_discussion.md), [skill-creation record](skill_creation.md), and replay [Task 1](../with_skill/task1_discussion.md), [architecture analysis](../with_skill/architecture_options.md) and [Task 2](../with_skill/task2_discussion.md). These are summarized actual exchanges, not instrumented transcripts. Baseline files were excluded during replay analysis/review and consulted only after the user's final acceptance and comparison authorization. Earlier statements that comparison was pending are historical.

Both runs produced an accepted modular-application ADR after **two actual user-feedback revisions**, v1 → v2 → v3. Baseline Task 2 entries 2/3 and replay entries 6/10 contain those requests. Assistant setup, explanations, self-review, verification and acceptance notes are not additional user reviews. Heading counts are not conversation-turn counts; the repeated baseline v3 request after tool interruptions was the same review request.

There are no comparable end-to-end timing, token, cost or exact model-setting measurements. Dates and replay clock observations do not establish active work duration. **Whether the skill made completion faster or saved tokens is inconclusive.**

## Observed comparison

| Aspect | Baseline | Skill-assisted replay |
| --- | --- | --- |
| Requirement coverage | Initial notes and ADR module mapping cover all 14 stories and the prose-only diet chatbot; usability and recipe/ingredient detail appear in context/drivers. | Explicit US-01–14 and PR-01–04 inventory and responsibility rows preserve the same scope, actors and access. More granular traceability is not additional product scope. |
| First draft | [Baseline v1](../baseline/adr_revisions/ADR-001-v1.md) already has drivers, ownership, deployment, alternatives, consequences and open choices. Its implementation-obligation table mixes safeguards with proposed favorite/cancellation behavior; the deletion-state distinction and actionable evidence table need later refinement. | [Replay v1](../with_skill/adr_revisions/ADR-001-v1.md) already separates safeguards/proposals/questions, labels deployment interactions and Google integration, distinguishes reservation/authorization/external acceptance, and supplies actionable reconsideration rows. It also overburdens the ADR with process provenance, disclaimers and operation codes. |
| Guidance still needed | User specifies scope, common journey, assumptions, detailed implementation concerns and review requirements. Two requested understanding checks remain unanswered; proceeding is not evidence of understanding. | User explicitly invokes the skill, controls phases, requests comparable journeys and reiterates policy authority, including local catalog/unique favorites in the B request. The skill does not remove the need for detailed prompts or real review. No understanding answers are invented. |
| First actual review | [Baseline v2 request](../baseline/task2_discussion.md): separate statement authority and add pending/reserved/authorized/accepted deletion states. | [Replay v2 request](../with_skill/task2_discussion.md): remove process detail, replace cryptic operation codes, consolidate reminder boundaries and shorten overlapping explanations. |
| Second actual review | Baseline v3: clarify release/process/interface/persistence diagram and Google; replace vague revisit prose with evidence/limitation/response criteria. | Replay v3: make A/B/C assessable through a common five-criterion decision matrix, equal reminder interpretation and concise rationale. |
| Final limitations | Proposed policies, integrations and source-only Mermaid review remain open/limited. | Same acceptance scope and diagram limitation; exhaustive notes and initial ADR verbosity are additional burdens, not demonstrated effort savings. |

The [skill](../../.agents/skills/requirements-to-adr/SKILL.md) carried reusable expectations into the new session: recording first, prose coverage, explicit authority categories, concrete boundaries, failure/recovery reasoning, actual selection versus acceptance, immutable revisions and actionable reconsideration. Its [creation evidence](skill_creation.md) identifies these lessons from the baseline. The replay's initial artifacts are consistent with that checklist, particularly avoiding the baseline v1 authority ambiguity. This is observed transfer, not proof that the skill alone caused the differences: user prompts also strongly reinforced it.

## Prompt and design differences

The baseline user directed a modular-monolith discussion first and explicitly requested two understanding questions. The replay user asked for an overview of three proposals before detailing A, invoked the skill, prohibited prior-answer access and required run metadata. The replay also explicitly retained conditional proactive reminders; baseline selected a durable worker arrangement while still leaving channel/timing open. Both supplied the same small-team/modest-traffic/limited-operations assumptions, not measured requirements.

The alternatives were materially different. Baseline microservices had **four services** (Identity/Profile, Catalog, Recommendations/Chat, Personal Workspace); replay B had **three** (Discovery, Account, Calendar). Baseline's illustrative AWS serverless pipeline used an outbox/change stream, per-event external schedules, queue and reconciliation. Replay C was vendor-neutral and used a recurring database dispatcher, queue and bounded user-partition transactions. Baseline consulted official product documentation; replay stated required capabilities without certifying a product. Baseline allowed catalog records or source mappings/cache, while replay explicitly carried local catalog placement as a pending proposal. These differences affect detail and reasoning workload; they are not a controlled skill-only experiment or evidence that one serverless topology is universally better.

## Consistent document-size observations

Counts use the same `wc -w -c` method on complete Markdown files, including tables, metadata and diagram source. They are whitespace-delimited words and UTF-8 bytes, **not tokens, effort or model cost**.

| ADR artifact | Baseline words / bytes | Replay words / bytes |
| --- | ---: | ---: |
| v1 | 1,622 / 12,525 | 3,345 / 26,313 |
| v2 | 1,850 / 14,045 | 2,249 / 17,600 |
| v3 | 2,175 / 16,467 | 2,441 / 19,061 |
| Accepted canonical | 2,206 / 16,681 | 2,456 / 19,226 |

Sources: baseline [revisions](../baseline/adr_revisions/ADR-001-v1.md) / [accepted ADR](../adr/ADR-001-recipecove-architecture.md), replay [revisions](../with_skill/adr_revisions/ADR-001-v1.md) / [accepted ADR](../with_skill/adr/ADR-001-recipecove-architecture.md). The replay's longer first draft and its concision-focused first review are a concrete disadvantage of exhaustive checklist execution. Both final artifacts retain full requested coverage; file length cannot establish usefulness or architectural effectiveness.

## Conclusion

The skill supplied a reusable workflow and made several baseline lessons visible earlier, but did not reduce the observed number of actual user-feedback revisions. The records support earlier explicit traceability/status discipline and also show excessive initial detail requiring correction. They do not establish speed, token or monetary savings, superior system behavior, or a causal improvement attributable only to the skill. Both assignments reached actual document acceptance with proposed product policies and unresolved choices still open. Mermaid remains source-inspected only; neither run implemented or behaviorally tested RecipeCove. Skill creation's unavailable Python validator and fallback static checks remain as recorded, not retroactively upgraded by replay completion.
