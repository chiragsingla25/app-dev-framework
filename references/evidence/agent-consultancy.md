# Evidence: agent-consultancy (Sep–Oct 2026)

agent-consultancy (`~/projects/agent-consultancy`) was a second build of this lifecycle: an orchestrator skill running intake, builder and QA subagents, with a git commit per feature. It was researched and built separately from this framework. This file records what its runs showed, so the changes imported from it (CHANGELOG 2026-10-10) can be checked against evidence.

The two original evaluation write-ups are copied alongside: `agent-consultancy-open-source-runs.md` and `agent-consultancy-from-scratch-builds.md`.

## Measured trials (24 Sep)

| Trial | Result | Lesson |
|---|---|---|
| humanize #379 (Python bug fix) | Correct, 6 min, $1.19 | Process held |
| vercel/ms #284 (TS bug fix) | **Regression shipped**: fixed huge numbers, crashed on tiny ones | Criteria covered the example, not the bug's class; QA's "unusual input" landed on the same side → §3c, reviewer's mirror case |
| ms #284 re-run after fixes | Correct, 189/189 tests, regression sweep compared old vs new | Class-of-bug criteria + old-vs-new sweep work → §3c, §6 |
| pretty-bytes from README only | 74% of upstream assertions; 11 QA rounds, 7 fails; code 3.8× upstream | QA too strict on unspecified numeric edges, missed "1000 kB" a user sees → FAIL only for criteria/regressions, user-visible first |
| python-dotenv from README only | 59% of upstream tests, 91% differential match; 4 real README-documented bugs | The spec is the ceiling: it builds what the README says → strange-result check (§3c) |

Cost tracked QA strictness, not project size: pretty-bytes is the smaller library but cost 46% more than dotenv, almost all of it in QA fail loops.

## Real use: 11 runs on ai-checkpoint (7–9 Oct)

- 30 features and 277 acceptance criteria across 11 runs. 34 per-feature QA reports, 13 FAIL, 2 OBJECTION.
- QA wrote ~308 KB of reports against ~60 KB of build logs. The user's own experience: QA took longer than the coding.
- **QA was worth having.** Nearly every FAIL was a real bug the builder's own tests missed:
  - credentials in URL userinfo not redacted
  - CLI tracebacks on non-object JSON
  - stderr broken by an encoding change
  - stdin re-encoded (a regression against HEAD)
  - a byte-level change to a tool description
  - a metric under-reporting stale answers
  - dependencies silently mis-ordered on resumed saves
  - an empty plan getting the wrong error through the MCP path

  One FAIL was arguably over-strict: duck-typed input to an internal API.
- **What went wrong was cadence and authority, not QA's value:**
  - QA ran after every feature attempt.
  - The orchestrator made 6 rulings on disputed criteria itself across 3 runs, each marked "reported to Chirag".
  - It once edited code itself.
  - It committed `.DS_Store` files.
- **Lessons the consultancy wrote down but never applied:** its own 24 Sep evaluation listed "FAIL only for unmet criteria or regressions, everything else is Notes", "user-visible first" and "a hard attempt ceiling even unattended". None of these reached its QA prompt before the ai-checkpoint runs. That explains most of the slowness.

## What was imported, and what wasn't

Imported (each backed by the above): checkable criteria and `Verify:` lines per phase; bug-class criteria and strange-result checks; tests as the commit gate; user-visible change lists; person-only rulings on disputed criteria; once-per-milestone fresh-context review with test citation, regression sweep, FAIL discipline and a three-round cap; commit hygiene; an opt-in continuous mode.

Not imported: the standing orchestrator, stage registry and planner, separate intake role, per-feature QA loop and JSON run folders. They conflict with this framework's "no standing multi-agent team" decision, and the runs show their cost.
