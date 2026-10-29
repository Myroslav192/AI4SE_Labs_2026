# Task 2 discussion notes — RecipeCove (baseline)

## Recording conventions

Maintain these notes in English while explaining the work to the user in Slovak. Record actual requests, explanations, feedback, revisions, open questions, and explicit approvals. Distinguish the user's selected architectural direction from acceptance of an ADR draft. Do not invent review comments, answers, or approval.

## Entry 1 — Task 2 begins; first ADR draft requested (2026-10-27)

### Actual user request

The user selected the modular monolith with durable reminder jobs and a background worker for this assignment, based on the three Task 1 proposals. They requested appending the choice and rationale to the Task 1 record while preserving prior discussion and unanswered questions. That selection is now recorded in [Task 1, Entry 5](task1_discussion.md#entry-5--user-selects-the-architectural-direction-2026-10-27).

Before drafting the ADR, the user requested starting these ongoing Task 2 notes. They requested an English first draft at `solution/adr/ADR-001-recipecove-architecture.md`, status **Proposed**, with an identical first-draft snapshot at `solution/baseline/adr_revisions/ADR-001-v1.md`. They want the draft to cover context/scope and sources; drivers separating requirements, provisional assumptions, and unknowns; module and data/deployment/transaction boundaries with a Mermaid diagram; all 14 stories and the chatbot; the two concrete alternatives and a concise comparison; implementation obligations and consequences; unresolved product choices and revisit triggers. The ADR should link to the detailed discussion rather than duplicate it.

The user explicitly left recipe-data source, chatbot implementation, reminder channel/timing, physical deletion policy, stack, and hosting open. They prohibited invented performance targets, measured cost rankings, or exactly-once external-delivery guarantees. The serverless assessment must apply to our concrete proposal rather than every possible serverless implementation.

### Initial assistant action and status

The assistant confirmed it would record the selected direction, start these notes before drafting, create a Proposed ADR, and preserve an identical v1 snapshot. These notes were created before the ADR draft. The architectural direction is selected for the exercise; the draft document and its detailed proposals require review.

No ADR draft has been reviewed or approved by the user. No Task 2 revisions or feedback have yet occurred. The two Task 1 understanding-check questions remain unanswered. Do not begin Task 3 or create skills in this exchange.

### First draft prepared and preserved

Created the first English ADR at [ADR-001](../adr/ADR-001-recipecove-architecture.md) and preserved its identical first-draft snapshot at [ADR-001-v1](adr_revisions/ADR-001-v1.md). The ADR is **Proposed** and explicitly distinguishes the user's selected direction from approval of the draft and its detailed policies. The snapshot is the baseline to preserve during later user-requested revisions.

The draft contains context/source links; a driver table separating requirements, provisional assumptions, architectural judgments and unknowns; five modules with owned data and a mapping of all 14 stories plus the chatbot; one backend release with separate web/worker roles and a Mermaid diagram; local transaction boundaries; comparison of the two concrete alternatives; implementation obligations; positive/negative consequences; open product/implementation decisions; and evidence for revisiting the architecture. It links to the detailed discussions rather than reproducing the full scenarios.

The main trade-off explained is simpler local consistency and fewer application-level operating components in exchange for shared release/datastore boundaries, web-process failure coupling, less targeted scaling, and continuing worker/operations responsibilities. The serverless assessment applies to the particular managed scheduler/queue/outbox proposal; it does not assert a universal serverless cost or complexity disadvantage. Recipe source, chatbot technology, reminder channel/exact timing, physical deletion policy, stack and host remain open.

Verification completed: canonical ADR source/discussion file links exist; the requirement mapping includes IDs 1–14 and the chatbot; status is Proposed; and `cmp` plus SHA-256 confirm the live ADR and v1 snapshot are byte-identical. Both hashes are `3a30222d067c26a97089a72f56c0709e596293837bdf19f3f480c38bbc3dc4f2`. The Mermaid source was inspected as part of reading the draft; no rendered-diagram validation or application implementation/test execution is claimed.

### Assistant's explanation and suggested review focus

The accompanying Slovak explanation describes the draft's progression from context and drivers through the decision/diagram/coverage to alternatives, obligations, consequences and open questions. The assistant identifies the following review topics; these are **not user review comments**:

- Whether the module boundaries, ownership and diagram are clear, and the story mapping adequately demonstrates full coverage.
- Whether the rationale and documented disadvantages are sufficiently supported by the provisional comparison assumptions.
- Whether the proposed deletion/cancellation boundary is acceptable: block new send authorizations and cancel pending work, while previously authorized/provider-accepted delivery may still complete; physical cleanup remains unspecified.
- Whether the document's level of detail and structure are concise enough and make unresolved product decisions visible without pretending to resolve them.

No user feedback, requested revision, first-draft approval, or acceptance of the detailed policies has been received. The two Task 1 understanding-check questions remain unanswered. Pause for the user's review before revising the ADR or beginning Task 3.

## Entry 2 — User requests ADR v2: policy status and deletion states (2026-10-27)

### Actual user feedback and requested revision

The user requested v2 while retaining the selected modular-monolith direction and status **Proposed**. They identified that v1's implementation-obligations table mixed technical safeguards and proposed product semantics. They asked for a concise distinction between selected architecture, required correctness/security safeguards, proposed policies needing confirmation, and unresolved product/integration choices. Authorization and reliable persistence must remain mandatory; duplicate-favorite behavior, cancellation semantics and open timing/delivery choices must not be misrepresented as explicit source requirements or newly approved decisions.

They requested a short calendar-deletion table for pending, claimed-but-not-authorized, already-authorized, and provider-accepted reminders. Claiming must be distinguished from final send authorization. The authoritative calendar-state check must prevent any new send authorization after deletion commits, while acknowledging that previously authorized or provider-accepted delivery may still complete. Logical deactivation can be atomic while physical dependent-record cleanup is separate; retention and physical deletion remain open.

The user requested preserving scope, rationale, disadvantages and assumptions, putting detailed algorithms in these notes if needed, updating the canonical ADR, creating an identical v2 snapshot, and leaving v1 unchanged. They requested a Slovak explanation and a pause before final acceptance or Task 3. This is revision feedback, not acceptance of the ADR or its product policies.

### Initial revision action

The assistant confirmed the planned distinctions, deletion-state table and preservation of v1. Before edits, the v1 snapshot SHA-256 was checked against the recorded original: `3a30222d067c26a97089a72f56c0709e596293837bdf19f3f480c38bbc3dc4f2`. No new answers to the Task 1 understanding-check questions were supplied.

### Changes made in v2

- Updated the canonical ADR revision to **v2**, retaining **Proposed**, the selected modular-monolith/durable-jobs/worker direction, the module/data/deployment structure and Mermaid diagram, all story mappings, alternative assessments, rationale, disadvantages and revisit criteria.
- Labeled the architectural direction as selected and local transaction boundaries as correctness safeguards. Replaced the mixed implementation-obligations table with explicit **Required safeguard**, **Proposed policy — confirm**, and **Unresolved choice** labels. The selected architecture is described in the preceding Decision section rather than repeated as another table row.
- Required authorization, private-data ownership checks, reliable local persistence, command idempotency and worker recovery remain obligations. Their mechanisms are architectural safeguards, not claims that the source file specified each one.
- Moved the one-favorite-per-user/recipe rule and repeated add/remove responses into a proposed-policy row, explicitly noting that stories 12–14 do not specify duplicate semantics. Replaying the same command safely remains distinct from deciding the result of separate intentional favorite commands.
- Centralized unresolved product, integration and implementation choices in the same status table and removed the duplicative standalone open-decisions list. Recipe source, chatbot implementation, reminder channel/timing, physical deletion/retention, stack, hosting, workload and team/cloud expertise remain unsettled.
- Added the four-row deletion-state table requested by the user. It distinguishes pending, claimed-but-not-authorized, already-authorized, and provider-accepted work at deletion commit. The claim is a reservation, not permission to send. The cancellation boundary is labeled as a proposed product policy, while coordination of final authorization with deletion is mandatory for correctness.
- Made the invariant explicit: no new send authorization, including one for a retry, may succeed after deletion commits. An attempt authorized earlier may still complete, and provider acceptance cannot be reliably retracted by local cancellation. No exactly-once external-delivery guarantee was added.
- Clarified atomic logical deactivation versus separate batched physical cleanup. Pending work becomes ineligible through authoritative inactive state even before dependent records are cleaned up. Retention, physical deletion and recovery policies remain open.

### Supporting concurrency explanation (kept out of the ADR)

One possible implementation uses a common per-calendar coordination gate within local datastore transactions (for example, the same calendar-row lock). This is explanatory design detail, not a selected database product or a newly approved product policy:

1. A worker claims a job using a bounded lease and attempt identity. Claiming alone grants no delivery permission.
2. Final authorization acquires the calendar coordination gate, verifies current active calendar state, the job's eligible state and current claim ownership, records authorization for that attempt, then commits. New event creation also checks active calendar state under the same coordination discipline.
3. Deletion acquires that same gate, commits logical deactivation and appropriate cancellation/cleanup intent, then releases it. Job rows need not all be rewritten before deactivation becomes effective. If authorization ordered first, its already-authorized attempt may finish; if deletion ordered first, authorization must fail. A stale read without transactional coordination cannot enforce this guarantee.
4. Provider calls take place outside the short database transaction. Authorization belongs to an attempt; a retry or replacement worker must obtain fresh authorization rather than reuse a permanent permission. Expired claim ownership must not allow an old worker to overwrite newer local state. An external outcome can still be ambiguous after a crash, so provider deduplication/status lookup remains conditional on the selected integration.
5. Cleanup may later remove dependent records, but it must not erase authoritative cancellation state while stale work can still need it. This requirement does not choose a retention duration or physical deletion policy.

### Artifacts, verification and remaining review

- Canonical v2: [ADR-001](../adr/ADR-001-recipecove-architecture.md).
- Identical v2 snapshot: [ADR-001-v2](adr_revisions/ADR-001-v2.md).
- Preserved original snapshot: [ADR-001-v1](adr_revisions/ADR-001-v1.md).

`cmp` confirmed byte identity between canonical v2 and its snapshot; both SHA-256 values are `6762377db063e11cfc9ab58b7d67f0d846378abf6456b38dbe9b3b6f249e3992`. The v1 hash is unchanged at `3a30222d067c26a97089a72f56c0709e596293837bdf19f3f480c38bbc3dc4f2`. Reviewed the v1/v2 diff; checked Proposed/v2 metadata, story IDs 1–14 and chatbot coverage, policy labels, all four reminder-state labels and canonical ADR file links. No rendered Mermaid or application-test result is claimed.

The accompanying Slovak explanation highlights that v2 makes the authority/status of statements visible, separates claim from delivery authorization, and distinguishes logical deactivation from physical cleanup while preserving the known in-flight-delivery limitation. These are the assistant's explanations of the revision, not additional user feedback.

V2 still awaits user review and final acceptance. Duplicate-favorite semantics and the proposed cancellation policy still require confirmation; unresolved choices in the ADR remain open. The two Task 1 understanding-check questions remain unanswered. No user approval or additional policy decision has been invented, and Task 3 has not begun. Pause after presenting v2 as requested.

## Entry 3 — Second review-driven revision: v3 diagram and reconsideration criteria (2026-10-28)

### Actual feedback and request

The user reported checking the archive and finding the v2 changes correctly implemented: statement statuses were separated, all four reminder states were described, v1 was unchanged, and v2 matched the canonical ADR. This confirms those revision checks, not final ADR acceptance or approval of the proposed product policies.

The user requested v3 as the second substantive review-driven revision, retaining the modular-monolith decision, **Proposed** status, v2 policy-status distinctions and deletion guarantees. They requested clearer diagram boundaries for the backend release, web/worker roles, local module interfaces and module-owned shared persistence; explicit Google identity integration; and a legend distinguishing network, local and persistence interactions without implying an external LLM.

They requested replacing the reconsideration paragraph with an actionable table of observable evidence/new requirements, the architectural limitation exposed, and responses to investigate. It must cover resource/workload contention, independent team releases, stronger availability/security isolation and validated hosting/operating evidence. Responses should include optimization or limited extraction where appropriate, without invented thresholds, measurements, team characteristics or cost rankings.

They also requested a concise consistency/readability review, preservation of all 14 stories and the chatbot, actual canonical-relative-link validation, renderer inspection if available (otherwise source inspection only), an identical v3 snapshot, unchanged v1/v2 snapshots, and a pause before final acceptance or Task 3. The English revision request was repeated after tool/context interruptions; it is treated as the same revision request, not a third review iteration.

### Initial access and renderer checks

Initial shell invocations failed to start with a `No such file or directory` execution error, and a subsequent tool call was aborted. After the request was repeated, `/bin/bash` successfully accessed the actual assignment directory; the canonical v2 and current discussion notes were then read. No verification is inferred from the failed attempts.

Before editing, the actual snapshot hashes matched the previously recorded originals: v1 `3a30222d067c26a97089a72f56c0709e596293837bdf19f3f480c38bbc3dc4f2`; v2 `6762377db063e11cfc9ab58b7d67f0d846378abf6456b38dbe9b3b6f249e3992`.

`command -v` found none of `mmdc`, `mermaid`, `mermaid-cli`, `node`, `nodejs`, `chromium`, `chromium-browser`, `google-chrome`, `firefox`, `playwright`, `bun`, or `deno` on PATH. The repository file search found no Mermaid/Playwright renderer setup outside excluded dependency/git directories. A local renderer was therefore not available through these checks; diagram verification for this revision will be explicitly limited to source inspection.

### Changes made in v3

- Set revision **v3** and added a last-revised date of 2026-10-28 while retaining the original record date and **Proposed** status. Shortened the repeated opening review disclaimer and standardized the Calendar and Reminders module name in the deployment explanation.
- Replaced the diagram with an explicit backend deployment/version boundary containing separate web and worker processes. The worker has a local job runner calling Calendar and Reminders code from the same release, visibly distinct from an independently deployed reminder service.
- Added Google outside the backend as the required identity provider. Browser/API and Google exchanges are labeled HTTPS; dashed arrows show local module-interface calls; thick arrows show access to shared persistence through owning-module code. The legend explains that persistence transport depends on hosting and that a release boundary does not imply one physical host. The duplicated Calendar and Reminders boxes represent the same code in different processes, coordinated by durable persisted jobs, not a web-to-worker RPC.
- Kept recipe-source, chatbot and delivery integrations omitted while unresolved; explicitly stated that an external LLM is not assumed.
- Replaced the reconsideration paragraph with five evidence/limitation/response rows: shared-resource contention; independently demanding Catalog/Recommendations workloads; confirmed independent team releases; stronger availability/security isolation requirements; and validated hosting/operating evidence. Responses include optimization, role tuning, managed hosting and selective extraction rather than automatic whole-system migration. All evidence is hypothetical/future, not an invented observation or measured cost ranking.
- Retained the existing decision drivers, all 14 story IDs and chatbot coverage, concrete alternative assessments, policy-status table, deletion-state section and positive/negative consequences. The architecture selection is unchanged. In particular, authorization and durable persistence remain safeguards; favorite/cancellation semantics remain proposed; retention and integration choices stay open.

### Verification actually performed

- Read the canonical v2 and inspected the v2/v3 diff for readability, naming and consistency. Compared the drivers, requirement mapping, alternatives, safeguards/deletion and consequences sections programmatically with v2; those sections are unchanged.
- Checked **Proposed/v3** metadata and all story IDs 1–14 plus the chatbot.
- Resolved every relative file-link target from the actual canonical ADR directory and confirmed the files exist:
  - `../../Tasks/data/RecipeCove.txt`
  - `../baseline/task1_discussion.md`
  - `../baseline/task2_discussion.md`
- Inspected the Mermaid source: process/release nesting, required Google node, labeled HTTPS exchanges, local-interface/persistence arrow distinctions and absence of worker-to-web RPC. A basic source check counted three balanced subgraphs and checked the intended labels/edge types. **No Mermaid renderer/parser or rendered visual inspection was performed.** Layout remains unverified in rendered form.
- `cmp` confirmed that [canonical v3](../adr/ADR-001-recipecove-architecture.md) and [snapshot v3](adr_revisions/ADR-001-v3.md) are byte-identical. Both SHA-256 values are `8869835e4d1db763b6adad4aa8a222dc48be166a3aaf854e5fa0a71b330ab204`.
- Post-edit SHA-256 checks confirmed [v1](adr_revisions/ADR-001-v1.md) and [v2](adr_revisions/ADR-001-v2.md) remain unchanged at their recorded hashes above. No application tests or measured performance/cost checks are claimed for this documentation revision.

### Explanation and remaining review issues

The accompanying Slovak explanation highlights the diagram's clearer distinction between release, processes, calls and persistence, and the reconsideration table's link from evidence to a bounded investigation. It reports source inspection only and the actual link/snapshot checks.

V3 awaits final user review; neither the ADR nor proposed product policies have final acceptance. Duplicate-favorite behavior, cancellation semantics and the existing unresolved timing, channel, source, chatbot, deletion/retention, stack and hosting choices remain open. A rendered layout review is still unavailable in this environment. The two Task 1 understanding-check questions remain unanswered. No Task 3 work has begun; pause after presenting v3.

## Entry 4 — Explicit final acceptance and baseline finalization (2026-10-28)

The user explicitly accepted **ADR-001 v3 as the final architecture decision document for this assignment**. They expressly stated that proposed product policies and unresolved choices remain open and that document acceptance must not silently approve them. This is final document acceptance, unlike the earlier direction selection and scoped confirmation of v2 changes.

They requested changing the canonical ADR to **Accepted**, adjusting review wording, preserving v1/v2/v3 unchanged, and saving an identical accepted copy at `solution/baseline/adr_revisions/ADR-001-final.md`. They requested freezing the finalized baseline discussions/snapshots for later comparison and preserving the source-only Mermaid verification limitation.

The assistant updated status and acceptance wording without changing the selected architecture, traceability, diagram, technical safeguards, proposed-policy labels, open choices, deletion guarantees or alternatives. The original v3 draft snapshot remains Proposed; the accepted final copy records the actual acceptance. The two earlier understanding-check questions remain unanswered.

The user also authorized the skill-creation part of Task 3, based on the actual assignment, both discussion records and ADR revisions, with a repository-local architecture/ADR workflow skill and a separate creation record. They explicitly prohibited simulating a new session or drawing comparison conclusions before a genuine replay. That subsequent work is recorded separately in `solution/task3/skill_creation.md`, not appended to the frozen baseline.

### Finalization verification and baseline closure

The canonical ADR is **Accepted** and byte-identical to [ADR-001-final](adr_revisions/ADR-001-final.md), confirmed by `cmp`. The accepted final snapshot SHA-256 is `4c886aa5dfb8f9bc78888f6b14df949fe5bd978076812d219c4f517ddbfd8a07`. The original v1/v2/v3 hashes remain unchanged at their previously recorded values. Canonical relative file links resolve in the actual repository; the diagram and deletion-state section are unchanged from v3.

Mermaid verification remains **source inspection only**; no rendered diagram, parser validation or visual layout inspection is claimed. No new performance measurements, cost conclusions, policy confirmations or understanding-check answers have been supplied.

**Task 2 is complete for this baseline:** the final ADR was explicitly accepted after two actual review-driven revisions. Proposed product policies and unresolved choices remain open. This closes the baseline record; preserve it, the Task 1 discussion and all snapshots unchanged during skill creation and the later replay. Integrity hashes are recorded separately under Task 3 to avoid further changes to these finalized discussions.
