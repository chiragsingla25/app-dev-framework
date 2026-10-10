# AI App Development Framework
### A repeatable process for building, verifying, and shipping AI apps with less hallucination

---

## 0. The core idea

Most people treat Claude Code (or Cursor) like a chat box: type a prompt, get code, ship it. That works for toy scripts. It falls apart the moment an app has more than one file, an agent that can take actions, or output that a user will actually trust.

The fix isn't a better prompt. It's **separating four things that "just ask the AI" collapses into one**:

1. **What to build** — a spec, written before code, that both you and Claude can check the result against
2. **What Claude should always know** — persistent, low-token context (CLAUDE.md, rules, skills)
3. **How the work gets verified** — tests, evals, and a second opinion, not "looks right to me"
4. **Where it runs** — a deployment target chosen by the app's shape, not by habit

This document is the reusable version of that separation. Drop it into any new project, adapt the specifics, and you get the same loop every time instead of reinventing your process per repo.

---

## 1. The six-stage loop

```
 Spec  →  Scaffold  →  Build
                          ↓
 Monitor  ←  Ship  ←  Verify
   ↻ feeds the next Spec
```

| Stage | What happens | Owned by |
|---|---|---|
| **Spec** | Interview-driven requirements doc, written before any code | You + Claude (`AskUserQuestion`) |
| **Scaffold** | Repo structure, CLAUDE.md, rules, skills, subagents committed | You (once per project, then reused) |
| **Build** | Plan → implement, in a fresh session, against the spec | Claude Code / Cursor |
| **Verify** | Tests, evals, adversarial review — the anti-hallucination gate | CI + a fresh-context reviewer |
| **Ship** | CI-gated deploy to the right target for the app's shape | GitHub Actions |
| **Monitor** | Tracing + a judge model watching production, feeding the next spec | MLflow / Langfuse / LangSmith |

The stages that most people skip are **Spec** and **Verify** — which is exactly why "prompt it directly" produces confident, hallucinated apps. Everything below fills in each stage.

---

## 2. Repo scaffold (copy this into every new project)

```
project/
├── CLAUDE.md                  # persistent, project-wide context (loaded every session)
├── AGENTS.md                  # same content, for tools that don't read CLAUDE.md (Cursor, others)
├── .claude/
│   ├── rules/                 # path-scoped conventions (e.g. rules for /api vs /frontend)
│   ├── skills/                # on-demand domain knowledge (SKILL.md), not loaded unless relevant
│   ├── agents/                # subagent defs: reviewer.md, debugger.md, data-scientist.md
│   ├── workflows/              # saved dynamic workflows (large audits, migrations)
│   └── settings.json          # hooks, permissions, allowed tools
├── docs/
│   └── proposal.md            # the approved scoping doc — written and signed off before scaffold
├── .env.example               # names every required key/secret; real .env is gitignored, filled by hand
├── specs/
│   └── 2026-09-05-claim-router.md
├── notebooks/
│   └── mvp.ipynb               # throwaway single-file prototype, validates the idea before scaffolding
├── src/
├── evals/
│   ├── golden_dataset.jsonl    # the questions/cases you always check against
│   ├── ragas_suite.py          # faithfulness / groundedness for RAG
│   └── promptfoo/              # prompt regression tests
├── .github/workflows/
│   ├── ci.yml                  # tests + eval gate on every PR
│   └── claude-review.yml       # automated PR review
├── Dockerfile
└── README.md
```

Check `CLAUDE.md`, `.claude/`, `docs/`, `specs/`, and `evals/` into git. They compound in value across every future session — a teammate (or future-you) opens the repo and Claude is already calibrated. **Never check in `.env` or real secrets** — `.env.example` lists the *names* of what's needed; the values live only in an untracked `.env` the person fills in. Proprietary APIs and org services are integrated through a scoped MCP server, not by pasting keys into config.

---

## 3. Stage 1 — Spec: interview before you build

Don't describe a feature in one line and let Claude guess the edge cases. Have it interview you:

```text
I want to build [feature]. Interview me in detail using the AskUserQuestion tool.
Ask about technical implementation, UI/UX, edge cases, and tradeoffs.
Don't ask obvious questions — dig into what I might not have considered.
Keep going until we've covered everything, then write a complete spec to
specs/YYYY-MM-DD-feature-name.md.
```

A good spec:
- Opens with **Prior art & scope rationale** — 2-3 comparable products, what's table-stakes (build early), what's overkill for this scale/purpose (cut explicitly), and the UX patterns worth copying. Don't invent from scratch what already has known-good shapes. If nothing comparable exists, say so and raise the verification bar to match.
- Names the specific files and interfaces involved
- States what's explicitly **out of scope** — the "overkill" list from prior art feeds straight into this
- Ends with a verification step that proves the feature works (a test to pass, a screenshot to match, an eval score to hit)
- For anything beyond a trivial change, breaks the build into named, ordered phases with a hard approval gate between them (§3a) — not one undifferentiated block of work

Then **start a fresh session** to implement it. The interview session's context is now dead weight — the spec is the only thing that needs to survive.

---

## 3a. Phased build plan — decompose before you build, not during

Name the phases in the spec itself; don't leave decomposition to whoever happens to build it later. This borrows the shape of tools like GitHub's Spec Kit (`specify → clarify → plan → tasks → implement`), where the task breakdown is a reviewable artifact, not an implicit judgment call made mid-build.

Format, inside the spec:
- **Phase N: <name>** — what it delivers, in one line
- Its own concrete checkpoint — a notebook cell that runs, a screen that renders, an eval that passes — proof it's actually done, not just "code written". Write it as a literal **`Verify: run <command> → you should see <result>`**, so whoever checks it runs the same thing
- **Acceptance criteria** — a short list of checkable statements, each one verifiable by running a command, reading output, or inspecting a file. "Works well", "is clean", "is fast" are not criteria. Any phase that takes input gets at least one failure or edge case. Error handling, validation and argument parsing are criteria of the phase that needs them, never phases of their own
- Ordered by dependency: smallest independently-verifiable slice first (one endpoint, one component, one agent node — see §5)
- **Milestones**: group the phases into milestones, each a set of phases release-qa reviews together. By default the whole spec is one milestone. When a milestone starts, the builder records `Milestone N base: <commit hash>` in the spec, which gives the reviewer its BASE for the regression sweep

**Each phase is a hard gate.** The builder implements one phase fully, reports what's built and what it verified, and stops — the next phase does not start until the person gives explicit go-ahead. This is stronger than the routine per-increment check-in inside a phase (§5): a phase boundary is a decision point the person owns, not a status update to skim past.

**Continuous mode (opt-in).** Once the proposal is approved, the person may waive the gates for named phases ("run phases 2–4 without stopping"). When the person waives the gates, the builder runs the clarify passes for all the waived phases at once, before going on. After that it goes straight from one phase to the next, but only when the finished phase's acceptance criteria are all met (a passing test, or a hand check where a test is impractical) and its `Verify:` line holds. It still stops for anything that needs the person: a new question that would change what gets built, a flag-back (§5), a disputed criterion (§3b), a failing test it can't fix in two tries, or scope that has grown. Continuous mode doesn't make a run unattended. A run is unattended only when the person has said they won't be available. Release-qa still runs at the milestone. This is the same single generalist (§7c), not a team. It trades check-ins for speed, so use it when the plan is solid and the person would rather review the result than each step. The default stays one gate per phase.

Skip explicit phasing only for a change small enough to describe in one sentence — a phase list for a one-file fix is ceremony, not decomposition.

---

## 3b. Deviations from spec — filled in during Build and Verify

The spec is written before code, so it's always partly wrong by the time code exists. That gap is the single most useful input to improving the process — but only if it's written down while it's fresh, not reconstructed from memory months later.

Every spec carries a **Deviations from spec** section, appended to during Build and Verify, not at planning time:

```markdown
## Deviations from spec

- [phase N / verify] <what diverged> — <why: library gap, mis-scoped phase, pattern
  fought the problem, spec-conformance gap> — <how it was resolved>
```

- **app-developer** adds an entry whenever a phase surfaces something the plan didn't see: a chosen library missing a capability, a phase that ballooned or turned out to depend on a later one, a pattern that the implementation kept working around. This is separate from flagging an architecture decision back (that still stops the build) — it's the smaller stuff that gets absorbed and would otherwise vanish.
- **release-qa** adds an entry for any spec-conformance gap it finds, and for any place where what shipped diverged from what was specified — including divergences the developer didn't record.

**Disputed criteria are recorded here too, and ruled on by the person, never by the builder or reviewer.** When the developer or release-qa finds an acceptance criterion that is wrong, contradictory or uncheckable, they don't reinterpret it in code or pass/fail it on their own reading. They finish everything the criterion doesn't affect, then stop, put the problem and a proposed wording to the person, and log the outcome:

```markdown
- [phase N / verify] RULING on "<criterion>" — raised by <developer|release-qa>: <problem>
  — ruled by <person>: <decision> — <reason>
```

A ruling that "looks mechanical" is still the person's call. In a run the person has said they won't be available for (unattended), the builder may proceed on a ruling marked `PROVISIONAL` and list every provisional ruling in its hand-off for confirmation.

Leave the section with a single "None" bullet if nothing diverged. That's a real result, not an empty formality.

The `evolve` skill reads this section across projects to decide what in the framework itself needs to change. An entry here isn't a criticism of the build — it's the raw material for the next version of the process.

---

## 3c. Bug fixes and behaviour changes: specify the class, not the example

A bug report describes one instance. Writing criteria for only that instance is how a fix ships a regression next to it. (In a trial on a real open-source issue, a "scientific notation" fix was written and tested for huge numbers only. JavaScript also uses scientific notation below 1e-6, and the new code crashed there.) For any fix or behaviour change, even one too small for a full consultation:

- **Name the class of the problem**, not the example ("numbers the runtime prints in scientific notation", not "Number.MAX_VALUE"). Check the language's actual behaviour to find where the class's edges are, rather than assuming.
- **Write a criterion for each edge, in both directions** wherever they apply: huge and tiny, positive and negative, empty and very long.
- **Add one criterion that inputs the code handled correctly before still produce the same output.** Any change in previously-correct behaviour that no criterion asks for is a regression.
- **Check every rule against an ordinary input before building it.** For each rule turned into a criterion, try one everyday input where the rule gives a strange-looking result ("round to 3 significant digits" applied to 1001 bytes gives "1000 B"). Raise those as clarify questions. A spec is built faithfully, so it's the ceiling: the strange result ships unless someone asks.

---

## 4. Stage 2 — Scaffold: CLAUDE.md and friends

This is the part most people get wrong: they either write nothing, or they write a 500-line CLAUDE.md that Claude starts ignoring because the important lines get lost in noise.

### What goes in CLAUDE.md

| ✅ Include | ❌ Exclude |
|---|---|
| Bash commands Claude can't guess (`make dev`, `pytest -k`) | Anything Claude can figure out by reading the code |
| Code style rules that differ from language defaults | Standard conventions Claude already knows |
| Test runner + how to run a single test | Full API docs — link instead |
| Repo etiquette (branch naming, PR conventions) | Anything that changes frequently |
| Architectural decisions specific to this project | Long tutorials or explanations |
| Environment quirks (required env vars, local setup gotchas) | "Write clean code" — self-evident |

Run `/init` in Claude Code to generate a starter from your existing structure, then prune. The test for every line: **would removing this cause a mistake?** If not, cut it.

### The rest of `.claude/`

- **`rules/`** — path-scoped conventions (different rules for `/frontend` vs `/agents`), so a large repo doesn't force one CLAUDE.md to cover everything
- **`skills/`** — domain knowledge or repeatable workflows that only apply *sometimes* (e.g. "how we structure a new evaluator," "how to add a new tool to the claims agent"). Claude loads these on demand instead of every session — keeps CLAUDE.md lean
- **`agents/`** — subagent definitions for isolated work: a `security-reviewer`, a `debugger`, a `data-scientist` that runs in its own context so research doesn't pollute your main conversation
- **`workflows/`** — for tasks bigger than one conversation can hold: a codebase-wide audit, a 500-file migration, cross-checked research. Ask for one in plain language ("use a workflow to audit every endpoint for missing auth checks") and save the script for reuse

---

## 5. Stage 3 — Build: plan before you implement

The default failure mode is Claude jumping straight to code and solving the wrong problem. Four-phase loop:

1. **Explore** — plan mode on, Claude reads and answers questions, makes no changes
2. **Plan** — "create a detailed implementation plan" — review and edit it before anything runs
3. **Implement** — approve the plan, let Claude code against it, verifying as it goes
4. **Commit** — descriptive message, PR opened

**The builder's own tests are the gate for each commit.** Every acceptance criterion gets a test that checks it as written (named or commented with the criterion it covers, so a reviewer can map them), and the full suite passes before the commit. Where a test is genuinely impractical, say how to check the criterion by hand instead. Release-qa still checks independently later. These tests are what make it safe for release-qa to look once per milestone instead of after every phase. If an existing test fails and looks unrelated, prove it against the last commit with `git worktree add "$(mktemp -d)" HEAD` (a scratch dir **outside** the repo, removed afterwards) rather than declaring it "known".

**List user-visible changes beyond the phase itself** in the phase report: changed output text, error messages, limits, defaults, tool descriptions. Side effects like these (a public error message changed while raising an internal limit) get past criteria and are what users actually notice.

**Commit only what belongs in the repo.** `scripts/safe_commit.py` (in this plugin) stages everything, but first adds OS and tool clutter it finds (`.DS_Store`, `__pycache__/`, `*.pyc`, `Thumbs.db`) to `.gitignore` and untracks any already committed. It refuses to commit files that look like secrets (`.env`, `*.pem`, keys) or a stray nested checkout (a scratch worktree made inside the repo), and warns if the tree isn't clean afterwards, so a commit hook or formatter that changed files doesn't slip by unnoticed. When working on someone else's repo, keep `specs/` and `docs/` out of commits with `.git/info/exclude`, so a pull request contains only the change.

Skip planning for genuinely small changes (a typo, a log line) — it's overhead you don't need when you could describe the diff in one sentence. Use it whenever the change touches multiple files or you're unsure of the approach.

**Clarify before each phase, not just once at the start.** Before beginning a phase's own Explore→Plan→Implement→Commit loop — including phase 1 — run a short clarify pass: up to ~5 targeted questions resolving ambiguity specific to *that phase's* scope (not the whole project again), fold the answers into that phase's section of the spec, then proceed. This is Spec Kit's `/clarify` gate applied recurringly: ambiguity that isn't visible until a phase is actually in front of you doesn't get papered over by a plan made phases earlier. Skip it only when a phase is genuinely unambiguous — say so rather than skipping silently.

Before folding a clarification's answers into the spec, check them against the spec's stated **Goal** (§1) and any **architecture assumption** they touch. A clarification that narrows the goal (an eval that no longer scores what the project exists to measure), picks an environment the architecture didn't assume, or swaps a stack choice the plan was sized against (a model/provider with a different quota) is not a phase detail to absorb — it's a flag-back to app-architect. Fold in the ones that resolve genuine local ambiguity; escalate the ones that move the project off its approved shape.

**Delegate research to subagents**, not your main thread: *"use subagents to investigate how our auth handles token refresh"* keeps your context clean for the actual implementation.

### MVP first: validate before you scaffold

For a new idea, or a pattern you haven't built before, don't start the four-phase loop against the full scaffolded repo. Build a single Jupyter notebook first — `notebooks/mvp.ipynb` — with one cell per step of the spec's core flow, run top to bottom. In this pass, one developer owns everything: the data/model/agent logic and whatever minimal output the idea needs to be checked (a printed result, a rendered dataframe, a quick plot, an inline widget) — no frontend/backend split, no services, no proper module structure. The only question the notebook has to answer is whether the idea actually works end to end.

**Make that check load-bearing, or say it isn't.** Two ways it comes back a false "validated": *too few cases* — a handful of hand-picked inputs won't surface a failure that only shows up systematically, so run enough varied cases, the awkward ones included, that a recurring failure would actually appear; and *wrong environment* — a GPU model on a machine with no GPU, or a paid API on a small free quota, tests the environment, not the idea. Run the notebook where the app will actually run, or the closest thing to it; if you can't, mark the result provisional rather than "validated."

Show the notebook's output before investing in the real build. If the core idea doesn't hold up, that's a cheap finding — cheaper than discovering it three files into a scaffolded repo. If it does, promote the validated logic into the real structure (§2) for the ordered-increment build; the notebook becomes disposable scratch work, not a dependency of the shipped app, and doesn't go through Verify or Ship itself.

---

## 6. Stage 4 — Verify: the anti-hallucination gate

This is the stage that actually determines whether your app hallucinates in production. Treat it as a first-class deliverable, not a step you do if there's time.

**Layer these, cheapest first:**

1. **Structured outputs everywhere a decision feeds downstream logic.** Free text that gets parsed with string matching is a hallucination surface. Force a schema (Pydantic/JSON schema) for anything an agent decides.
2. **Grounding + citation requirement.** For RAG or tool-using agents: no claim without a retrieved source ID attached. If the model can't cite it, it doesn't get to say it.
3. **Golden dataset + regression evals, run in CI on every PR** — not just at the end:
   - **RAGAS** for RAG faithfulness / answer relevancy / context precision
   - **promptfoo** or **DeepEval** for prompt regression testing across model/prompt changes
   - A fixed set of adversarial cases (the ones that broke last time) that must keep passing
4. **Judge-LLM pattern** for agentic outputs — an LLM (or small model) scoring the *decision*, not just the text, against a rubric. Four dimensions worth reusing across almost any agentic app:
   - Evidence consistency — does the output match what was actually retrieved/observed?
   - Hallucination detection — are there claims with no support in context?
   - Decision validity — is the output label/action actually a valid option?
   - Rationale sufficiency — does the stated reasoning actually justify the decision?
5. **Adversarial review subagent** — after implementation, a *fresh-context* subagent reviews the diff against the spec, not the code it just wrote. It has no attachment to its own reasoning, so it catches gaps a self-review misses. This plugin ships one: `agents/reviewer.md`. What makes it useful rather than slow, learned from 34 review rounds across 11 real runs:
   - **Once per milestone (§3a), over its phases together** — not after every phase. Review after every feature took longer than the building did in practice, and reviewers wrote five times as much text as builders.
   - **Run the test suite once**, then map each criterion to its test. A test that really checks what the criterion says (right input, right assertion, not mocked away) and passes is the evidence; don't redo it by hand. Hand-check only criteria with no sound test.
   - **What a user sees first** — the spec's main examples, typical inputs, how output reads — before exotic numeric limits.
   - **One or two adversarial inputs per phase**, including the mirror of any reported bug (if the bug was about huge values, try tiny ones).
   - **A regression sweep against the old code**: for touched code paths, run inputs the old code handled against both the milestone's BASE (checked out with `git worktree add "$(mktemp -d)" <BASE>`, outside the repo) and the new code. Anything that worked before and now differs, without a criterion asking for it, is a fail.
   - **FAIL only for a written criterion not met, or a regression.** Everything else goes under Notes, which never trigger a rebuild. Without this rule, review drifted into chasing edge cases nobody specified (seven failed rounds on bigint-vs-number agreement above 2^53 for a library whose README never mentions it; code 3.8× upstream's size) while missing the "1000 kB" a user would see.
   - **A hard cap of three fix rounds per phase**, unattended or not, then the person decides. In the one comparable pair measured, the smaller project cost 46% more, almost all of it in review fail loops.
   - **It never edits code and never rewrites a criterion.** A criterion it thinks is wrong goes to the person (§3b).
6. **Human-in-the-loop checkpoints** for anything high-stakes — plan-mode approval, a confirmation step before an agent takes an irreversible action. Don't let autonomy creep past what the task's risk actually justifies.

If you can't verify a change, don't ship it — that's the rule, not a suggestion.

---

## 7. Agentic architecture: pick the simplest thing that works

The biggest hallucination risk in agentic systems isn't the model — it's **using an agent where a deterministic pipeline would do**. Agents introduce unpredictability; only pay for it when the task genuinely needs dynamic branching.

> **On the specifics:** the *pattern* categories below (single call, pipeline, RAG, single agent, multi-agent, MCP) are durable — they don't go stale. The *library or framework* you'd use to implement one of them does. Don't pick one from memory — research current options for the specific pattern and app before finalizing.

Decision order, cheapest/most reliable first:

| Shape | Use when | Example |
|---|---|---|
| **Single call + structured output** | Classification, extraction, one clear decision | Claim label from a report |
| **Deterministic pipeline (DAG)** | Steps are known ahead of time, no dynamic routing needed | Ingest → chunk → embed → index |
| **RAG (single retriever)** | Knowledge-grounded Q&A over a fixed corpus | A psychology-assistant chatbot |
| **Single agent, tool-use (ReAct)** | Needs to take external actions, moderate complexity | A car-deal finder with MCP tools |
| **Supervisor + worker multi-agent** | Task decomposes into specialized roles needing coordination | Claims evaluation across evidence, policy, and rationale checks |
| **MCP server** | You want to expose the app's tools/data to *any* MCP client, not just your own UI | Turning an internal tool into something Claude Code, Claude Desktop, or a teammate's agent can call |

Start one level down from what feels natural. If a pipeline can do it, don't reach for an agent just because agents are more interesting to build.

---

## 7a. Research is a second opinion, not a menu

Presenting 2-3 researched options and waiting for a pick is necessary but not sufficient — it still puts the AI's shortlist in charge of the decision space. Once options are on the table, explicitly invite the person to push back or propose something the research didn't surface, especially wherever they have direct standing on the call: their own production experience, their own domain (a data scientist judging a chunking or evaluation strategy is not the same conversation as asking them to pick a UI framework). A flat "any thoughts?" is easy to rubber-stamp past — when the decision is high-stakes or squarely in the person's own expertise, reach for one of §7b's elicitation techniques instead of the generic prompt. Let the answer actually change the recommendation, not just get logged as their preference among the choices given.

This applies everywhere framework.md asks you to "research, then decide together": pattern selection (§7), tool/library choice (§11), verification approach (§6), deployment target (§8).

---

## 7b. Elicitation techniques (borrowed from BMAD-Method)

A generic "does this match your read?" is a start, but it's easy to rubber-stamp past. When a decision is high-stakes, or the person has direct standing on it, reach for a specific technique instead — named techniques force a sharper answer than an open invitation to object. This is a reference table any skill in this framework can invoke on demand ("run a pre-mortem on this"), not a checklist to run on every decision — pick the one that fits, running all eight on one choice is ceremony, not rigor.

| Technique | Use it to... |
|---|---|
| **Pre-mortem** | "Assume this choice caused a production incident six months from now — what was it?" Surfaces the failure mode research didn't. |
| **Inversion** | "What would make this the wrong choice?" — argue against your own recommendation before they have to. |
| **First-principles** | Strip the recommendation back to the actual constraint it's solving for, and check the constraint is real before defending the solution. |
| **Red team / blue team** | Argue the strongest case *against* the recommended option, then have the person (or a fresh-context subagent) argue for it. Useful when a decision is contentious or you suspect your own bias toward the familiar tool. |
| **Socratic questioning** | Don't state the tradeoff — ask the question that leads them to it ("what happens to this approach at 10x the data volume?"). Draws out judgment rather than supplying it. |
| **Constraint removal** | "If [cost / timeline / team size] weren't a constraint, what would you build instead?" — separates what they actually want from what they're settling for. |
| **Stakeholder mapping** | Name who else is affected by this decision (a future maintainer, an end user, a downstream team) and check the recommendation still holds from their seat. |
| **Analogical reasoning** | "What's this most like among systems you've actually run?" — pulls in real experience a generic web search can't surface. |

---

## 7c. Delivery model: how the build is executed, separate from what it is

The architecture pattern (§7) is about the *app*. The delivery model is about the *build process* — who implements it and how the work is divided. Pick the least machinery that fits, and justify anything past the default by naming what requires it.

| Model | Use when | Cost you're taking on |
|---|---|---|
| **Single generalist developer, end to end** *(default)* | Almost everything short of a large build. One builder holds the whole picture — logic, frontend, backend — and works in dependency order. | None beyond the build itself. |
| **Generalist + review gates** | The build is quality-sensitive, or touches something that has to be right. The fresh-context reviewer (§6 item 5) runs at extra points the proposal names: the end of specific risky phases (a storage format, a design others build on), on top of the review at each milestone. | One extra review pass per named phase. Worth it for correctness-critical work; overkill for a throwaway demo. |
| **Generalist + parallel subagents for named independent chunks + review gates** | The build genuinely contains parallelizable work: chunks with a clean interface and little shared state — several unrelated endpoints, independent integrations, a batch of isolated components. Name the chunks and the shared contract/types file up front; build that contract first. | Coordination + reconciliation. Only pays off when the chunks are actually independent. |

**A blanket "frontend agent + backend agent" split is not the third model.** Frontend and backend share the API contract, data models, and types — they drift apart when built in parallel, and reconciling the drift costs more than the parallelism saves. Parallelize genuinely independent slices, not layers of the same feature. The "continuous review" instinct is real and valuable — deliver it through review gates, not through a supervisor agent watching a builder agent, which isn't a capability that exists.

Record the chosen model and its justification in `docs/proposal.md` so app-developer executes the build the way it was scoped, not by its own default.

---

## 8. Deployment: match the target to the app's shape

> **On the specifics:** this table names categories and example providers as of when this was written. Hosting options and pricing shift constantly — research current fits for the project's actual requirements (budget, GPU need, expected traffic) rather than picking a name off this list on autopilot.

| App shape | Best fit | Why |
|---|---|---|
| RAG demo / chatbot UI for a portfolio or interview | **HuggingFace Spaces** (Gradio/Streamlit) | Free, zero-infra, good for showing evals alongside the demo |
| Next.js/React frontend, API routes | **Vercel** | Zero-config CI/CD, edge functions, fastest iteration loop |
| GPU inference, batch jobs, scheduled agent runs | **Modal** | Serverless GPU, pay-per-second, Python-native, built-in cron |
| Persistent multi-agent backend (FastAPI, always-on) | **AWS Fargate / Fly.io / Railway** | Matches a Docker-based service that needs to stay warm |
| Cloud-native agentic system with managed vector search | **Cloud Run + Vertex AI / Bedrock Agents** | For when the stack is already GCP/AWS-committed |
| Open-source tool or MCP server for others to install | **GitHub + a plugin/marketplace entry** | Distributable, versioned, one-line install for other Claude Code users |

Pick this at **Spec** time, not at deploy time — it changes how you structure the app (e.g. Modal wants functions, Fargate wants a long-running process).

---

## 9. CI/CD: make Verify unavoidable

```yaml
# .github/workflows/ci.yml (shape, not exact syntax)
on: [pull_request]
jobs:
  test-and-eval:
    steps:
      - run: pytest
      - run: python evals/ragas_suite.py --fail-under 0.85
      - run: promptfoo eval --fail-on-regression
  claude-review:
    steps:
      - uses: anthropics/claude-code-action@v1
        # reviews the diff against CLAUDE.md conventions automatically
```

The point: a PR can't merge if the eval score regresses, not just if unit tests fail. This is what turns "Verify" from a manual step you sometimes remember into a gate you can't skip.

---

## 10. One-page checklist

- [ ] Prior art researched — 2-3 comparable products, table-stakes vs overkill named, before the spec is written
- [ ] Resource & capability inventory taken at intake (local machine, existing accounts, proprietary APIs, budget tier) and written into CLAUDE.md
- [ ] `docs/proposal.md` written and explicitly approved before any scaffolding
- [ ] Delivery model (single dev / + review gates / + parallel subagents for named chunks) chosen and justified in the proposal
- [ ] Secrets kept out of git — `.env.example` names them, real `.env` is untracked and hand-filled
- [ ] Spec written and reviewed before implementation starts
- [ ] Spec breaks the build into named phases with a hard approval gate between them, not one undifferentiated build
- [ ] Each phase gets its own short clarify pass before work starts, not just one clarify pass at the very beginning
- [ ] CLAUDE.md under ~150 lines, checked into git, pruned regularly
- [ ] Skills used for anything project-specific but not always-relevant
- [ ] Simplest architecture that could work (pipeline before agent, single agent before multi-agent)
- [ ] Research presented as a second opinion the person can push back on, not just a menu to pick from — especially inside their own domain expertise
- [ ] High-stakes or domain-expertise decisions use a named elicitation technique (§7b), not just a generic "thoughts?" prompt
- [ ] Structured outputs wherever a decision feeds downstream logic
- [ ] Golden dataset + eval suite runs in CI, not just locally
- [ ] Every phase has checkable acceptance criteria and a literal `Verify: run X → see Y` line
- [ ] Bug fixes specify the class and both edges, plus "previously-correct inputs unchanged" (§3c)
- [ ] Every acceptance criterion has a test; the suite passes before each commit
- [ ] Disputed criteria are ruled on by the person and logged in Deviations, never decided by the builder or reviewer
- [ ] Adversarial review subagent checks the diff against the spec once per milestone, fails only on unmet criteria or regressions, and stops after three fix rounds
- [ ] Deviations from spec (§3b) recorded during Build and Verify, not reconstructed later
- [ ] Deployment target chosen at spec time, matched to app shape
- [ ] Tracing wired up before first real user, not after the first incident
- [ ] Production monitoring feeds back into the next Spec

---

## 11. Mapping this to what you already use

*(A snapshot of your toolkit as of when this was written — not a standing recommendation. Check current options before reusing any of these on a new project; the landscape moves fast.)*

You don't need new tools for most of this — it's mostly about sequencing what you already reach for:

- **LangGraph / LangChain** → the Build stage, for single-agent and pipeline shapes
- **AutoGen (supervisor+worker)**, **Google ADK + A2A** → the multi-agent row of the architecture table, when the task genuinely needs role decomposition
- **RAGAS, LangSmith** → the Verify stage's eval layer, especially for RAG groundedness
- **MLflow tracing on Unity Catalog** → the Monitor stage — you already have this wired up for JLLM; the same pattern (trace every decision, score it against a rubric) generalizes to any agentic project, not just claims evaluation
- **The JLLM evaluation dimensions** (evidence consistency, hallucination detection, decision validity, rationale sufficiency) → lift these out as a reusable judge-rubric template across your portfolio projects, not just the Suncorp system
- **MCP servers** (you've already built these for the sustainability platform and car-deal finder) → the natural distribution format when a project graduates from demo to something others can plug into

---

## 12. What's deliberately left out (for now)

This is a framework for building applications well and quickly — spec, scaffold, build, verify, ship, monitor. It's not a production-hardening framework, and that's on purpose: bolting those concerns onto a fast-iteration loop slows down every project, including the ones that never touch production traffic.

When a project actually needs to productionize, treat these as a follow-on framework rather than trying to satisfy them from day one:

- **Security & adversarial robustness** — prompt injection defense, output sanitization, secrets handling in tool calls, jailbreak resistance
- **Cost & latency engineering** — model selection per subtask, prompt caching strategy, runaway-cost circuit breakers
- **Production failure handling** — kill switches, degraded-mode fallback, rollback of a bad prompt/model version
- **Compliance & audit trail** — data residency, retention policy, explainability, accountability for a wrong decision
- **Eval calibration** — checking the judge LLM itself against human ground truth, not just trusting its score
- **Production monitoring & observability** — tracing, drift detection, a judge model reviewing live traffic. This isn't a skill or scheduled task yet. Whether and when a given project needs it is a call for the app-architect skill to make explicitly during intake — flag it, don't build it — so the question doesn't just get forgotten.

Revisit this list at the point a project crosses from demo/portfolio into something real users or real money touch — not before.
