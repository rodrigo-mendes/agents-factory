#!/usr/bin/env python3
"""The old path scripts/gen-docs-catalog.py still works and delegates to the documenting-agent-packages skill.
The full tests of the generator live with the skill (packages/factory/package-docs/.../scripts/tests/)."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

WRAPPER = Path(__file__).resolve().parent.parent / "gen-docs-catalog.py"


def run(*args):
    return subprocess.run([sys.executable, str(WRAPPER), *args], capture_output=True, text=True, encoding="utf-8")


class WrapperTests(unittest.TestCase):
    def test_delegates_with_an_explicit_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "packages").mkdir()
            result = run("--root", tmp, "--check-manuals")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Manual coverage (0 packages, 0 bundles)", result.stdout)

    def test_adds_the_repository_root_when_none_is_given(self):
        result = run("--check-manuals")
        self.assertIn("Manual coverage (", result.stdout)
        self.assertNotIn("0 packages", result.stdout)


if __name__ == "__main__":
    unittest.main()
