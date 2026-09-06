---
name: reset
description: Resets a project scaffolded by this framework back to a clean slate so app-architect can run a fresh consultation on it. Archives everything the framework generated (CLAUDE.md, specs/, src/, notebooks/, evals/, data/, scaffold config, app entrypoints) into a timestamped .archive/ folder inside the project rather than deleting it outright, then clears it from the working tree — leaves .git/ and any prior .archive/ contents untouched. Defaults to a full wipe; if the person asks for a narrower reset (e.g. keep the spec, only clear generated code) do that instead. Use whenever the person asks to clean up, reset, start over, wipe, or clear a project/workspace built with this framework so they can begin again.
---

# Reset

You're clearing a project back to a blank slate, not deleting the person's work. The whole point of this skill is making "start again" safe — nothing gets permanently destroyed, it gets moved out of the way.

Read `${CLAUDE_PLUGIN_ROOT}/references/framework.md` §2 for the scaffold shape you're resetting back past.

## How to run a reset

1. **Confirm the target and scope before touching anything.** Default to the current project directory unless told otherwise. List what actually exists there — `CLAUDE.md`, `AGENTS.md`, `.claude/`, `specs/`, `notebooks/`, `src/`, `evals/`, `data/`, `.github/`, `Dockerfile`, `README.md`, `requirements.txt`, `.gitignore`, any app entrypoint (`app.py` or equivalent) — and confirm with the person that a full reset is what they want, not a narrower one (step 4). This is a disruptive action; a quick "here's what I'm about to archive" beats a silent sweep even though nothing is truly destroyed.

2. **Never touch `.git/`, and never touch anything outside the project directory.** If it's a git repo, working-tree files get archived and cleared exactly as usual, but git history and `.git/` itself are left alone — this is a workspace reset, not a repo reset. If there are uncommitted changes, say so before proceeding; archiving preserves them, but `git status` will look different afterward and that shouldn't be a surprise.

3. **Archive, don't delete.** Create `.archive/<UTC-timestamp>/` inside the project (creating `.archive/` itself if it doesn't exist yet). Move every top-level file/folder being reset into it, preserving relative structure. Never sweep an existing `.archive/` into a new one — prior resets stay exactly where they were. This is what makes a bad reset trivially recoverable: the person can just move things back out.

4. **Default to a full reset; narrow it only if asked.** Unless the person specifically asks to keep something ("reset but keep the spec," "just clear the generated code"), archive everything the framework scaffolds and whatever got built on top of it — effectively all of framework.md §2's layout. If asked for a narrower reset, move only the specific pieces named and state explicitly what's being kept and why.

5. **Report exactly what happened, then stop.** State what got archived and where (`.archive/<timestamp>/...`), confirm the project directory now matches what was asked for (empty, or down to just what was kept), and hand back to app-architect for the next consultation. Don't start one yourself — running a fresh intake isn't this skill's job.

## When not to run

- If the directory doesn't look like something this framework scaffolded (no `CLAUDE.md`, no `specs/`, nothing recognizable), say so and double-check what the person actually wants archived before moving anything — don't assume every file in an unfamiliar directory is framework output.
- If a full reset would archive uncommitted git changes the person hasn't mentioned, surface that explicitly before proceeding rather than finding out after.

## Tone

Matter-of-fact and precise about what's about to move and where it's going — this is closer to "tidying up" than "tearing down," and the person should feel that from how you describe it, not just from the archive existing after the fact.
