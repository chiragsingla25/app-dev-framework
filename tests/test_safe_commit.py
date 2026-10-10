import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "safe_commit.py"
sys.path.insert(0, str(SCRIPT.parent))
import safe_commit  # noqa: E402


def git(d, *args):
    return subprocess.run(["git", *args], cwd=d, capture_output=True, text=True).stdout


def new_repo(d):
    for cmd in (["init", "-q"], ["config", "user.name", "t"], ["config", "user.email", "t@t"]):
        subprocess.run(["git", *cmd], cwd=d, check=True)


def run(d, *args):
    return subprocess.run([sys.executable, str(SCRIPT), "-C", d, *args],
                          capture_output=True, text=True)


class Patterns(unittest.TestCase):
    def test_junk(self):
        self.assertEqual(safe_commit.is_junk("a/.DS_Store"), ".DS_Store")
        self.assertEqual(safe_commit.is_junk("src/__pycache__/m.cpython-310.pyc"), "__pycache__/")
        self.assertEqual(safe_commit.is_junk("nb/.ipynb_checkpoints/x.ipynb"), ".ipynb_checkpoints/")
        self.assertIsNone(safe_commit.is_junk("src/app.py"))
        self.assertIsNone(safe_commit.is_junk("docs/DS_Store.md"))

    def test_secrets(self):
        for p in [".env", "config/.env.local", "certs/server.pem", "id_rsa"]:
            self.assertTrue(safe_commit.is_secret(p), p)
        for p in [".env.example", "env.py", "keys.md", "src/environment.ts"]:
            self.assertFalse(safe_commit.is_secret(p), p)


class Cli(unittest.TestCase):
    def test_clutter_ignored_and_untracked(self):
        with tempfile.TemporaryDirectory() as d:
            new_repo(d)
            (Path(d) / "src").mkdir()
            (Path(d) / "src" / ".DS_Store").write_text("x")
            git(d, "add", "-A"); git(d, "commit", "-qm", "old")
            (Path(d) / ".DS_Store").write_text("x")
            (Path(d) / "src" / "__pycache__").mkdir()
            (Path(d) / "src" / "__pycache__" / "m.pyc").write_text("x")
            (Path(d) / "src" / "app.py").write_text("print(1)\n")
            r = run(d, "-m", "Phase 1: app", "-m", "Spec: specs/x.md")
            self.assertEqual(r.returncode, 0, r.stderr)
            tracked = git(d, "ls-files")
            self.assertIn("src/app.py", tracked)
            self.assertNotIn(".DS_Store", tracked)
            self.assertNotIn("__pycache__", tracked)
            gi = (Path(d) / ".gitignore").read_text()
            self.assertIn(".DS_Store", gi)
            self.assertIn("__pycache__/", gi)
            self.assertEqual(git(d, "status", "--short").strip(), "")
            self.assertIn("Spec: specs/x.md", git(d, "log", "-1", "--format=%B"))

    def test_secret_refused_and_unstaged(self):
        with tempfile.TemporaryDirectory() as d:
            new_repo(d)
            (Path(d) / ".env").write_text("KEY=1")
            (Path(d) / ".env.example").write_text("KEY=")
            r = run(d, "-m", "x")
            self.assertEqual(r.returncode, 2)
            self.assertIn(".env", r.stderr)
            self.assertNotIn(".env.example", r.stderr)
            self.assertEqual(git(d, "diff", "--cached", "--name-only").strip(), "")

    def test_scratch_worktree_inside_repo_refused(self):
        with tempfile.TemporaryDirectory() as d:
            new_repo(d)
            (Path(d) / "a.py").write_text("1\n")
            git(d, "add", "-A"); git(d, "commit", "-qm", "base")
            subprocess.run(["git", "worktree", "add", "-q", "scratch", "HEAD"], cwd=d, check=True)
            (Path(d) / "b.py").write_text("2\n")
            r = run(d, "-m", "x")
            self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
            self.assertIn("scratch", r.stderr)
            self.assertEqual(git(d, "diff", "--cached", "--name-only").strip(), "")

    def test_nothing_to_commit(self):
        with tempfile.TemporaryDirectory() as d:
            new_repo(d)
            self.assertEqual(run(d, "-m", "x").returncode, 3)

    def test_not_a_repo(self):
        with tempfile.TemporaryDirectory() as d:
            r = run(d, "-m", "x")
            self.assertEqual(r.returncode, 2)
            self.assertIn("ERROR", r.stderr)


if __name__ == "__main__":
    unittest.main()
