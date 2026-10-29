"""Unit tests for the handoff scripts. Run from the skill directory:

    python -m unittest discover -s scripts/tests

Fixtures: tests/fixtures/{profiles,quarkus,oci}. board.py rewrites status.md, so tests
that run it work on a temporary copy of the fixture tree.
"""
import contextlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
sys.path.insert(0, SCRIPTS)

import _handoff_lib as lib  # noqa: E402
import _mini_yaml  # noqa: E402
import board  # noqa: E402
import check_records  # noqa: E402
import detect_drift  # noqa: E402

FIX = os.path.join(HERE, "fixtures")
Q_PROFILE = os.path.join(FIX, "profiles", "quarkus-aws.yaml")
OCI_PROFILE = os.path.join(FIX, "profiles", "oci.yaml")
Q_REL = os.path.join("quarkus", "openspec", "changes", "list-tenant-items", "handoff")
OCI_REL = os.path.join("oci", "docs", "handoff", "func-api-facade")
Q_DIR = os.path.join(FIX, Q_REL)
OCI_DIR = os.path.join(FIX, OCI_REL)


def run(module, argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = module.main(argv)
    return code, out.getvalue(), err.getvalue()


class TempCase(unittest.TestCase):
    def tmp(self):
        path = tempfile.mkdtemp(prefix="handoff-test-")
        self.addCleanup(shutil.rmtree, path, True)
        return path

    def copy_fixture(self, rel):
        dest = os.path.join(self.tmp(), "handoff")
        shutil.copytree(os.path.join(FIX, rel), dest)
        return dest

    def write(self, path, text):
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)

    def read(self, path):
        with open(path, encoding="utf-8") as fh:
            return fh.read()

    def add_record(self, directory, name, fm_lines, sections):
        body = "".join("\n## %s\n\ntext\n" % s for s in sections)
        self.write(os.path.join(directory, name), "---\n" + "\n".join(fm_lines) + "\n---\n" + body)

    def add_review(self, directory, nn, outcome, created):
        self.add_record(directory, "review-%s.md" % nn, [
            "kind: review", "id: review-%s" % nn, "from: quarkus-code-reviewer",
            "to: building-quarkus-aws-saas", "change: list-tenant-items",
            "refs: [result-01-code]", "outcome: %s" % outcome, "createdAt: %s" % created,
        ], ["Findings", "ADR check"])


class TestMiniYaml(unittest.TestCase):
    def test_mapping_sequences_and_flow(self):
        doc = _mini_yaml.load(
            "# comment\n"
            "name: demo   # trailing\n"
            "count: 3\n"
            "flag: true\n"
            "empty:\n"
            "quoted: \"a: b # not a comment\"\n"
            "nested:\n"
            "  inner: [a, b, 'c d']\n"
            "rules:\n"
            "  - when: {kind: report, role: [code, stripe]}\n"
            "    then: reviewer\n"
            "  - when: {pending_deltas: \">0\"}\n"
            "    then: sync\n"
            "plain:\n"
            "  - x\n"
            "  - y\n")
        self.assertEqual(doc["name"], "demo")
        self.assertEqual(doc["count"], 3)
        self.assertIs(doc["flag"], True)
        self.assertIsNone(doc["empty"])
        self.assertEqual(doc["quoted"], "a: b # not a comment")
        self.assertEqual(doc["nested"]["inner"], ["a", "b", "c d"])
        self.assertEqual(doc["rules"][0], {"when": {"kind": "report", "role": ["code", "stripe"]},
                                           "then": "reviewer"})
        self.assertEqual(doc["rules"][1]["when"]["pending_deltas"], ">0")
        self.assertEqual(doc["plain"], ["x", "y"])

    def test_errors(self):
        for bad in ("a: |\n  text\n", "a: &x 1\n", "a: [1, 2\n", "\ta: 1\n", "a: 1\na: 2\n",
                    "just text\n"):
            with self.assertRaises(_mini_yaml.YamlError, msg=bad):
                _mini_yaml.load(bad)

    def test_frontmatter(self):
        fm, body = _mini_yaml.parse_frontmatter(
            '---\nkind: report\nfrom: "@agent"\nrefs: [a, b]\ncreatedAt: 2026-11-04T10:15:00Z\n---\n\n## X\n')
        self.assertEqual(fm["from"], "@agent")
        self.assertEqual(fm["refs"], ["a", "b"])
        self.assertEqual(fm["createdAt"], "2026-11-04T10:15:00Z")
        self.assertIn("## X", body)
        with self.assertRaises(_mini_yaml.YamlError):
            _mini_yaml.parse_frontmatter("no frontmatter here")


class TestCheckRecords(TempCase):
    def test_quarkus_valid_set(self):
        code, out, _ = run(check_records, [Q_DIR, "--profile", Q_PROFILE])
        self.assertEqual(code, 0, out)

    def test_oci_valid_set(self):
        code, out, _ = run(check_records, [OCI_DIR, "--profile", OCI_PROFILE])
        self.assertEqual(code, 0, out)

    def test_missing_spec_impact_section(self):
        d = self.copy_fixture(Q_REL)
        path = os.path.join(d, "result-01-code.md")
        self.write(path, self.read(path).replace("## Spec impact", "## Impact"))
        code, out, _ = run(check_records, [d, "--profile", Q_PROFILE])
        self.assertEqual(code, 1)
        self.assertIn("result-01-code.md: missing required section '## Spec impact'", out)

    def test_broken_ref(self):
        d = self.copy_fixture(Q_REL)
        path = os.path.join(d, "result-01-code.md")
        self.write(path, self.read(path).replace("refs: [wo-01-code]", "refs: [wo-99-code]"))
        code, out, _ = run(check_records, [d, "--profile", Q_PROFILE])
        self.assertEqual(code, 1)
        self.assertIn("broken ref 'wo-99-code'", out)

    def test_invalid_outcome(self):
        d = self.copy_fixture(Q_REL)
        path = os.path.join(d, "review-01.md")
        self.write(path, self.read(path).replace("outcome: approved", "outcome: maybe"))
        code, out, _ = run(check_records, [d, "--profile", Q_PROFILE])
        self.assertEqual(code, 1)
        self.assertIn("invalid outcome 'maybe'", out)

    def test_limit_zero_rejected_unless_confirmed(self):
        d = self.copy_fixture(Q_REL)
        override = os.path.join(self.tmp(), "handoff-profile.yaml")
        self.write(override, "limits:\n  review_rounds: 0\n")
        code, out, _ = run(check_records, [d, "--profile", Q_PROFILE, "--override", override])
        self.assertEqual(code, 1)
        self.assertIn("limits.review_rounds must be an integer >= 1", out)
        self.write(override, "limits_zero_confirmed: true\nlimits:\n  review_rounds: 0\n")
        code, out, _ = run(check_records, [d, "--profile", Q_PROFILE, "--override", override])
        self.assertEqual(code, 0, out)

    def test_non_integer_limit_rejected(self):
        d = self.copy_fixture(Q_REL)
        override = os.path.join(self.tmp(), "o.yaml")
        self.write(override, "limits:\n  review_rounds: many\n")
        code, out, _ = run(check_records, [d, "--profile", Q_PROFILE, "--override", override])
        self.assertEqual(code, 1)
        self.assertIn("review_rounds", out)

    def test_verifier_must_not_be_author(self):
        d = self.copy_fixture(Q_REL)
        self.add_record(d, "verify-E6.md", [
            "kind: verify", "id: verify-E6", "from: quarkus-lambda-integrator",
            "to: building-quarkus-aws-saas", "change: list-tenant-items", "stage: E6",
            "refs: [result-01-code]", "outcome: pass", "createdAt: 2026-11-04T11:00:00Z",
        ], ["Criteria", "Evidence"])
        code, out, _ = run(check_records, [d, "--profile", Q_PROFILE])
        self.assertEqual(code, 1)
        self.assertIn("never verifies its own work", out)

    def test_report_family_outcomes_share_one_vocabulary(self):
        d = self.copy_fixture(Q_REL)
        sections = {"deploy-report": ["Deployed", "Validation", "Next step"],
                    "diagnosis-report": ["Symptom", "Root cause", "Evidence", "Exact fix",
                                         "Classification", "Next step"]}
        agents = {"deploy-report": "aws-lambda-deployer", "diagnosis-report": "aws-lambda-debugger"}
        for kind in ("deploy-report", "diagnosis-report"):
            for outcome in ("success", "partial", "failed", "needs-input"):
                name = "%s-%s.md" % (kind, outcome)
                self.add_record(d, name, [
                    "kind: " + kind, "id: %s-%s" % (kind, outcome), "from: " + agents[kind],
                    "to: building-quarkus-aws-saas", "change: list-tenant-items",
                    "refs: [result-01-code]", "outcome: " + outcome,
                    "createdAt: 2026-11-04T13:00:00Z"], sections[kind])
        code, out, _ = run(check_records, [d, "--profile", Q_PROFILE])
        self.assertEqual(code, 0, out)
        self.add_record(d, "deploy-report-bad.md", [
            "kind: deploy-report", "id: deploy-report-bad", "from: aws-lambda-deployer",
            "to: building-quarkus-aws-saas", "change: list-tenant-items", "outcome: pass",
            "createdAt: 2026-11-04T13:00:00Z"], sections["deploy-report"])
        code, out, _ = run(check_records, [d, "--profile", Q_PROFILE])
        self.assertEqual(code, 1)
        self.assertIn("invalid outcome 'pass' for kind deploy-report", out)

    def test_verify_outcome_vocabulary_is_pass_fail_only(self):
        d = self.copy_fixture(Q_REL)
        fm = ["kind: verify", "id: verify-E6", "from: aws-lambda-debugger",
              "to: building-quarkus-aws-saas", "change: list-tenant-items", "stage: E6",
              "refs: [result-01-code]", "createdAt: 2026-11-04T11:00:00Z"]
        self.add_record(d, "verify-E6.md", fm + ["outcome: success"], ["Criteria", "Evidence"])
        code, out, _ = run(check_records, [d, "--profile", Q_PROFILE])
        self.assertEqual(code, 1)
        self.assertIn("invalid outcome 'success' for kind verify", out)
        # a verifier that is not the producer of the ref passes
        self.add_record(d, "verify-E6.md", fm + ["outcome: pass"], ["Criteria", "Evidence"])
        code, out, _ = run(check_records, [d, "--profile", Q_PROFILE])
        self.assertEqual(code, 0, out)

    def test_escalation_needs_two_to_four_options(self):
        d = self.copy_fixture(Q_REL)
        fm = ["kind: escalation", "id: escalation-01", "from: building-quarkus-aws-saas",
              "to: user", "change: list-tenant-items", "task: T1", "status: open",
              "createdAt: 2026-11-04T12:00:00Z"]
        body = "\n## Attempts\n\n- 1\n\n## Evidence\n\n- e\n\n## Hypothesis\n\n- h\n\n## Options\n\n"
        self.write(os.path.join(d, "escalation-01.md"), "---\n" + "\n".join(fm) + "\n---\n" + body + "- only one\n")
        code, out, _ = run(check_records, [d, "--profile", Q_PROFILE])
        self.assertEqual(code, 1)
        self.assertIn("2-4 options", out)
        self.write(os.path.join(d, "escalation-01.md"),
                   "---\n" + "\n".join(fm) + "\n---\n" + body + "- relax R1\n- new ADR\n")
        code, out, _ = run(check_records, [d, "--profile", Q_PROFILE])
        self.assertEqual(code, 0, out)

    def test_spec_delta_requires_openspec_section(self):
        d = self.copy_fixture(Q_REL)
        fm = ["kind: spec-delta", "id: spec-delta-01", "from: spec-synchronizer",
              "to: building-quarkus-aws-saas", "change: list-tenant-items", "status: proposed",
              "createdAt: 2026-11-04T12:00:00Z"]
        self.write(os.path.join(d, "spec-delta-01.md"),
                   "---\n" + "\n".join(fm) + "\n---\n\n## Questions\n\n- none\n")
        code, out, _ = run(check_records, [d, "--profile", Q_PROFILE])
        self.assertEqual(code, 1)
        self.assertIn("ADDED Requirements", out)
        self.write(os.path.join(d, "spec-delta-01.md"),
                   "---\n" + "\n".join(fm) + "\n---\n\n## MODIFIED Requirements\n\n"
                   "### Requirement: R1 list\n\n## Questions\n\n- none\n")
        code, out, _ = run(check_records, [d, "--profile", Q_PROFILE])
        self.assertEqual(code, 0, out)


class TestProfileAndLimits(TempCase):
    def test_limit_precedence_and_sources(self):
        profile, errs = lib.load_profile(Q_PROFILE)
        self.assertEqual(errs, [])
        override = os.path.join(self.tmp(), "handoff-profile.yaml")
        self.write(override, "limits:\n  review_rounds: 3\n")
        p = lib.effective_params(profile)
        self.assertEqual((p["limits"]["review_rounds"], p["sources"]["limits.review_rounds"]),
                         (2, "profile"))
        p = lib.effective_params(profile, override)
        self.assertEqual((p["limits"]["review_rounds"], p["sources"]["limits.review_rounds"]),
                         (3, "override (handoff-profile.yaml)"))
        p = lib.effective_params(profile, override, ["change=x", "limits.review_rounds=4"])
        self.assertEqual((p["limits"]["review_rounds"], p["sources"]["limits.review_rounds"]),
                         (4, "args"))
        self.assertEqual(p["limits"]["build_attempts"], 3)
        self.assertEqual(p["sources"]["limits.build_attempts"], "profile")
        self.assertEqual(p["ignored"], ["change"])

    def test_args_zero_needs_confirmation(self):
        profile, _ = lib.load_profile(Q_PROFILE)
        p = lib.effective_params(profile, None, ["limits.deploy_cycles=0"])
        self.assertTrue(p["errors"])
        p = lib.effective_params(profile, None, ["limits.deploy_cycles=0", "limits_zero_confirmed=true"])
        self.assertEqual(p["errors"], [])
        self.assertEqual(p["limits"]["deploy_cycles"], 0)

    def test_limit_reached_rule_must_be_first(self):
        d = self.tmp()
        bad = os.path.join(d, "bad.yaml")
        text = self.read(Q_PROFILE)
        first = ("  - when: {limit_reached: any}\n    then: escalate\n")
        self.assertIn(first, text)
        moved = text.replace(first, "") + first
        self.write(bad, moved)
        profile, errs = lib.load_profile(bad)
        self.assertIsNone(profile)
        self.assertTrue(any("limit_reached" in e for e in errs), errs)
        code, _, err = run(board, [self.copy_fixture(Q_REL), "--profile", bad])
        self.assertEqual(code, 1)
        self.assertIn("limit_reached", err)

    def test_unknown_matcher_and_target(self):
        d = self.tmp()
        bad = os.path.join(d, "bad.yaml")
        text = self.read(Q_PROFILE).replace("then: deploy\n", "then: nobody\n")
        text = text.replace("  - when: {all_tasks: done}", "  - when: {colour: red}")
        self.write(bad, text)
        _, errs = lib.load_profile(bad)
        self.assertTrue(any("unknown matcher 'colour'" in e for e in errs), errs)
        self.assertTrue(any("nobody" in e for e in errs), errs)


class TestBoard(TempCase):
    def test_quarkus_fixture_next_is_deploy_and_approvals_kept(self):
        d = self.copy_fixture(Q_REL)
        code, out, _ = run(board, [d, "--profile", Q_PROFILE, "--sync-sha", "abc123"])
        self.assertEqual(code, 0, out)
        self.assertIn("NEXT: role=deploy agent=aws-lambda-deployer rule=11", out)
        status = self.read(os.path.join(d, "status.md"))
        self.assertIn("2026-11-04: user approved the task plan (E5).", status)
        self.assertIn("lastSyncedSha: \"abc123\"", status)
        self.assertIn("| limits.review_rounds | 2 | profile |", status)
        self.assertIn("| T1 | done |", status)
        code, out, _ = run(check_records, [d, "--profile", Q_PROFILE])
        self.assertEqual(code, 0, out)

    def test_limit_zero_escalates_on_first_failure_not_before(self):
        d = self.copy_fixture(Q_REL)
        args = ["--args", "limits.deploy_cycles=0", "limits_zero_confirmed=true"]
        code, out, _ = run(board, [d, "--profile", Q_PROFILE] + args)
        self.assertEqual(code, 0, out)
        self.assertNotIn("NEXT: escalate", out)
        self.add_record(d, "result-02-deploy.md", [
            "kind: deploy-report", "id: result-02-deploy", "from: aws-lambda-deployer",
            "to: building-quarkus-aws-saas", "change: list-tenant-items", "task: deploy",
            "outcome: failed", "createdAt: 2026-11-04T12:00:00Z",
        ], ["Release", "Approval", "Evidence", "Suggested next step"])
        code, out, _ = run(board, [d, "--profile", Q_PROFILE] + args)
        self.assertIn("NEXT: escalate limit=deploy_cycles", out)

    def test_sha_is_preserved_between_runs(self):
        d = self.copy_fixture(Q_REL)
        run(board, [d, "--profile", Q_PROFILE, "--sync-sha", "abc123"])
        run(board, [d, "--profile", Q_PROFILE])
        self.assertIn("lastSyncedSha: \"abc123\"", self.read(os.path.join(d, "status.md")))

    def test_oci_fixture_next_is_debugger(self):
        d = self.copy_fixture(OCI_REL)
        code, out, _ = run(board, [d, "--profile", OCI_PROFILE])
        self.assertEqual(code, 0, out)
        self.assertIn("NEXT: role=debugger agent=oci-debugger rule=3", out)

    def test_limit_reached_rule_wins_over_later_matches(self):
        d = self.copy_fixture(Q_REL)
        # review-01 -> changes-requested, review-02 -> changes-requested, then a new code report
        path = os.path.join(d, "review-01.md")
        self.write(path, self.read(path).replace("outcome: approved", "outcome: changes-requested"))
        self.add_review(d, "02", "changes-requested", "2026-11-04T11:00:00Z")
        self.add_record(d, "result-02-code.md", [
            "kind: report", "id: result-02-code", "from: quarkus-lambda-integrator",
            "to: building-quarkus-aws-saas", "change: list-tenant-items", "refs: [review-02]",
            "outcome: success", "spec_impact: none", "createdAt: 2026-11-04T11:30:00Z",
        ], ["Done", "Evidence", "Spec impact", "Suggested next step"])
        code, out, _ = run(board, [d, "--profile", Q_PROFILE])
        self.assertEqual(code, 0, out)
        self.assertIn("NEXT: escalate limit=review_rounds task=T1 rule=1", out)
        # raising the limit per run removes the escalation; the report rule matches next
        code, out, _ = run(board, [d, "--profile", Q_PROFILE, "--args", "limits.review_rounds=3"])
        self.assertEqual(code, 0, out)
        self.assertIn("NEXT: role=reviewer agent=quarkus-code-reviewer,stripe-advisor rule=2", out)
        status = self.read(os.path.join(d, "status.md"))
        self.assertIn("| limits.review_rounds | 3 | args |", status)

    def test_answered_escalation_resets_counter(self):
        d = self.copy_fixture(Q_REL)
        path = os.path.join(d, "review-01.md")
        self.write(path, self.read(path).replace("outcome: approved", "outcome: changes-requested"))
        self.add_review(d, "02", "changes-requested", "2026-11-04T11:00:00Z")
        code, out, _ = run(board, [d, "--profile", Q_PROFILE])
        self.assertIn("NEXT: escalate limit=review_rounds", out)
        self.write(os.path.join(d, "escalation-01.md"),
                   "---\nkind: escalation\nid: escalation-01\nfrom: building-quarkus-aws-saas\n"
                   "to: user\nchange: list-tenant-items\ntask: T1\nlimit: review_rounds\n"
                   "status: answered\ncreatedAt: 2026-11-04T11:10:00Z\n"
                   "answeredAt: 2026-11-04T11:20:00Z\n---\n\n## Attempts\n\n- a\n\n## Evidence\n\n- e\n\n"
                   "## Hypothesis\n\n- h\n\n## Options\n\n- one\n- two\n")
        code, out, _ = run(board, [d, "--profile", Q_PROFILE])
        self.assertEqual(code, 0, out)
        self.assertNotIn("escalate", out)

    def test_uncovered_divergence_means_drift_then_delta_covers_it(self):
        d = self.copy_fixture(Q_REL)
        path = os.path.join(d, "result-01-code.md")
        self.write(path, self.read(path).replace("spec_impact: none", "spec_impact: divergence"))
        # make the report the latest event so rule order is visible: move review to changes-free
        os.remove(os.path.join(d, "review-01.md"))
        code, out, _ = run(board, [d, "--profile", Q_PROFILE])
        self.assertIn("NEXT: role=reviewer", out)  # rule 2 (report success) precedes drift (rule 4)
        self.add_record(d, "spec-delta-01.md", [
            "kind: spec-delta", "id: spec-delta-01", "from: spec-synchronizer",
            "to: building-quarkus-aws-saas", "change: list-tenant-items",
            "refs: [result-01-code]", "status: proposed", "createdAt: 2026-11-04T12:00:00Z",
        ], ["MODIFIED Requirements", "Questions"])
        code, out, _ = run(board, [d, "--profile", Q_PROFILE])
        self.assertIn("NEXT: role=orchestrator", out)  # pending delta -> show it to the user
        self.assertIn("pending spec-deltas: 1", self.read(os.path.join(d, "status.md")))

    def test_external_drift_arg_routes_to_sync(self):
        d = self.copy_fixture(Q_REL)
        code, out, _ = run(board, [d, "--profile", Q_PROFILE, "--args", "drift=true"])
        self.assertEqual(code, 0, out)
        self.assertIn("NEXT: role=sync agent=spec-synchronizer rule=4", out)

    def test_invalid_limit_in_args_exits_1(self):
        d = self.copy_fixture(Q_REL)
        code, _, err = run(board, [d, "--profile", Q_PROFILE, "--args", "limits.review_rounds=0"])
        self.assertEqual(code, 1)
        self.assertIn("limits.review_rounds", err)


@unittest.skipUnless(shutil.which("git"), "git not installed")
class TestDetectDrift(TempCase):
    def git(self, repo, *args):
        return subprocess.run(["git", "-c", "commit.gpgsign=false"] + list(args), cwd=repo, check=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              universal_newlines=True).stdout.strip()

    def make_repo(self):
        repo = self.tmp()
        self.git(repo, "init", "-q")
        self.git(repo, "config", "user.email", "t@example.com")
        self.git(repo, "config", "user.name", "Test")
        os.makedirs(os.path.join(repo, "src"))
        self.write(os.path.join(repo, "src", "App.java"), "class App {}\n")
        self.git(repo, "add", "-A")
        self.git(repo, "commit", "-q", "-m", "base")
        return repo

    def test_drift_then_covered_by_report(self):
        repo = self.make_repo()
        sha = self.git(repo, "rev-parse", "HEAD")
        change = os.path.join(repo, "openspec", "changes", "x", "handoff")
        os.makedirs(change)
        self.write(os.path.join(change, "status.md"),
                   "---\nkind: status\nid: status\nlastSyncedSha: \"%s\"\n---\n\n# s\n" % sha)
        self.write(os.path.join(repo, "src", "App.java"), "class App { int x; }\n")
        self.write(os.path.join(repo, "src", "Other.java"), "class Other {}\n")
        self.git(repo, "add", "-A")
        self.git(repo, "commit", "-q", "-m", "work")

        code, out, _ = run(detect_drift, [repo, "--change", change])
        self.assertEqual(code, 2, out)
        self.assertIn("DRIFT: src/App.java", out)
        self.assertIn("DRIFT: src/Other.java", out)
        self.assertNotIn("openspec", out)

        self.write(os.path.join(change, "deploy-report.md"),
                   "---\nkind: deploy-report\nid: deploy-report\nfrom: x\nto: y\nchange: x\n"
                   "outcome: success\ncreatedAt: 2026-11-04T10:00:00Z\n---\n\n"
                   "## Spec impact\n\n- Files: `src/App.java`, `src/Other.java`\n")
        code, out, _ = run(detect_drift, [repo, "--change", change])
        self.assertEqual(code, 0, out)
        self.assertIn("NO DRIFT", out)

    def test_error_when_no_synced_sha(self):
        repo = self.make_repo()
        change = os.path.join(repo, "handoff")
        os.makedirs(change)
        self.write(os.path.join(change, "status.md"),
                   "---\nkind: status\nid: status\nlastSyncedSha: \"none\"\n---\n")
        code, _, err = run(detect_drift, [repo, "--change", change])
        self.assertEqual(code, 1)
        self.assertIn("lastSyncedSha", err)


class TestTimestamps(TempCase):
    def test_parse_ts_handles_zulu_offset_and_date(self):
        z = lib.parse_ts("2026-11-04T10:00:00Z")
        self.assertEqual(lib.parse_ts("2026-11-04T12:00:00+02:00"), z)
        self.assertEqual(lib.parse_ts("2026-11-04T05:00:00-0500"), z)
        self.assertEqual(lib.parse_ts("2026-11-04T10:00"), z)
        self.assertEqual(lib.parse_ts("2026-11-04").hour, 0)
        self.assertIsNone(lib.parse_ts("2026-13-40T00:00:00Z"))
        self.assertIsNone(lib.parse_ts("<ISO timestamp>"))

    def test_latest_record_uses_time_not_string_order(self):
        d = self.copy_fixture(Q_REL)
        # a = 10:00Z but sorts later as a string; b = 11:00Z is the real latest
        for rid, created in (("result-02-code", "2026-12-01T12:00:00+02:00"),
                             ("result-03-code", "2026-12-01T11:00:00Z")):
            self.add_record(d, rid + ".md", [
                "kind: report", "id: " + rid, "from: quarkus-lambda-integrator",
                "to: building-quarkus-aws-saas", "change: list-tenant-items",
                "refs: [wo-01-code]", "outcome: success", "spec_impact: none",
                "createdAt: " + created,
            ], ["Done", "Evidence", "Spec impact", "Suggested next step"])
        profile, _ = lib.load_profile(Q_PROFILE)
        state = lib.compute_state(lib.load_records(d, profile), profile,
                                  lib.effective_params(profile))
        self.assertEqual(state["event"]["id"], "result-03-code")

    def test_unparseable_timestamp_falls_back_with_warning(self):
        d = self.copy_fixture(Q_REL)
        path = os.path.join(d, "review-01.md")
        text = self.read(path)
        import re as _re
        self.write(path, _re.sub(r"createdAt: .*", "createdAt: not-a-time", text))
        code, _, err = run(board, [d, "--profile", Q_PROFILE])
        self.assertEqual(code, 0)
        self.assertIn("unparseable timestamp", err)


class TestMentionedPaths(unittest.TestCase):
    def test_exact_match_only(self):
        paths = detect_drift.mentioned_paths(
            "- Files: `src/App.javascript`, src/dir/\n"
            "Changed ./src/Other.java. and `lib/` too\n")
        self.assertIn("src/App.javascript", paths)
        self.assertIn("src/Other.java", paths)
        self.assertNotIn("src/App.java", paths)
        self.assertNotIn("src/dir/Inner.java", paths)  # a directory mention covers no file


@unittest.skipUnless(shutil.which("git"), "git not installed")
class TestDetectDriftExact(TempCase):
    git = TestDetectDrift.git
    make_repo = TestDetectDrift.make_repo

    def _setup(self, report_files):
        repo = self.make_repo()
        sha = self.git(repo, "rev-parse", "HEAD")
        change = os.path.join(repo, "openspec", "changes", "x", "handoff")
        os.makedirs(change)
        self.write(os.path.join(change, "status.md"),
                   "---\nkind: status\nid: status\nlastSyncedSha: \"%s\"\n---\n\n# s\n" % sha)
        self.write(os.path.join(change, "result-01.md"),
                   "---\nkind: report\nid: result-01\nfrom: x\nto: y\nchange: x\noutcome: success\n"
                   "createdAt: 2026-11-04T10:00:00Z\n---\n\n## Spec impact\n\n%s\n" % report_files)
        return repo, change

    def test_substring_mention_does_not_cover_file(self):
        repo, change = self._setup("- Files: `src/App.javascript.bak`, `src/` ")
        self.write(os.path.join(repo, "src", "App.java"), "class App { int x; }\n")
        self.git(repo, "add", "-A")
        self.git(repo, "commit", "-q", "-m", "work")
        code, out, _ = run(detect_drift, [repo, "--change", change])
        self.assertEqual(code, 2, out)
        self.assertIn("DRIFT: src/App.java", out)

    def test_worktree_flag_sees_uncommitted_edit(self):
        repo, change = self._setup("- Files: none")
        self.write(os.path.join(repo, "src", "App.java"), "class App { int hand; }\n")
        code, out, _ = run(detect_drift, [repo, "--change", change])
        self.assertEqual(code, 0, out)  # uncommitted edit is invisible by default
        code, out, _ = run(detect_drift, [repo, "--change", change, "--include-worktree"])
        self.assertEqual(code, 2, out)
        self.assertIn("DRIFT: src/App.java", out)

    def test_relpath_value_error_is_an_error_line(self):
        from unittest import mock
        repo, change = self._setup("- Files: none")
        with mock.patch.object(detect_drift.os.path, "relpath", side_effect=ValueError("path is on mount 'C:'")):
            code, _, err = run(detect_drift, [repo, "--change", change])
        self.assertEqual(code, 1)
        self.assertIn("error:", err)


class TestCli(unittest.TestCase):
    def test_help_works_for_every_script(self):
        for script in ("check_records.py", "board.py", "detect_drift.py"):
            proc = subprocess.run([sys.executable, os.path.join(SCRIPTS, script), "--help"],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  universal_newlines=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("usage:", proc.stdout.lower())


class TestDriftAcceptedDelta(TempCase):
    """An ACCEPTED spec-delta covers the paths in its ## Files section; other statuses do not (no git)."""

    def _delta(self, d, status):
        lines = ["---", "kind: spec-delta", "id: spec-delta-01", "from: spec-synchronizer", "to: o",
                 "change: x", "status: %s" % status, "createdAt: 2026-11-04T10:00:00Z", "---", "",
                 "## Files", "", "- `src/main/java/Hand.java`", ""]
        self.write(os.path.join(d, "spec-delta-01.md"), "\n".join(lines))

    def test_accepted_delta_covers_its_files(self):
        d = self.tmp()
        self._delta(d, "accepted")
        self.assertIn("src/main/java/Hand.java",
                      detect_drift.mentioned_paths(detect_drift._mentioned_text(d)))

    def test_proposed_delta_covers_nothing(self):
        for status in ("proposed", "revise", "rejected"):
            d = self.tmp()
            self._delta(d, status)
            self.assertNotIn("src/main/java/Hand.java",
                             detect_drift.mentioned_paths(detect_drift._mentioned_text(d)), status)


if __name__ == "__main__":
    unittest.main()
