import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "deliver" / "scripts" / "deliver.py"
sys.path.insert(0, str(SCRIPT.parent))

import deliver  # noqa: E402

REAL = deliver.load_registry(ROOT / "stages" / "registry.json")

# A bigger pool shaped like the later phases, to prove the ordering logic
# holds once research/journey/mock/architecture are added.
FUTURE = {s["id"]: s for s in [
    {"id": "intake", "agent": "a", "always": True, "needs": ["request"], "produces": ["intake", "features"]},
    {"id": "research", "agent": "a", "needs": ["intake"], "produces": ["research"]},
    {"id": "spec", "agent": "a", "needs": ["intake"], "produces": ["spec"]},
    {"id": "journey", "agent": "a", "needs": ["spec"], "produces": ["journey"]},
    {"id": "mock", "agent": "a", "needs": ["journey"], "produces": ["mock"]},
    {"id": "architecture", "agent": "a", "needs": ["spec"], "produces": ["architecture"]},
    {"id": "build", "agent": "a", "per_feature": True, "needs": ["features"], "produces": ["code"]},
    {"id": "qa", "agent": "a", "per_feature": True, "needs": ["features", "code"], "produces": ["qa-report"]},
]}


class PlanTests(unittest.TestCase):
    def test_intake_always_included(self):
        self.assertEqual(deliver.plan(REAL, ["build"])["order"], ["intake", "build"])

    def test_full_phase_one(self):
        r = deliver.plan(REAL, ["qa", "build"])  # order of request doesn't matter
        self.assertEqual(r["order"], ["intake", "build", "qa"])
        self.assertEqual(r["per_feature"], ["build", "qa"])
        self.assertEqual(r["skipped"], [])

    def test_qa_without_build_is_rejected(self):
        with self.assertRaisesRegex(deliver.PlanError, "qa needs 'code'.*add: build"):
            deliver.plan(REAL, ["qa"])

    def test_unknown_stage(self):
        with self.assertRaisesRegex(deliver.PlanError, "unknown stage"):
            deliver.plan(REAL, ["deploy"])

    def test_mock_without_journey_is_rejected(self):
        with self.assertRaisesRegex(deliver.PlanError, "mock needs 'journey'"):
            deliver.plan(FUTURE, ["spec", "mock", "build"])

    def test_small_project_skips_front_half(self):
        r = deliver.plan(FUTURE, ["build", "qa"])
        self.assertEqual(r["order"], ["intake", "build", "qa"])
        self.assertIn("mock", r["skipped"])

    def test_big_project_order_falls_out_of_dependencies(self):
        r = deliver.plan(FUTURE, ["qa", "mock", "architecture", "journey", "spec", "research", "build"])
        o = r["order"]
        for before, after in [("intake", "spec"), ("spec", "journey"), ("journey", "mock"),
                              ("spec", "architecture"), ("build", "qa")]:
            self.assertLess(o.index(before), o.index(after), f"{before} should precede {after}")

    def test_cycle_detected(self):
        reg = {
            "a": {"id": "a", "agent": "x", "needs": ["b-out"], "produces": ["a-out"]},
            "b": {"id": "b", "agent": "x", "needs": ["a-out"], "produces": ["b-out"]},
        }
        with self.assertRaisesRegex(deliver.PlanError, "cycle"):
            deliver.plan(reg, ["a", "b"])


class FeatureTests(unittest.TestCase):
    good = [{"id": "F-001", "title": "Rename files", "acceptance": ["renames *.txt to *.md"]}]

    def test_good(self):
        self.assertEqual(deliver.validate_features(self.good), [])

    def test_bad_shapes(self):
        self.assertTrue(deliver.validate_features([]))
        self.assertTrue(deliver.validate_features([{"id": "1", "title": "x", "acceptance": ["y"]}]))
        self.assertTrue(deliver.validate_features([{"id": "F-001", "title": "x", "acceptance": []}]))
        dup = self.good + self.good
        self.assertTrue(any("duplicate" in p for p in deliver.validate_features(dup)))


class CliTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)

    def test_init_plan_features_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            r = self.run_cli("init", "Build a CLI that renames files!", "--project", d)
            self.assertEqual(r.returncode, 0, r.stderr)
            run_dir = Path(r.stdout.strip())
            self.assertTrue((run_dir / "request.md").exists())
            self.assertIn("build-a-cli-that-renames-files", run_dir.name)

            r = self.run_cli("plan", str(run_dir), "build", "qa", "--reason", "small script")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("intake -> build -> qa", r.stdout)
            plan = json.loads((run_dir / "plan.json").read_text())
            self.assertEqual(plan["reason"], "small script")

            r = self.run_cli("features", str(run_dir))
            self.assertEqual(r.returncode, 2)  # intake hasn't written it yet
            (run_dir / "features.json").write_text(json.dumps(FeatureTests.good))
            r = self.run_cli("features", str(run_dir))
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("F-001", r.stdout)

    def test_private_run_is_not_committed(self):
        with tempfile.TemporaryDirectory() as d:
            subprocess.run(["git", "init", "-q", d], check=True)
            r = self.run_cli("init", "fix a bug", "--project", d, "--private")
            self.assertEqual(r.returncode, 0, r.stderr)
            run_dir = Path(r.stdout.splitlines()[0])
            self.assertIn("/delivery/", (Path(d) / ".git" / "info" / "exclude").read_text())
            status = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"],
                                    cwd=d, capture_output=True, text=True).stdout
            self.assertNotIn("delivery", status)
            self.assertTrue((run_dir / "request.md").exists())
            # running it twice doesn't duplicate the exclude line
            self.run_cli("init", "another", "--project", d, "--private")
            text = (Path(d) / ".git" / "info" / "exclude").read_text()
            self.assertEqual(text.count("/delivery/"), 1)

    def test_private_outside_git_fails_cleanly(self):
        with tempfile.TemporaryDirectory() as d:
            r = self.run_cli("init", "x", "--project", d, "--private")
            self.assertEqual(r.returncode, 2)
            self.assertIn("not a git repository", r.stderr)

    def test_plan_error_exit_code(self):
        with tempfile.TemporaryDirectory() as d:
            r = self.run_cli("plan", d, "qa")
            self.assertEqual(r.returncode, 2)
            self.assertIn("add: build", r.stderr)


if __name__ == "__main__":
    unittest.main()
