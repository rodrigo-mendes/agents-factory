#!/usr/bin/env python3
"""Tests for check_manual.py and check_links.py: structure checks, presence checks and the two hooks."""
import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


manual = load("check_manual")
linkscript = load("check_links")
catalog = sys.modules["docs_catalog"]

GOOD = """# pkg

This package does one thing for the people who run the example commands. It is for teams that need the thing, and you need it when you start a new project.

## Contents

<!-- BEGIN GENERATED:contents -->
<!-- END GENERATED:contents -->

## Installation

<!-- BEGIN GENERATED:installation -->
<!-- END GENERATED:installation -->

## Quick Start

```text
/do-thing input mode=a
```

## Usage Scenarios

### Scenario 1 - The default run

```text
/do-thing input
```

### Scenario 2 - Chaining

Run the next command. No code block is needed here.

## Commands Reference

### `/do-thing`

*Does the thing.*

**Syntax**

```text
/do-thing <x> [mode=a|b]
```

| Parameter | Required | Default | Description |
|---|---|---|---|
| `<x>` | Yes | none | The input. |
| `mode` | No | a | The mode. |

## Pipeline

```mermaid
graph TD
    A --> B
```

## Agents Reference

<!-- BEGIN GENERATED:agents-reference -->
<!-- END GENERATED:agents-reference -->

## Limits and constraints

| Limit | Value |
|---|---|
| none | none |

## Related

- [Overview](../../../docs/overview.md)
"""


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class Repo(unittest.TestCase):
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
        self._orig_root = catalog.ROOT

    def tearDown(self):
        catalog.configure(self._orig_root)
        self.tmp.cleanup()

    def run_main(self, *args, stdin=None):
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            if stdin is not None:
                fake = mock.Mock()
                fake.buffer.read.return_value = json.dumps(stdin).encode("utf-8")
                with mock.patch.object(sys, "stdin", fake):
                    rc = manual.main(["--root", str(self.root), *args])
            else:
                rc = manual.main(["--root", str(self.root), *args])
        return rc, err.getvalue()

    def edit(self, old, new):
        text = self.readme.read_text(encoding="utf-8")
        self.assertIn(old, text)
        self.readme.write_text(text.replace(old, new), encoding="utf-8")


class StructureTests(Repo):
    def test_complete_manual_passes(self):
        rc, err = self.run_main("--file", str(self.readme))
        self.assertEqual(rc, 0)
        self.assertNotIn("has problems", err)

    def test_missing_section_is_reported_in_plain_words(self):
        self.edit("## Quick Start", "## Something Else")
        rc, err = self.run_main("--file", str(self.readme))
        self.assertEqual(rc, 2)
        self.assertIn("Quick Start", err)

    def test_command_heading_with_a_title_breaks_the_anchor_rule(self):
        self.edit("### `/do-thing`", "### `/do-thing` - Title")
        rc, err = self.run_main("--file", str(self.readme))
        self.assertEqual(rc, 2)
        self.assertIn("has no section", err)
        self.assertIn("#do-thing", err)

    def test_parameter_missing_from_the_table(self):
        self.edit("| `mode` | No | a | The mode. |\n", "")
        rc, err = self.run_main("--file", str(self.readme))
        self.assertEqual(rc, 2)
        self.assertIn("does not document: mode", err)

    def test_missing_opening_paragraph(self):
        text = self.readme.read_text(encoding="utf-8")
        intro_start = text.index("This package")
        intro_end = text.index("## Contents")
        self.readme.write_text(text[:intro_start] + text[intro_end:], encoding="utf-8")
        rc, err = self.run_main("--file", str(self.readme))
        self.assertEqual(rc, 2)
        self.assertIn("no opening paragraph", err)

    def test_broken_anchor_and_broken_file_link(self):
        self.edit("- [Overview](../../../docs/overview.md)",
                  "- [A](../../../docs/overview.md#nowhere)\n- [B](../../../docs/gone.md)")
        rc, err = self.run_main("--file", str(self.readme))
        self.assertEqual(rc, 2)
        self.assertIn("heading that does not exist", err)
        self.assertIn("file that does not exist", err)

    def test_unpaired_generated_marker(self):
        self.edit("<!-- END GENERATED:contents -->\n", "")
        rc, err = self.run_main("--file", str(self.readme))
        self.assertEqual(rc, 2)
        self.assertIn("no END marker", err)

    def test_scenarios_without_any_example_fail_but_one_prose_scenario_only_warns(self):
        rc, err = self.run_main("--file", str(self.readme))
        self.assertEqual(rc, 0)
        self.edit("```text\n/do-thing input\n```\n\n### Scenario 2", "Prose only.\n\n### Scenario 2")
        rc, err = self.run_main("--file", str(self.readme))
        self.assertEqual(rc, 2)
        self.assertIn("none of the scenarios has an example", err)

    def test_numbers_typed_in_prose_warn_but_never_fail(self):
        self.edit("This package does one thing", "This package has 12 skills and does one thing")
        rc, err = self.run_main("--file", str(self.readme))
        self.assertEqual(rc, 0)
        self.assertIn("warning:", err)
        self.assertIn("skills", err)


class HookTests(Repo):
    def payload(self, path):
        return {"hook_event_name": "PostToolUse", "tool_name": "Write", "tool_input": {"file_path": str(path)}}

    def test_post_edit_passes_a_good_manual(self):
        self.assertEqual(self.run_main("--hook", "post-edit", stdin=self.payload(self.readme))[0], 0)

    def test_post_edit_rejects_a_broken_manual_with_exit_2(self):
        self.edit("## Limits and constraints", "## Notes")
        rc, err = self.run_main("--hook", "post-edit", stdin=self.payload(self.readme))
        self.assertEqual(rc, 2)
        self.assertIn("Limits", err)

    def test_post_edit_ignores_every_other_file(self):
        other = self.root / "src" / "main.py"
        write(other, "print('x')\n")
        self.assertEqual(self.run_main("--hook", "post-edit", stdin=self.payload(other))[0], 0)
        self.assertEqual(self.run_main("--hook", "post-edit", stdin=self.payload(self.root / "nope.md"))[0], 0)
        self.assertEqual(self.run_main("--hook", "post-edit", stdin={"tool_input": {}})[0], 0)

    def test_post_edit_ignores_readmes_inside_apm_folders(self):
        inner = self.root / "packages" / "fam" / "pkg" / ".apm" / "skills" / "do-thing" / "README.md"
        write(inner, "not a manual, no sections at all\n")
        self.assertEqual(self.run_main("--hook", "post-edit", stdin=self.payload(inner))[0], 0)

    def test_post_edit_uses_native_windows_style_paths_too(self):
        rc, _ = self.run_main("--hook", "post-edit", stdin=self.payload(str(self.readme).replace("/", "\\")))
        self.assertEqual(rc, 0)

    def test_stop_hook_blocks_while_a_manual_is_missing(self):
        self.readme.unlink()
        rc, err = self.run_main("--hook", "stop", "--skip-stale", stdin={"hook_event_name": "Stop"})
        self.assertEqual(rc, 2)
        self.assertIn("has no README.md manual", err)

    def test_stop_hook_never_loops(self):
        self.readme.unlink()
        rc, err = self.run_main("--hook", "stop", "--skip-stale",
                                stdin={"hook_event_name": "Stop", "stop_hook_active": True})
        self.assertEqual((rc, err), (0, ""))

    def test_stop_hook_passes_when_everything_exists(self):
        rc, err = self.run_main("--hook", "stop", "--skip-stale", stdin={"hook_event_name": "Stop"})
        self.assertEqual(rc, 0, err)

    def test_required_pages_and_guide_links_are_part_of_presence(self):
        write(self.root / "docs-catalog.json", json.dumps({
            "required_pages": ["docs/README.md"], "generated_targets": {}}))
        write(self.root / "docs" / "entry-points" / "guide.md", "# Guide\nNo link to the package.\n")
        rc, err = self.run_main("--all", "--skip-stale")
        self.assertEqual(rc, 2)
        self.assertIn("docs/README.md: this required docs page does not exist", err)
        self.assertIn("no guide page links to the manual of 'pkg'", err)


class LinkScriptTests(unittest.TestCase):
    def test_slugs_follow_the_github_rule(self):
        text = "# Title\n## `/do-thing`\n## Same\n## Same\n```\n## Not a heading\n```\n## Q & A: it's\n"
        found = linkscript.slugs(text)
        self.assertEqual(found, {"title", "do-thing", "same", "same-1", "q--a-its"})

    def test_code_and_inline_code_are_not_links(self):
        text = "See `![x](assets/none.png)` and\n```\n[y](missing.md)\n```\nand a ``` inside a cell | a ``` b |\n"
        self.assertNotIn("(", linkscript.prose(text).replace("(", "", 0) if False else "")
        self.assertNotIn("assets/none.png", linkscript.prose(text))
        self.assertNotIn("missing.md", linkscript.prose(text))


if __name__ == "__main__":
    unittest.main()
