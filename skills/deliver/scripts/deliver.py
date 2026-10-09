#!/usr/bin/env python3
"""Deterministic helpers for the /deliver orchestrator.

The orchestrator (an LLM) decides WHICH stages a project needs and WHEN QA
should look. This script does everything that shouldn't be a judgement call:
  - where a run's files live              (init)
  - the order stages run in               (plan, from each stage's needs/produces)
  - which features each QA round covers   (plan --qa-after)
  - whether intake's handoff is usable    (features)
  - what a QA round decided, per feature  (verdicts)
  - committing without junk or secrets    (commit)
  - where an interrupted run got to       (status)

Standard library only, so it runs anywhere Claude Code runs.
"""
from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import json
import re
import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_REGISTRY = PLUGIN_ROOT / "stages" / "registry.json"
STARTING_ARTIFACTS = {"request"}

# OS and tool clutter that must never be committed: (filename glob, .gitignore line)
JUNK = [
    (".DS_Store", ".DS_Store"),
    ("._*", "._*"),
    ("Thumbs.db", "Thumbs.db"),
    ("desktop.ini", "desktop.ini"),
    ("*.pyc", "*.pyc"),
]
JUNK_DIRS = [("__pycache__", "__pycache__/")]
# Files that look like secrets. Committing one is refused, not fixed silently.
SECRETS = [".env", ".env.*", "*.pem", "*.key", "id_rsa", "id_ed25519", "*.p12"]
SECRET_OK = [".env.example", ".env.sample", ".env.template"]

VERDICT_RE = re.compile(r"^\s*[-*]?\s*(F-\d{3})\s*:\s*(PASS|FAIL|OBJECTION)\b", re.M)
FIRST_LINE_RE = re.compile(r"^VERDICT:\s*(PASS|FAIL|OBJECTION)\s*$")


class PlanError(Exception):
    pass


# ---------- registry + planning (pure functions, unit-tested) ----------

def load_registry(path: Path) -> dict[str, dict]:
    data = json.loads(Path(path).read_text())
    stages = {}
    for s in data["stages"]:
        if s["id"] in stages:
            raise PlanError(f"duplicate stage id in registry: {s['id']}")
        stages[s["id"]] = s
    return stages


def plan(registry: dict[str, dict], requested: list[str]) -> dict:
    """Return the run order for the requested stages.

    Stages marked `always` are added automatically. Every artifact a stage
    `needs` must be produced by an earlier selected stage (or be a starting
    artifact). Order is derived from those dependencies; ties keep registry
    order so plans are stable and readable.
    """
    unknown = [s for s in requested if s not in registry]
    if unknown:
        raise PlanError(
            f"unknown stage(s): {', '.join(unknown)}. "
            f"Known: {', '.join(registry)}"
        )

    selected = [sid for sid in registry
                if sid in requested or registry[sid].get("always")]

    producers: dict[str, list[str]] = {}
    for sid in selected:
        for art in registry[sid].get("produces", []):
            producers.setdefault(art, []).append(sid)

    missing = []
    for sid in selected:
        for need in registry[sid].get("needs", []):
            if need in STARTING_ARTIFACTS or need in producers:
                continue
            could = [o for o, s in registry.items()
                     if need in s.get("produces", [])]
            hint = f" (add: {', '.join(could)})" if could else " (no stage produces it)"
            missing.append(f"{sid} needs '{need}'{hint}")
    if missing:
        raise PlanError("unsatisfied dependencies: " + "; ".join(missing))

    deps = {sid: set() for sid in selected}
    for sid in selected:
        for need in registry[sid].get("needs", []):
            for p in producers.get(need, []):
                if p != sid:
                    deps[sid].add(p)

    order: list[str] = []
    remaining = list(selected)
    while remaining:
        ready = [s for s in remaining if deps[s] <= set(order)]
        if not ready:
            raise PlanError("dependency cycle between: " + ", ".join(remaining))
        order.append(ready[0])
        remaining.remove(ready[0])

    return {
        "order": order,
        "skipped": [sid for sid in registry if sid not in selected],
        "per_feature": [sid for sid in order if registry[sid].get("per_feature")],
        "at_checkpoints": [sid for sid in order if registry[sid].get("at_checkpoints")],
        "agents": {sid: registry[sid]["agent"] for sid in order},
    }


def qa_batches(feature_ids: list[str], qa_after: list[str]) -> list[list[str]]:
    """Split features (in build order) into QA rounds.

    QA runs after each feature named in qa_after, and always after the last
    feature. Default (no qa_after) is a single round at the end.
    """
    if not feature_ids:
        raise PlanError("no features to check")
    unknown = [f for f in qa_after if f not in feature_ids]
    if unknown:
        raise PlanError(f"--qa-after names unknown feature(s): {', '.join(unknown)}")
    cut = set(qa_after) | {feature_ids[-1]}
    batches, current = [], []
    for fid in feature_ids:
        current.append(fid)
        if fid in cut:
            batches.append(current)
            current = []
    return batches


def validate_features(data) -> list[str]:
    """Return a list of problems with features.json (empty list = usable)."""
    if not isinstance(data, list) or not data:
        return ["features.json must be a non-empty list"]
    problems, seen = [], set()
    for i, f in enumerate(data):
        where = f"feature[{i}]"
        if not isinstance(f, dict):
            problems.append(f"{where} is not an object")
            continue
        fid = f.get("id", "")
        if not re.fullmatch(r"F-\d{3}", str(fid)):
            problems.append(f"{where} id must look like F-001, got {fid!r}")
        elif fid in seen:
            problems.append(f"{where} duplicate id {fid}")
        seen.add(fid)
        if not str(f.get("title", "")).strip():
            problems.append(f"{where} ({fid}) has no title")
        acc = f.get("acceptance")
        if not isinstance(acc, list) or not acc or not all(str(a).strip() for a in acc):
            problems.append(f"{where} ({fid}) needs at least one acceptance criterion")
    return problems


def parse_verdicts(text: str, expect: list[str] | None = None) -> tuple[dict[str, str], list[str]]:
    """Read a QA round report. Returns ({feature: verdict}, problems)."""
    problems = []
    lines = text.splitlines()
    m = FIRST_LINE_RE.match(lines[0].strip()) if lines else None
    if not m:
        problems.append("first line must be exactly 'VERDICT: PASS|FAIL|OBJECTION'")
    verdicts: dict[str, str] = {}
    for fid, v in VERDICT_RE.findall(text):
        if fid in verdicts and verdicts[fid] != v:
            problems.append(f"{fid} has conflicting verdicts")
        verdicts.setdefault(fid, v)
    for fid in expect or []:
        if fid not in verdicts:
            problems.append(f"no verdict line for {fid} (expected '{fid}: PASS|FAIL|OBJECTION')")
    extra = [f for f in verdicts if expect and f not in expect]
    if extra:
        problems.append(f"verdicts for features not in this round: {', '.join(extra)}")
    if m and verdicts:
        vals = set(verdicts.values())
        overall = "OBJECTION" if "OBJECTION" in vals else "FAIL" if "FAIL" in vals else "PASS"
        if m.group(1) != overall:
            problems.append(f"first line says {m.group(1)} but the per-feature verdicts add up to {overall}")
    return verdicts, problems


def slugify(text: str, limit: int = 40) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return (slug[:limit].rstrip("-")) or "run"


# ---------- git helpers ----------

def git(project: Path, *args, check=True) -> str:
    out = subprocess.run(["git", *args], cwd=project, capture_output=True, text=True)
    if check and out.returncode != 0:
        raise PlanError(f"git {' '.join(args)} failed: {out.stderr.strip() or out.stdout.strip()}")
    return out.stdout


def is_junk(path: str) -> str | None:
    """Return the .gitignore line that covers path if it is clutter, else None."""
    parts = path.split("/")
    for d, line in JUNK_DIRS:
        if d in parts[:-1]:
            return line
    name = parts[-1]
    for pat, line in JUNK:
        if fnmatch.fnmatch(name, pat):
            return line
    return None


def is_secret(path: str) -> bool:
    name = path.split("/")[-1]
    if name in SECRET_OK:
        return False
    return any(fnmatch.fnmatch(name, p) for p in SECRETS)


def clean_junk(project: Path) -> list[str]:
    """Ignore and untrack clutter. Returns a list of what was done."""
    tracked = [p for p in git(project, "ls-files", "-z").split("\0") if p]
    untracked = [p for p in git(project, "ls-files", "-z", "--others",
                                "--exclude-standard").split("\0") if p]
    lines_needed, to_untrack = set(), []
    for p in tracked + untracked:
        line = is_junk(p)
        if line:
            lines_needed.add(line)
            if p in tracked:
                to_untrack.append(p)
    done = []
    gi = project / ".gitignore"
    existing = gi.read_text().splitlines() if gi.exists() else []
    new = sorted(l for l in lines_needed if l not in existing)
    if new:
        with gi.open("a") as fh:
            if existing and existing[-1].strip() != "":
                fh.write("\n")
            fh.write("\n".join(new) + "\n")
        done.append("added to .gitignore: " + ", ".join(new))
    if to_untrack:
        git(project, "rm", "--cached", "-q", "--", *to_untrack)
        done.append("stopped tracking: " + ", ".join(to_untrack))
    return done


# ---------- CLI ----------

def exclude_locally(project: Path, pattern: str = "/delivery/") -> Path:
    """Add pattern to the repo's .git/info/exclude (a local, never-committed ignore)."""
    out = subprocess.run(["git", "rev-parse", "--git-dir"], cwd=project,
                         capture_output=True, text=True)
    if out.returncode != 0:
        raise PlanError(f"{project} is not a git repository")
    git_dir = Path(out.stdout.strip())
    if not git_dir.is_absolute():
        git_dir = project / git_dir
    exclude = git_dir / "info" / "exclude"
    exclude.parent.mkdir(parents=True, exist_ok=True)
    lines = exclude.read_text().splitlines() if exclude.exists() else []
    if pattern not in lines:
        with exclude.open("a") as fh:
            if lines and lines[-1] != "":
                fh.write("\n")
            fh.write(pattern + "\n")
    return exclude


def project_of(run_dir: Path) -> Path:
    # RUN is <project>/delivery/<run name>
    return run_dir.resolve().parents[1]


def load_features(run_dir: Path) -> list[dict]:
    return json.loads((run_dir / "features.json").read_text())


def cmd_init(args) -> int:
    project = Path(args.project).resolve()
    if args.private:
        try:
            exclude_locally(project)
        except PlanError as e:
            print(f"INIT ERROR: {e}", file=sys.stderr)
            return 2
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = project / "delivery" / f"{stamp}-{slugify(args.request)}"
    run_dir.mkdir(parents=True, exist_ok=False)
    (run_dir / "request.md").write_text(f"# Request\n\n{args.request.strip()}\n")
    (run_dir / "qa").mkdir()
    print(run_dir)
    if args.private:
        print("Run files are excluded from git (.git/info/exclude); commits will contain project changes only.")
    return 0


def cmd_plan(args) -> int:
    run_dir = Path(args.run_dir)
    registry = load_registry(Path(args.registry))
    try:
        result = plan(registry, args.stages)
        if result["at_checkpoints"]:
            fpath = run_dir / "features.json"
            if fpath.exists():
                ids = [f["id"] for f in json.loads(fpath.read_text())]
                result["qa_rounds"] = qa_batches(ids, args.qa_after)
            elif args.qa_after:
                raise PlanError("--qa-after needs features.json; run intake first")
            else:
                result["qa_rounds"] = "end"
        elif args.qa_after:
            raise PlanError("--qa-after given but qa is not in the plan")
    except PlanError as e:
        print(f"PLAN ERROR: {e}", file=sys.stderr)
        return 2
    result["reason"] = args.reason or ""
    result["created"] = dt.datetime.now().isoformat(timespec="seconds")
    (run_dir / "plan.json").write_text(json.dumps(result, indent=2) + "\n")
    print("Running: " + " -> ".join(result["order"]))
    print("Skipping: " + (", ".join(result["skipped"]) or "nothing"))
    if result["per_feature"]:
        print("Looped per feature: " + ", ".join(result["per_feature"]))
    rounds = result.get("qa_rounds")
    if isinstance(rounds, list):
        desc = "; ".join(f"after {b[-1]} ({', '.join(b)})" for b in rounds)
        print(f"QA rounds: {len(rounds)} - {desc}")
    elif rounds == "end":
        print("QA rounds: 1 - after the last feature")
    return 0


def cmd_features(args) -> int:
    path = Path(args.run_dir) / "features.json"
    if not path.exists():
        print(f"HANDOFF ERROR: {path} does not exist", file=sys.stderr)
        return 2
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        print(f"HANDOFF ERROR: features.json is not valid JSON: {e}", file=sys.stderr)
        return 2
    problems = validate_features(data)
    if problems:
        print("HANDOFF ERROR:\n  " + "\n  ".join(problems), file=sys.stderr)
        return 2
    for f in data:
        print(f"{f['id']}\t{f['title']}")
    return 0


def cmd_verdicts(args) -> int:
    path = Path(args.run_dir) / "qa" / f"round-{args.round}.md"
    if not path.exists():
        print(f"QA ERROR: {path} does not exist", file=sys.stderr)
        return 2
    verdicts, problems = parse_verdicts(path.read_text(), args.expect)
    if problems:
        print("QA ERROR:\n  " + "\n  ".join(problems), file=sys.stderr)
        return 2
    for fid, v in verdicts.items():
        print(f"{fid}\t{v}")
    return 0


def cmd_commit(args) -> int:
    run_dir = Path(args.run_dir)
    project = project_of(run_dir)
    try:
        for line in clean_junk(project):
            print(line)
        git(project, "add", "-A")
        staged = [p for p in git(project, "diff", "--cached", "--name-only", "-z").split("\0") if p]
        secrets = [p for p in staged if is_secret(p)]
        if secrets:
            git(project, "reset", "-q")
            print("COMMIT ERROR: refusing to commit files that look like secrets: "
                  + ", ".join(secrets) + ". Add them to .gitignore (or tell the user).",
                  file=sys.stderr)
            return 2
        if not staged:
            print("COMMIT ERROR: nothing to commit", file=sys.stderr)
            return 3
        git(project, "commit", "-q", "-m", args.message, "-m", f"Run: {run_dir.resolve().name}")
        print(git(project, "log", "-1", "--format=%h %s").strip())
        left = git(project, "status", "--short").strip()
        if left:
            print("LEFT OVER after commit (hooks or formatters?):\n" + left)
    except PlanError as e:
        print(f"COMMIT ERROR: {e}", file=sys.stderr)
        return 2
    return 0


def cmd_status(args) -> int:
    run_dir = Path(args.run_dir).resolve()
    project = project_of(run_dir)
    try:
        feats = load_features(run_dir)
    except (OSError, json.JSONDecodeError):
        print("no usable features.json yet: intake has not finished")
        return 0
    subjects = git(project, "log", "--format=%h %s", f"--grep=Run: {run_dir.name}",
                   check=False).splitlines()
    qa_dir = run_dir / "qa"
    last_qa: dict[str, str] = {}
    rounds = sorted(qa_dir.glob("round-*.md"),
                    key=lambda p: int(re.sub(r"\D", "", p.stem) or 0)) if qa_dir.exists() else []
    for r in rounds:
        verdicts, _ = parse_verdicts(r.read_text())
        for fid, v in verdicts.items():
            last_qa[fid] = f"{v} ({r.name})"
    # older runs wrote one report per feature attempt
    for r in sorted(qa_dir.glob("F-*-attempt-*.md")) if qa_dir.exists() else []:
        m = FIRST_LINE_RE.match(r.read_text().splitlines()[0].strip()) if r.stat().st_size else None
        if m:
            last_qa[r.name[:5]] = f"{m.group(1)} ({r.name})"
    print("feature\tcommits\tlast QA\ttitle")
    for f in feats:
        fid = f["id"]
        hashes = [s.split()[0] for s in subjects if s.split(" ", 1)[1].startswith(fid)]
        print(f"{fid}\t{','.join(reversed(hashes)) or '-'}\t{last_qa.get(fid, '-')}\t{f['title']}")
    dirty = git(project, "status", "--short").strip()
    print("uncommitted changes: " + ("yes" if dirty else "none"))
    print("summary.md: " + ("written" if (run_dir / "summary.md").exists() else "not yet"))
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="deliver.py")
    sub = p.add_subparsers(dest="cmd", required=True)

    pi = sub.add_parser("init", help="create a run folder for a request")
    pi.add_argument("request")
    pi.add_argument("--project", default=".")
    pi.add_argument("--private", action="store_true",
                    help="keep run files out of commits (for repos you don't own)")
    pi.set_defaults(fn=cmd_init)

    pp = sub.add_parser("plan", help="order the chosen stages and write plan.json")
    pp.add_argument("run_dir")
    pp.add_argument("stages", nargs="*")
    pp.add_argument("--reason", default="")
    pp.add_argument("--qa-after", nargs="*", default=[], metavar="F-xxx",
                    help="extra QA checkpoints; QA always runs after the last feature")
    pp.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    pp.set_defaults(fn=cmd_plan)

    pf = sub.add_parser("features", help="validate features.json and list feature ids")
    pf.add_argument("run_dir")
    pf.set_defaults(fn=cmd_features)

    pv = sub.add_parser("verdicts", help="read RUN/qa/round-N.md and list per-feature verdicts")
    pv.add_argument("run_dir")
    pv.add_argument("round", type=int)
    pv.add_argument("--expect", nargs="*", default=None, metavar="F-xxx")
    pv.set_defaults(fn=cmd_verdicts)

    pc = sub.add_parser("commit", help="ignore/untrack clutter, refuse secrets, commit everything")
    pc.add_argument("run_dir")
    pc.add_argument("-m", "--message", required=True)
    pc.set_defaults(fn=cmd_commit)

    ps = sub.add_parser("status", help="where a run got to: commits and last QA verdict per feature")
    ps.add_argument("run_dir")
    ps.set_defaults(fn=cmd_status)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
