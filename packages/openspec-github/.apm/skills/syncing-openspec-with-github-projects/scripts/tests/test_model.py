"""Unit tests of the pure model (_model.py). Run from the skill directory:

    OPENSPEC_GITHUB_HANDOFF_SCRIPTS=<handoff-core scripts> python -m unittest discover -s scripts/tests

No network, no gh: only texts and handoff records from tests/fixtures/repo.
"""
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fake_gh  # noqa: E402

fake_gh.prepare_imports()
import _model as model  # noqa: E402

lib = model.lib
REPO = os.path.join(fake_gh.FIXTURES, "repo")
CHANGE_DIR = os.path.join(REPO, "openspec", "changes", fake_gh.CHANGE)
TRACKER = {"kind": "github-projects", "owner": "acme", "owner_type": "organization",
           "project_number": 7, "repo": "acme/shop", "approval_source": "github",
           "approvers": ["alice", "bob"], "bot_login": "openspec-bot[bot]"}


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


class ModelCase(unittest.TestCase):
    def setUp(self):
        self.profile, errs = lib.load_profile(fake_gh.PROFILE)
        self.assertEqual(errs, [])

    def handoff_copy(self):
        tmp = tempfile.mkdtemp(prefix="osgh-model-")
        self.addCleanup(shutil.rmtree, tmp, True)
        dest = os.path.join(tmp, "handoff")
        shutil.copytree(os.path.join(CHANGE_DIR, "handoff"), dest)
        return dest

    def write(self, path, text):
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)

    def inputs(self, handoff=None, **extra):
        handoff = handoff or os.path.join(CHANGE_DIR, "handoff")
        adrs = [model.adr_info(n, read(os.path.join(REPO, "openspec/specs/architecture/adr", n)))
                for n in sorted(os.listdir(os.path.join(REPO, "openspec/specs/architecture/adr")))]
        records = lib.load_records(handoff, self.profile)
        texts = [read(os.path.join(CHANGE_DIR, n)) for n in ("proposal.md", "design.md", "tasks.md")]
        inp = {"change": fake_gh.CHANGE, "repo": "acme/shop",
               "proposal": read(os.path.join(CHANGE_DIR, "proposal.md")),
               "tasks": read(os.path.join(CHANGE_DIR, "tasks.md")), "records": records,
               "adrs": model.referenced_adrs(adrs, texts), "adr_dir": "openspec/specs/architecture/adr",
               "status_md": read(os.path.join(handoff, "status.md")), "approval_source": "github"}
        inp.update(extra)
        return inp

    def issue(self, desired, key):
        return [i for i in desired["issues"] if i["key"] == key][0]


class TestParsing(ModelCase):
    def test_tasks_groups_and_items(self):
        tasks = model.parse_tasks(read(os.path.join(CHANGE_DIR, "tasks.md")))
        self.assertEqual([t["id"] for t in tasks], ["T1", "T2"])
        self.assertEqual(tasks[0]["title"], "Items endpoint")
        self.assertEqual([i["id"] for i in tasks[0]["items"]], ["1.1", "1.2"])
        self.assertTrue(all(i["done"] for i in tasks[0]["items"]))
        self.assertEqual(model.checkbox_status(tasks[1]["items"]), "Todo")

    def test_tasks_without_headings_group_by_number(self):
        tasks = model.parse_tasks("- [ ] 3.1 alpha\n- [x] 3.2 beta\n")
        self.assertEqual(tasks[0]["id"], "T3")
        self.assertEqual(tasks[0]["title"], "alpha")
        self.assertEqual(model.checkbox_status(tasks[0]["items"]), "In progress")

    def test_adr_info_and_reference_filter(self):
        info = model.adr_info("003-tenant-isolation.md", "# ADR-003: Tenant isolation\n\nStatus: accepted\n")
        self.assertEqual((info["num"], info["title"], info["status"]), ("003", "Tenant isolation", "accepted"))
        self.assertIsNone(model.adr_info("README.md", ""))
        other = model.adr_info("004-x.md", "# ADR-004: X\n")
        kept = model.referenced_adrs([info, other], ["we follow ADR-003"])
        self.assertEqual([a["num"] for a in kept], ["003"])

    def test_stage_from_verify_records(self):
        recs = lib.load_records(os.path.join(CHANGE_DIR, "handoff"), self.profile)
        self.assertEqual(model.stage_of(recs), ("E2", False))
        self.assertEqual(model.stage_of(recs, "E5")[0], "E5")
        self.assertEqual(model.stage_of([])[0], "E1")


class TestDesiredState(ModelCase):
    def test_fixture_mapping(self):
        d = model.desired_state(self.inputs())
        self.assertEqual(d["stage"], "E2")
        keys = [i["key"] for i in d["issues"]]
        self.assertEqual(keys, ["change", "task:T1", "task:T2", "adr:003"])
        change = self.issue(d, "change")
        self.assertEqual(change["title"], "change: list-tenant-items")
        self.assertEqual(change["fields"], {"Kind": "change", "Change": "list-tenant-items",
                                            "Stage": "E2", "Status": "In progress", "Gate": "E2 pending"})
        self.assertIn("Tenants need to list", change["body"])
        self.assertIn("https://github.com/acme/shop/blob/HEAD/openspec/changes/list-tenant-items/proposal.md",
                      change["body"])
        t1, t2 = self.issue(d, "task:T1"), self.issue(d, "task:T2")
        self.assertEqual((t1["state"], t1["reason"], t1["fields"]["Status"]), ("closed", "completed", "Done"))
        self.assertEqual((t2["state"], t2["fields"]["Status"]), ("open", "Todo"))
        self.assertEqual(t1["title"], "task: T1 Items endpoint")
        self.assertEqual(t1["parent"], "change")
        self.assertEqual(self.issue(d, "adr:003")["fields"]["Status"], "Done")
        for obj in d["issues"] + d["comments"]:
            self.assertTrue(obj["body"].startswith(model.BOT_MARKER), obj["key"])

    def test_delta_comment_and_summary(self):
        d = model.desired_state(self.inputs())
        delta = [c for c in d["comments"] if c["key"] == "delta:spec-delta-01"][0]
        self.assertIn("<!-- openspec-github:delta status=proposed -->", delta["body"])
        self.assertIn("`/accept delta-01`", delta["body"])
        self.assertIn("## Questions", delta["body"])
        summary = [c for c in d["comments"] if c["key"] == "summary"][0]
        self.assertIn("/approve E2", summary["body"])

    def test_task_status_from_work_orders(self):
        h = self.handoff_copy()
        p = os.path.join(h, "wo-01-code.md")
        for status, want, state in (("in-progress", "In progress", "open"), ("pending", "Todo", "open"),
                                    ("blocked", "Blocked", "open"), ("cancelled", "Done", "closed")):
            self.write(p, read(os.path.join(CHANGE_DIR, "handoff", "wo-01-code.md"))
                       .replace("status: done", "status: %s" % status))
            t1 = self.issue(model.desired_state(self.inputs(h)), "task:T1")
            self.assertEqual((t1["fields"]["Status"], t1["state"]), (want, state), status)
            if status == "cancelled":
                self.assertEqual(t1["reason"], "not_planned")

    def add_escalation(self, h, status):
        self.write(os.path.join(h, "escalation-01.md"), "\n".join([
            "---", "kind: escalation", "id: escalation-01", "from: building-quarkus-aws-saas",
            "to: user", "change: list-tenant-items", "task: T2", "limit: review_rounds",
            "status: %s" % status, "createdAt: 2026-11-04T11:00:00Z", "---", "",
            "## Attempts", "", "two", "", "## Evidence", "", "x", "", "## Hypothesis", "", "y", "",
            "## Options", "", "1. Retry with a new reviewer", "2. Drop the task", ""]))

    def test_escalation_becomes_blocked_sub_issue(self):
        h = self.handoff_copy()
        self.add_escalation(h, "open")
        d = model.desired_state(self.inputs(h))
        esc = self.issue(d, "escalation:escalation-01")
        self.assertIn("blocked", esc["labels"])
        self.assertEqual((esc["state"], esc["fields"]["Status"], esc["parent"]), ("open", "Blocked", "change"))
        self.assertIn("1. Retry with a new reviewer", esc["body"])
        self.assertIn("/answer escalation-01", esc["body"])
        self.assertEqual(self.issue(d, "change")["fields"]["Status"], "Blocked")
        self.add_escalation(h, "answered")
        esc = self.issue(model.desired_state(self.inputs(h)), "escalation:escalation-01")
        self.assertEqual((esc["state"], esc["labels"]), ("closed", ["openspec"]))

    def test_needs_input_report_closes_when_referenced(self):
        h = self.handoff_copy()
        self.write(os.path.join(h, "result-02-code.md"), "\n".join([
            "---", "kind: report", "id: result-02-code", "from: quarkus-lambda-integrator",
            "to: building-quarkus-aws-saas", "change: list-tenant-items", "refs: [wo-01-code]",
            "outcome: needs-input", "createdAt: 2026-11-04T12:00:00Z", "---", "",
            "## Questions", "", "1. Which page size?", ""]))
        ni = self.issue(model.desired_state(self.inputs(h)), "escalation:result-02-code")
        self.assertEqual((ni["state"], ni["title"]), ("open", "needs-input: result-02-code"))
        self.write(os.path.join(h, "wo-02-code.md"), "\n".join([
            "---", "kind: work-order", "id: wo-02-code", "from: building-quarkus-aws-saas",
            "to: quarkus-lambda-integrator", "change: list-tenant-items", "task: T2",
            "refs: [result-02-code]", "status: pending", "createdAt: 2026-11-04T13:00:00Z", "---", ""]))
        ni = self.issue(model.desired_state(self.inputs(h)), "escalation:result-02-code")
        self.assertEqual(ni["state"], "closed")

    def test_closing_closes_everything(self):
        d = model.desired_state(self.inputs(closing=True))
        self.assertTrue(all(i["state"] == "closed" for i in d["issues"]))
        self.assertEqual(self.issue(d, "change")["fields"]["Status"], "Done")

    def test_truncation(self):
        body = model.truncate("x" * 70000, "https://example/f.md")
        self.assertLessEqual(len(body), model.BODY_LIMIT)
        self.assertTrue(body.endswith("full text: https://example/f.md)"))
        self.assertEqual(model.truncate("short", "l"), "short")


class TestStateFile(ModelCase):
    def test_round_trip_through_mini_yaml(self):
        state = model.new_state(TRACKER)
        state["project_id"] = "PVT_1"
        state["fields"] = {"Status": {"id": "F1", "options": {"In Progress": "o:1", "Todo": "o2"}}}
        state["change"] = {"issue": 12, "url": "https://github.com/a/b/issues/12", "labels": ["x", "y"],
                           "fields": {"Gate": 'E2 "pending"', "Change": "a: b #c [d]"}, "parent_linked": True}
        state["adrs"] = {"003": {"issue": 14}}
        state["deltas"] = {"spec-delta-01": {"comment_id": 991, "sha": "ab"}}
        state["pulled"] = {"555": "gate=E2", "556": "line\nbreak\\"}
        text = model.dump_state(state)
        back = model.load_state(text, TRACKER)
        for key in ("project_id", "fields", "change", "adrs", "deltas", "pulled", "tracker"):
            self.assertEqual(back[key], state[key], key)

    def test_rejects_foreign_schema_and_detects_tracker_mismatch(self):
        with self.assertRaises(ValueError):
            model.load_state("schema: 9\n", TRACKER)
        state = model.load_state('tracker: {owner: "other", repo: "acme/shop"}\n', TRACKER)
        self.assertEqual(model.tracker_mismatch(state, TRACKER), ["owner"])

    def test_field_and_label_edits(self):
        self.assertEqual(model.field_edits({"Status": "In progress"}, {"Status": "In Progress"}), [])
        self.assertEqual(model.field_edits({"Gate": "E2 pending"}, {"Gate": "E2 approved"}), [])
        self.assertEqual(model.field_edits({"Gate": "E3 pending"}, {"Gate": "E2 approved"}),
                         [("Gate", "E3 pending")])
        self.assertEqual(model.label_edits(["openspec"], ["openspec", "blocked", "theirs"]), ([], ["blocked"]))
        self.assertEqual(model.option_id({"options": {"In Progress": "o1"}}, "in progress"), "o1")


class TestTracker(unittest.TestCase):
    def test_project_file_wins_key_by_key(self):
        t, errs = model.resolve_tracker({"kind": "github-projects", "owner": "x", "owner_type": "user",
                                         "project_number": 1, "repo": "x/y", "bot_login": "ci[bot]"},
                                        {"tracker": {"owner": "acme", "owner_type": "organization"}})
        self.assertEqual(errs, [])
        self.assertEqual((t["owner"], t["owner_type"], t["repo"]), ("acme", "organization", "x/y"))

    def test_absent_means_disabled_and_errors_surface(self):
        self.assertEqual(model.resolve_tracker(None, None)[0]["kind"], "none")
        _, errs = model.resolve_tracker(None, {"kind": "github-projects", "owner": "a"})
        self.assertTrue(any("owner_type" in e for e in errs))

    def test_template_asset_is_valid(self):
        path = os.path.join(os.path.dirname(fake_gh.SCRIPTS), "assets", "github.template.yaml")
        t, errs = model.resolve_tracker(None, model._mini_yaml.load(read(path)))
        self.assertEqual(errs, [])
        self.assertEqual(t["bot_login"], "openspec-bot[bot]")


class TestCommands(unittest.TestCase):
    def test_grammar(self):
        p = model.parse_command
        self.assertEqual(p("/approve E2")["kind"], "gate")
        self.assertEqual(p("/reject E3 needs more tests")["text"], "needs more tests")
        self.assertEqual(p("/accept delta-01")["target"], "01")
        self.assertEqual(p("/revise delta-02 use 25 per page")["verdict"], "revise")
        self.assertEqual(p("/answer escalation-01 drop the task")["kind"], "escalation")
        self.assertEqual(p("/approve E2\r\nthanks")["target"], "E2")
        for ignored in ("lgtm", "/lgtm", "", "approve E2", " /approve E2"):
            self.assertIsNone(p(ignored), ignored)
        for bad in ("/approve E2 now", "/approve e2", "/approve E10", "/reject E2", "/accept delta-1",
                    "/approve E2; rm -rf /", "/approve  E2", "/answer escalation-01"):
            with self.assertRaises(model.CommandError, msg=bad):
                p(bad)

    def test_injection_looking_body_is_text(self):
        cmd = model.parse_command("/approve E2\n$(rm -rf /)")
        self.assertEqual(cmd["line"], "/approve E2")
        body = model.confirmation_body({"change": "c", "gate": "E2", "verdict": "approved", "by": "alice",
                                        "comment_url": "u", "comment_id": 1, "created_at": "t"},
                                       "/approve E2\n$(rm -rf /)")
        self.assertIn("> $(rm -rf /)", body)


class TestEvaluate(unittest.TestCase):
    def ctx(self, **over):
        issue = {"change": "c", "obj": "change", "trusted": True, "labels": [], "state": "open",
                 "created_at": "2026-11-05T09:00:00Z", "stage": "E2", "stage_updated_at": "2026-11-05T10:00:00Z"}
        issue.update(over.pop("issue", {}))
        base = {"author": "alice", "body": "/approve E2", "created_at": "2026-11-05T11:00:00Z",
                "tracker": TRACKER, "issue": issue, "delta": None}
        base.update(over)
        return base

    def check(self, line, ctx, ok, reason_part=""):
        res = model.evaluate(model.parse_command(line), ctx)
        self.assertEqual(res["ok"], ok, res)
        self.assertIn(reason_part, res["reason"])
        return res

    def test_accept_gate(self):
        res = self.check("/approve E2", self.ctx(), True)
        self.assertEqual(res["label"], "gate:E2:approved")
        self.assertEqual(self.check("/reject E2 no", self.ctx(), True)["label"], "gate:E2:rejected")

    def test_refusals(self):
        stranger = self.check("/approve E2", self.ctx(author="mallory"), False, "not in tracker.approvers")
        self.assertTrue(stranger["silent"])                  # never answer strangers (audit F6)
        bot = self.check("/approve E2", self.ctx(author="openspec-bot[bot]"), False, "bot login")
        self.assertTrue(bot["silent"])
        self.check("/approve E2", self.ctx(body="/approve E2\n" + model.BOT_MARKER), False, "bot marker")
        self.check("/approve E3", self.ctx(), False, "out of order")
        self.check("/approve E4", self.ctx(issue={"stage": "E4"}), False, "not a gate")
        self.check("/approve E2", self.ctx(created_at="2026-11-05T09:59:00Z"), False, "older")
        self.check("/approve E2", self.ctx(issue={"stage_updated_at": None}), False, "updatedAt")
        self.check("/approve E2", self.ctx(issue={"labels": ["gate:E2:approved"]}), False, "already")
        self.check("/approve E2", self.ctx(issue={"trusted": False}), False, "trusted")
        self.check("/approve E2", self.ctx(issue={"obj": "task:T1"}), False, "change issue")

    def test_delta_and_escalation(self):
        delta = {"status": "proposed", "updated_at": "2026-11-05T10:30:00Z"}
        self.assertEqual(self.check("/accept delta-01", self.ctx(delta=delta), True)["label"], "delta:01:accepted")
        self.check("/accept delta-01", self.ctx(), False, "no spec-delta")
        self.check("/accept delta-01", self.ctx(delta=dict(delta, status="accepted")), False, "not open")
        self.check("/accept delta-01", self.ctx(delta=dict(delta, updated_at="2026-11-05T12:00:00Z")), False, "older")
        esc = {"obj": "escalation:escalation-01"}
        self.check("/answer escalation-01 drop it", self.ctx(issue=esc), True)
        self.check("/answer escalation-01 drop it", self.ctx(), False, "that escalation")
        self.check("/answer escalation-01 x", self.ctx(issue=dict(esc, state="closed")), False, "closed")


class TestPullHelpers(unittest.TestCase):
    DECISION = {"change": "c", "gate": "E2", "verdict": "approved", "by": "alice",
                "comment_url": "https://github.com/acme/shop/issues/1#issuecomment-7", "comment_id": 7,
                "created_at": "2026-11-05T11:00:00Z"}

    def test_decision_round_trip(self):
        body = model.confirmation_body(self.DECISION, "/approve E2\n```yaml\ndecision: {gate: E9}\n```")
        self.assertEqual(model.parse_decision(body), self.DECISION)
        self.assertIsNone(model.parse_decision(body.replace(model.BOT_MARKER, "")))

    def test_recheck(self):
        user = {"user": {"login": "alice"}, "body": "/approve E2", "created_at": "2026-11-05T11:00:00Z"}
        r = model.recheck_user_comment
        self.assertIsNone(r(self.DECISION, user, "2026-11-05T11:00:05Z", TRACKER))
        self.assertIn("edited", r(self.DECISION, dict(user, body="/approve E3"), "2026-11-05T11:00:05Z", TRACKER))
        self.assertIn("differs", r(self.DECISION, dict(user, user={"login": "bob"}), "2026-11-05T11:00:05Z", TRACKER))
        self.assertIn("older", r(self.DECISION, user, "2026-11-05T10:00:00Z", TRACKER))
        self.assertIn("not found", r(self.DECISION, None, "x", TRACKER))
        on_issue = dict(user, issue_url="https://api.github.com/repos/acme/shop/issues/1")
        self.assertIsNone(r(self.DECISION, on_issue, "2026-11-05T11:00:05Z", TRACKER, ("acme/shop", 1)))
        self.assertIn("not on issue #2", r(self.DECISION, on_issue, "2026-11-05T11:00:05Z", TRACKER,
                                           ("acme/shop", 2)))
        self.assertIn("not on issue", r(self.DECISION, user, "2026-11-05T11:00:05Z", TRACKER, ("acme/shop", 1)))

    def test_recheck_gate(self):
        d = dict(self.DECISION, gate="E9")
        conf_body = model.confirmation_body(d, "/approve E9")
        user = {"user": {"login": "alice"}, "body": "/approve E9", "created_at": d["created_at"],
                "issue_url": "https://api.github.com/repos/acme/shop/issues/1"}
        confs = [{"id": 3, "user": {"login": "openspec-bot[bot]"}, "body": conf_body,
                  "created_at": "2026-11-05T11:00:09Z"}]
        issue = {"change": "c", "obj": "change", "trusted": True, "stage": "E9",
                 "stage_updated_at": "2026-11-05T10:00:00Z"}
        rg = model.recheck_gate
        ok, why = rg("E9", confs, lambda cid: user, TRACKER, issue, "acme/shop", 1)
        self.assertTrue(ok, why)
        forged = [dict(confs[0], user={"login": "mallory"})]
        self.assertFalse(rg("E9", forged, lambda cid: user, TRACKER, issue, "acme/shop", 1)[0])
        late = dict(issue, stage_updated_at="2026-11-05T12:00:00Z")
        self.assertIn("older than the current Stage", rg("E9", confs, lambda cid: user, TRACKER, late,
                                                          "acme/shop", 1)[1][0])
        self.assertFalse(rg("E9", confs, lambda cid: user, TRACKER, dict(issue, obj="task:T1"), "acme/shop", 1)[0])
        self.assertFalse(rg("E9", confs, lambda cid: user, TRACKER, dict(issue, stage="E7"), "acme/shop", 1)[0])

    def test_approval_line_and_append(self):
        line = model.approval_line(self.DECISION, "https://github.com/acme/shop/issues/1", '/approve E2\nsay "ok"')
        self.assertEqual(line, '- 2026-11-05T11:00:00Z | gate=E2 | subject=https://github.com/acme/shop/issues/1 | '
                               'source=github https://github.com/acme/shop/issues/1#issuecomment-7 login=alice | '
                               'user said: "/approve E2 say \\"ok\\""')
        status = "# x\n\n## Approvals\n\n(none recorded)\n\n## Last synced SHA\n\n`none`\n"
        out = model.append_approval(status, line)
        self.assertNotIn("(none recorded)", out)
        self.assertLess(out.index(line), out.index("## Last synced SHA"))
        self.assertIn("## Approvals\n\n" + line, model.append_approval("# x\n", line))
        twice = model.append_approval(out, "- second")
        self.assertLess(twice.index(line), twice.index("- second"))

    def test_change_id_from_issue(self):
        body = model.header("list-tenant-items", "change")
        self.assertEqual(model.change_id_from_issue("whatever", body), "list-tenant-items")
        self.assertEqual(model.change_id_from_issue("change: add-2fa", ""), "add-2fa")
        self.assertIsNone(model.change_id_from_issue("change: ../etc", ""))



class TrustFailsClosed(unittest.TestCase):
    def test_no_lists_trusts_nobody(self):
        self.assertFalse(model.trusted_author("stranger", {}))
        self.assertFalse(model.trusted_author("", {"bot_login": "ci[bot]"}))

    def test_bot_and_approvers_are_trusted(self):
        t = {"approvers": ["alice"], "bot_login": "ci[bot]"}
        self.assertTrue(model.trusted_author("alice", t))
        self.assertTrue(model.trusted_author("ci[bot]", t))
        self.assertFalse(model.trusted_author("mallory", t))


OK_PATCH = """diff --git a/openspec/changes/x/proposal.md b/openspec/changes/archive/2026-11-05-x/proposal.md
similarity index 100%
rename from openspec/changes/x/proposal.md
rename to openspec/changes/archive/2026-11-05-x/proposal.md
diff --git a/openspec/specs/items/spec.md b/openspec/specs/items/spec.md
index 1111111..2222222 100644
--- a/openspec/specs/items/spec.md
+++ b/openspec/specs/items/spec.md
@@ -1 +1,2 @@
 a
+b
diff --git a/openspec/specs/new/spec.md b/openspec/specs/new/spec.md
new file mode 100644
index 0000000..3333333
"""


class TestCheckPatch(unittest.TestCase):
    """Archive publish guard (audit N2): both sides of every file pair under openspec/, regular modes."""

    def refused(self, text, part):
        problems = model.check_patch(text)
        self.assertTrue(any(part in p for p in problems), problems)

    def test_openspec_only_patch_is_allowed(self):
        self.assertEqual(model.check_patch(OK_PATCH), [])

    def test_rename_from_github_into_openspec_is_refused(self):
        self.refused("diff --git a/.github/workflows/x.yml b/openspec/x.yml\nsimilarity index 100%\n"
                     "rename from .github/workflows/x.yml\nrename to openspec/x.yml\n", ".github/workflows/x.yml")
        self.refused("diff --git a/openspec/a b/openspec/b\ncopy from .github/openspec-github/_gh.py\n"
                     "copy to openspec/b\n", "copy from")

    def test_add_outside_openspec_is_refused(self):
        self.refused("diff --git a/.github/evil.yml b/.github/evil.yml\nnew file mode 100644\n", "outside")
        self.refused("diff --git a/openspec/../.github/x b/openspec/../.github/x\n", "outside")

    def test_mode_change_is_refused(self):
        self.refused("diff --git a/openspec/run.sh b/openspec/run.sh\nold mode 100644\nnew mode 100755\n",
                     "mode change")

    def test_symlink_and_submodule_are_refused(self):
        self.refused("diff --git a/openspec/l b/openspec/l\nnew file mode 120000\n", "120000")
        self.refused("diff --git a/openspec/m b/openspec/m\nindex 0000000..4444444 160000\n", "160000")

    def test_quoted_or_empty_patch_is_refused(self):
        self.refused('diff --git "a/openspec/\\303\\251" "b/openspec/\\303\\251"\n', "quoted")
        self.refused("", "no file")


if __name__ == "__main__":
    unittest.main()
