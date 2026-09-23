# agent-consultancy

A small software organization made of Claude Code agents. You describe what you want; an orchestrator sizes the work, picks only the stages it needs from a pool of roles, and delivers it feature by feature with a git commit per passing feature.

This is **phase one: the spine**. Three roles, one orchestrator, one run folder. Everything later plugs into the same shape.

## How it works

```
/deliver "what you want"
   │
   ├─ intake (always)      → delivery/<run>/intake.md, features.json
   ├─ orchestrator decides → plan.json  (which stages; order computed from dependencies)
   ├─ YOU APPROVE          ← features, stages, open questions
   └─ per feature:
        builder → qa → PASS: git commit
                     → FAIL: builder again (max 3 attempts) → then back to you
                     → OBJECTION (the spec is wrong): you rule → decisions.md
```

| Piece | What it is | Why it's that kind of thing |
|---|---|---|
| `skills/deliver` | The orchestrator. Runs in your main session. | It's the only part that reasons about what happens next, and only the main session can dispatch subagents to all roles. |
| `agents/intake`, `builder`, `qa` | Roles, as subagents | Each gets its own context. QA can't edit code and doesn't trust the build log, so it can't be talked into a pass. |
| `stages/registry.json` | The pool of stages, each declaring what it `needs` and `produces` | The orchestrator picks stages; the order falls out of the dependencies. |
| `skills/deliver/scripts/deliver.py` | Deterministic helpers: `init`, `plan`, `features` | Anything that shouldn't be a judgement call (ordering, handoff validation) is code, not prompt. |
| `delivery/<run>/` in your project | The shared folder | Agents coordinate through files, never by relaying each other's words. |
| git | Version control and audit trail | One commit per feature that passed QA, plus a run summary. |

### A run folder

```
delivery/20260923-231500-rename-cli/
  request.md       what you asked for
  intake.md        understanding, size, recommended stages, open questions
  features.json    F-001… with checkable acceptance criteria
  plan.json        stages run, stages skipped, reason
  build-log.md     builder's notes per attempt
  qa/F-001-attempt-1.md   VERDICT: PASS|FAIL|OBJECTION + evidence
  decisions.md     objections and your rulings (raw material for the retrospective)
  summary.md       what happened, per feature, with commit hashes
```

## Install

Local, for trying it:

```bash
claude --plugin-dir ~/projects/agent-consultancy
```

Or as a local marketplace so it's available in every session:

```
/plugin marketplace add ~/projects/agent-consultancy
/plugin install consultancy@agent-consultancy
```

Then, in any project directory:

```
/consultancy:deliver a CLI that renames files by extension, with a dry-run flag
```

## Adding a stage later

1. Write the agent in `agents/`.
2. Add an entry to `stages/registry.json` with `needs` and `produces`.
3. Mention it in the intake agent's list of available stages.

The planner needs no changes. `tests/test_deliver.py` already checks the ordering logic against the full future pool (research, spec, journey, mock, architecture).

## Roadmap

1. **Spine** (this): intake, builder, QA, orchestrator, run folder, git. Objections go to you as the single owner.
2. **Front half**: research, spec, user journey, clickable HTML mock, architecture. Your approval after the mock and after architecture.
3. **Enforcement**: security scan as a hook after every build step; handoff validation as hooks; objections routed to the domain owner (business vs technical) instead of always to you.
4. **Memory**: a retrospective after every run, writing candidate lessons. Nothing acts on them yet.
5. **Evolution**: versioned role definitions with rollback, autonomous tuning of existing roles, then proposals for new roles once a problem recurs three times.

## Tests

```bash
python3 -m unittest discover -s tests -v
```
