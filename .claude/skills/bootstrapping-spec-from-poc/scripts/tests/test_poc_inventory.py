"""Unit tests for poc_inventory.py. Run from the skill directory:

    python -m unittest discover -s scripts/tests

Fixtures: tests/fixtures/{quarkus-nextjs,express-react,openapi-only,empty}. Each holds a small,
fake POC; the scripts only read them.
"""
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import poc_inventory as inv  # noqa: E402

FIX = os.path.join(HERE, "fixtures")


def fx(*parts):
    return os.path.join(FIX, *parts)


def run(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = inv.main(argv)
    return code, out.getvalue(), err.getvalue()


def endpoints(data):
    return sorted((e["method"], e["path"]) for e in data["back"]["endpoints"])


class QuarkusNextjs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = inv.build_inventory(fx("quarkus-nextjs", "back"), fx("quarkus-nextjs", "front"))

    def test_jaxrs_endpoints_join_class_and_method_paths(self):
        self.assertEqual(endpoints(self.data),
                         [("GET", "/items"), ("GET", "/items/{id}"), ("POST", "/items")])

    def test_every_finding_has_file_and_line(self):
        for e in self.data["back"]["endpoints"]:
            self.assertTrue(e["file"].endswith("ItemResource.java"))
            self.assertGreater(e["line"], 0)

    def test_nextjs_app_routes(self):
        paths = sorted(r["path"] for r in self.data["front"]["routes"])
        self.assertEqual(paths, ["/items", "/items/[id]"])

    def test_front_call_without_endpoint_is_front_only(self):
        front_only = self.data["cross"]["front_only"]
        self.assertEqual([(f["method"], f["path"]) for f in front_only], [("POST", "/items/{}/archive")])

    def test_unused_endpoint_is_back_only(self):
        self.assertEqual([(b["method"], b["path"]) for b in self.data["cross"]["back_only"]], [("POST", "/items")])

    def test_shortcuts_report_kind_but_never_the_secret_value(self):
        kinds = sorted(s["kind"] for s in self.data["back"]["shortcuts"])
        self.assertIn("hardcoded-secret", kinds)
        self.assertIn("cors-wildcard", kinds)
        self.assertIn("todo", kinds)
        self.assertNotIn("poc-fixture-not-a-real-key", json.dumps(self.data))

    def test_tests_become_scenario_candidates(self):
        names = sorted(t["name"] for t in self.data["back"]["tests"] + self.data["front"]["tests"])
        self.assertIn("create_withoutName_returns400", names)
        self.assertIn("shows empty state when there are no items", names)

    def test_errors_validations_models_states(self):
        self.assertEqual(sorted({e["status"] for e in self.data["back"]["errors"]}), ["201", "400", "404"])
        self.assertEqual(sorted(v["rule"] for v in self.data["back"]["validations"]), ["NotBlank", "Size"])
        self.assertIn("ItemRequest", [m["name"] for m in self.data["back"]["models"]])
        self.assertIn("empty", [s["kind"] for s in self.data["front"]["states"]])
        self.assertTrue(self.data["front"]["forms"])


class ExpressReact(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = inv.build_inventory(fx("express-react", "back"), fx("express-react", "front"))

    def test_express_endpoints(self):
        self.assertEqual(endpoints(self.data),
                         [("DELETE", "/api/orders/:id"), ("GET", "/api/orders"), ("POST", "/api/orders")])

    def test_router_config_routes(self):
        self.assertEqual(sorted(r["path"] for r in self.data["front"]["routes"]), ["/", "/orders"])

    def test_absolute_localhost_call_still_matches(self):
        self.assertEqual(self.data["cross"]["front_only"], [])
        self.assertEqual(len(self.data["cross"]["matched"]), 2)

    def test_cors_and_localhost_shortcuts(self):
        self.assertIn("cors-wildcard", [s["kind"] for s in self.data["back"]["shortcuts"]])
        self.assertIn("localhost-url", [s["kind"] for s in self.data["front"]["shortcuts"]])


class OpenApiOnly(unittest.TestCase):
    def test_openapi_is_primary_source_and_cross_is_absent_without_front(self):
        data = inv.build_inventory(fx("openapi-only", "back"))
        self.assertEqual(len(data["back"]["openapi"]), 1)
        self.assertEqual(endpoints(data), [("GET", "/invoices"), ("GET", "/invoices/{id}"), ("POST", "/invoices")])
        self.assertTrue(all(e["source"] == "openapi" for e in data["back"]["endpoints"]))
        self.assertIsNone(data["cross"])
        self.assertIsNone(data["front"])


class Cli(unittest.TestCase):
    def test_empty_poc_exits_2(self):
        code, _, err = run(["--back", fx("empty", "back")])
        self.assertEqual(code, 2)
        self.assertIn("nothing detected", err)

    def test_no_root_exits_1(self):
        code, _, err = run([])
        self.assertEqual(code, 1)
        self.assertIn("--back or --front", err)

    def test_missing_dir_exits_1(self):
        code, _, _ = run(["--back", fx("does-not-exist")])
        self.assertEqual(code, 1)

    def test_out_writes_json_and_prints_summary(self):
        tmp = tempfile.mkdtemp(prefix="poc-inv-")
        self.addCleanup(shutil.rmtree, tmp, True)
        out_file = os.path.join(tmp, "nested", "inventory.json")
        code, stdout, _ = run(["--back", fx("quarkus-nextjs", "back"), "--front", fx("quarkus-nextjs", "front"),
                               "--out", out_file])
        self.assertEqual(code, 0)
        self.assertIn("FRONT_ONLY: POST /items/{}/archive", stdout)
        self.assertIn("SHORTCUT: hardcoded-secret", stdout)
        with open(out_file, encoding="utf-8") as fh:
            self.assertEqual(json.load(fh)["counts"]["endpoints"], 3)

    def test_skipped_dirs_are_ignored(self):
        tmp = tempfile.mkdtemp(prefix="poc-inv-")
        self.addCleanup(shutil.rmtree, tmp, True)
        os.makedirs(os.path.join(tmp, "node_modules", "lib"))
        with open(os.path.join(tmp, "node_modules", "lib", "x.js"), "w") as fh:
            fh.write('app.get("/hidden", h);\n')
        code, _, _ = run(["--back", tmp])
        self.assertEqual(code, 2)


class Normalize(unittest.TestCase):
    def test_parameter_styles_collapse(self):
        for raw in ("/items/{id}", "/items/:id", "/items/[id]", "/items/<id>", "${BASE}/items/${id}",
                    "http://localhost:8080/items/{id}?x=1"):
            self.assertEqual(inv.normalize_path(raw), "/items/{}", raw)


if __name__ == "__main__":
    unittest.main()
