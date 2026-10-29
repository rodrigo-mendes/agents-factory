#!/usr/bin/env python3
"""Tests for scripts/oci-cleanup.py. Offline: tests/fakes/fake_cli.py plays the OCI CLI (OCI_CMD),
so nothing ever reaches OCI. Run: python3 tests/run_tests.py
"""
import datetime
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.normpath(os.path.join(HERE, "..", "scripts", "oci-cleanup.py"))
FAKE_CLI = os.path.join(HERE, "fakes", "fake_cli.py")

COMP = "ocid1.compartment.oc1..test"
TEN = "ocid1.tenancy.oc1..test"
MUTATING = ("delete", "remove", "update", "bulk-delete", "schedule-secret-deletion", "schedule-vault-deletion")


def data(items):
    return json.dumps({"data": items})


# One resource (or more) in every phase. Rules match contiguous argv tokens (+ "also" tokens anywhere).
FIXTURE = [
    {"match": ["monitoring", "alarm", "list"], "stdout": data([{"id": "alarm1", "display-name": "alarm-a"}])},
    {"match": ["logging", "log-group", "list"], "stdout": data([{"id": "lg1", "display-name": "lg-a"}])},
    {"match": ["logging", "log", "list"], "stdout": data([{"id": "log1", "display-name": "log-a"}])},
    {"match": ["ons", "topic", "list"], "stdout": data([{"topic-id": "topic1", "name": "topic-a"}])},
    {"match": ["ons", "subscription", "list"], "stdout": data([{"id": "sub1"}])},
    {"match": ["apigateway", "deployment", "list"], "stdout": data([{"id": "dep1", "display-name": "dep-a"}])},
    {"match": ["apigateway", "gateway", "list"], "stdout": ""},
    {"match": ["fn", "application", "list"], "stdout": data([{"id": "app1", "display-name": "app-a"}])},
    {"match": ["fn", "function", "list"], "stdout": data([{"id": "fn1", "display-name": "fn-a"}])},
    {"match": ["vault", "secret", "list"], "stdout": data([
        {"id": "sec1", "secret-name": "sec-a", "lifecycle-state": "ACTIVE"},
        {"id": "sec2", "secret-name": "sec-old", "lifecycle-state": "PENDING_DELETION"}])},
    {"match": ["kms", "vault", "list"], "stdout": data([
        {"id": "vault1", "display-name": "vault-a", "lifecycle-state": "ACTIVE"},
        {"id": "vault2", "display-name": "vault-gone", "lifecycle-state": "DELETED"}])},
    {"match": ["os", "bucket", "list"], "stdout": data([{"name": "bucket-a"}])},
    {"match": ["network", "vcn", "list"], "stdout": data([{"id": "vcn1", "display-name": "vcn-a",
                                                           "default-route-table-id": "rt-def",
                                                           "default-security-list-id": "sl-def"}])},
    {"match": ["network", "nsg", "list"], "stdout": data([{"id": "nsg1", "display-name": "nsg-a"}])},
    {"match": ["network", "nsg", "rules", "list"], "stdout": data([{"id": "r1"}, {"id": "r2"}])},
    {"match": ["network", "subnet", "list"], "stdout": data([{"id": "subnet1", "display-name": "subnet-a"}])},
    {"match": ["network", "route-table", "list"], "stdout": data([{"id": "rt-def"}, {"id": "rt1", "display-name": "rt-a"}])},
    {"match": ["network", "security-list", "list"], "stdout": data([{"id": "sl-def"}])},
    {"match": ["network", "internet-gateway", "list"], "stdout": data([{"id": "ig1"}])},
    {"match": ["iam", "policy", "list"], "also": [COMP], "stdout": data([{"id": "pol-comp", "name": "comp-pol"}])},
    {"match": ["iam", "policy", "list"], "also": [TEN], "stdout": data([
        {"id": "pol-proj", "name": "myproject-policy", "statements": ["allow group x to read all-resources in tenancy"]},
        {"id": "pol-ocid", "name": "other", "statements": ["allow any-user to use functions in compartment id %s" % COMP]},
        {"id": "pol-admin", "name": "Tenant Admin Policy",
         "statements": ["ALLOW GROUP Administrators to manage all-resources IN TENANCY"]}])},
    {"match": ["iam", "dynamic-group", "list"], "stdout": data([
        {"id": "dg-proj", "name": "myproject-dg", "matching-rule": "ALL {resource.type = 'fnfunc'}"},
        {"id": "dg-other", "name": "unrelated", "matching-rule": "ALL {resource.type = 'instance'}"}])},
    {"match": ["artifacts", "container", "repository", "list"], "also": [COMP],
     "stdout": json.dumps({"data": {"items": [{"id": "repo1", "display-name": "myproject/fn-a"}]}})},
    {"match": ["artifacts", "container", "image", "list"],
     "stdout": json.dumps({"data": {"items": [{"id": "img1", "version": "0.0.1"}]}})},
]


class OciCleanupTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.log = os.path.join(self.tmp, "calls.jsonl")

    def run_cleanup(self, *args, stdin="", fixture=None, env_extra=None, drop=()):
        rules = os.path.join(self.tmp, "rules.json")
        with open(rules, "w", encoding="utf-8") as fh:
            json.dump(FIXTURE if fixture is None else fixture, fh)
        env = {k: v for k, v in os.environ.items() if not k.startswith(("OCI_", "VAULT_", "SECRET_"))}
        env.update({"OCI_COMPARTMENT_OCID": COMP, "OCI_TENANCY_OCID": TEN, "OCI_NAMESPACE": "ns-test",
                    "OCI_COMPARTMENT_NAME": "mycomp", "OCI_PROJECT_FILTER": "myproject",
                    "OCI_CMD": '"%s" "%s"' % (sys.executable, FAKE_CLI), "OCI_CLEANUP_SLEEP_FACTOR": "0",
                    "FAKE_RULES": rules, "FAKE_LOG": self.log, "OCI_CLEANUP_ALLOW_PIPE": "1"})
        env.update(env_extra or {})
        for key in drop:
            env.pop(key, None)
        proc = subprocess.run([sys.executable, SCRIPT] + list(args), input=stdin.encode(), env=env,
                              capture_output=True, timeout=120)
        return proc.returncode, proc.stdout.decode("utf-8"), proc.stderr.decode("utf-8")

    def calls(self):
        if not os.path.exists(self.log):
            return []
        with open(self.log, encoding="utf-8") as fh:
            return [json.loads(line)["argv"] for line in fh]

    def mutating_calls(self):
        return [c for c in self.calls() if any(tok in MUTATING for tok in c)]

    # ---- guards -------------------------------------------------------------
    def test_missing_required_env_var_exits_1_without_oci_calls(self):
        for var in ("OCI_COMPARTMENT_OCID", "OCI_TENANCY_OCID", "OCI_NAMESPACE"):
            rc, out, err = self.run_cleanup("--dry-run", drop=(var,))
            self.assertEqual(rc, 1)
            self.assertIn("%s must be set" % var, err)
            self.assertEqual(out, "")
        self.assertEqual(self.calls(), [])

    def test_missing_oci_cli_exits_1(self):
        rc, _out, err = self.run_cleanup("--dry-run", env_extra={"OCI_CMD": "no-such-oci-cli-xyz"})
        self.assertEqual(rc, 1)
        self.assertIn("ERROR: 'no-such-oci-cli-xyz' not installed", err)

    def test_live_run_refused_without_exact_delete(self):
        for answer in ("no\n", "", "delete\n", "DELETE please\n"):
            rc, out, _err = self.run_cleanup(stdin=answer)
            self.assertEqual(rc, 0, answer)
            self.assertIn("LIVE (resources WILL be deleted)", out)
            self.assertIn("WARNING: This PERMANENTLY deletes OCI resources.", out)
            self.assertTrue(out.rstrip().endswith("Aborted."), answer)
            self.assertNotIn("Phase:", out)
        self.assertEqual(self.calls(), [])

    def test_unknown_argument_is_live_mode_and_still_requires_confirmation(self):
        rc, out, _err = self.run_cleanup("--dryrun", stdin="")
        self.assertEqual(rc, 0)
        self.assertIn("LIVE", out)
        self.assertIn("Aborted.", out)
        self.assertEqual(self.calls(), [])

    # ---- dry-run --------------------------------------------------------------
    def test_dry_run_lists_without_mutating(self):
        rc, out, err = self.run_cleanup("--dry-run")
        self.assertEqual(rc, 1, err)  # parity: the bash script's dry-run exit status was 1
        self.assertEqual(self.mutating_calls(), [])
        self.assertNotIn("[DELETE]", out)
        self.assertNotIn("Type 'DELETE'", out + err)
        self.assertIn("DRY-RUN (no deletions)", out)
        for line in ("[DRY-RUN]\x1b[0m Would delete: Alarm alarm-a", "Would delete: Secret sec-a → schedule ",
                     "Would delete: NSG nsg-a", "Would delete: internet-gateway ig1", "Would delete: VCN vcn-a",
                     "Would delete: Image myproject/fn-a:0.0.1", "Would delete: Repository myproject/fn-a"):
            self.assertIn(line, out)
        self.assertNotIn("sec-old", out)
        self.assertNotIn("vault-gone", out)
        self.assertIn("[SKIP]\x1b[0m   Default RT (deleted with VCN)", out)
        self.assertIn("Policy (tenancy): myproject-policy", out)
        self.assertIn("Policy (tenancy): other", out)
        self.assertNotIn("Tenant Admin Policy", out)
        self.assertNotIn("unrelated", out)
        self.assertIn("Found:   \x1b[1;33m22\x1b[0m", out)
        self.assertIn("Re-run without --dry-run to execute.", out)
        first = self.calls()[0]
        self.assertEqual(first[:4], ["--profile", "DEFAULT", "--auth", "api_key"])

    def test_dry_run_empty_compartment_is_clean(self):
        rc, out, _err = self.run_cleanup("--dry-run", fixture=[])
        self.assertEqual(rc, 1)
        self.assertIn("Compartment is clean.", out)
        self.assertIn("Trying tenancy-level search (filter: myproject)...", out)
        self.assertEqual(out.count("[NONE]"), 11)

    def test_empty_compartment_name_never_selects_admin_policies(self):
        # Safety change (user decision 2026-10-28): an empty filter matches nothing, so an empty
        # OCI_COMPARTMENT_NAME no longer selects every tenancy policy (the bash/jq version did).
        _rc, out, _err = self.run_cleanup("--dry-run", env_extra={"OCI_COMPARTMENT_NAME": ""})
        self.assertNotIn("Tenant Admin Policy", out)
        self.assertEqual(self.mutating_calls(), [])

    def test_piped_delete_is_refused_without_a_terminal(self):
        # Safety: an agent piping DELETE must not start a live run (no TTY, no test opt-in).
        rc, out, _err = self.run_cleanup(stdin="DELETE" + chr(10), drop=("OCI_CLEANUP_ALLOW_PIPE",))
        self.assertIn("needs DELETE typed at an interactive terminal", out)
        self.assertEqual(self.mutating_calls(), [])

    def test_empty_project_filter_selects_no_tenancy_object(self):
        # Safety (user decision 2026-10-28): OCI_PROJECT_FILTER has no implicit default; empty matches
        # nothing in phase 7 (tenancy policies, dynamic groups) and skips the tenancy-level OCIR search.
        _rc, out, _err = self.run_cleanup("--dry-run", env_extra={"OCI_PROJECT_FILTER": "", "OCI_COMPARTMENT_NAME": ""})
        self.assertNotIn("myproject-policy", out)
        self.assertNotIn("Dynamic group: myproject-dg", out)
        # compartment-level repositories are still in scope; only the tenancy-level search needs the filter
        self.assertEqual(self.mutating_calls(), [])

    def test_invalid_jq_escape_in_filter_matches_nothing(self):
        _rc, out, _err = self.run_cleanup("--dry-run", env_extra={"OCI_PROJECT_FILTER": r"my\.project"})
        self.assertIn("No dynamic groups matching 'my\\.project'", out)
        self.assertIn("No tenancy-level policies matching filter", out)

    # ---- live -----------------------------------------------------------------
    def test_live_run_with_confirmation_deletes_in_order(self):
        rc, out, err = self.run_cleanup(stdin="DELETE\n")
        self.assertEqual(rc, 0, out + err)
        self.assertNotIn("[FAIL]", out)
        self.assertIn("Cleanup complete.", out)
        muts = self.mutating_calls()
        flat = [" ".join(c[4:]) for c in muts]
        order = ["monitoring alarm delete", "logging log delete", "logging log-group delete",
                 "ons subscription delete", "ons topic delete", "apigateway deployment delete",
                 "fn function delete", "fn application delete", "vault secret schedule-secret-deletion",
                 "kms vault schedule-vault-deletion", "os object bulk-delete", "os bucket delete",
                 "network nsg rules remove", "network nsg delete", "network subnet delete",
                 "network route-table update", "network route-table delete", "network internet-gateway delete",
                 "network vcn delete", "iam policy delete", "iam dynamic-group delete",
                 "artifacts container image delete", "artifacts container repository delete"]
        positions = [next(i for i, f in enumerate(flat) if f.startswith(o)) for o in order]
        self.assertEqual(positions, sorted(positions))
        self.assertIn('["r1","r2"]', [c[-1] for c in muts if "remove" in c])
        deleted_policies = [c[c.index("--policy-id") + 1] for c in muts if "--policy-id" in c]
        self.assertEqual(deleted_policies, ["pol-comp", "pol-ocid", "pol-proj"])
        self.assertEqual([c for c in muts if "dg-other" in c], [])
        self.assertEqual([c for c in muts if "rt-def" in c or "sl-def" in c or "sec2" in c], [])
        when = {c[c.index("--secret-id" if "--secret-id" in c else "--vault-id") + 1]:
                c[c.index("--time-of-deletion") + 1] for c in muts if "--time-of-deletion" in c}
        now = datetime.datetime.now(datetime.timezone.utc)
        for ident, days in (("sec1", 2), ("vault1", 7)):
            ts = datetime.datetime.strptime(when[ident], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
            self.assertAlmostEqual((ts - now).total_seconds(), days * 86400, delta=120)

    def test_live_run_failed_delete_retries_and_exits_1(self):
        fixture = [{"match": ["apigateway", "deployment", "delete"], "rc": 1}] + FIXTURE
        rc, out, _err = self.run_cleanup(stdin="DELETE\n", fixture=fixture)
        self.assertEqual(rc, 1)
        self.assertIn("Retry 1/2 for Deployment: dep-a (15s)...", out)
        self.assertIn("[FAIL]\x1b[0m Deployment: dep-a", out)
        self.assertNotIn("Cleanup complete.", out)
        self.assertEqual(len([c for c in self.calls() if "deployment" in c and "delete" in c]), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
