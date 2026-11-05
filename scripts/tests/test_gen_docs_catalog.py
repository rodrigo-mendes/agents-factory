#!/usr/bin/env python3
"""Tests for scripts/gen-docs-catalog.py: discovery on a fixture tree, block replacement and --check."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "gen-docs-catalog.py"
spec = importlib.util.spec_from_file_location("gen_docs_catalog", SCRIPT)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class FixtureTree(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.packages = self.root / "packages"
        write(self.packages / "fam" / "pkg-a" / "apm.yml",
              "name: agents-factory-pkg-a\nversion: 2.1.0\ndescription: Package A.\n"
              "dependencies:\n  apm:\n    - path: ../pkg-b\n  mcp: []\nincludes: auto\n")
        write(self.packages / "fam" / "pkg-a" / ".apm" / "skills" / "do-thing" / "SKILL.md",
              "---\nname: do-thing\ndescription: >\n  Does a thing.\n  Second line.\n"
              "disable-model-invocation: true\ncontext: fork\n---\nBody\n")
        write(self.packages / "fam" / "pkg-a" / ".apm" / "skills" / "know-how" / "SKILL.md",
              "---\nname: know-how\ndescription: \"Knowledge.\"\n---\nBody\n")
        write(self.packages / "fam" / "pkg-a" / ".apm" / "agents" / "worker.md",
              "---\nname: worker\ndescription: w\nmodel: sonnet\n---\n")
        write(self.packages / "fam" / "pkg-a" / ".apm" / "instructions" / "rule.md", "---\npaths: []\n---\n")
        write(self.packages / "fam" / "pkg-b" / "apm.yml", "name: pkg-b\nversion: 1.0.0\n")
        write(self.packages / "fam" / "pkg-b" / "README.md", "# pkg-b\n")
        # bundles and nested .apm folders must never be counted as packages
        write(self.packages / "bundles" / "bun" / "apm.yml",
              "name: bundle-bun\nversion: 1.0.0\ndescription: >-\n  A bundle.\n  Second line.\n"
              "dependencies:\n  apm:\n    - path: ../../fam/pkg-a\n")
        write(self.packages / "bundles" / "bun" / "export.yml",
              "# comment\nagents:\n  - worker\nskills: cited   # only cited\ninclude:\n  - skills/x*\n")
        write(self.packages / "fam" / "pkg-a" / ".apm" / "skills" / "x" / "apm.yml", "name: nested\n")
        self._orig = gen.PACKAGES
        gen.PACKAGES = self.packages

    def tearDown(self):
        gen.PACKAGES = self._orig
        self.tmp.cleanup()


class DiscoveryTests(FixtureTree):
    def test_counts_exclude_bundles_and_nested(self):
        ps = gen.discover_packages()
        self.assertEqual([p.rel for p in ps], ["fam/pkg-a", "fam/pkg-b"])
        c = gen.counts(ps)
        self.assertEqual((c["packages"], c["skills"], c["commands"], c["knowledge"]), (2, 2, 1, 1))
        self.assertEqual((c["agents"], c["rules"]), (1, 1))

    def test_skill_kinds_and_orchestrators(self):
        ps = gen.discover_packages()
        kinds = {s.name: s.kind for s in ps[0].skills}
        self.assertEqual(kinds, {"do-thing": "command", "know-how": "knowledge"})
        gen.INLINE_ORCHESTRATORS.add("know-how")
        try:
            kinds = {s.name: s.kind for s in gen.discover_packages()[0].skills}
            self.assertEqual(kinds["know-how"], "orchestrator")
        finally:
            gen.INLINE_ORCHESTRATORS.discard("know-how")

    def test_folded_description_and_dependencies(self):
        ps = gen.discover_packages()
        self.assertEqual(ps[0].skills[0].description, "Does a thing. Second line.")
        self.assertEqual(ps[0].skills[1].description, "Knowledge.")
        self.assertEqual(ps[0].dependencies, ["pkg-b"])


class DependencyAndBlockRenderTests(FixtureTree):
    def test_path_form_dependencies_resolve_to_package_names(self):
        ps = gen.discover_packages()
        self.assertEqual(ps[0].dependencies, ["pkg-b"])
        self.assertEqual(gen.parse_dependencies(self.packages / "bundles" / "bun" / "apm.yml"), ["pkg-a"])

    def test_export_spec_scalars_lists_and_comments(self):
        spec = gen.read_export_spec(self.packages / "bundles" / "bun" / "export.yml")
        self.assertEqual(spec, {"agents": ["worker"], "skills": "cited", "include": ["skills/x*"]})

    def test_apm_meta_folded_description(self):
        meta = gen.read_apm_meta(self.packages / "bundles" / "bun" / "apm.yml")
        self.assertEqual((meta["name"], meta["description"]), ("bundle-bun", "A bundle. Second line."))

    def test_installation_block(self):
        ps = gen.discover_packages()
        text = gen.render_installation(ps[0], ps, {"pkg-a"})
        self.assertIn("`agents-factory-pkg-a`", text)
        self.assertIn("`2.1.0`", text)
        self.assertIn("listed directly in the root `apm.yml`", text)
        self.assertIn("| Also installs | `pkg-b` |", text)
        self.assertIn("apm install <path-to-agents-factory>/packages/fam/pkg-a --target claude", text)
        text_b = gen.render_installation(ps[1], ps, set())
        self.assertIn("installed transitively, through `pkg-a`", text_b)

    def test_agents_reference_block(self):
        ps = gen.discover_packages()
        routed = gen.routed_commands(ps)
        self.assertIn("| [`worker`](.apm/agents/worker.md) | sonnet |", gen.render_agents_reference(ps[0], routed))
        self.assertIn("no subagents", gen.render_agents_reference(ps[1], routed))

    def test_bundle_contents_marks_subset_and_links_packages(self):
        ps = gen.discover_packages()
        bundles = gen.discover_bundles()
        self.assertEqual([b.name for b in bundles], ["bun"])
        text = gen.render_bundle_contents(bundles[0], ps)
        self.assertIn("[`pkg-a`](../../fam/pkg-a/README.md)", text)
        self.assertIn("Also installed as dependencies:** [`pkg-b`]", text)
        self.assertIn("Sold as a subset", text)
        self.assertIn("[`/do-thing`](../../fam/pkg-a/README.md#do-thing)", text)


class ManualCheckTests(FixtureTree):
    def test_hint_params_reads_keys_and_flags_only(self):
        hint = "<tech> [mode=a|b] [--apply] (e.g. depth=deep iterations=3)"
        self.assertEqual(gen.hint_params(hint), ["--apply", "depth", "iterations", "mode"])

    def test_section_of_matches_entry_point_headings_not_scenarios(self):
        text = ("### Scenario 1 — uses `/do-thing` once\nnot this\n"
                "## Commands Reference\n### `/do-thing`\nthis one\n#### sub\ndeeper\n### `/other`\nno\n")
        body = gen.section_of(text, "do-thing")
        self.assertIn("this one", body)
        self.assertIn("deeper", body)
        self.assertNotIn("no\n", body.split("deeper")[1])
        self.assertNotIn("not this", body)

    def test_check_manuals_reports_missing_and_passes_when_complete(self):
        ps = gen.discover_packages()
        bundles = gen.discover_bundles()
        _, entries, documented, problems = gen.check_manuals(ps, bundles)
        self.assertEqual((entries, documented), (1, 0))
        self.assertTrue(any("missing section 'Installation'" in p for p in problems))
        self.assertTrue(any("bundle bun: README.md missing" in p for p in problems))
        complete = ("## Installation\n## Quick Start\n## Usage Scenarios\n## Commands Reference\n"
                    "### `/do-thing`\n```text\n/do-thing\n```\n\n"
                    "## Pipeline\n## Agents Reference\n## Limits\n## Related\n")
        write(ps[0].dir / "README.md", complete)
        write(ps[1].dir / "README.md", complete)
        write(self.packages / "bundles" / "bun" / "README.md",
              "<!-- BEGIN GENERATED:contents -->\n<!-- END GENERATED:contents -->\n")
        _, entries, documented, problems = gen.check_manuals(ps, gen.discover_bundles())
        self.assertEqual((entries, documented, problems), (1, 1, []))


class BlockTests(FixtureTree):
    def test_replace_block_only_touches_markers(self):
        text = "head\n<!-- BEGIN GENERATED:totals -->\nold\n<!-- END GENERATED:totals -->\ntail"
        new, found = gen.replace_block(text, "totals", "NEW")
        self.assertTrue(found)
        self.assertEqual(new, "head\n<!-- BEGIN GENERATED:totals -->\nNEW\n<!-- END GENERATED:totals -->\ntail")

    def test_missing_markers_reported(self):
        new, found = gen.replace_block("no markers", "totals", "X")
        self.assertFalse(found)
        self.assertEqual(new, "no markers")

    def test_main_check_detects_stale_then_passes_after_write(self):
        target = self.root / "README.md"
        write(target, "<!-- BEGIN GENERATED:totals -->\nstale\n<!-- END GENERATED:totals -->\n"
                      "<!-- BEGIN GENERATED:packages -->\nstale\n<!-- END GENERATED:packages -->\n")
        orig_targets = gen.TARGETS
        gen.TARGETS = {target: ["totals", "packages"]}
        orig_root = gen.ROOT
        gen.ROOT = self.root
        try:
            self.assertEqual(gen.main(["--check"]), 1)
            self.assertEqual(gen.main([]), 0)
            self.assertEqual(gen.main(["--check"]), 0)
            self.assertIn("| Subagents | 1 |", target.read_text(encoding="utf-8"))
        finally:
            gen.TARGETS = orig_targets
            gen.ROOT = orig_root


if __name__ == "__main__":
    unittest.main()
