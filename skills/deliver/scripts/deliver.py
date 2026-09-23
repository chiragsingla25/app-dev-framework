#!/usr/bin/env python3
"""Deterministic helpers for the /deliver orchestrator.

The orchestrator (an LLM) decides WHICH stages a project needs.
This script decides everything that shouldn't be a judgement call:
  - where a run's files live            (init)
  - the order stages run in             (plan, from each stage's needs/produces)
  - whether intake's handoff is usable  (features)

Standard library only, so it runs anywhere Claude Code runs.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_REGISTRY = PLUGIN_ROOT / "stages" / "registry.json"
STARTING_ARTIFACTS = {"request"}


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

    # Every need must be satisfiable within the selection.
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

    # Stage-level edges: a stage runs after every selected producer of its needs.
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
        order.append(ready[0])  # registry order breaks ties
        remaining.remove(ready[0])

    return {
        "order": order,
        "skipped": [sid for sid in registry if sid not in selected],
        "per_feature": [sid for sid in order if registry[sid].get("per_feature")],
        "agents": {sid: registry[sid]["agent"] for sid in order},
    }


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


def slugify(text: str, limit: int = 40) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return (slug[:limit].rstrip("-")) or "run"


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
    pp.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    pp.set_defaults(fn=cmd_plan)

    pf = sub.add_parser("features", help="validate features.json and list feature ids")
    pf.add_argument("run_dir")
    pf.set_defaults(fn=cmd_features)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
