# app-dev-framework

A spec-driven **AI App Development Framework** packaged as Claude Code skills. It separates the four things that "just ask the AI" collapses into one — *what to build*, *what Claude should always know*, *how the work gets verified*, *where it runs* — into a repeatable loop.

The durable process lives in [`references/framework.md`](references/framework.md); the skills are its moving parts.

## Skills

| Skill | Stage | Does |
|---|---|---|
| `app-architect` | Spec + Scaffold | Intake interview, spec with a phased build plan, simplest architecture that fits, researched (not recited) stack and hosting, then scaffolds the repo. |
| `app-developer` | Build | Validates the core flow in an MVP notebook, then works the spec's phases as hard gates — clarify, explore, plan, implement, commit, stop for approval. |
| `release-qa` | Verify + Ship | Independent check: reads the spec and the real diff, runs layered eval + adversarial review, wires CI, deploys to the finalised target. |
| `reset` | — | Archives everything the framework generated into a timestamped `.archive/` folder so `app-architect` can start fresh. |
| `evolve` | Retrospective | Cross-project retrospective. `capture` logs how a finished project's process actually went to `ledger/`; `distill` folds lessons that recur across 2+ projects back into the other skills. |

## Install

```bash
git clone <this-repo-url> ~/.claude/skills/app-dev-framework
```

Claude Code auto-loads any plugin under `~/.claude/skills/`. Restart your session, then start a project with `/app-architect` (or just pitch an app idea).

Update later with:

```bash
git -C ~/.claude/skills/app-dev-framework pull
```

## Contributing a retrospective

The framework improves from real project outcomes. After you finish or ship a project built with it:

1. Run `/evolve capture` in that project. It writes `ledger/YYYY-MM-DD-<project-slug>.md`.
2. Open a PR that adds **only that one file** (see [`ledger/README.md`](ledger/README.md) for the format).

Because each retro is its own file, contributors' PRs never conflict. The maintainer periodically runs `/evolve distill`, which promotes patterns seen across two or more projects into proposed diffs against the skills or `framework.md`, each approved one at a time and recorded in [`CHANGELOG.md`](CHANGELOG.md). Don't run `distill` against the shared repo yourself — contribute observations, not changes.

## Layout

```
.claude-plugin/plugin.json   plugin manifest
references/framework.md       the durable process (skills read this)
skills/*/SKILL.md             the five skills
ledger/                       per-project retrospectives (evolve capture)
CHANGELOG.md                  accepted framework changes (evolve distill)
app-developer-workspace/      skill-creator eval cases; run outputs are gitignored
```
