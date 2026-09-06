# Evolve ledger

One file per completed project built with this framework, named `YYYY-MM-DD-<project-slug>.md`, written by the `evolve` skill's `capture` mode. `distill` reads every file here to find lessons that recur across two or more projects.

**One file per project so contributor pull requests never collide.** Don't edit someone else's entry — add your own file. Contribute by opening a PR that adds a single `ledger/*.md` file and nothing else.

## Entry format

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

Whoever runs `distill` won't have your codebase — only this file. The **What it was / Stakes / Pattern / Stack** lines are what let `distill` tell whether two people hit the same process problem on comparable projects or different ones. Fill them in even when they feel obvious.

An empty "What diverged" list is a valid result — it means the process held, and it still counts toward the project total.
