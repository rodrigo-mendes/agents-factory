"""Tests of gate_command.py against the offline fake gh (tests/fake_gh.py). No network.

Each test mirrors the fixture change into the simulated GitHub with ``push --apply`` (the
simulated token identity is the bot), then feeds one issue_comment payload through the
environment, exactly as openspec-gate.yml does.
"""
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fake_gh  # noqa: E402

fake_gh.prepare_imports()
import _model as model  # noqa: E402
import gate_command  # noqa: E402
import gh_projects_sync as sync  # noqa: E402

BOT = "openspec-bot[bot]"


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


class GateCase(unittest.TestCase):
    """setUpClass mirrors the fixture once; every test gets a copy of the repo and of the sim."""

    @classmethod
    def setUpClass(cls):
        cls.base = tempfile.mkdtemp(prefix="osgh-gate-base-")
        shutil.copytree(os.path.join(fake_gh.FIXTURES, "repo"), os.path.join(cls.base, "repo"))
        with fake_gh.FakeGh(cls.base) as fake:
            code, _, err = fake_gh.run_main(sync, ["push", os.path.join(cls.base, "repo"), "--change",
                                                   fake_gh.CHANGE, "--profile", fake_gh.PROFILE, "--apply"])
            assert code == 0, err
            cls.base_sim = fake.sim()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.base, True)

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="osgh-gate-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.repo = os.path.join(self.tmp, "repo")
        shutil.copytree(os.path.join(self.base, "repo"), self.repo)
        self.fake = fake_gh.FakeGh(self.tmp, sim=self.base_sim)
        self.fake.__enter__()
        self.addCleanup(self.fake.__exit__)
        self.saved_env = {k: os.environ.get(k) for k in gate_command.ENV_KEYS}
        self.addCleanup(self.restore_env)
        self.handoff = os.path.join(self.repo, "openspec/changes", fake_gh.CHANGE, "handoff")
        self.state = model.load_state(read(os.path.join(self.handoff, "github.yaml")), {})
        self.change_issue = self.state["change"]["issue"]

    def restore_env(self):
        for k, v in self.saved_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def comment(self, body, author="alice", issue=None, created_at=None):
        issue = issue or self.change_issue
        cid, ts = self.fake.add_comment(issue, author, body)
        os.environ.update({"COMMENT_BODY": body, "COMMENT_AUTHOR": author,
                           "COMMENT_URL": "https://github.com/acme/shop/issues/%d#issuecomment-%d" % (issue, cid),
                           "COMMENT_ID": str(cid), "ISSUE_NUMBER": str(issue),
                           "CREATED_AT": created_at or ts})
        return cid

    def evaluate(self, apply=True):
        argv = ["evaluate", self.repo, "--profile", fake_gh.PROFILE] + (["--apply"] if apply else [])
        return fake_gh.run_main(gate_command, argv)

    def bot_comments(self, issue=None):
        issue = issue or self.change_issue
        return [c for c in self.fake.sim()["comments"].values()
                if c["issue"] == issue and c["author"] == BOT and c["body"].startswith(model.BOT_MARKER)
                and model.parse_key_marker(c["body"])[0] is None]

    def labels(self, issue=None):
        return self.fake.sim()["issues"][str(issue or self.change_issue)]["labels"]


class TestGateAccept(GateCase):
    def test_approve_current_gate(self):
        self.comment("/approve E2")
        code, out, err = self.evaluate()
        self.assertEqual(code, 0, err)
        self.assertIn("ACCEPTED: approved E2 by alice", out)
        self.assertIn("gate:E2:approved", self.labels())
        conf = self.bot_comments()
        self.assertEqual(len(conf), 1)
        decision = model.parse_decision(conf[0]["body"])
        self.assertEqual((decision["gate"], decision["verdict"], decision["by"]), ("E2", "approved", "alice"))
        item = [i for i in self.fake.sim()["items"].values() if i["content"] == "I_%d" % self.change_issue][0]
        self.assertEqual(item["values"]["F_Gate"]["value"], "E2 approved")
        self.assertNotIn("fake-token-value", out + err)

    def test_injection_looking_body_is_quoted_text(self):
        self.comment("/approve E2\n$(rm -rf /)")
        code, out, _ = self.evaluate()
        self.assertEqual(code, 0)
        self.assertIn("ACCEPTED", out)
        body = self.bot_comments()[0]["body"]
        self.assertIn("> $(rm -rf /)", body)
        for call in self.fake.calls():
            self.assertNotIn("rm -rf", " ".join(call["argv"]))  # body travels on stdin only

    def test_dry_run_writes_nothing(self):
        self.comment("/approve E2")
        code, out, _ = self.evaluate(apply=False)
        self.assertEqual(code, 0)
        self.assertIn("PLAN gh api -X POST repos/acme/shop/issues/%d/labels" % self.change_issue, out)
        self.assertEqual(self.fake.mutations(), [])

    def test_accept_delta_creates_label_lazily(self):
        self.comment("/accept delta-01")
        code, out, err = self.evaluate()
        self.assertEqual(code, 0, err)
        self.assertIn("ACCEPTED", out)
        self.assertIn("delta:01:accepted", self.labels())
        self.assertIn("delta:01:accepted", self.fake.sim()["labels"])

    def test_answer_escalation_on_its_issue(self):
        handoff = self.handoff
        with open(os.path.join(handoff, "escalation-01.md"), "w", encoding="utf-8") as fh:
            fh.write("---\nkind: escalation\nid: escalation-01\nfrom: building-quarkus-aws-saas\nto: user\n"
                     "change: list-tenant-items\nstatus: open\ncreatedAt: 2026-11-04T11:00:00Z\n---\n\n"
                     "## Options\n\n1. a\n2. b\n")
        fake_gh.run_main(sync, ["push", self.repo, "--change", fake_gh.CHANGE, "--profile",
                                fake_gh.PROFILE, "--apply"])
        state = read(os.path.join(handoff, "github.yaml"))
        esc_issue = model.load_state(state, {})["escalations"]["escalation-01"]["issue"]
        self.comment("/answer escalation-01 take option 2", issue=esc_issue)
        code, out, err = self.evaluate()
        self.assertEqual(code, 0, err)
        self.assertIn("ACCEPTED: answered 01", out)
        self.assertEqual(len(self.bot_comments(esc_issue)), 1)


class TestGateRefuse(GateCase):
    def assert_refused(self, reason_part, posts=True):
        code, out, err = self.evaluate()
        self.assertEqual(code, 0, err)
        self.assertNotIn("ACCEPTED", out)
        self.assertNotIn("gate:E2:approved", self.labels())
        conf = self.bot_comments()
        if posts:
            self.assertEqual(len(conf), 1, out)
            self.assertIn("Not recorded", conf[0]["body"])
            self.assertIn(reason_part, conf[0]["body"])
            self.assertIsNone(model.parse_decision(conf[0]["body"]))
        else:
            self.assertEqual(conf, [])
            self.assertEqual(self.fake.mutations(), [])
            self.assertIn(reason_part, out)
        return out

    def test_author_not_in_allowlist_is_ignored_silently(self):
        self.comment("/approve E2", author="mallory")
        self.assert_refused("not in tracker.approvers", posts=False)

    def test_non_approver_malformed_command_is_ignored_silently(self):
        self.comment("/approve E2 please", author="mallory")
        self.assert_refused("not in tracker.approvers", posts=False)

    def test_bot_author_is_ignored_silently(self):
        self.comment("/approve E2", author=BOT)
        self.assert_refused("bot login", posts=False)

    def test_bot_marker_in_body(self):
        self.comment("/approve E2\n" + model.BOT_MARKER)
        self.assert_refused("bot marker")

    def test_out_of_order_gate(self):
        self.comment("/approve E3")
        self.assert_refused("out of order")

    def test_comment_older_than_stage(self):
        self.comment("/approve E2", created_at="2026-01-01T00:00:00Z")
        self.assert_refused("older than the current Stage")

    def test_malformed_command(self):
        self.comment("/approve E2 please")
        self.assert_refused("malformed command")

    def test_unknown_verb_is_ignored(self):
        self.comment("/lgtm")
        self.assert_refused("not a gate command", posts=False)

    def test_approval_source_chat_is_ignored(self):
        path = os.path.join(self.repo, "openspec", "github-tracker.yaml")
        text = read(path).replace("approval_source: github", "approval_source: chat")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        self.comment("/approve E2")
        self.assert_refused("approval_source is chat", posts=False)


class TestRecheck(GateCase):
    """gate_command.py recheck --gate E9: what the archive workflow runs before acting (audit F5/F12)."""

    def setUp(self):
        GateCase.setUp(self)
        code, _, err = fake_gh.run_main(sync, ["push", self.repo, "--change", fake_gh.CHANGE, "--profile",
                                               fake_gh.PROFILE, "--stage", "E9", "--apply"])
        self.assertEqual(code, 0, err)

    def recheck(self):
        os.environ["ISSUE_NUMBER"] = str(self.change_issue)
        return fake_gh.run_main(gate_command, ["recheck", self.repo, "--profile", fake_gh.PROFILE,
                                               "--gate", "E9"])

    def approve_e9(self):
        cid = self.comment("/approve E9")
        code, out, err = self.evaluate()
        self.assertIn("ACCEPTED", out, err)
        return cid

    def test_passes_after_a_confirmed_approval(self):
        self.approve_e9()
        self.fake.reset_log()
        code, out, err = self.recheck()
        self.assertEqual(code, 0, out + err)
        self.assertIn("RECHECK OK: approved by alice", out)
        self.assertEqual(self.fake.mutations(), [])

    def test_fails_on_the_label_alone(self):
        sim = self.fake.sim()
        sim["issues"][str(self.change_issue)]["labels"].append("gate:E9:approved")
        self.fake.save_sim(sim)
        code, out, _ = self.recheck()
        self.assertEqual(code, 1)
        self.assertIn("RECHECK FAILED: no confirmation of E9", out)

    def test_fails_when_the_user_comment_was_edited(self):
        cid = self.approve_e9()
        sim = self.fake.sim()
        sim["comments"][str(cid)]["body"] = "/reject E9 changed my mind"
        self.fake.save_sim(sim)
        code, out, _ = self.recheck()
        self.assertEqual(code, 1)
        self.assertIn("edited", out)

    def test_fails_when_the_user_comment_is_on_another_issue(self):
        cid = self.approve_e9()
        sim = self.fake.sim()
        sim["comments"][str(cid)]["issue"] = self.state["tasks"]["T2"]["issue"]
        self.fake.save_sim(sim)
        code, out, _ = self.recheck()
        self.assertEqual(code, 1)
        self.assertIn("not on issue #%d" % self.change_issue, out)

    def test_fails_when_the_stage_moved_on(self):
        self.approve_e9()
        fake_gh.run_main(sync, ["push", self.repo, "--change", fake_gh.CHANGE, "--profile",
                                fake_gh.PROFILE, "--stage", "E8", "--apply"])
        code, out, _ = self.recheck()
        self.assertEqual(code, 1)
        self.assertIn("Stage E8, not E9", out)


class TestGateMisc(GateCase):
    def test_tracker_disabled_exit_3(self):
        with open(os.path.join(self.repo, "openspec", "github-tracker.yaml"), "w", encoding="utf-8") as fh:
            fh.write("kind: none\n")
        self.comment("/approve E2")
        code, out, _ = self.evaluate()
        self.assertEqual((code, out.strip()), (3, "tracker disabled"))

    def test_missing_payload_is_an_error(self):
        os.environ.pop("COMMENT_BODY", None)
        code, _, err = self.evaluate()
        self.assertEqual(code, 1)
        self.assertIn("COMMENT_BODY", err)

    def test_resolve_change(self):
        os.environ["ISSUE_TITLE"] = "change: list-tenant-items"
        os.environ["ISSUE_BODY"] = "label text is never used"
        self.addCleanup(os.environ.pop, "ISSUE_TITLE", None)
        self.addCleanup(os.environ.pop, "ISSUE_BODY", None)
        code, out, _ = fake_gh.run_main(gate_command, ["resolve-change", self.repo])
        self.assertEqual((code, out.strip()), (0, "change=list-tenant-items"))
        os.environ["ISSUE_TITLE"] = "change: does-not-exist"
        self.assertEqual(fake_gh.run_main(gate_command, ["resolve-change", self.repo])[0], 1)
        os.environ["ISSUE_TITLE"] = "change: x; rm -rf /"
        self.assertEqual(fake_gh.run_main(gate_command, ["resolve-change", self.repo])[0], 1)

    def test_check_patch_cli(self):
        good = os.path.join(self.tmp, "good.patch")
        bad = os.path.join(self.tmp, "bad.patch")
        with open(good, "w", encoding="utf-8") as fh:
            fh.write("diff --git a/openspec/a.md b/openspec/a.md\nnew file mode 100644\n")
        with open(bad, "w", encoding="utf-8") as fh:
            fh.write("diff --git a/.github/x b/openspec/x\nrename from .github/x\nrename to openspec/x\n")
        code, out, _ = fake_gh.run_main(gate_command, ["check-patch", good])
        self.assertEqual((code, out.strip()), (0, "PATCH OK"))
        code, out, _ = fake_gh.run_main(gate_command, ["check-patch", bad])
        self.assertEqual(code, 1)
        self.assertIn("PATCH REFUSED", out)

    def test_payload_never_on_argv(self):
        self.comment("/approve E2")
        self.evaluate()
        for call in self.fake.calls():
            self.assertNotIn("/approve E2", json.dumps(call["argv"]))


if __name__ == "__main__":
    unittest.main()
