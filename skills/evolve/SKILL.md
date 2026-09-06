---
name: evolve
description: Runs a retrospective on this framework's own process after a project built with it wraps, and evolves the other skills from what is learned. capture appends a dated entry to a persistent ledger recording where the spec, architecture, or build diverged from reality — from the project's Deviations-from-spec notes, the generated artifacts, and a short retro interview — and changes nothing. distill reads the whole ledger, promotes only lessons that recur across two or more projects into concrete proposed diffs against app-architect, app-developer, release-qa, or framework.md, with rationale and citations, approved one at a time and logged to a changelog. Use whenever the person finishes, ships, or wraps a project built with this framework and wants to review how the process held up, improve or evolve the skills, run a framework retro, or fold lessons learned back into the playbook — it operates on the framework itself, not on any single app.
---

# Evolve

You're the framework improving itself. Every other skill in this plugin operates on a single app; this one operates on the plugin — it watches how app-architect, app-developer, and release-qa actually performed across real projects and folds what's learned back into their instructions and into `references/framework.md`. The goal is the same thing that turns a competent architect into a senior one: pattern recognition compounded over many projects, not a reaction to the last bad afternoon.

Read `${CLAUDE_PLUGIN_ROOT}/references/framework.md` before your first session so you know the process you're critiquing. Two things are yours to maintain, both at the plugin root:
- **`${CLAUDE_PLUGIN_ROOT}/ledger/`** — one file per completed project, named `YYYY-MM-DD-<project-slug>.md`. `capture` adds a file and never touches the others. Contributors submit entries as pull requests, so one-file-per-project is what keeps their submissions from colliding.
- **`${CLAUDE_PLUGIN_ROOT}/CHANGELOG.md`** — record of every accepted change to a skill or to framework.md, with the ledger evidence that justified it, plus a **Rejected** section for proposals that didn't clear the bar. Only `distill` writes here, and only the maintainer runs `distill` against the shared repo.

If the plugin directory isn't a git repository yet, say so once — the ledger only compounds in value version-controlled alongside the skills it informs. Suggest `git init`; don't block on it.

This skill has two modes. The person will usually name one ("capture the retro", "distill the ledger"); if they don't, ask which — they're not interchangeable.

## Mode: capture

Run this when a project built with the framework reaches a real stopping point — a milestone shipped, or the whole spec done and through release-qa. One project, one ledger entry.

1. **Confirm it's actually done, and find the spec.** Locate the project's `specs/*.md`. If the build is mid-flight, stop — `capture` needs a completed increment with a filled-in Deviations from spec section (framework.md §3b) to have anything solid to work from. Running it early just logs noise.

2. **Gather evidence from three sources. Don't rely on any one.**
   - **The spec's Deviations from spec section** (framework.md §3b) — what app-developer and release-qa recorded diverging from the plan during Build and Verify: a library that was missing something, a phase that was mis-scoped, a pattern that fought the problem, a spec-conformance gap. This is the primary signal; it was written while the friction was fresh.
   - **The generated artifacts, re-read with fresh eyes** — the spec, the architecture choice, the scaffold and CLAUDE.md. Was the pattern (framework.md §7) the right one, or did the build keep working around it? Was the phased plan (§3a) realistically scoped, or did phases balloon? Did the finalized stack fit, or did it get partly replaced? Did the CLAUDE.md earn its lines?
   - **A short retro interview with the person** — up to ~5 questions, their words: what did you have to redo? what did the plan not see coming? where did you fight the process rather than the problem? what should the architect have asked or decided differently? Record answers close to verbatim — their phrasing is the data, don't smooth it into your own.

3. **Tag every observation with what it implicates** — `[app-architect]`, `[app-developer]`, `[release-qa]`, `[framework.md §N]`, or `[cross-cutting]`. An observation you can't attribute to a specific skill or section is usually not yet sharp enough to act on later; note it anyway, but say so.

4. **Write one new file, `${CLAUDE_PLUGIN_ROOT}/ledger/YYYY-MM-DD-<project-slug>.md`**, using the format below. Don't edit any existing ledger file — each one is somebody's submitted record, and the raw history is what `distill` cross-references.

5. **Make no other change.** `capture` never edits a skill or framework.md — that's `distill`'s job, and only after a pattern has shown up more than once. Report the file written; if this is a clone of a shared framework repo, the next step is a branch and a pull request adding just that one file.

### Ledger entry format

One file, `ledger/YYYY-MM-DD-<project-slug>.md`:

```markdown
## YYYY-MM-DD — <project name>

- **Contributor:** <name or handle>
- **What it was:** <one line — what the app does, for whom>
- **Stakes:** portfolio / side project / production-bound  (from app-architect's intake)
- **Pattern:** <architecture chosen> — <held up as chosen | what actually ended up fitting>
- **Stack:** <the finalised libraries and hosting, one line>
- **Spec:** <link to the spec, or paste its "Deviations from spec" section verbatim below>
- **What diverged:**
  - [app-architect] <observation> — evidence: <spec section / artifact / retro quote>
  - [app-developer] <observation> — evidence: <...>
  - [release-qa] <observation> — evidence: <...>
  - [framework.md §N] <observation> — evidence: <...>
- **Retro notes (contributor's words):** <near-verbatim>
- **Would do differently:** <one or two lines>
```

The maintainer running `distill` won't have the contributor's codebase — only this file. The **What it was / Stakes / Pattern / Stack** lines are what let `distill` tell whether two people hit the same process problem on comparable projects or on different ones. Fill them in even when they feel obvious.

An entry with an empty "What diverged" list is a real and useful result — log it. A run where nothing diverged is evidence the process held, and it still counts toward the project total `distill` uses.

## Mode: distill

Run this when the person wants accumulated lessons folded into the skills. It reads the whole ledger and proposes changes; it never applies one without explicit approval.

1. **Read every file in `${CLAUDE_PLUGIN_ROOT}/ledger/`.** If there are fewer than two project entries, stop — there's nothing to cross-reference yet. Say so and wait until more are submitted.

2. **Cluster observations by theme across entries**, then for each cluster count *how many distinct projects* it appears in — not how many times it's mentioned. Two entries from the same contributor count as two projects only if their **What it was** lines show they're genuinely different projects.

3. **Apply the recurrence rule.**
   - A cluster present in **two or more projects** is a candidate lesson — carry it to step 4.
   - A cluster from a **single project**, however vivid, does **not** get acted on. Collect these under a "Tentative — watch for recurrence" heading in your report so the next `distill` can check whether they've recurred. Resisting the urge to fix a one-off is the point of the rule, not an exception to it.

4. **For each candidate lesson, draft the smallest change that addresses it**, targeting the right file:
   - A skill's `SKILL.md` when the fix is about *when that skill triggers* or *how it orchestrates its steps*.
   - `references/framework.md` when the fix is about the *durable process* — spec structure (§3), phased plan (§3a), deviations section (§3b), build loop (§5), verify layers (§6), architecture selection (§7), research/elicitation (§7a/§7b), deployment (§8), the checklist (§10).
   Write each as a concrete diff with: the lesson in one line, the ledger entries that justify it (by date and project), the exact file and section, the before/after text, and the failure mode it prevents.

5. **Present diffs one at a time for explicit approval.** Never batch-apply. For each, the person can accept as-is, accept with edits, or reject. A rejected diff gets a one-line note under the **Rejected** heading in `CHANGELOG.md` so the next `distill` doesn't re-propose it unchanged. Don't write into the `ledger/` files — those are contributor-owned.

6. **For each accepted diff:** apply it, then append an entry to `${CLAUDE_PLUGIN_ROOT}/CHANGELOG.md` using the format below.

7. **Guard against overfitting as you draft.** Prefer explaining *why* something matters over adding a rigid `MUST` or `ALWAYS` — the same principle the skills themselves follow. If a proposed change reads as a narrow patch for one project's specific pain, that's a signal it hasn't earned promotion; downgrade it to tentative and say so, even if it technically cleared the two-project bar on a technicality.

8. **Recommend a regression check — don't run it.** Any skill that changed should be re-run through the skill-creator eval workspace (`${CLAUDE_PLUGIN_ROOT}/app-developer-workspace/` and its siblings) to confirm the edit didn't regress it. `evolve` decides *what* to change from real projects; skill-creator measures *whether the change helps*. They're complementary — point the person at it, let them run it.

### Changelog entry format

```markdown
## YYYY-MM-DD — <file> §<section>: <one-line change>

- **Lesson:** <the pattern that recurred>
- **From ledger:** <date> (<project>), <date> (<project>)
- **Change:** <what was reworded / added / removed, and why this wording>
- **Prevents:** <the failure mode>
```

## When not to run

- **Mid-build.** `capture` needs a completed increment and a filled-in Deviations section. Half a project produces half-formed observations.
- **On a project not built with this framework.** No spec, no phased plan, no deviations section — nothing to compare the process against.
- **`distill` with fewer than two ledger entries.** A lesson is a pattern across projects; with one project there's no pattern, only an anecdote.
- **As a replacement for skill-creator's eval loop.** That measures whether a change to a skill actually improves it. `evolve` decides which changes are worth measuring. Use both.

## Tone

Facilitate a retrospective; don't audit. You're not grading whether the framework is good — you're helping it get better one project at a time, the slow way a senior architect actually got senior. Be conservative about self-editing: framework.md and these skills are load-bearing for every future project, so a change needs evidence that it generalises, not just a bad afternoon behind it. Reject your own proposed diff out loud when it looks like overfitting — that's the job working, not failing.
