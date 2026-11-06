#!/usr/bin/env python3
"""Tests for the APM hook shim (.apm/hooks/manual_hook.py): it finds check_manual.py in whichever target folder
the skill was installed to, forwards the hook JSON and exit code, and never blocks when the skill is absent.
Skipped when the shim is not next to this skill (an installed copy keeps the shim under <target>/hooks/)."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
SHIM = Path(__file__).resolve().parents[4] / "hooks" / "manual_hook.py"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_check_manual import GOOD, write  # noqa: E402


@unittest.skipUnless(SHIM.is_file(), "the hook shim is not next to this skill")
class ShimTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        pkg = self.root / "packages" / "fam" / "pkg"
        write(pkg / "apm.yml", "name: pkg\nversion: 1.0.0\n")
        write(pkg / ".apm" / "skills" / "do-thing" / "SKILL.md",
              "---\nname: do-thing\ndescription: Does a thing.\nargument-hint: \"<x> [mode=a|b]\"\n"
              "context: fork\nagent: worker\ndisable-model-invocation: true\n---\n")
        write(self.root / "docs-catalog.json", json.dumps({"required_pages": [], "generated_targets": {}}))
        write(self.root / "docs" / "overview.md", "# Overview\n")
        self.readme = pkg / "README.md"
        write(self.readme, GOOD)

    def tearDown(self):
        self.tmp.cleanup()

    def install_checker(self, target=".claude"):
        dest = self.root / target / "skills" / "documenting-agent-packages" / "scripts"
        dest.mkdir(parents=True)
        for name in ("check_manual.py", "check_links.py", "docs_catalog.py"):
            shutil.copy2(SCRIPTS / name, dest / name)

    def run_shim(self, event, payload, root=None):
        env = dict(os.environ, CLAUDE_PROJECT_DIR=str(root or self.root), PYTHONDONTWRITEBYTECODE="1")
        done = subprocess.run([sys.executable, str(SHIM), event], input=json.dumps(payload).encode("utf-8"),
                              capture_output=True, env=env, cwd=str(self.root))
        return done.returncode, done.stderr.decode("utf-8", "replace")

    def payload(self, path):
        return {"hook_event_name": "PostToolUse", "tool_name": "Write", "tool_input": {"file_path": str(path)}}

    def test_good_manual_passes_through_the_claude_install(self):
        self.install_checker(".claude")
        self.assertEqual(self.run_shim("post-edit", self.payload(self.readme))[0], 0)

    def test_broken_manual_returns_exit_2_and_the_message(self):
        self.install_checker(".claude")
        self.readme.write_text(GOOD.replace("## Quick Start", "## Something Else"), encoding="utf-8")
        rc, err = self.run_shim("post-edit", self.payload(self.readme))
        self.assertEqual(rc, 2)
        self.assertIn("Quick Start", err)

    def test_other_targets_are_searched_too(self):
        self.install_checker(".github")
        self.readme.write_text(GOOD.replace("## Limits and constraints", "## Notes"), encoding="utf-8")
        self.assertEqual(self.run_shim("post-edit", self.payload(self.readme))[0], 2)

    def test_source_checkout_is_the_fallback(self):
        dest = self.root / "packages" / "fam" / "docs-pkg" / ".apm" / "skills" / "documenting-agent-packages" / "scripts"
        dest.mkdir(parents=True)
        for name in ("check_manual.py", "check_links.py", "docs_catalog.py"):
            shutil.copy2(SCRIPTS / name, dest / name)
        self.readme.write_text(GOOD.replace("## Related", "## Elsewhere"), encoding="utf-8")
        self.assertEqual(self.run_shim("post-edit", self.payload(self.readme))[0], 2)

    def test_a_missing_install_never_blocks_editing(self):
        self.readme.write_text("# broken\n", encoding="utf-8")
        self.assertEqual(self.run_shim("post-edit", self.payload(self.readme)), (0, ""))

    def test_files_that_are_not_manuals_pass(self):
        self.install_checker(".claude")
        other = self.root / "src" / "main.py"
        write(other, "print('x')\n")
        self.assertEqual(self.run_shim("post-edit", self.payload(other))[0], 0)

    def test_unknown_event_is_harmless(self):
        self.install_checker(".claude")
        rc, err = self.run_shim("nonsense", {})
        self.assertEqual(rc, 0)
        self.assertIn("usage", err)


if __name__ == "__main__":
    unittest.main()
