"""Tests of gh_projects_sync.py, _vendor.py, _gh.py and the workflow templates. No network, no
real gh: every gh call goes to tests/fake_gh.py (an in-memory GitHub persisted per test).
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fake_gh  # noqa: E402

fake_gh.prepare_imports()
import _gh as gh  # noqa: E402
import _model as model  # noqa: E402
import _vendor  # noqa: E402
import gate_command  # noqa: E402
import gh_projects_sync as sync  # noqa: E402

REAL_UNCOMMITTED = sync.uncommitted_reason
SKILL = os.path.dirname(fake_gh.SCRIPTS)
WORKFLOWS = os.path.join(SKILL, "assets", "workflows")
BOT = "openspec-bot[bot]"
PINS = {"actions/checkout": ("3d3c42e5aac5ba805825da76410c181273ba90b1", "v7.0.1"),
        "actions/create-github-app-token": ("64ab729a6294000f5aa4a4bc0b73d1f32bc45510", "v3.3.0"),
        "actions/setup-python": ("6d4fd22b20465ccc0f7354476588e8df7c9ca0e0", "v7.1.0")}


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


class SyncCase(unittest.TestCase):
    sim = None

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="osgh-sync-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.repo = os.path.join(self.tmp, "repo")
        shutil.copytree(getattr(self, "base_repo", None) or os.path.join(fake_gh.FIXTURES, "repo"), self.repo)
        self.fake = fake_gh.FakeGh(self.tmp, sim=self.sim, overrides=getattr(self, "overrides", None))
        self.fake.__enter__()
        self.addCleanup(self.fake.__exit__)
        self.handoff = os.path.join(self.repo, "openspec", "changes", fake_gh.CHANGE, "handoff")

    def sync(self, command, *extra):
        argv = [command, self.repo, "--change", fake_gh.CHANGE, "--profile", fake_gh.PROFILE] + list(extra)
        return fake_gh.run_main(sync, argv)

    def state(self):
        return model.load_state(read(os.path.join(self.handoff, "github.yaml")), {})

    def edit(self, name, old, new):
        path = os.path.join(self.handoff, name)
        text = read(path)
        self.assertIn(old, text)
        write(path, text.replace(old, new))


class AppliedCase(SyncCase):
    """Starts from the fixture already mirrored once (push --apply in setUpClass)."""

    @classmethod
    def setUpClass(cls):
        cls.base = tempfile.mkdtemp(prefix="osgh-sync-base-")
        cls.base_repo = os.path.join(cls.base, "repo")
        shutil.copytree(os.path.join(fake_gh.FIXTURES, "repo"), cls.base_repo)
        with fake_gh.FakeGh(cls.base) as fake:
            code, _, err = fake_gh.run_main(sync, ["push", cls.base_repo, "--change", fake_gh.CHANGE,
                                                   "--profile", fake_gh.PROFILE, "--apply"])
            assert code == 0, err
            cls.sim = fake.sim()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.base, True)


# ===================================================================== push

class TestPushFresh(SyncCase):
    def test_dry_run_makes_no_mutating_call(self):
        code, out, err = self.sync("push")
        self.assertEqual(code, 0, err)
        self.assertIn("PLAN gh api -X POST repos/acme/shop/issues", out)
        self.assertEqual(self.fake.mutations(), [])
        self.assertFalse(os.path.exists(os.path.join(self.handoff, "github.yaml")))

    def test_apply_creates_then_second_apply_is_a_no_op(self):
        code, out, err = self.sync("push", "--apply")
        self.assertEqual(code, 0, err)
        sim = self.fake.sim()
        titles = sorted(i["title"] for i in sim["issues"].values())
        self.assertEqual(titles, ["adr: 003 Tenant isolation", "change: list-tenant-items",
                                  "task: T1 Items endpoint", "task: T2 Documentation"])
        change = [i for i in sim["issues"].values() if i["title"].startswith("change:")][0]
        children = [i for i in sim["issues"].values() if i.get("parent") == change["number"]]
        self.assertEqual(len(children), 3)
        self.assertEqual(len(sim["items"]), 4)
        values = [i for i in sim["items"].values() if i["content"] == change["node_id"]][0]["values"]
        self.assertEqual(values["F_Stage"]["value"], "O_Stage_E2")
        self.assertEqual(values["F_Status"]["value"], "O_Status_1")   # built-in "In Progress"
        self.assertEqual(len(sim["comments"]), 2)                       # spec-delta-01 + summary
        for c in list(sim["comments"].values()) + list(sim["issues"].values()):
            self.assertTrue(c["body"].startswith(model.BOT_MARKER))
        self.fake.reset_log()
        code, out, err = self.sync("push", "--apply")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.fake.mutations(), [])
        self.assertIn("applied 0 write(s)", out)

    def test_tracker_disabled_exit_3(self):
        write(os.path.join(self.repo, "openspec", "github-tracker.yaml"), "kind: none\n")
        code, out, _ = self.sync("push", "--apply")
        self.assertEqual((code, out.strip()), (3, "tracker disabled"))
        self.assertEqual(self.fake.calls(), [])

    def test_old_gh_is_rejected(self):
        self.fake.set_overrides([{"match": ["--version"], "stdout": "gh version 2.93.0 (2026-05-27)\n"}])
        code, _, err = self.sync("push")
        self.assertEqual(code, 1)
        self.assertIn("older than the required 2.94.0", err)

    def test_non_pinned_gh_warns(self):
        self.fake.set_overrides([{"match": ["--version"], "stdout": "gh version 2.99.0 (2026-09-01)\n"}])
        code, _, err = self.sync("push")
        self.assertEqual(code, 0)
        self.assertIn("not the family pin 2.103.x", err)

    def test_auth_failure_never_prints_the_token(self):
        self.fake.set_overrides([{"match": ["auth", "status"], "code": 1,
                                  "stderr": "token fake-token-value-123456 invalid"}])
        code, out, err = self.sync("push")
        self.assertEqual(code, 1)
        self.assertIn("gh auth status failed", err)
        self.assertNotIn("fake-token-value-123456", out + err)
        self.assertFalse(any("--show-token" in c["argv"] for c in self.fake.calls()))

    def test_invalid_tracker_is_an_error(self):
        write(os.path.join(self.repo, "openspec", "github-tracker.yaml"),
              "kind: github-projects\nowner: acme\nowner_type: team\nproject_number: 7\nrepo: acme/shop\n")
        code, _, err = self.sync("push")
        self.assertEqual(code, 1)
        self.assertIn("owner_type", err)

    def test_user_owner_prints_classic_pat_warning(self):
        path = os.path.join(self.repo, "openspec", "github-tracker.yaml")
        write(path, read(path).replace("owner_type: organization", "owner_type: user"))
        code, _, err = self.sync("push")
        self.assertEqual(code, 1)          # the simulated project is organization-owned only
        self.assertIn("classic personal access token", err)


class TestPushApplied(AppliedCase):
    def test_adoption_without_state_file_issues_no_write(self):
        os.remove(os.path.join(self.handoff, "github.yaml"))
        code, out, err = self.sync("push", "--apply")
        self.assertEqual(code, 0, err)
        self.assertIn("ADOPT change -> #101", out)
        self.assertEqual(self.fake.mutations(), [])
        self.assertEqual(self.state()["change"]["issue"], 101)

    def test_task_status_follows_work_order(self):
        self.edit("wo-01-code.md", "status: done", "status: in-progress")
        code, _, err = self.sync("push", "--apply")
        self.assertEqual(code, 0, err)
        t1 = self.state()["tasks"]["T1"]
        issue = self.fake.sim()["issues"][str(t1["issue"])]
        self.assertEqual(issue["state"], "open")
        self.assertEqual(t1["fields"]["Status"], "In progress")

    def test_escalation_blocked_then_answered(self):
        write(os.path.join(self.handoff, "escalation-01.md"),
              "---\nkind: escalation\nid: escalation-01\nfrom: building-aws-saas-serverless-quarkus-react-nextjs\nto: user\n"
              "change: list-tenant-items\nstatus: open\ncreatedAt: 2026-11-04T11:00:00Z\n---\n\n"
              "## Options\n\n1. a\n2. b\n")
        self.assertEqual(self.sync("push", "--apply")[0], 0)
        esc = self.state()["escalations"]["escalation-01"]
        issue = self.fake.sim()["issues"][str(esc["issue"])]
        self.assertIn("blocked", issue["labels"])
        self.assertEqual(issue["parent"], self.state()["change"]["issue"])
        self.assertEqual(esc["fields"]["Status"], "Blocked")
        self.assertEqual(self.state()["change"]["fields"]["Status"], "Blocked")
        self.edit("escalation-01.md", "status: open", "status: answered")
        self.assertEqual(self.sync("push", "--apply")[0], 0)
        issue = self.fake.sim()["issues"][str(esc["issue"])]
        self.assertEqual((issue["state"], issue["labels"]), ("closed", ["openspec"]))

    def test_delta_comment_is_edited_in_place(self):
        before = dict(self.fake.sim()["comments"])
        self.edit("spec-delta-01.md", "status: proposed", "status: accepted")
        self.fake.reset_log()
        self.assertEqual(self.sync("push", "--apply")[0], 0)
        writes = [" ".join(c["argv"]) for c in self.fake.mutations()]
        self.assertTrue(any("PATCH repos/acme/shop/issues/comments/9001" in w for w in writes), writes)
        self.assertFalse(any("/comments --input" in w and "POST" in w for w in writes), writes)
        after = self.fake.sim()["comments"]
        self.assertEqual(set(after), set(before))
        self.assertIn("status=accepted", after["9001"]["body"])
        self.assertNotIn("/accept delta-01", after["9001"]["body"])

    def test_stage_override_and_close(self):
        self.assertEqual(self.sync("push", "--stage", "E3", "--apply")[0], 0)
        self.assertEqual(self.state()["change"]["fields"]["Stage"], "E3")
        code, _, err = self.sync("close", "--apply")
        self.assertEqual(code, 0, err)
        self.assertTrue(all(i["state"] == "closed" for i in self.fake.sim()["issues"].values()))
        self.assertEqual(self.state()["change"]["fields"]["Status"], "Done")

    def test_status_in_sync_then_diverged(self):
        code, out, err = self.sync("status")
        self.assertEqual(code, 0, out + err)
        self.assertIn("IN SYNC", out)
        path = os.path.join(self.repo, "openspec", "changes", fake_gh.CHANGE, "proposal.md")
        write(path, read(path).replace("Tenants need", "Customers need"))
        code, out, _ = self.sync("status")
        self.assertEqual(code, 2)
        self.assertIn("DIVERGE change: title/body differ", out)
        self.assertEqual(self.fake.mutations(), [])


class TestOperatorLogin(SyncCase):
    """Family rule 13 / audit F1: never run with an approver's gh login when approvals come from GitHub."""

    def test_approver_login_is_refused_for_every_subcommand(self):
        self.fake.set_viewer("alice")
        for command in ("bootstrap", "push", "pull", "close", "status"):
            code, out, err = self.sync(command)
            self.assertEqual(code, 1, command)
            self.assertIn("'alice' is in tracker.approvers", err, command)
            self.assertIn("approve in the browser", err, command)
        self.assertEqual(self.fake.mutations(), [])

    def test_non_approver_login_is_allowed(self):
        self.fake.set_viewer("ci-machine-user")
        self.assertEqual(self.sync("push")[0], 0)

    def test_chat_approval_source_is_unaffected(self):
        path = os.path.join(self.repo, "openspec", "github-tracker.yaml")
        write(path, read(path).replace("approval_source: github", "approval_source: chat"))
        self.fake.set_viewer("alice")
        self.assertEqual(self.sync("push")[0], 0)
        self.assertFalse(any(c["argv"][:2] == ["api", "user"] for c in self.fake.calls()))

    def test_unknown_login_refused_locally_allowed_in_actions(self):
        sim = self.fake.sim()
        sim["viewer_is_app"] = True
        self.fake.save_sim(sim)
        saved = os.environ.pop("GITHUB_ACTIONS", None)
        try:
            code, _, err = self.sync("push")
            self.assertEqual(code, 1)
            self.assertIn("cannot determine the gh login", err)
            os.environ["GITHUB_ACTIONS"] = "true"
            code, _, err = self.sync("push")
            self.assertEqual(code, 0, err)
            self.assertIn("continuing in Actions", err)
        finally:
            os.environ.pop("GITHUB_ACTIONS", None)
            if saved is not None:
                os.environ["GITHUB_ACTIONS"] = saved


class TestCliDefaults(SyncCase):
    def test_repo_root_defaults_to_cwd(self):
        old = os.getcwd()
        os.chdir(self.repo)
        try:
            code, out, err = fake_gh.run_main(sync, ["push", "--change", fake_gh.CHANGE, "--profile", fake_gh.PROFILE])
        finally:
            os.chdir(old)
        self.assertEqual(code, 0, err)
        self.assertIn("planned", out)

    def test_missing_profile_prints_a_hint(self):
        code, _, err = fake_gh.run_main(sync, ["push", "--change", fake_gh.CHANGE])
        self.assertEqual(code, 2)
        self.assertIn("hint: pass --profile", err)
        self.assertIn("handoff-profile.yaml", err)


# ===================================================================== pull

def git(repo, *args):
    return subprocess.run(["git", "-C", repo, "-c", "commit.gpgsign=false", "-c", "core.autocrlf=false"]
                          + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")


def git_commit_all(case, repo):
    """git init + commit everything; skip (like handoff-core) when the sandbox forbids it."""
    if not shutil.which("git"):
        case.skipTest("git not installed")
    for args in (["init", "-q"], ["config", "user.email", "t@example.com"], ["config", "user.name", "T"],
                 ["add", "-A"], ["commit", "-q", "-m", "base"]):
        proc = git(repo, *args)
        if proc.returncode != 0:
            case.skipTest("git %s not possible here: %s" % (args[0], proc.stderr.strip()))


class TestPull(AppliedCase):
    """pull behaviour; the committed-file check (F7) is stubbed here and tested in TestTrustAnchors*."""

    dirty = {}

    def setUp(self):
        AppliedCase.setUp(self)
        self.profile = os.path.join(self.repo, "handoff-profile.yaml")
        shutil.copy(fake_gh.PROFILE, self.profile)
        original = sync.uncommitted_reason
        self.addCleanup(setattr, sync, "uncommitted_reason", original)
        sync.uncommitted_reason = lambda path: self.dirty.get(os.path.basename(path))

    def sync(self, command, *extra):
        argv = [command, self.repo, "--change", fake_gh.CHANGE, "--profile", self.profile] + list(extra)
        return fake_gh.run_main(sync, argv)

    def gate(self, body, author="alice"):
        issue = self.state()["change"]["issue"]
        cid, ts = self.fake.add_comment(issue, author, body)
        env = {"COMMENT_BODY": body, "COMMENT_AUTHOR": author, "COMMENT_ID": str(cid),
               "COMMENT_URL": "https://github.com/acme/shop/issues/%d#issuecomment-%d" % (issue, cid),
               "ISSUE_NUMBER": str(issue), "CREATED_AT": ts}
        saved = {k: os.environ.get(k) for k in env}
        os.environ.update(env)
        try:
            code, out, err = fake_gh.run_main(gate_command, ["evaluate", self.repo, "--profile",
                                                             fake_gh.PROFILE, "--apply"])
        finally:
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        self.assertEqual(code, 0, err)
        return cid

    def test_pull_records_bot_confirmed_approval_once(self):
        self.gate("/approve E2\nlooks good")
        code, out, err = self.sync("pull")
        self.assertEqual(code, 0, err)
        self.assertIn("PLAN append status.md ## Approvals:", out)
        self.assertNotIn("gate=E2", read(os.path.join(self.handoff, "status.md")))
        code, out, err = self.sync("pull", "--apply")
        self.assertEqual(code, 0, err)
        self.assertIn("TRUST approvers=alice,bob bot_login=openspec-bot[bot]", out)
        status = read(os.path.join(self.handoff, "status.md"))
        self.assertIn('| gate=E2 | subject=https://github.com/acme/shop/issues/101 | source=github '
                      'https://github.com/acme/shop/issues/101#issuecomment-', status)
        self.assertIn('login=alice | user said: "/approve E2 looks good"', status)
        self.assertIn("2026-11-04: user approved the task plan (E5).", status)
        self.assertEqual(len(self.state()["pulled"]), 1)
        self.fake.reset_log()
        code, out, _ = self.sync("pull", "--apply")
        self.assertEqual(code, 0)
        self.assertEqual(read(os.path.join(self.handoff, "status.md")).count("gate=E2"), 1)
        self.assertEqual(self.fake.mutations(), [])

    def test_pull_ignores_confirmations_not_written_by_the_bot(self):
        user_cid, ts = self.fake.add_comment(101, "alice", "/approve E2")
        forged = model.confirmation_body({"change": fake_gh.CHANGE, "gate": "E2", "verdict": "approved",
                                          "by": "alice", "comment_url": "u", "comment_id": user_cid,
                                          "created_at": ts}, "/approve E2")
        self.fake.add_comment(101, "mallory", forged)
        code, out, _ = self.sync("pull", "--apply")
        self.assertEqual(code, 0)
        self.assertIn("0 approval line(s)", out)
        self.assertNotIn("gate=E2", read(os.path.join(self.handoff, "status.md")))

    def test_pull_refuses_an_edited_user_comment(self):
        cid = self.gate("/approve E2")
        sim = self.fake.sim()
        sim["comments"][str(cid)]["body"] = "/approve E3"
        self.fake.save_sim(sim)
        code, out, _ = self.sync("pull", "--apply")
        self.assertEqual(code, 0)
        self.assertIn("REFUSED confirmation", out)
        self.assertNotIn("gate=E2", read(os.path.join(self.handoff, "status.md")))

    def test_delta_decision_is_printed_as_json(self):
        self.gate("/revise delta-01 use 25 per page")
        code, out, _ = self.sync("pull", "--apply")
        self.assertEqual(code, 0)
        line = [l for l in out.splitlines() if l.startswith("DECISION ")][0]
        doc = model.json.loads(line[len("DECISION "):])
        self.assertEqual((doc["delta"], doc["verdict"], doc["user_said"]),
                         ("delta-01", "revise", "/revise delta-01 use 25 per page"))

    def test_pull_refuses_a_user_comment_on_another_issue(self):
        cid = self.gate("/approve E2")
        sim = self.fake.sim()
        sim["comments"][str(cid)]["issue"] = self.state()["tasks"]["T2"]["issue"]
        self.fake.save_sim(sim)
        code, out, _ = self.sync("pull", "--apply")
        self.assertEqual(code, 0)
        self.assertIn("not on issue #101", out)
        self.assertNotIn("gate=E2", read(os.path.join(self.handoff, "status.md")))

    def test_anchor_outside_a_git_work_tree_fails_closed(self):
        lone = os.path.join(self.tmp, "lone.yaml")
        write(lone, "x: 1\n")
        self.assertIsNotNone(REAL_UNCOMMITTED(lone))

    def test_dirty_anchor_file_refuses(self):
        self.dirty = {"github-tracker.yaml": "has uncommitted changes or is not committed (git status: M)"}
        code, _, err = self.sync("pull", "--apply")
        self.assertEqual(code, 1)
        self.assertIn("github-tracker.yaml has uncommitted changes", err)
        self.assertIn("committed at HEAD", err)

    def test_chat_approval_source_refuses(self):
        path = os.path.join(self.repo, "openspec", "github-tracker.yaml")
        write(path, read(path).replace("approval_source: github", "approval_source: chat"))
        code, _, err = self.sync("pull", "--apply")
        self.assertEqual(code, 1)
        self.assertIn("approval_source is chat", err)

    def test_help_marks_pull_orchestrator_only(self):
        self.assertIn("ORCHESTRATOR ONLY", sync.build_parser().format_help() + sync.__doc__)


class TestTrustAnchorsGit(AppliedCase):
    """Real git: pull refuses anchors that are not committed unchanged at HEAD (audit F7)."""

    def setUp(self):
        AppliedCase.setUp(self)
        self.profile = os.path.join(self.repo, "handoff-profile.yaml")
        shutil.copy(fake_gh.PROFILE, self.profile)
        git_commit_all(self, self.repo)

    sync = TestPull.sync

    def test_clean_anchors_pass(self):
        code, out, err = self.sync("pull")
        self.assertEqual(code, 0, err)
        self.assertIn("TRUST approvers=alice,bob", out)

    def test_pull_refuses_uncommitted_tracker_file(self):
        path = os.path.join(self.repo, "openspec", "github-tracker.yaml")
        write(path, read(path).replace("approvers: [alice, bob]", "approvers: [alice, bob, mallory]"))
        code, _, err = self.sync("pull", "--apply")
        self.assertEqual(code, 1)
        self.assertIn("github-tracker.yaml has uncommitted changes", err)

    def test_pull_refuses_uncommitted_profile(self):
        with open(self.profile, "a", encoding="utf-8") as fh:
            fh.write("# edited\n")
        code, _, err = self.sync("pull", "--apply")
        self.assertEqual(code, 1)
        self.assertIn("handoff-profile.yaml has uncommitted changes", err)


# ===================================================================== bootstrap and vendoring

class TestBootstrap(SyncCase):
    sim = fake_gh.default_sim(with_fields=False, status_options=("Todo", "In Progress", "Done"))

    def test_dry_run_plans_fields_and_labels(self):
        code, out, err = self.sync("bootstrap")
        self.assertEqual(code, 0, err)
        self.assertEqual(out.count("PLAN gh project field-create 7 --owner acme"), 4)
        self.assertEqual(out.count("PLAN gh label create"), len(model.LABELS))
        self.assertIn("has no option 'Blocked'", err)
        self.assertEqual(self.fake.mutations(), [])

    def test_install_workflows_conflict_writes_nothing(self):
        dest = os.path.join(self.repo, ".github", "workflows")
        os.makedirs(dest, exist_ok=True)
        with open(os.path.join(dest, "openspec-gate.yml"), "w", encoding="utf-8") as fh:
            fh.write("name: local edit\n")
        code, out, err = self.sync("bootstrap", "--apply", "--vendor", "--install-workflows")
        self.assertNotEqual(code, 0)
        self.assertIn("nothing written", err)
        self.assertEqual(sorted(os.listdir(dest)), ["openspec-gate.yml"])

    def test_apply_vendor_and_install_workflows(self):
        code, out, err = self.sync("bootstrap", "--apply", "--vendor", "--install-workflows")
        self.assertEqual(code, 0, err)
        names = [f["name"] for f in self.fake.sim()["project"]["fields"]]
        for n in ("Stage", "Kind", "Change", "Gate"):
            self.assertIn(n, names)
        state = self.state()
        self.assertIn("Stage", state["fields"])
        target = os.path.join(self.repo, ".github", "openspec-github")
        self.assertEqual(_vendor.verify(target), [])
        self.assertEqual(state["vendor"]["version"], _vendor.VERSION)
        self.assertEqual(len(state["vendor"]["sha256"]), 64)
        for name in os.listdir(WORKFLOWS):
            self.assertTrue(os.path.isfile(os.path.join(self.repo, ".github", "workflows", name)))
        self.fake.reset_log()
        code, out, err = self.sync("bootstrap", "--apply", "--vendor", "--install-workflows")
        self.assertEqual(code, 0, err)
        self.assertEqual([c for c in self.fake.mutations()], [])
        with open(os.path.join(target, "_gh.py"), "a", encoding="utf-8") as fh:
            fh.write("# tampered\n")
        self.assertIn("modified _gh.py (sha256 differs from the manifest)", _vendor.verify(target))

    def test_existing_different_workflow_is_not_overwritten(self):
        dest = os.path.join(self.repo, ".github", "workflows")
        os.makedirs(dest)
        write(os.path.join(dest, "openspec-gate.yml"), "name: mine\n")
        code, _, err = self.sync("bootstrap", "--apply", "--install-workflows")
        self.assertEqual(code, 1)
        self.assertIn("openspec-gate.yml", err)
        self.assertEqual(read(os.path.join(dest, "openspec-gate.yml")), "name: mine\n")

    def test_vendored_copy_runs_standalone(self):
        self.assertEqual(self.sync("bootstrap", "--apply", "--vendor")[0], 0)
        target = os.path.join(self.repo, ".github", "openspec-github")
        import subprocess
        env = dict(os.environ)
        env.pop("OPENSPEC_GITHUB_HANDOFF_SCRIPTS", None)
        proc = subprocess.run([sys.executable, os.path.join(target, "gh_projects_sync.py"), "--help"],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, encoding="utf-8")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("ORCHESTRATOR ONLY", proc.stdout)


# ===================================================================== _gh wrapper

class TestGhWrapper(SyncCase):
    def test_rate_limit_retries_are_bounded(self):
        self.fake.set_overrides([{"match": ["api"], "code": 1, "stderr": "API rate limit exceeded"}])
        with self.assertRaises(gh.GhError):
            gh.run(["api", "-X", "GET", "rate_limit"])
        self.assertEqual(len(self.fake.calls()), gh.MAX_RETRIES + 1)

    def test_errors_redact_the_token(self):
        self.fake.set_overrides([{"match": ["api"], "code": 1, "stderr": "bad fake-token-value-123456"}])
        with self.assertRaises(gh.GhError) as cm:
            gh.run(["api", "user"])
        self.assertNotIn("fake-token-value-123456", str(cm.exception))
        self.assertIn("***", str(cm.exception))

    def test_stub_on_path_is_found_like_a_real_executable(self):
        bin_dir = fake_gh.write_wrappers(os.path.join(self.tmp, "bin"))
        saved = os.environ.pop("OPENSPEC_GITHUB_GH")
        old_path = os.environ["PATH"]
        os.environ["PATH"] = bin_dir + os.pathsep + old_path
        try:
            version, warning = gh.check_version()
        finally:
            os.environ["PATH"] = old_path
            os.environ["OPENSPEC_GITHUB_GH"] = saved
        self.assertEqual(version, (2, 103, 3))
        self.assertIsNone(warning)

    def test_never_shell_true_nor_show_token(self):
        import ast
        for name in ("_gh.py", "gh_projects_sync.py", "gate_command.py", "_vendor.py", "_model.py"):
            tree = ast.parse(read(os.path.join(fake_gh.SCRIPTS, name)))
            for node in ast.walk(tree):
                if isinstance(node, ast.keyword) and node.arg == "shell":
                    self.fail("%s passes shell= to a call" % name)
                if isinstance(node, ast.Constant) and node.value == "--show-token":
                    self.fail("%s uses --show-token as an argument" % name)


# ===================================================================== workflow templates

def run_blocks(text):
    """Yield the text of every run: step (inline or block scalar)."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"^(\s*)(?:- )?run:\s*(.*)$", line)
        if not m:
            continue
        if m.group(2) not in ("|", ">", "|-", ">-"):
            yield m.group(2)
            continue
        indent = len(m.group(1))
        block = []
        for nxt in lines[i + 1:]:
            if nxt.strip() and len(nxt) - len(nxt.lstrip()) <= indent:
                break
            block.append(nxt)
        yield "\n".join(block)


def jobs_of(text):
    """[(job name, job text)] from the jobs: block (2-space job keys)."""
    body = text.split("\njobs:\n", 1)[1]
    parts = re.split(r"(?m)^  ([a-z][a-z0-9-]*):\n", body)
    return list(zip(parts[1::2], parts[2::2]))


def steps_of(job):
    return re.split(r"(?m)^      - ", job)[1:]


class TestWorkflowTemplates(unittest.TestCase):
    def files(self):
        names = sorted(n for n in os.listdir(WORKFLOWS) if n.endswith(".yml"))
        self.assertEqual(names, ["openspec-archive.yml", "openspec-board-sync.yml", "openspec-ci.yml",
                                 "openspec-gate.yml"])
        return [(n, read(os.path.join(WORKFLOWS, n))) for n in names]

    def test_actionlint_if_installed(self):
        exe = shutil.which("actionlint")
        if not exe:
            self.skipTest("actionlint not installed (structural checks below still run)")
        import subprocess
        proc = subprocess.run([exe] + [os.path.join(WORKFLOWS, n) for n, _ in self.files()],
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8")
        self.assertEqual(proc.returncode, 0, proc.stdout)

    def test_structure(self):
        for name, text in self.files():
            self.assertNotIn("\t", text, name)
            self.assertIn("# Trust boundary:", text, name)
            self.assertRegex(text, r"(?m)^name: openspec-", name)
            self.assertRegex(text, r"(?m)^on:\n", name)
            self.assertRegex(text, r"(?m)^permissions:\n  contents: read$", name)
            self.assertRegex(text, r"(?m)^concurrency:\n  group: openspec-", name)
            self.assertRegex(text, r"(?m)^jobs:\n", name)
            jobs = re.findall(r"(?m)^  ([a-z-]+):\n", text.split("\njobs:\n", 1)[1])
            self.assertTrue(jobs, name)
            self.assertEqual(text.count("    timeout-minutes:"), len(jobs), name)
            self.assertEqual(len(re.findall(r"(?m)^    permissions:$", text)), len(jobs), name)
            code = "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("#"))
            self.assertNotIn("pull_request_target", code, name)
            self.assertNotIn("app-id:", text, name)
            self.assertNotIn("secrets.GITHUB_TOKEN", text, name)
            self.assertNotRegex(text, r"(?m)^\s+contents: write", name)   # GITHUB_TOKEN stays read-only

    def test_actions_are_sha_pinned(self):
        for name, text in self.files():
            uses = re.findall(r"uses: ([^@\s]+)@(\S+)(.*)", text)
            self.assertTrue(uses, name)
            for action, ref, comment in uses:
                self.assertIn(action, PINS, name)
                sha, tag = PINS[action]
                self.assertEqual(ref, sha, "%s: %s" % (name, action))
                self.assertEqual(comment.strip(), "# %s" % tag, "%s: %s" % (name, action))

    def test_event_text_never_inside_run(self):
        for name, text in self.files():
            for block in run_blocks(text):
                self.assertNotIn("${{", block, "%s: expression inside run:\n%s" % (name, block))

    def test_no_token_while_third_party_code_runs(self):
        """Family rule 15: no step running npm / openspec carries a token, nor any later step of its job."""
        token_marks = ("GH_TOKEN", "secrets.", "steps.app-token", "steps.read-token")
        for name, text in self.files():
            for job_name, job in jobs_of(text):
                tainted = False
                for step in steps_of(job):
                    third_party = re.search(r"(?m)^\s*(npm|openspec)\s", step)   # a command line, not prose
                    has_token = any(m in step for m in token_marks)
                    if third_party:
                        tainted = True
                        self.assertNotIn("--global @", step, "%s/%s: npm without --ignore-scripts" % (name, job_name))
                    if tainted:
                        self.assertFalse(has_token, "%s/%s: token in or after a third-party step:\n%s"
                                         % (name, job_name, step))
        archive = dict(self.files())["openspec-archive.yml"]
        publish = dict(jobs_of(archive))["publish"]
        self.assertIn("needs: prepare", publish)
        self.assertNotIn("npm", publish)
        self.assertIn("grep -v '^openspec/'", publish)
        jobs = dict(jobs_of(archive))
        self.assertEqual(list(jobs), ["authorize", "prepare", "publish"])
        authorize, prepare = jobs["authorize"], jobs["prepare"]
        self.assertIn("gate_command.py recheck . --profile \"$PROFILE\" --gate E9", authorize)
        self.assertNotIn("npm", authorize)
        self.assertNotIn("permission-contents: write", authorize)
        self.assertIn("needs: authorize", prepare)
        for mark in ("GH_TOKEN", "secrets.", "create-github-app-token"):
            self.assertNotIn(mark, prepare)                 # prepare holds no token at all (N7)
        self.assertLess(publish.index("gate_command.py check-patch"), publish.index("git apply"))
        self.assertIn("--no-renames", publish)

    def test_credential_paths(self):
        for name, text in self.files():
            if name == "openspec-ci.yml":
                self.assertNotIn("secrets.", text)
                continue
            self.assertIn("vars.OPENSPEC_OWNER_TYPE == 'organization'", text, name)
            self.assertIn("client-id: ${{ vars.OPENSPEC_APP_CLIENT_ID }}", text, name)
            self.assertIn("private-key: ${{ secrets.OPENSPEC_APP_PRIVATE_KEY }}", text, name)
            self.assertIn("secrets.OPENSPEC_PROJECT_PAT", text, name)
            self.assertIn("permission-", text, name)

    def test_specific_triggers(self):
        files = dict(self.files())
        gate = files["openspec-gate.yml"]
        self.assertIn("issue_comment:\n    types: [created]", gate)
        self.assertIn("!github.event.issue.pull_request && contains(join(github.event.issue.labels.*.name, ','), "
                      "'openspec') && startsWith(github.event.comment.body, '/')", gate)
        for key in ("COMMENT_BODY", "COMMENT_AUTHOR", "COMMENT_URL", "COMMENT_ID", "ISSUE_NUMBER", "CREATED_AT"):
            self.assertRegex(gate, r"%s: \$\{\{ github\.event\." % key)
        self.assertIn("openspec-gate-${{ github.event.issue.number }}", gate)
        self.assertIn("cancel-in-progress: false", gate)
        self.assertIn("permission-organization-projects: write", gate)
        ci = files["openspec-ci.yml"]
        self.assertIn("pull_request:", ci)
        self.assertIn("@fission-ai/openspec@1.15.0", ci)
        self.assertIn("--type change --strict --json --no-interactive", ci)
        archive = files["openspec-archive.yml"]
        self.assertIn("github.event.label.name == 'gate:E9:approved'", archive)
        self.assertIn("github.event.sender.login == vars.OPENSPEC_BOT_LOGIN", archive)
        self.assertIn('git push origin "HEAD:refs/heads/$branch"', archive)
        self.assertIn("openspec archive \"$CHANGE_ID\" --yes", archive)
        self.assertEqual(len(re.findall(r"git push", archive)), 1)
        self.assertIn("refusing to push the default branch", archive)
        sync_wf = files["openspec-board-sync.yml"]
        self.assertIn("gh_projects_sync.py push . --change \"$id\" --profile \"$PROFILE\" --apply", sync_wf)
        self.assertIn("format('refs/heads/{0}', github.event.repository.default_branch)", sync_wf)


if __name__ == "__main__":
    unittest.main()
