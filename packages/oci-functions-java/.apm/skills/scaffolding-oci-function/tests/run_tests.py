#!/usr/bin/env python3
"""Tests for assets/build-push.py. Offline: the template is copied into a temporary
services/<func>/ tree and tests/fakes/fake_cli.py plays docker (DOCKER_CMD) — nothing
reaches a real registry. Run: python3 tests/run_tests.py
"""
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.normpath(os.path.join(HERE, "..", "assets", "build-push.py"))
FAKE_CLI = os.path.join(HERE, "fakes", "fake_cli.py")
PASSWORD = "ocir-AuthT0ken-NEVER-PRINT"

ENV_FILE = """# OCIR settings
export OCIR_REGION=gru
OCIR_NAMESPACE="tenancyns"   # namespace
OCIR_REPO='serverless-app'
OCIR_USERNAME="${OCIR_NAMESPACE}/user@example.com"
OCIR_PASSWORD=%s
""" % PASSWORD


class BuildPushTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.func_dir = os.path.join(self.root, "services", "func-orders")
        os.makedirs(self.func_dir)
        shutil.copy(TEMPLATE, os.path.join(self.func_dir, "build-push.py"))
        self.write("func.yaml", "schema_version: 20180708\nname: func-orders\nversion: 0.0.7\n")
        self.write(os.path.join("..", ".env"), ENV_FILE)
        self.log = os.path.join(self.root, "docker.jsonl")
        self.rules = os.path.join(self.root, "rules.json")
        self.set_rules([])

    def write(self, rel, text):
        with open(os.path.join(self.func_dir, rel), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)

    def set_rules(self, rules):
        with open(self.rules, "w", encoding="utf-8") as fh:
            json.dump(rules, fh)

    def run_build(self, *args, env_extra=None):
        env = {k: v for k, v in os.environ.items() if not k.startswith("OCIR_") and k != "PLATFORM"}
        env.update({"DOCKER_CMD": '"%s" "%s"' % (sys.executable, FAKE_CLI), "FAKE_LOG": self.log,
                    "FAKE_RULES": self.rules, "HTTP_PROXY": "http://proxy.invalid:3128"})
        env.update(env_extra or {})
        proc = subprocess.run([sys.executable, os.path.join(self.func_dir, "build-push.py")] + list(args),
                              env=env, stdin=subprocess.DEVNULL, capture_output=True, timeout=60)
        return proc.returncode, proc.stdout.decode("utf-8"), proc.stderr.decode("utf-8")

    def calls(self):
        if not os.path.exists(self.log):
            return []
        with open(self.log, encoding="utf-8") as fh:
            return [json.loads(line) for line in fh]

    def env_path(self):
        return os.path.join(self.func_dir, "..", ".env")

    # ---- validation -----------------------------------------------------------
    def test_missing_env_file_exits_1(self):
        os.remove(self.env_path())
        rc, out, _err = self.run_build()
        self.assertEqual(rc, 1)
        self.assertEqual(out, "ERROR: %s not found.\n       Copy services/.env.example to services/.env "
                              "and fill in values.\n" % self.env_path())
        self.assertEqual(self.calls(), [])

    def test_missing_required_variable_exits_1(self):
        self.write(os.path.join("..", ".env"), ENV_FILE.replace("OCIR_PASSWORD=%s" % PASSWORD, "OCIR_PASSWORD="))
        rc, out, _err = self.run_build()
        self.assertEqual(rc, 1)
        self.assertEqual(out, "ERROR: OCIR_PASSWORD is not set in %s\n" % self.env_path())
        self.assertEqual(self.calls(), [])

    def test_required_variable_may_come_from_environment(self):
        self.write(os.path.join("..", ".env"), ENV_FILE.replace("export OCIR_REGION=gru\n", ""))
        rc, out, _err = self.run_build(env_extra={"OCIR_REGION": "fra"})
        self.assertEqual(rc, 0)
        self.assertIn("==> Logging in to fra.ocir.io", out)

    # ---- happy path -----------------------------------------------------------
    def test_login_build_push_happy_path(self):
        rc, out, err = self.run_build()
        self.assertEqual(rc, 0, err)
        image = "gru.ocir.io/tenancyns/serverless-app/func-orders:0.0.7"
        self.assertEqual(out, "==> Logging in to gru.ocir.io\n==> Building %s (platform: linux/amd64)\n"
                              "==> Pushing %s\n\nDone! Image URI:\n  %s\n" % (image, image, image))
        login, build, push = self.calls()
        self.assertEqual(login["argv"], ["login", "gru.ocir.io", "-u", "tenancyns/user@example.com", "--password-stdin"])
        self.assertEqual(login["stdin"], PASSWORD + "\n")
        self.assertEqual(build["argv"], ["build", "--platform", "linux/amd64", "-t", image, self.func_dir])
        self.assertEqual(build["proxy_env"], [])
        self.assertTrue(login["proxy_env"])  # only the build step drops the proxy variables
        self.assertEqual(push["argv"], ["push", image])
        for call in (login, build, push):
            self.assertNotIn(PASSWORD, " ".join(call["argv"]))
        self.assertNotIn(PASSWORD, out + err)

    def test_tag_argument_and_platform_override(self):
        rc, out, _err = self.run_build("1.2.3", env_extra={"PLATFORM": "linux/arm64"})
        self.assertEqual(rc, 0)
        self.assertIn("func-orders:1.2.3 (platform: linux/arm64)", out)
        self.assertEqual(self.calls()[1]["argv"][2], "linux/arm64")

    # ---- failures ---------------------------------------------------------------
    def test_login_failure_stops_with_docker_exit_code(self):
        self.set_rules([{"match": ["login"], "rc": 3}])
        rc, out, _err = self.run_build()
        self.assertEqual(rc, 3)
        self.assertNotIn("==> Building", out)
        self.assertEqual(len(self.calls()), 1)

    def test_build_failure_skips_push(self):
        self.set_rules([{"match": ["build"], "rc": 5}])
        rc, out, _err = self.run_build()
        self.assertEqual(rc, 5)
        self.assertNotIn("==> Pushing", out)

    def test_func_yaml_problems(self):
        self.write("func.yaml", "version: 0.0.1\n")
        self.assertEqual(self.run_build()[0], 1)  # grep found no `name:` line
        os.remove(os.path.join(self.func_dir, "func.yaml"))
        rc, _out, err = self.run_build()
        self.assertEqual(rc, 2)
        self.assertIn("No such file or directory", err)
        self.assertFalse([c for c in self.calls() if c["argv"][0] == "build"])

    @unittest.skipUnless(os.name != "nt" or shutil.which("bash"), "needs bash to run preflight.sh")
    def test_failing_preflight_aborts_before_docker(self):
        scripts = os.path.join(self.root, "scripts")
        os.makedirs(scripts)
        preflight = os.path.join(scripts, "preflight.sh")
        with open(preflight, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("#!/usr/bin/env bash\necho \"preflight for $1\"\nexit 4\n")
        os.chmod(preflight, os.stat(preflight).st_mode | stat.S_IEXEC)
        rc, out, _err = self.run_build()
        self.assertEqual(rc, 4)
        self.assertIn("==> Running pre-flight checks...\npreflight for ", out)
        self.assertEqual(self.calls(), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
