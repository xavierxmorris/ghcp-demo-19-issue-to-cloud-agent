from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path

PWSH = shutil.which("pwsh")
ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(PWSH, "PowerShell is optional for the portable Python path")
class RunnerTests(unittest.TestCase):
    def run_script(self, *arguments):
        return subprocess.run(
            [PWSH, "-NoLogo", "-NoProfile", "-NonInteractive", "-File", str(ROOT / "go.ps1"), *arguments],
            cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=30, check=False,
        )

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


if __name__ == "__main__":
    unittest.main()
