#!/usr/bin/env python3
"""Tests for the usage-manual step of scripts/export-bundle.py: link rewriting, filtering of generated
tables, the not-included banner, doc building from a fixture repo and the detector scan."""
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("export_bundle", SCRIPTS / "export-bundle.py")
eb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eb)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


README_A = """# pkg-a

Package A does a thing.

## Installation

<!-- BEGIN GENERATED:installation -->
| Item | Value |
| Source folder | `packages/fam/pkg-a` |
<!-- END GENERATED:installation -->

See [the other manual](../pkg-b/README.md#intro), [a repo file](../../docs/x.md),
[the site](https://example.com/page), [a section](#local) and ![diagram](img/d.png).

## Contents

<!-- BEGIN GENERATED:contents -->
**Depends on:** `pkg-b`
**Used by:** none

| Type | Name | What it does |
|---|---|---|
| command | [`/kept-cmd`](.apm/skills/kept-cmd/SKILL.md) | Kept. |
| command | [`/dropped-cmd`](.apm/skills/dropped-cmd/SKILL.md) | Dropped. |
| agent (sonnet) | [`kept-agent`](.apm/agents/kept-agent.md) | Kept. |
| agent (sonnet) | [`dropped-agent`](.apm/agents/dropped-agent.md) | Dropped. |
| rule | [`kept-rule`](.apm/instructions/kept-rule.md) | Kept. |
<!-- END GENERATED:contents -->

## Agents Reference

<!-- BEGIN GENERATED:agents-reference -->
| Agent | Model |
|---|---|
| [`kept-agent`](.apm/agents/kept-agent.md) | sonnet |
| [`dropped-agent`](.apm/agents/dropped-agent.md) | sonnet |
<!-- END GENERATED:agents-reference -->
"""


class FixtureRepo(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name).resolve()
        self._orig = eb.REPO
        eb.REPO = self.repo
        a = self.repo / "packages" / "fam" / "pkg-a"
        b = self.repo / "packages" / "fam" / "pkg-b"
        write(a / "apm.yml", "name: pkg-a\n")
        write(b / "apm.yml", "name: pkg-b\n")
        write(a / "README.md", README_A)
        write(b / "README.md", "# pkg-b\n\nPackage B.\n")
        for skill in ("kept-cmd", "dropped-cmd"):
            write(a / ".apm" / "skills" / skill / "SKILL.md", f"---\nname: {skill}\n---\n")
        for agent in ("kept-agent", "dropped-agent"):
            write(a / ".apm" / "agents" / f"{agent}.agent.md", f"---\nname: {agent}\n---\n")
        write(a / ".apm" / "instructions" / "kept-rule.instructions.md", "---\npaths: []\n---\n")
        self.a, self.b = a, b

    def tearDown(self):
        eb.REPO = self._orig
        self.tmp.cleanup()

    def owner(self, pkg: Path) -> str:
        return "local:" + pkg.as_posix()


class LinkTests(FixtureRepo):
    def test_links_between_included_packages_stay_local_and_others_become_text(self):
        local = {self.a: "pkg-a.md", self.b: "pkg-b.md"}
        out = eb.rewrite_links(README_A, self.a, local)
        self.assertIn("[the other manual](pkg-b.md#intro)", out)
        self.assertIn("a repo file,", out)
        self.assertNotIn("../../docs/x.md", out)
        self.assertIn("[the site](https://example.com/page)", out)
        self.assertIn("[a section](#local)", out)
        self.assertNotIn("![", out)  # images do not exist in the export

    def test_link_to_a_package_that_is_not_exported_becomes_plain_text(self):
        out = eb.rewrite_links("See [b](../pkg-b/README.md).", self.a, {self.a: "pkg-a.md"})
        self.assertEqual(out, "See b.")


class FilterTests(FixtureRepo):
    def test_filter_replaces_install_and_drops_excluded_rows(self):
        kept = {"skills": {"kept-cmd"}, "agents": {"kept-agent"}, "rules": {"kept-rule"}}
        out = eb.filter_generated(README_A, kept)
        self.assertIn(eb.INSTALL_NOTE, out)
        self.assertNotIn("Source folder", out)
        self.assertIn("`/kept-cmd`", out)
        self.assertNotIn("dropped-cmd", out)
        self.assertNotIn("dropped-agent", out)
        self.assertIn("kept-agent", out)
        self.assertNotIn("**Depends on:**", out)
        self.assertNotIn("**Used by:**", out)

    def test_banner_lists_what_is_missing_and_is_empty_when_complete(self):
        own = eb.own_names(self.a)
        self.assertEqual(own["agents"], {"kept-agent", "dropped-agent"})
        self.assertEqual(own["rules"], {"kept-rule"})
        kept = {"skills": {"kept-cmd"}, "agents": {"kept-agent"}, "rules": {"kept-rule"}}
        banner = eb.not_included_banner(own, kept)
        self.assertIn("`dropped-cmd`", banner)
        self.assertIn("`dropped-agent`", banner)
        self.assertNotIn("rules", banner)
        self.assertEqual(eb.not_included_banner(own, own), "")


class BuildDocsTests(FixtureRepo):
    def test_build_docs_for_a_subset_bundle(self):
        files = [(".claude/skills/kept-cmd/SKILL.md", self.owner(self.a)),
                 (".claude/agents/kept-agent.md", self.owner(self.a)),
                 (".claude/rules/kept-rule.md", self.owner(self.a))]
        docs = eb.build_docs(files, ".claude", "demo-bundle", {"description": "A demo."})
        self.assertEqual(sorted(docs), ["README.md", "pkg-a.md"])
        text = docs["pkg-a.md"]
        self.assertTrue(text.startswith("# pkg-a\n"))
        self.assertIn("includes only part of this package", text)
        self.assertNotIn("GENERATED", text)
        self.assertNotIn("dropped-agent", text.split("Not included:", 1)[1].split("\n", 1)[1])
        self.assertIn("- [pkg-a](pkg-a.md)", docs["README.md"])
        self.assertIn("A demo.", docs["README.md"])

    def test_files_of_unknown_owners_are_ignored(self):
        docs = eb.build_docs([(".claude/skills/x/SKILL.md", "local:/elsewhere/not-a-package")],
                             ".claude", "demo", {})
        self.assertEqual(docs, {})

    def test_package_dir_of_resolves_the_deepest_package_folder(self):
        self.assertEqual(eb.package_dir_of(self.owner(self.a)), self.a)
        self.assertEqual(eb.package_dir_of(self.owner(self.a / ".apm" / "skills")), self.a)
        self.assertIsNone(eb.package_dir_of("local:C:/somewhere/else"))


class DetectorTests(unittest.TestCase):
    def test_scan_docs_blocks_client_names_and_reports_the_doc_file(self):
        findings = eb.scan_docs({"pkg-a.md": "clean line\nBuilt for ACCENTURE projects\n"})
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0][:2], ("docs/pkg-a.md", 2))

    def test_scan_docs_passes_clean_text(self):
        self.assertEqual(eb.scan_docs({"pkg-a.md": "Nothing sensitive here.\n"}), [])


if __name__ == "__main__":
    unittest.main()
