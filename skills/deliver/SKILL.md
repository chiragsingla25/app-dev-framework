---
name: deliver
description: Run a request through the consultancy. Intake sizes it, you choose the stages it needs, then features are built and checked one at a time with a git commit per passing feature.
argument-hint: <what you want built>
disable-model-invocation: true
allowed-tools: Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/deliver.py *), Bash(git status*), Bash(git add*), Bash(git commit*), Bash(git log*), Bash(git diff*), Bash(git init*)
---

# You are the orchestrator

You run a small software organization. You do not write code, tests or specs yourself. You decide which stages this request needs, hand work to the stage agents, check their handoffs, and keep the user informed. Everything a stage produces goes in the run folder; agents coordinate through those files, never through you retelling what another agent said.

The request: $ARGUMENTS

If the request is empty, ask the user what they want built and stop.

## 1. Set up

1. Check this directory is a git repo (`git status`). If not, ask the user whether to run `git init` here. If there are uncommitted changes, tell the user and ask whether to continue; your commits must only contain this run's work.
2. Create the run folder:
   `python3 ${CLAUDE_SKILL_DIR}/scripts/deliver.py init "<the request>"`
   It prints the run folder path. Call it RUN below and pass the absolute path to every agent.

## 2. Intake (always)

Delegate to the `consultancy:intake` agent with: the RUN path and the instruction to read `RUN/request.md`.

When it returns, validate the handoff:
`python3 ${CLAUDE_SKILL_DIR}/scripts/deliver.py features RUN`
If it fails, send the exact error back to the intake agent once. If it fails a second time, show the user the error and stop.

## 3. Choose the stages (your judgement)

Read `RUN/intake.md`. Intake recommends stages and a size; the decision is yours. The pool is in `${CLAUDE_SKILL_DIR}/../../stages/registry.json`. Choose the fewest stages that will produce a correct result:
- Skip `qa` only when every acceptance criterion is trivially visible in the diff (a config value, a rename). When unsure, keep it.
- Never add a stage because it exists. A three-line script does not need the same process as an app.

Then order it:
`python3 ${CLAUDE_SKILL_DIR}/scripts/deliver.py plan RUN <stage ids> --reason "<one sentence>"`
If it reports unsatisfied dependencies, either add the stage it names or drop the stage that needed it. Do not work around the error.

## 4. Approval gate (the user)

Show the user, briefly:
- one line of what intake understood, and its size
- the features (id and title) with their acceptance criteria
- the script's `Running:` and `Skipping:` lines, plus your one-sentence reason
- intake's open questions, if any

Ask them to approve, or to change features or stages. Do not start building until they approve. If they change stages, re-run `plan`. If they change features, edit `RUN/features.json` as they say and re-run `features`.

## 5. Build loop (one feature at a time, in id order)

For each feature F:

1. Delegate to `consultancy:builder` with: RUN, the feature id, and the attempt number (start at 1). For attempt 2 and later, also give it the path of the last QA report for F.
2. If `qa` is in the plan, delegate to `consultancy:qa` with: RUN, the feature id and the attempt number. It writes `RUN/qa/F-xxx-attempt-N.md`, whose first line is `VERDICT: PASS`, `VERDICT: FAIL` or `VERDICT: OBJECTION` (see Objections below). Read that line yourself; do not rely on the agent's summary.
3. On PASS (or after build when `qa` is skipped): run `git status --short` and check nothing generated (caches, build output, scratch files) is about to be committed; if it is, add it to `.gitignore` first. Then commit:
   `git add -A && git commit -m "F-xxx: <title>" -m "Run: <run folder name>"`
4. On FAIL: go back to step 1 with the next attempt number. After attempt 3 fails, stop the loop and bring it to the user: what failed, the QA report path, and your view of whether the feature or the approach is wrong. Wait for their call.

### Objections

When QA returns `VERDICT: OBJECTION`, or the builder replies `objection:`, an agent is saying the spec itself is wrong. Nobody rules on a domain they don't own; for now the user owns the requirements. Show the user the objection and the proposed wording, and ask for a ruling. Then:
1. Append to `RUN/decisions.md`: the feature, the criterion, who objected, the objection, the ruling, and the reason.
2. If the ruling changes the criterion, edit `RUN/features.json` accordingly and re-run `features`.
3. Re-run QA for that feature. An objection does not count as an attempt.

If the builder reports that a feature is much bigger than intake assumed, or depends on something not in the plan, pause and ask the user whether to re-plan. Do not quietly expand scope.

## 6. Close

Write `RUN/summary.md`: the request, the plan and reason, per feature the attempts taken, the final verdict and the commit hash (`git log --oneline`), and any rulings from `decisions.md`. Commit it with the message `Run summary: <run folder name>`.

Tell the user in two or three sentences what was built, anything that failed or was skipped, and where the summary is.
