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

## 2026-10-10 — framework.md §3a, §3b, §3c (new), §5, §6, §10; app-developer, release-qa, app-architect; new agents/reviewer.md and scripts/safe_commit.py: import what held up from agent-consultancy

- **Lesson:** Imported, not distilled. agent-consultancy was a separate orchestrator-and-subagents build of this same lifecycle, run on 11 ai-checkpoint deliveries (7–9 Oct) and 5 measured trials on open-source projects (24 Sep). Its evidence clears the two-project bar for each item below, but it comes from that system, not from this ledger. Full evidence: `references/evidence/agent-consultancy.md`.
- **From:** agent-consultancy evaluations 2026-09-24 (humanize #379, vercel/ms #284, pretty-bytes, python-dotenv); ai-checkpoint runs 2026-10-07 to 2026-10-09.
- **Change:**
  - §3a: every phase gets checkable acceptance criteria and a literal `Verify: run X → see Y` line (also IMPROVEMENTS 3.1). Opt-in continuous mode lets the person waive named phase gates; the default is unchanged.
  - §3b: disputed criteria are ruled on by the person and logged in Deviations; provisional rulings only in runs the person left unattended.
  - §3c (new): bug fixes specify the class, both edges, previously-correct inputs unchanged, and a strange-result check on each rule.
  - §5: the builder's tests (one per criterion, full suite green) gate each commit; user-visible side effects are listed; commits go through `scripts/safe_commit.py`.
  - §6 item 5: review happens once per milestone in a fresh-context `reviewer` agent. It runs the suite once, cites sound tests, looks at what a user sees first, sweeps for regressions against the old code, FAILs only on unmet criteria or regressions (the rest are Notes), and has a hard cap of three fix rounds.
- **Prevents:** a fix shipping a regression on the other edge of its own bug class (ms #284); review costing more than building (34 review reports at 5× the builders' text, 13 fails across 11 runs); review drifting into unspecified edge cases while missing what users see (pretty-bytes: 7 failed rounds, code 3.8× upstream); agents rewriting criteria themselves (6 self-made rulings across 3 runs); `.DS_Store` and run clutter landing in commits.
- **Deliberately not imported:** the standing orchestrator, stage registry and planner, separate intake role, per-feature QA, and JSON run folders. These conflict with "no standing multi-agent team" and "every added piece must pay its maintenance cost" (IMPROVEMENTS.md).

---

## 2026-09-06 — bootstrap

`evolve` skill added to the framework: `capture` (add a per-project file under `ledger/`) and `distill` (promote lessons recurring across 2+ projects into approved diffs against the skills or framework.md). Supporting changes: framework.md §3b defines the **Deviations from spec** section; app-developer and release-qa now record divergences there during Build and Verify. No ledger evidence — this is the mechanism, not a lesson from it.

---

## Rejected

`distill` proposals that were considered and turned down, so they aren't re-proposed unchanged. One line each: date, the proposed change, why it was rejected.

_(none yet)_
