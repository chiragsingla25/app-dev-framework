# app-dev-framework — improvement backlog

Owner context: solo setup (just this user's own product-building workflow). Retros will
**not** be run consistently — so the framework is treated as a **strong static system that
gets hand-tuned occasionally**, not a self-improving one. Get changes right up front.

Origin: a test prompt — "Build a anime image creator deployed into hugging face, that
create a anime image based on description" — where `app-architect` did not trigger, followed
by a partner discussion about what the framework does poorly.

---

## Decisions locked

- **No standing multi-agent team.** A frontend-agent + backend-agent split is the multi-agent
  pattern the framework exists to argue against. Parallel subagents are used only for
  genuinely independent work chunks with a clean interface, identified per-project by the
  architect, plus review gates for the "constant critique" benefit. Revisit only if a real
  project shows a generalist developer drowning.
- **No API-key store.** Proprietary/org integrations go through a scoped MCP server + a
  `.env` the user fills in. Secrets never in `CLAUDE.md` or any tracked file.
- **Not maxing out machinery for its own sake.** Every added hook/skill/subagent must pay
  its maintenance cost.
- **First focus: Discovery / scoping.** Build depth and verification come after one real
  project runs through the improved discovery flow.

---

## Workstream 1 — Discovery & scoping (`app-architect`) · DONE 2026-09-06

Applied to `skills/app-architect/SKILL.md` (steps: resource inventory in 1, new 1b prior art,
2 spec carries prior-art section, new 3b delivery model, 7 proposal+signoff gate, 8 scaffold)
and `references/framework.md` (§2 scaffold tree + secrets note, §3 spec opens with prior art,
new §7c delivery model, §10 checklist). Verified via `claude -p` that a consultation now lists
resource inventory, prior-art research, delivery-model choice, and a "nothing builds until you
approve docs/proposal.md" gate. Other four skills untouched.


| # | Change | Files |
|---|---|---|
| 1.1 | **Prior-art research step.** 2–3 comparable products; for each: table-stakes feature set, what's overkill, notable UX patterns. Output → "Prior art & scope rationale" section in SPEC.md naming what we copy and what we deliberately cut. | `skills/app-architect/SKILL.md`, `references/framework.md` §3 |
| 1.2 | **Resource & capability intake.** Inventory in step 1: local machine (OS, runtimes, GPU), accounts/services on hand, org/proprietary APIs (flag which need an MCP server), budget/effort tier. Written into project `CLAUDE.md` under "Available resources". Secrets → scaffold empty `.env.example` + `.gitignore`; user fills real `.env`. | `skills/app-architect/SKILL.md`, `references/framework.md` §2, §4 |
| 1.3 | **Proposal + signoff gate.** Consultation produces `docs/proposal.md` (problem, prior-art summary, scope in/out, architecture + delivery model, stack, deployment, phased plan, effort tier); optionally also an artifact for phone review. **Nothing scaffolds until the user approves it.** Run in plan mode where the harness supports it. | `skills/app-architect/SKILL.md` step 7 |
| 1.4 | **Explicit delivery-model decision.** Architect picks + justifies: (a) single generalist end-to-end [default]; (b) generalist + review gates; (c) generalist + parallel subagents for *named* independent workstreams + review gates. Anything past (a) must name the specific parallel chunks. | `skills/app-architect/SKILL.md`, `references/framework.md` §7c (new) |

## Workstream 2 — Build depth (`app-developer`) · LATER (after 1 real project)

- 2.1 Real UI → invoke existing `frontend-design` / `design` skills, not an auto-generated shell.
- 2.2 Add `references/frontend.md` + `references/backend.md` — depth checklists the single
  developer consults (API-contract discipline, state, errors, a11y / schema, auth,
  validation, migrations).
- 2.3 Parallel subagent chunks only where 1.4 flagged them: shared contract/types file
  written first, then reconcile + review pass.

## Workstream 3 — Verification · LATER (small, high-trust payoff)

- 3.1 `framework.md` §3a: every phase checkpoint is a literal `Verify: run X → you should see Y`.
  `app-developer` runs it before declaring the phase done.
- 3.2 Scaffold a commented-out phase-gate hook (`.claude/settings.json`) that runs the
  checkpoint command and surfaces pass/fail. Opt-in per project.
- 3.3 `release-qa` explicitly runs `/code-review` and `security-review` instead of reinventing review.

## Workstream 4 — Standards & the light retro · ALONGSIDE

- 4.1 Cross-project rules into user-global `~/.claude/CLAUDE.md`: always prior-art research,
  always runnable checkpoints, secrets never tracked, delivery-model must be justified.
- 4.2 Keep the one-line deviation record (`§3b`); run `evolve distill` only once entries pile up.
- 4.3 Remove "self-improving / grows over time" language from skill docs; frame as a static
  framework that's occasionally hand-tuned.

---

## Not doing

Standing multi-agent team · PM-agent live supervision (not a real subagent capability) ·
any API-key store · adding hooks/MCP/subagents for their own sake.
