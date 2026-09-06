## 2026-09-06 — Local PDF RAG

- **Contributor:** singlachirag25@gmail.com
- **What it was:** Fully-local retrieval-augmented Q&A over a small set of text-based PDFs — a portfolio / interview piece optimised for a clean, readable pipeline and a visible evaluation story.
- **Stakes:** portfolio
- **Pattern:** single-retriever RAG (framework.md §7, row 3) — held up exactly as chosen. Deterministic ingest pipeline + retrieve-then-generate; no agent, no tool use, no dynamic routing. The LCEL chain stayed visible end to end; no working-around the pattern.
- **Stack:** LangChain 1.x (LCEL, `langchain-ollama` / `langchain-chroma` / `langchain-huggingface`), PyMuPDF loader, `BAAI/bge-small-en-v1.5` local embeddings, persistent Chroma, Ollama `llama3.2:3b` for generation *and* the faithfulness judge, Streamlit UI, hand-rolled golden-JSONL eval, local-only deploy (no Docker, no host). Finalised stack fit; nothing got replaced.
- **Spec:** `specs/2026-09-06-local-pdf-rag.md`. "Deviations from spec" section pasted verbatim below.

- **What diverged:**
  - [app-developer] The **Deviations from spec** section (framework.md §3b) was never opened during Build. release-qa created it and back-filled Verify findings; no per-phase build divergences were recorded while they were fresh, so any that occurred are lost. Retro confirms divergences did happen — "things diverged, not written down." Evidence: spec Deviations bullet 1; retro Q1.
  - [framework.md §3b] Nothing in the phase-gate loop (§3a / §5) forces the Deviations section to be touched. A phase can pass its hard gate — "report what's built + verified, stop for go-ahead" — with the section untouched, and it only surfaced here because a separate fresh-context Verify pass existed to catch it. The obligation is stated in §3b but has no checkpoint carrying it. Evidence: spec Deviations bullet 1; §3a phase-gate checklist has no deviations line.
  - [app-architect] "Visible evaluation story" is named as the project's core purpose (spec §1) but left abstract — the spec never says what the eval must be able to *answer*. A Phase 4 clarification then scoped `expected_answer` rows to "reference/documentation only," so the shipped eval conforms to the spec yet cannot score answer correctness — the retrieval metric only checks the expected file is in top-k, and the faithfulness judge scores a grounded refusal as 1.0. The stated point of the project is unmet *while conforming to spec*. Evidence: spec §1 Purpose vs. Phase 4 clarifications vs. Deviations bullet 2; retro Q2/Q4 — "should've been nailed in the spec," "define 'evaluation story' concretely."
  - [app-architect] Model feasibility check was too shallow. Spec §7 open question asked to "confirm `llama3.2:3b` gives usable answers"; the MVP notebook confirmed it on 3 hand-picked questions and declared "core pattern validated." The 20-row golden set later exposed a systematic ~15% false-refusal rate on answerable questions (golden rows 6, 11, 17 return the literal `IDK` string every run despite hit-rate 1.00 and the answer being in the corpus). 3 questions was not enough signal to clear a model as feasible. Evidence: spec §7, Phase 0 clarifications, Deviations bullet 3.
  - [app-architect] The single sanctioned Phase 4 tuning pass was gated only on retrieval hit-rate < ~0.8. Retrieval scored a perfect 1.00, so the trigger never fired — even though faithfulness sat at 0.76 and ~15% of answerable questions were being refused. The one tuning lever the plan permitted was keyed to the metric that was already fine; the refusal problem had no path to a fix and shipped as a known limitation. Evidence: Phase 4 checkpoint text; Deviations bullets 3 & 4.
  - [release-qa] Faithfulness judge uses the *same* 3B Ollama model that generates the answers. Two runs at temperature 0 produced different per-row scores; a verifiably-correct answer (golden row 1) scored 0.00 in one run and was unflagged in another; both runs hit an aggregate 0.76 by coincidence. README presents "0.76" as a stable baseline without noting run-to-run variance. framework.md §12 lists judge calibration as deliberately out of scope so this conforms — but the self-judging circularity was never surfaced as a risk at intake, and the README's baseline table over-claims stability. Evidence: spec §2 stack (Eval row), Deviations bullet 4, README "Known rough edges."
  - [cross-cutting] Verify worked. Every gap above was caught and recorded by release-qa reading the diff against the spec with fresh context. The process failure was upstream — an abstract purpose in the spec and no Build-time deviation logging — not in the Verify layer, which did its job.
  - [not diverged — process held] CLAUDE.md stayed at 64 lines (budget ~150), every line load-bearing. The per-phase clarify gate (§3a / §5) was followed and its outputs folded visibly into the spec as dated "Phase N clarifications" blocks. Deployment target (local-only) was chosen at spec time and correctly matched the app's shape — Ollama can't run on HF Spaces free tier, so the §8 portfolio-RAG default was rightly overridden. Architecture selection (§7) was clean.

- **Retro notes (contributor's words):**
  - On the missing Deviations section: divergences happened during the phases, they just weren't written down — "recording them in the spec wasn't front-of-mind" while building.
  - On the eval scope: the correctness gap "should've been nailed in the spec" — app-architect should have defined concretely what "evaluation story" means before Phase 4, rather than leaving it abstract enough that the eval could conform to spec and still miss the point.
  - On redo: "nothing major to redo" — the build mostly went to plan; the issues that turned up were logged as known limitations rather than fixed.
  - On architect gaps: "define 'evaluation story' concretely" — the project's stated point was left abstract, so a phase-level clarification could quietly narrow it without anyone checking the narrowing against §1.

- **Would do differently:** In the spec, make "evaluation story" concrete — list the questions the eval must be able to answer (including "did it return the right answer?") — so a later phase clarification can't narrow it below the stated purpose without that showing up as a conflict. Open the Deviations-from-spec section at Phase 0 and treat "updated the section (or wrote 'None')" as part of each phase's hard gate, so it's a live artifact rather than a Verify-time reconstruction.

---

### Spec "Deviations from spec" section (verbatim)

- [build] The section itself was missing until the Verify pass — app-developer
  never opened a **Deviations from spec** section during the phased build
  (framework.md §3b requires it maintained during Build). release-qa created it
  and back-filled the Verify findings below. No per-phase build divergences were
  recorded at the time, so any that occurred are lost.
- [verify] **Eval scores no answer correctness.** `evals/golden_dataset.jsonl`
  carries an `expected_answer` per row but neither gated metric compares against
  it — retrieval hit-rate only checks the expected *file* is in top-k, and the
  faithfulness judge scores a grounded refusal as 1.0. Phase 4 clarifications
  explicitly made `expected_answer` "reference/documentation only", so the
  implementation conforms to the spec as written — but the spec's own §1 Purpose
  calls a "visible evaluation story" the point of the project, and the eval as
  built cannot answer "does it return the right answer?". Not resolved; recorded
  as a known limitation. Suggested fix: add a reference-match judge metric, or
  document the gap and promote the refusal count to a recorded/gated number.
- [verify] **~15% false-refusal rate on answerable questions.** Golden rows 6, 11
  and 17 (FISMA statutory authority; the four Implementation Tiers; the first
  tenet of zero trust) return the exact `IDK` string on every run, even though
  retrieval brings the correct document (hit-rate 1.00) and the answers are
  present in the sample corpus. `llama3.2:3b` is over-conservative. Neither gated
  metric surfaces this — a refusal *raises* the faithfulness mean. `run_eval.py`
  prints `refusals N/20` but the README baseline table omits it. The spec's
  Phase 4 tuning trigger is keyed to retrieval hit-rate < ~0.8, which never
  fires here, so the one sanctioned tuning pass went unspent. Not resolved.
- [verify] **Faithfulness judge is non-deterministic and mis-calibrated.** Two
  full runs at `temperature=0` produced different per-row scores; golden row 1
  (a verifiably correct answer, matches the query smoke test) scored 0.00 in one
  run and was unflagged in another. Both runs landed at an aggregate 0.76 by
  coincidence. README documents the 3B judge's paraphrase under-scoring but
  presents "0.76" as a stable baseline without noting run-to-run variance.
  Acknowledged as a known rough edge; acceptable for portfolio scope.
- [verify] **No CI gate.** framework.md §9 wants `--fail-under` wired into
  `.github/workflows/`; there is no `.github/` directory. Spec §6 explicitly
  defers this ("not set up now — portfolio scope"), so it conforms to the spec.
  The Ship stage's "wire or confirm the CI gate" cannot be completed; accepted
  given the local-only deploy target and no git remote.
- [verify] **Minor:** `scripts/check_env.py:44` imports `ollama`, which is not in
  the deliberately direct-deps-only `requirements.txt` (resolves transitively via
  `langchain-ollama`). `src/rag.py:104` `k = k or config.TOP_K` treats an
  explicit `k=0` as "unset". Neither affects a normal run.
