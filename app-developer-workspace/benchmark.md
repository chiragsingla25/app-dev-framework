# app-developer skill — benchmark (iteration 1)

**Runs per configuration:** 1 (not 3 — bounded for cost; treat variance figures as indicative only)

## Summary

| Configuration | Pass rate | Avg time (s) | Avg tokens |
|---|---|---|---|
| with_skill | 100% | 679 | 80231 |
| without_skill | 25% | 1564 | 85150 |
| **delta** | **+0.75** | **-884.9** | **-4920** |

## Per-eval

### eval 0 — continue-pdf-rag-spec (8 assertions)
- with_skill: 8/8 passed
- without_skill: 4/8 passed

### eval 1 — no-spec-flag-back (4 assertions)
- with_skill: 4/4 passed
- without_skill: 0/4 passed

## Notes
- Both configurations pass the stack-fidelity and spec-reading assertions equally on eval 0 (continue-pdf-rag-spec) — these don't discriminate skill value on their own, since the spec itself is detailed enough that a capable baseline follows it too.
- The real separation on eval 0 is process discipline: with_skill stopped at a checkpoint, wrote tests, and left final certification to release-qa; without_skill built the entire spec (including the UI) in one pass with no check-in and no unit tests, self-certifying the whole thing as verified and complete.
- Eval 1 (no-spec-flag-back) is the sharpest signal: with_skill scores 4/4 by refusing to build and handing back to app-architect, exactly as the skill instructs; without_skill scores 0/4, treating 'start building' as license to invent a stack and ship a full app with no spec at all — the exact failure mode the skill exists to prevent.
- with_skill used less than half the wall-clock time and slightly fewer tokens on average, mostly driven by eval 1's near-instant, correct refusal versus the baseline's multi-minute full build — 'do less, but the right amount' is cheaper as well as safer here.
- Only 1 run per configuration was executed (not the usual 3) to bound cost; the pass-rate gap on both evals is large enough (0.75 average delta) to be a meaningful signal even from a single run, but re-running with more samples would be needed before trusting the stddev/variance figures.