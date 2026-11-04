"""Tests for check_feature_coverage.py (unittest, standard library only)."""
import contextlib
import io
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import check_feature_coverage as cfc  # noqa: E402

FIXTURES = os.path.join(HERE, "fixtures")


def run(case, *extra):
    base = os.path.join(FIXTURES, case)
    argv = ["--spec-root", os.path.join(base, "openspec"),
            "--features", os.path.join(base, "features")] + list(extra)
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cfc.main(argv)
    return code, out.getvalue(), err.getvalue()


class CoverageTests(unittest.TestCase):
    def test_complete(self):
        code, out, _ = run("complete", "--json")
        data = json.loads(out)
        self.assertEqual(code, 0)
        self.assertEqual(len(data["covered"]), 2)
        self.assertEqual(data["missing"], [])
        self.assertEqual(data["orphans"], [])

    def test_missing_scenario(self):
        code, out, _ = run("missing-scenario", "--json")
        data = json.loads(out)
        self.assertEqual(code, 1)
        self.assertEqual([m["scenario"] for m in data["missing"]], ["blank name"])
        self.assertEqual(data["summary"]["covered"], 1)

    def test_requirement_without_scenarios_is_a_gap(self):
        code, out, _ = run("empty-requirement", "--json")
        data = json.loads(out)
        self.assertEqual(code, 1)
        self.assertEqual(data["missing"], [])
        self.assertEqual([e["requirement"] for e in data["empty_requirements"]], ["R2"])
        self.assertEqual(data["empty_requirements"][0]["reason"], "no-scenarios")
        self.assertEqual(data["summary"]["empty_requirements"], 1)
        code, out, _ = run("empty-requirement")
        self.assertEqual(code, 1)
        self.assertIn("EMPTY", out)

    def test_orphan_feature(self):
        code, out, _ = run("orphan-feature", "--json")
        data = json.loads(out)
        self.assertEqual(code, 1)
        reasons = {o["scenario"]: o["reason"] for o in data["orphans"]}
        self.assertEqual(reasons["invented behaviour"], "unknown-requirement")
        self.assertEqual(reasons["no requirement tag"], "no-requirement-tag")
        self.assertEqual(data["missing"], [])

    def test_delta_with_plain_keywords(self):
        base = os.path.join(FIXTURES, "delta")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = cfc.main(["--spec-root", os.path.join(base, "openspec"), "--change", "add-x",
                             "--features", os.path.join(base, "features"), "--json"])
        data = json.loads(out.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual([c["requirement"] for c in data["covered"]], ["R2"])

    def test_delta_without_change_flag_finds_nothing(self):
        base = os.path.join(FIXTURES, "delta")
        with contextlib.redirect_stdout(io.StringIO()):
            code = cfc.main(["--spec-root", os.path.join(base, "openspec"),
                             "--features", os.path.join(base, "features")])
        self.assertEqual(code, 2)

    def test_requirement_without_rid_uses_slug_tag(self):
        code, out, _ = run("no-rid", "--json")
        data = json.loads(out)
        self.assertEqual(code, 0)
        self.assertEqual(data["covered"][0]["requirement"], "@req-greet-a-known-visitor")

    def test_no_features_exit_2(self):
        base = os.path.join(FIXTURES, "complete")
        with contextlib.redirect_stdout(io.StringIO()):
            code = cfc.main(["--spec-root", os.path.join(base, "openspec"),
                             "--features", os.path.join(base, "does-not-exist")])
        self.assertEqual(code, 2)

    def test_usage_error_exit_3(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as ctx:
                cfc.main(["--spec-root", "openspec"])
        self.assertEqual(ctx.exception.code, 3)

    def test_strict_without_gherkin_module_warns_and_continues(self):
        try:
            import gherkin.parser  # noqa: F401
            self.skipTest("gherkin module is installed")
        except ImportError:
            pass
        code, _, err = run("complete", "--strict")
        self.assertEqual(code, 0)
        self.assertIn("warning", err)

    def test_rename_moves_base_requirement(self):
        merged = {"R1 Old title": 1}
        self.assertEqual(cfc.req_key("R1 Old title"), cfc.req_key("R1 New title"))
        self.assertNotEqual(cfc.req_key("Old title"), cfc.req_key("New title"))
        self.assertTrue(merged)


if __name__ == "__main__":
    unittest.main()
