# Open-source trial runs: 2026-09-24

Two real open issues from public repos, each run through `/consultancy:deliver` unattended (headless `claude -p`; the orchestrator was told to record its approval-gate questions and its own calls in `decisions.md`). Afterwards each result was checked independently of the pipeline.

| | humanize #379 | vercel/ms #284 |
|---|---|---|
| Language | Python | TypeScript |
| Issue | `precisedelta()` drops the sign of negative timedeltas | `format()` emits scientific notation that `parse()` can't read back |
| Baseline tests | 744 passed | 167 passed |
| Plan chosen | intake → build → qa | intake → build → qa |
| Features / criteria | 1 / 10 | 1 / 7 |
| Attempts | 1, PASS | 1, PASS |
| Time / cost | 6 min / $1.19 | 8 min / $1.40 |
| Models used | claude-sonnet-5 throughout (headless default) | same |
| Tests after | 752 passed | 176 passed |
| Independent verdict | **Correct.** ruff, format and `mypy --strict` clean; odd inputs (−1 day+1s, −400 days, −1µs, −0.0) all right | **Regression shipped.** `format(1e-7)` and `format(5e-324)` now throw `RangeError` (they returned `"1e-7ms"` / `"5e-324ms"` before) |

## What worked

- **Sizing.** Both correctly came out as one feature. The intake splitting rule from the smoke runs held.
- **Decision records.** Both runs wrote clear `decisions.md` entries: what they'd have asked, what they chose, and why. The ms run explicitly reasoned about fixing `format()` rather than widening `parse()`'s input grammar.
- **QA independence.** In the ms run, QA noticed the builder had raised `parse()`'s length cap from 100 to 320 (a denial-of-service guard), and checked it on its own: it measured the worst-case regex time and verified the boundary. Independent timing agrees: worst case goes from about 160µs to 640µs, bounded.
- **Conventions.** The humanize fix followed the repo's own style (lazy imports, doctest examples in the docstring) and passed the project's own linters without being told to run them.

## What failed, and the fix each points to

1. **The spec only covered the reported example, not the class of bug.** The issue says "scientific notation"; intake wrote criteria for `Number.MAX_VALUE` only. JavaScript also uses scientific notation below 1e-6, and the new code crashes there. The 100% coverage report didn't catch it either.
   *Fix:* intake names the class of the bug and writes at least one criterion for each boundary of it (large and small, positive and negative), not just the example.
2. **QA's "try an input the builder didn't" landed on the same side of the bug.** It tried big values, empty strings and bogus units, but never tiny numbers.
   *Fix:* QA must try the inverse or mirror case of the reported input, and must re-check any code path the change touched for inputs it previously handled (a regression sweep, not just criterion checks).
3. **Run artifacts were committed into the target repo.** `delivery/` landed in both upstream-bound commits, which would pollute a pull request.
   *Fix:* a per-run choice: keep `delivery/` in the repo for your own projects, or put it outside the tree (or git-ignored) when contributing to someone else's.
4. **A security-relevant change went through with no security role.** The length cap exists because of a past ReDoS advisory against this library. QA happened to check it; nothing required it to.
   *Fix:* bring the phase-three security hook forward. A cheap per-commit scan that flags changes to input limits, validation and regexes would have made this mandatory.
5. **No model is pinned.** Headless runs defaulted to Sonnet for every role.
   *Fix:* pin a model per role in the agent frontmatter (strongest for intake and QA, where these misses happened).
6. **The public error message was changed as a side effect** ("between 1 and 99" became "between 1 and 320"). This is harmless here, but nobody flagged it as a user-visible change.
   *Fix:* the builder lists user-visible changes (output text, error messages, limits) in the build log, and the orchestrator shows them at close.

## Takeaway

One of two real fixes would have been safe to open as a pull request. The failure wasn't in building. It was upstream (the spec was too narrow) and in verification (QA's adversarial checks were too narrow). This matches the MAST finding that specification and verification failures dominate. The next changes belong in intake and QA, not the builder.
