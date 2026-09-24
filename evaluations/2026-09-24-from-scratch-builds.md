# From-scratch builds vs the real projects: 2026-09-24

Also covers the re-run of vercel/ms #284 after the intake/QA fixes (commit 67b6b58).

## Method

For each project, the pipeline got only the upstream README, in an empty git repo, with the instruction to implement it without using the real package. It ran unattended (the orchestrator logged the questions it would have asked and its own calls). Then the result was scored against the real project in two ways:

- **pretty-bytes (JavaScript):** upstream's own `test.js`, run through a stand-in for AVA that counts every assertion instead of stopping at a test's first failure. Upstream scores 309/309 on it.
- **python-dotenv (Python):** (1) differential testing: 121 input/mode combinations (the 55 `.env` inputs from upstream's parser tests, plus 22 expansion cases written from the README, each through `dotenv_values` and `load_dotenv` with and without override), compared output for output; (2) upstream's `test_main.py` and `test_cli.py`, with imports of internal modules made optional. Upstream passes 173 of these here.

Every failure was then classified by whether the README actually specifies the behaviour.

Caveat: both libraries are well known, so the model may recall parts of them. The results below suggest it mostly didn't; it followed the README where upstream's real behaviour differs from it.

## Results

| | pretty-bytes | python-dotenv |
|---|---|---|
| Features / criteria | 5 / 31 | 6 / 71 |
| QA rounds (fails) | 11 (7) | 8 (2) |
| Time / cost | 75 min / $14.48 | 51 min / $9.89 |
| Source size vs upstream | 696 vs 182 lines (3.8×) | 1366 vs 1119 lines (1.2×) |
| Upstream tests | **228/309 assertions (74%)**, 8/20 tests | **102/173 tests (59%)** |
| Differential match | n/a | **110/121 (91%)** |

### Where the builds differ from upstream

**pretty-bytes: 81 failed assertions. None contradict a clear README statement.**
- 57: *rounding carries into the next unit.* Upstream shows 999,999 B as "1 MB"; ours shows "1000 kB". The README never mentions this. Upstream's tests for it are named "rounding carries across every … boundary", which suggests it's a later fix the README never picked up.
- 18: *integer digits.* The README says "round to 3 significant digits". Ours does that literally (1001 B → "1000 B", 82,718,100 YB → "82,700,000 YB"). Upstream keeps all integer digits. Here upstream disagrees with its own README.
- 6: *error message wording.* The README says only "throws a TypeError". Ours throws a TypeError with a different message.

**python-dotenv: 71 failed upstream tests. Only 4 are README-documented behaviour.**
- 4 real bugs: a comment after an empty value (`a= # note` should give `a=""`; ours gives `"# note"`). The README says "values can be followed by a comment".
- 1 ambiguous: `${VAR}` inside single quotes. Upstream expands it; ours doesn't (Bash semantics). The README says only "POSIX variable expansion".
- 42 undocumented conventions: how `set_key` quotes values when writing (upstream uses single quotes, ours double), the CLI `--quote` / `--export` / `--format shell` flags, CLI messages and exit codes, and which values `PYTHON_DOTENV_DISABLED` accepts beyond `1`.
- 24 undocumented API surface or internals: `encoding=` and `follow_symlinks=` parameters, log messages, the internal `DotEnv` class.
- The differential run also found: a leading byte-order mark drops the first line (common with files saved on Windows), and unusual keys like `[` are rejected. Neither is in the README; the BOM one is a genuine robustness bug.
- `dotenv run` with a missing command prints a Python traceback instead of an error message.

### vercel/ms #284 re-run (after the intake/QA fixes)

Correct this time. `parse()` accepts exponent notation, `format()` is unchanged, and the length limit stays at 100. Huge, tiny, negative and ordinary values all round-trip; `1e`, `e3` and `1e+` are still rejected; 189/189 tests pass. Intake wrote 11 criteria covering both ends of the problem, QA's regression sweep compared old and new code, and `delivery/` stayed out of the commit. User-visible change, flagged by the run: `ms('1e3')` now returns 1000. One new gap: the repo's formatter changed a file after commit, leaving the tree dirty (fixed in 46d7bd5).

## What this says about the pipeline

1. **It builds what the spec says, faithfully. The spec is the ceiling.** Almost every divergence traces to something the README doesn't say, or says differently from how upstream behaves. Intake did catch one README contradiction (the fixedWidth examples) and logged its reading. It did not flag the obvious product question: "should 999,999 B read as 1000 kB?"
2. **QA has swung from too lenient to too strict, and aimed at the wrong things.** After the ms lesson ("try the mirror case"), QA on pretty-bytes spent seven failed rounds on bigint-vs-number agreement above 2^53 and on whether 1e24 is exactly representable. None of that is in the README, and it made the code 3.8× the size of upstream's. Meanwhile it never flagged "1000 kB", which any user would see. It chases numeric edge cases, not what a user sees.
3. **The attempt cap is soft when unattended.** The orchestrator accepted F-001 after 3 failed attempts, and allowed F-004 a 4th, logging both decisions. The reasoning was sound, but the cap only bites when a human is present.
4. **Cost scales with QA strictness, not project size.** pretty-bytes is the smaller library and cost 46% more than dotenv, almost entirely in QA fail loops.

## Changes this points to

- **QA verdicts:** FAIL only for a written criterion not met, or something that worked before and now doesn't. Anything else QA finds goes under "Notes", which don't trigger a rebuild. Skip the old-vs-new comparison on new projects.
- **QA priorities:** check what a user sees first (the first examples in the README, typical inputs, how output reads), before exotic numeric limits.
- **Intake on specs:** for every rule it turns into a criterion, check at least one ordinary input where the rule gives a strange-looking result (3 significant digits applied to 1001), and list those as open questions.
- **A hard ceiling on attempts** that even unattended runs respect (e.g. stop after 4 and mark the feature incomplete), so cost can't run away.
