# Framework changelog

Every accepted change to a skill or to `references/framework.md`, written by the `evolve` skill's `distill` mode, with the ledger evidence that justified it. app-architect skims this at the start of a consultation so past lessons actually reach the next project.

Only `distill` writes here, and only the maintainer runs `distill` against the shared repo. Contributors feed observations via `ledger/` pull requests; the maintainer curates changes here.

Format:

```markdown
## YYYY-MM-DD — <file> §<section>: <one-line change>

- **Lesson:** <the pattern that recurred>
- **From ledger:** <date> (<project>), <date> (<project>)
- **Change:** <what was reworded / added / removed, and why this wording>
- **Prevents:** <the failure mode>
```

---

## 2026-09-07 — framework.md §5: check phase clarifications against the goal and architecture assumptions

- **Lesson:** A clarification made after the proposal is approved (or a mid-build pivot) can quietly narrow the spec's stated goal or invalidate an architecture assumption, and get folded into the phase with nobody checking it back against either.
- **From ledger:** 2026-09-06 (Local PDF RAG) — a Phase 4 clarification scoped `expected_answer` rows to "reference only", so the shipped eval conforms to the spec yet cannot score the answer correctness that §1 calls the point of the project. 2026-09-07 (Anime clip generator) — Phase 0's clarify pass chose a local-MPS validation environment the architecture (hosted ZeroGPU) never assumed and the laptop couldn't run; a mid-build LLM-backend swap to HF Inference Providers went in without re-checking the free-tier capacity the original Gemini/Groq choice had been sized against.
- **Change:** Added one paragraph to §5's "Clarify before each phase": before folding a clarification in, check it against §1's Goal and any architecture assumption it touches; a clarification that narrows the goal, changes the assumed environment, or swaps a plan-sized stack choice is a flag-back to app-architect, not a phase detail to absorb.
- **Prevents:** Shipping something that conforms to the spec but no longer serves its stated purpose; and losing hours to a phase decision that quietly contradicted the approved architecture.

## 2026-09-07 — framework.md §5: MVP validation must be load-bearing (enough cases, right environment)

- **Lesson:** The MVP-notebook pass can return a false "validated" — either from too few test cases to expose a failure that only shows up systematically, or from running somewhere that can't exercise the real workload, so it validates the environment instead of the idea.
- **From ledger:** 2026-09-06 (Local PDF RAG) — "validated" on 3 hand-picked questions; the 20-row golden set later showed a systematic ~15% false-refusal rate the MVP never had the signal to catch. 2026-09-07 (Anime clip generator) — the MVP notebook was run on a GPU-less 16 GB laptop that could not run video diffusion at any useful scale; ~2h went to hardware limits before the real signal came from the actual deploy target.
- **Change:** Added one paragraph to §5's "MVP first: validate before you scaffold", right after the "only question the notebook has to answer" line: names the two false-pass modes (too few cases / wrong environment) and says to run the notebook where the app will actually run, or mark the result provisional. Kept it explanatory, no MUST; dropped project-specific numbers per maintainer edit.
- **Prevents:** Scaffolding a full build on an MVP result that looked green but never tested the thing that later breaks.

## 2026-09-06 — bootstrap

`evolve` skill added to the framework: `capture` (add a per-project file under `ledger/`) and `distill` (promote lessons recurring across 2+ projects into approved diffs against the skills or framework.md). Supporting changes: framework.md §3b defines the **Deviations from spec** section; app-developer and release-qa now record divergences there during Build and Verify. No ledger evidence — this is the mechanism, not a lesson from it.

---

## Rejected

`distill` proposals that were considered and turned down, so they aren't re-proposed unchanged. One line each: date, the proposed change, why it was rejected.

_(none yet)_
