# Assessment by laguna-s-2.1

# Week 03 Prompting
- Awarded: 5b out of 5b
- Commentary: All four tasks are fully and rigorously completed. The student selected three original prompting frameworks (ICIO, RTF, CO-STAR) from frompting.com, applied them through an IDE coding agent to 155 text-to-SQL questions, measured timing, proposed and implemented a complementary Balanced Row F1 metric, and ran paired statistical tests. The work is transparent about limitations (identical SQL output across prompts, ID mismatch between references and database, end-to-end rather than pure inference timing, single run). Deliverables include reports, data files, reproducible Python (stdlib-only), and figures.

## Task 1
- Awarded: 1b   (max 1b)
- Commentary: Three frameworks (ICIO, RTF, CO-STAR) were chosen from frompting.com; ROSES and zero-shot were explicitly avoided. Each prompt uses two few-shot demonstrations, the same schema, shared interpretation rules, and an identical {{question}} substitution contract. prompts.json stores all three templates with ids, sources and metadata; icio_v1.txt, rtf_v1.txt, co_star_v1.txt are readable variants. The report explains why each framework was chosen, where it was found, and what is expected. Demonstrations use invented cities and were validated on a synthetic database. This satisfies the output requirements.

## Task 2
- Awarded: 1b   (max 1b)
- Commentary: Three independent Codex chats (GPT-6.1 Sol / Medium) were run, one session per prompt, on all 155 questions. Predictions are stored as CSVs with per-row question IDs and preserved question text; inference/agent timing was measured (ICIO 320.25s, RTF 264.46s, CO-STAR 176.22s). Evaluation reused the instructor's evaluator via a patched CLI (schema header skipped, predictions passed as arguments) without altering data or references. A brief report compares accuracy (43/155 for all three) with accuracy and agent-time visualizations. The student transparently reports that only end-to-end agent time was captured, not pure inference time, and documents the identical-SQL finding and the reference ID mismatch.

## Task 3
- Awarded: 1b   (max 1b)
- Commentary: The student proposed a novel Balanced Row F1 (BRF1): multiset row-F1 averaged over empty-reference and non-empty-reference strata, complementing (not replacing) exact execution accuracy. The metric is argued as applicable and invention-worthy, handles edge cases (both empty, one empty, errors/failures) correctly, and is explicitly noted not to remap or rename IDs. Implementation lives in metrics.py (stdlib-only, no hard-coded counts), scores were computed for all three prompts, and produce reproduce_scores.py recomputes them from Task 2 results. The report compares the metric values for the three prompts and shows the components (empty F1 100%, nonempty F1 ~0.0003%, BRF1 ~50.0%) together with a visualization.

## Task 4
- Awarded: 2b   (max 2b)
- Commentary: A detailed report reiterates the Task 2/3 comparison with summary tables (accuracy, BRF1 components, agent time), references graphs, and runs paired statistical tests. Because all three prompts produced identical SQL, McNemar and stratified paired permutation tests return p=1.0 (Holm-adjusted) with [0,0] confidence intervals; the student correctly states this means no observed difference, not equivalence. The report considers the prompts, the model, and the coding agent as factors, explains timing differences, discusses the reference ID/STRATA mismatch, and outlines scope/limitations and a follow-up experiment. methodology_sk.md documents the planned methods, and paired_statistics.py (stdlib-only) plus statistics.json make the analysis reproducible.

<!--
NOTES FOR THE GRADER (delete this comment block in the output file):
- Max points: Task 1 = 1b, Task 2 = 1b, Task 3 = 1b, Task 4 = 2b. Total = 5b.
- The overall "Awarded" score MUST equal the sum of the four task scores.
- Half-points (0.5b steps) are allowed.
- Replace <model_name> with your model label.
- Keep the structure and headings exactly as above.
-->
