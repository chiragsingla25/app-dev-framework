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

## 2026-09-06 — bootstrap

`evolve` skill added to the framework: `capture` (add a per-project file under `ledger/`) and `distill` (promote lessons recurring across 2+ projects into approved diffs against the skills or framework.md). Supporting changes: framework.md §3b defines the **Deviations from spec** section; app-developer and release-qa now record divergences there during Build and Verify. No ledger evidence — this is the mechanism, not a lesson from it.

---

## Rejected

`distill` proposals that were considered and turned down, so they aren't re-proposed unchanged. One line each: date, the proposed change, why it was rejected.

_(none yet)_
