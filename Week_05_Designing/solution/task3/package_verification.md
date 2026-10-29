# Submission verification

The deliverable is `RecipeCove_submission.zip`, with `SUBMISSION.md`, `Tasks/`, `.agents/` and `solution/` directly at its root. The ZIP uses an explicit allowlist: 27 regular files and 13 directory entries, including the hidden skill directory. It contains the four assigned inputs, original/replay records and revisions, skill, creation evidence, comparison, guide and integrity records. No nested archive, duplicate transport tree, cache, credential file or unrelated project brief is included.

## Checks performed

| Check | Observed result |
| --- | --- |
| Canonical acceptance and scope | Original and replay canonical ADRs are Accepted; proposed policies/open choices remain open. Original accepted record is unchanged. Replay acceptance changes metadata/status/review wording and final-snapshot navigation only. |
| Accepted snapshots | Original canonical equals baseline final snapshot; replay canonical equals replay final snapshot, byte for byte. Replay final SHA-256: `5188820b28ac8cc26abf8b8a6f5cfc2db2fcb5a73d2c4c231d49818f5bd38a79`. |
| Historical preservation | Both sets of v1/v2/v3 retain Proposed status and their recorded hashes. A pre-change manifest checked 20 protected source, skill, baseline and historical-replay files unchanged; the original seven-entry baseline manifest also passed. Replay discussion's pre-acceptance prefix was preserved. |
| Acceptance did not change substantive architecture | Ownership/diagram, traceability, safeguards, reminder table, policy/question tables, decision matrix and reconsideration content match replay v3. |
| Requirement coverage | Original module mapping contains all stories 1–14 plus chatbot; replay contains all US-01–14 and PR-01–04. Source meaning was inspected in the comparison. Identifier checks are not behavioral validation. |
| ZIP readability/content | With `zip`/`unzip` executables unavailable, available `IO::Compress::Zip` created the archive and `IO::Uncompress::Unzip` read it in strict mode. Every member was extracted; unsafe/duplicate/unexpected names were rejected and every extracted file matched its source bytes. |
| Integrity manifests in extracted copy | The [submission manifest](submission_manifest.sha256) verifies 26 content files; it excludes itself to avoid self-reference. The [original manifest](baseline_manifest.sha256) verifies all seven original frozen files. |
| Hidden skill | `.agents/` is an explicit ZIP directory entry; extracted `.agents/skills/requirements-to-adr/SKILL.md` is present and retains SHA-256 `6a3f111469a5a553810cf968533427610774de0c57e70507348d83f3253995fb`. All current skill-directory files are included. |
| Extracted navigation | Local Markdown targets from the submission guide, both canonical ADRs and the remaining packaged Markdown files resolve. A linked heading was checked against heading text. Historical snapshot exceptions are interpreted as explained below. External website targets were not revalidated. |

Checks were first run on a candidate package, then rerun after updating completion/verification records and regenerating the content manifest and release ZIP. Temporary verifier scripts/extracted copies live outside the archive. The [comparison](comparison.md) uses actual review requests and consistent `wc -w -c` document sizes, not note-heading counts as turns.

## Historical relative-link convention

The four original snapshots in `solution/baseline/adr_revisions/` preserve canonical document bytes originally authored for `solution/adr/`. Their 23 internal file-link references need that **original canonical origin**. For example, `../../Tasks/data/RecipeCove.txt` resolves from `solution/adr/`, but not from the snapshot directory. The navigation check verified those targets from the canonical origin; it did not claim they work as ordinary snapshot-directory-relative links.

No historical snapshot was rewritten and no duplicate transport folder was added to disguise this convention. Use the guide's original canonical ADR for ordinary navigation. Replay snapshots are at the same relative depth as their canonical document, so their links resolve normally.

## Verification limits

Mermaid remains **source inspection only**: no renderer/parser or rendered visual review was available. No RecipeCove implementation, behavioral effectiveness, performance or cost validation was performed. Comparable run timing, tokens, cost and exact model settings are unavailable; no speed/token saving is established. Skill creation's unavailable Python validator and recorded fallback static checks remain historical facts, not a newly successful validator run. Archive/hash/link checks establish packaging consistency, not architectural quality or product-policy approval.
