#!/usr/bin/env python3
"""Commit everything in the current repo, minus clutter and secrets.

    python3 safe_commit.py -m "Phase 2: upload flow (specs/2026-10-10-app.md)"

Before staging, adds any OS/tool clutter it finds (.DS_Store, __pycache__/,
*.pyc, Thumbs.db ...) to .gitignore and untracks copies already committed.
After `git add -A`, refuses (and unstages) if anything looks like a secret.
After committing, warns if the tree is still dirty (a hook or formatter
changed files), so every commit leaves a clean tree.

Exit codes: 0 committed, 2 refused or git error, 3 nothing to commit.
Standard library only.
"""
from __future__ import annotations

import argparse
import fnmatch
import subprocess
import sys
from pathlib import Path

JUNK = [  # (filename glob, .gitignore line)
    (".DS_Store", ".DS_Store"),
    ("._*", "._*"),
    ("Thumbs.db", "Thumbs.db"),
    ("desktop.ini", "desktop.ini"),
    ("*.pyc", "*.pyc"),
]
JUNK_DIRS = [("__pycache__", "__pycache__/"), (".ipynb_checkpoints", ".ipynb_checkpoints/")]
SECRETS = [".env", ".env.*", "*.pem", "*.key", "id_rsa", "id_ed25519", "*.p12"]
SECRET_OK = [".env.example", ".env.sample", ".env.template"]


class GitError(Exception):
    pass


def git(repo: Path, *args: str) -> str:
    out = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True)
    if out.returncode != 0:
        raise GitError(f"git {' '.join(args)}: {(out.stderr or out.stdout).strip()}")
    return out.stdout


def is_junk(path: str) -> str | None:
    """The .gitignore line that covers path if it is clutter, else None."""
    parts = path.split("/")
    for d, line in JUNK_DIRS:
        if d in parts[:-1]:
            return line
    for pat, line in JUNK:
        if fnmatch.fnmatch(parts[-1], pat):
            return line
    return None


def is_secret(path: str) -> bool:
    name = path.split("/")[-1]
    return name not in SECRET_OK and any(fnmatch.fnmatch(name, p) for p in SECRETS)


def clean_junk(repo: Path) -> list[str]:
    tracked = [p for p in git(repo, "ls-files", "-z").split("\0") if p]
    untracked = [p for p in git(repo, "ls-files", "-z", "--others", "--exclude-standard").split("\0") if p]
    needed, untrack = set(), []
    for p in tracked + untracked:
        line = is_junk(p)
        if line:
            needed.add(line)
            if p in tracked:
                untrack.append(p)
    done = []
    gi = repo / ".gitignore"
    existing = gi.read_text().splitlines() if gi.exists() else []
    new = sorted(l for l in needed if l not in existing)
    if new:
        with gi.open("a") as fh:
            if existing and existing[-1].strip():
                fh.write("\n")
            fh.write("\n".join(new) + "\n")
        done.append("added to .gitignore: " + ", ".join(new))
    if untrack:
        git(repo, "rm", "--cached", "-q", "--", *untrack)
        done.append("stopped tracking: " + ", ".join(untrack))
    return done


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("-m", "--message", required=True, action="append",
                    help="commit message; repeat for extra paragraphs")
    ap.add_argument("-C", "--repo", default=".")
    args = ap.parse_args(argv)
    try:
        repo = Path(git(Path(args.repo), "rev-parse", "--show-toplevel").strip())
        for line in clean_junk(repo):
            print(line)
        git(repo, "add", "-A")
        staged = [p for p in git(repo, "diff", "--cached", "--name-only", "-z").split("\0") if p]
        secrets = [p for p in staged if is_secret(p)]
        if secrets:
            git(repo, "reset", "-q")
            print("REFUSED: these look like secrets: " + ", ".join(secrets)
                  + ". Add them to .gitignore, or ask the person.", file=sys.stderr)
            return 2
        if not staged:
            print("nothing to commit", file=sys.stderr)
            return 3
        msg_args = [a for m in args.message for a in ("-m", m)]
        git(repo, "commit", "-q", *msg_args)
        print(git(repo, "log", "-1", "--format=%h %s").strip())
        left = git(repo, "status", "--short").strip()
        if left:
            print("LEFT OVER after commit (a hook or formatter changed files?):\n" + left)
    except GitError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
