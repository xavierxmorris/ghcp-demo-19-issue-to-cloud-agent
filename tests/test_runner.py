from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

PWSH = shutil.which("pwsh")
ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(PWSH, "PowerShell is optional for the portable Python path")
class RunnerTests(unittest.TestCase):
    def run_script(self, *arguments, root=ROOT):
        return subprocess.run(
            [PWSH, "-NoLogo", "-NoProfile", "-NonInteractive", "-File", str(root / "go.ps1"), *arguments],
            cwd=root, capture_output=True, text=True, encoding="utf-8", timeout=30, check=False,
        )

    def enterprise_workspace(self, root):
        shutil.copy2(ROOT / "go.ps1", root / "go.ps1")
        shutil.copytree(ROOT / "issue_agent", root / "issue_agent", ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(ROOT / "fixtures", root / "fixtures")

    def test_missing_consent_stops_before_python_or_network(self):
        result = self.run_script("-Live", "-Repository", "invalid")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("requires -AcceptLiveRun", result.stderr)

    def test_explicit_false_consent_is_not_treated_as_authorization(self):
        result = self.run_script("-Live", "-AcceptLiveRun:$false", "-Repository", "invalid")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("requires -AcceptLiveRun", result.stderr)

    def test_conflicting_modes_are_not_silently_ignored(self):
        result = self.run_script("-Check", "-Live", "-AcceptLiveRun", "-Repository", "invalid")
        self.assertNotEqual(result.returncode, 0)

    def test_manual_mode_prints_without_running_work(self):
        result = self.run_script("-Manual")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("UNASSIGNED issue", result.stdout)
        self.assertIn("Assignment is not migration completion", result.stdout)
        self.assertIn("Enterprise rehearsal", result.stdout)

    def test_enterprise_and_live_modes_cannot_be_combined(self):
        result = self.run_script("-Enterprise", "-Live", "-AcceptLiveRun", "-Repository", "invalid")
        self.assertNotEqual(result.returncode, 0)

    def test_enterprise_false_does_not_silently_ignore_ledger_options(self):
        result = self.run_script("-Enterprise:$false", "-Ledger", "out/not-created.sqlite3")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("require -Enterprise", result.stderr)

    def test_enterprise_limit_cannot_exceed_the_policy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.enterprise_workspace(root)
            result = self.run_script("-Enterprise", "-MaxNew", "4", "-NoBrowser", root=root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not raise", result.stderr)

    def test_enterprise_runner_executes_local_rehearsal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.enterprise_workspace(root)
            result = self.run_script("-Enterprise", "-NoBrowser", root=root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('"new_local_work_items": 2', result.stdout)
            self.assertIn("no GitHub API", result.stdout)


if __name__ == "__main__":
    unittest.main()
