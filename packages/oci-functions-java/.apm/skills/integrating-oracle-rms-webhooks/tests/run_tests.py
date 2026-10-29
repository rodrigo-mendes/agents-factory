#!/usr/bin/env python3
"""Tests for the RMS/MFCS scripts. Offline: a local http.server fake plays IDCS + RMS + the listener,
and tests/fakes/fake_cli.py plays `oci` / `terraform`. Run: python3 tests/run_tests.py
"""
import base64
import http.server
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
FAKE_CLI = os.path.join(HERE, "fakes", "fake_cli.py")

CLIENT_ID = "fake-client-id"
CLIENT_SECRET = "S3cr3t-NEVER-PRINT"
TOKEN = "tok-FAKE-123"
BASIC = "Basic " + base64.b64encode(("%s:%s" % (CLIENT_ID, CLIENT_SECRET)).encode()).decode()


class FakeHandler(http.server.BaseHTTPRequestHandler):
    requests = []

    def log_message(self, *_args):
        pass

    def _reply(self, code, body, headers=None):
        data = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _handle(self):
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length).decode() if length else ""
        FakeHandler.requests.append({"method": self.command, "path": self.path,
                                     "headers": dict(self.headers), "body": body})
        path = urllib.parse.urlsplit(self.path).path
        auth = self.headers.get("Authorization", "")
        if path == "/token":
            if auth == BASIC and body == "grant_type=client_credentials&scope=rgbu:merch:MFCS-PAR1":
                return self._reply(200, json.dumps({"access_token": TOKEN, "expires_in": 3600}))
            return self._reply(401, json.dumps({"error": "invalid_client"}))
        if path.startswith("/mi/") and auth != "Bearer " + TOKEN:
            return self._reply(401, "{}")
        if path == "/mi/services/foundation/item/100010000":
            return self._reply(200, json.dumps({"items": [{"item": "100010000", "status": "A"}]}))
        if path == "/mi/services/foundation/item/302":
            return self._reply(302, "<html>redirect</html>", {"Location": "/should-not-follow"})
        if path == "/mi/services/foundation/item":
            return self._reply(200, json.dumps({"items": [], "hasMore": False}))
        if path == "/mi/services/administration/operations/webhooks/manage":
            return self._reply(200, json.dumps({"ok": True}))
        if path == "/listener":
            return self._reply(200, "accepted")
        if path == "/listener-500":
            return self._reply(500, "boom")
        return self._reply(404, json.dumps({"error": "not found"}))

    do_GET = do_POST = _handle


class RmsScriptsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), FakeHandler)
        cls.base = "http://127.0.0.1:%d" % cls.server.server_address[1]
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.tmp = tempfile.mkdtemp()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def setUp(self):
        FakeHandler.requests = []
        self.log = os.path.join(self.tmp, "calls-%s.jsonl" % self.id().rsplit(".", 1)[-1])

    def run_script(self, name, *args, env_extra=None, creds=True):
        env = {k: v for k, v in os.environ.items()
               if k.lower() not in ("http_proxy", "https_proxy", "all_proxy", "no_proxy")
               and k not in ("CLIENT_ID", "CLIENT_SECRET", "LISTENER", "SERVICE", "ITEMS", "UUID")}
        env.update({"RMS_TOKEN_URL": self.base + "/token", "RMS_MERCH_BASE": self.base + "/mi",
                    "TF_DIR": self.tmp, "FAKE_LOG": self.log, "PYTHONIOENCODING": "utf-8",
                    "OCI_CMD": '"%s" "%s"' % (sys.executable, FAKE_CLI),
                    "TERRAFORM_CMD": '"%s" "%s"' % (sys.executable, FAKE_CLI)})
        if creds:
            env.update({"CLIENT_ID": CLIENT_ID, "CLIENT_SECRET": CLIENT_SECRET})
        env.update(env_extra or {})
        proc = subprocess.run([sys.executable, os.path.join(SCRIPTS, name)] + list(args), env=env,
                              stdin=subprocess.DEVNULL, capture_output=True, timeout=60)
        return proc.returncode, proc.stdout.decode("utf-8"), proc.stderr.decode("utf-8")

    def assert_no_secret(self, *texts):
        for text in texts:
            self.assertNotIn(CLIENT_SECRET, text)
            self.assertNotIn(base64.b64encode(CLIENT_SECRET.encode()).decode(), text)

    # ---- argument validation -------------------------------------------------
    def test_unknown_arg_exits_2(self):
        for name in ("rms-get.py", "register-webhook.py", "simulate-webhook.py"):
            rc, _out, err = self.run_script(name, "--bogus")
            self.assertEqual(rc, 2, name)
            self.assertIn("arg desconhecido: --bogus", err)

    def test_option_without_value_exits_1(self):
        rc, _out, err = self.run_script("rms-get.py", "--id")
        self.assertEqual(rc, 1)
        self.assertIn("unbound variable", err)

    def test_help_exits_0(self):
        rc, out, _err = self.run_script("rms-get.py", "--help")
        self.assertEqual(rc, 0)
        self.assertIn("Uso:", out)
        self.assertNotIn("!/usr/bin/env", out)
        self.assertEqual(FakeHandler.requests, [])

    def test_simulate_requires_listener_and_valid_mode(self):
        self.assertEqual(self.run_script("simulate-webhook.py")[0], 2)
        rc, _out, err = self.run_script("simulate-webhook.py", "--listener", self.base + "/listener", "--mode", "x")
        self.assertEqual(rc, 2)
        self.assertIn("MODE inválido: X", err)
        self.assertEqual(FakeHandler.requests, [])

    def test_register_requires_listener_and_valid_action(self):
        rc, _out, err = self.run_script("register-webhook.py")
        self.assertEqual(rc, 2)
        self.assertIn("--listener é obrigatório p/ register", err)
        rc, _out, err = self.run_script("register-webhook.py", "--action", "nuke")
        self.assertEqual(rc, 2)
        self.assertIn("ação inválida: nuke", err)
        self.assertFalse([r for r in FakeHandler.requests if "webhooks/manage" in r["path"]])

    # ---- token / secret handling ---------------------------------------------
    def test_rms_token_prints_token_never_secret(self):
        rc, out, err = self.run_script("rms-token.py")
        self.assertEqual(rc, 0)
        self.assertTrue(out.endswith(TOKEN + "\n"))
        self.assertIn("[i] Credenciais OAuth via env.", out)
        self.assert_no_secret(out, err)

    def test_rms_token_bad_credentials_exit_1(self):
        rc, out, err = self.run_script("rms-token.py", env_extra={"CLIENT_SECRET": "wrong"})
        self.assertEqual(rc, 1)
        self.assertEqual(out, "")
        self.assertIn("Falha ao obter token", err)

    def test_vault_path_reads_state_and_secret_bundle(self):
        rules = os.path.join(self.tmp, "rules-vault.json")
        with open(rules, "w", encoding="utf-8") as fh:
            json.dump([
                {"match": ["state", "show", "oci_vault_secret.rest_proxy_oauth_client_id[0]"],
                 "stdout": '# oci_vault_secret.x:\nresource "oci_vault_secret" "x" {\n    id = "ocid1.vaultsecret.id"\n}\n'},
                {"match": ["state", "show", "oci_vault_secret.rest_proxy_oauth_client_secret[0]"],
                 "stdout": '    id             = "ocid1.vaultsecret.secret"\n'},
                {"match": ["--secret-id", "ocid1.vaultsecret.id"], "stdout": base64.b64encode(CLIENT_ID.encode()).decode() + "\n"},
                {"match": ["--secret-id", "ocid1.vaultsecret.secret"], "stdout": base64.b64encode(CLIENT_SECRET.encode()).decode() + "\n"},
            ], fh)
        rc, out, err = self.run_script("rms-token.py", creds=False, env_extra={"FAKE_RULES": rules})
        self.assertEqual(rc, 0, err)
        self.assertTrue(out.endswith(TOKEN + "\n"))
        self.assertIn("Credenciais carregadas do Vault.", out)
        self.assert_no_secret(out, err)
        with open(self.log, encoding="utf-8") as fh:
            calls = [json.loads(line)["argv"] for line in fh]
        oci_calls = [c for c in calls if "secret-bundle" in c]
        self.assertEqual(len(oci_calls), 2)
        self.assertEqual(oci_calls[0][:6], ["--profile", "poc", "--auth", "security_token", "--region", "sa-saopaulo-1"])
        self.assertIn("-chdir=%s" % self.tmp, calls[0])

    def test_vault_path_missing_state_exits_1(self):
        rc, out, err = self.run_script("rms-get.py", "--id", "1", creds=False)
        self.assertEqual(rc, 1)
        self.assertIn("OCIDs dos secrets não achados no state", err)
        self.assertEqual(FakeHandler.requests, [])

    # ---- rms-get -------------------------------------------------------------
    def test_rms_get_by_id_happy_path(self):
        rc, out, err = self.run_script("rms-get.py", "--entity", "foundation/item", "--id", "100010000")
        self.assertEqual(rc, 0, err)
        self.assertIn("-- HTTP 200 --", out)
        self.assertIn('"item": "100010000"', out)
        get = [r for r in FakeHandler.requests if r["method"] == "GET"][0]
        self.assertEqual(get["path"], "/mi/services/foundation/item/100010000")
        self.assertEqual(get["headers"]["Authorization"], "Bearer " + TOKEN)
        self.assertNotIn(TOKEN, out + err)
        self.assert_no_secret(out, err)

    def test_rms_get_delta_query_encoding(self):
        rc, out, _err = self.run_script("rms-get.py", "--since", "2026-05-29T02:01:56Z",
                                        "--include", "items.item,items.itemDescription", "--raw")
        self.assertEqual(rc, 0)
        self.assertEqual(out, '{"items": [], "hasMore": false}\n')
        get = [r for r in FakeHandler.requests if r["method"] == "GET"][0]
        self.assertEqual(get["path"], "/mi/services/foundation/item?limit=1000&since=2026-05-29T02%3A01%3A56Z"
                                      "&include=items.item%2Citems.itemDescription")

    def test_rms_get_redirect_not_followed_exit_1(self):
        rc, out, err = self.run_script("rms-get.py", "--id", "302")
        self.assertEqual(rc, 1)
        self.assertIn("-- HTTP 302 --", out)
        self.assertIn("redirect IDCS Cloud Gate", err)
        self.assertFalse([r for r in FakeHandler.requests if r["path"] == "/should-not-follow"])

    def test_rms_get_404_exit_1(self):
        rc, _out, err = self.run_script("rms-get.py", "--id", "nope")
        self.assertEqual(rc, 1)
        self.assertIn("HTTP 404", err)

    # ---- register-webhook ----------------------------------------------------
    def test_register_and_disable_happy_path(self):
        for action, enabled in (("register", "Y"), ("disable", "N")):
            FakeHandler.requests = []
            rc, out, err = self.run_script("register-webhook.py", "--action", action,
                                           "--listener", "https://gw/hook")
            self.assertEqual(rc, 0, err)
            self.assertIn("PASS=1", out)
            post = [r for r in FakeHandler.requests if "webhooks/manage" in r["path"]][0]
            self.assertEqual(post["method"], "POST")
            self.assertEqual(post["headers"]["Content-Type"], "application/json")
            item = json.loads(post["body"])["items"][0]
            self.assertEqual(item, {"service": "foundation/item", "credentialName": "APP_TESTE_BLUM",
                                    "listenerUrl": "https://gw/hook", "includePayload": "Y", "enabled": enabled,
                                    "intervalSeconds": 10, "pageLimit": 1000,
                                    "queryParameter": "include=items.action,items.item,items.status,items.itemDescription",
                                    "heartbeatIntervalHours": 1})
            self.assert_no_secret(out, err)
            self.assertNotIn(TOKEN, out + err)

    def test_register_list_uses_get_without_body(self):
        rc, out, _err = self.run_script("register-webhook.py", "--action", "list")
        self.assertEqual(rc, 0)
        req = [r for r in FakeHandler.requests if "webhooks/manage" in r["path"]][0]
        self.assertEqual((req["method"], req["body"]), ("GET", ""))
        self.assertIn('"ok": true', out)

    def test_register_http_error_exit_1(self):
        rc, out, _err = self.run_script("register-webhook.py", "--action", "list",
                                        env_extra={"MANAGE_URL": self.base + "/mi/missing"})
        self.assertEqual(rc, 1)
        self.assertIn("FAIL=1", out)

    # ---- simulate-webhook ----------------------------------------------------
    def test_simulate_payload_happy_path(self):
        rc, out, err = self.run_script("simulate-webhook.py", "--listener", self.base + "/listener",
                                       "--items", "1, 2,,3", "--uuid", "u-1")
        self.assertEqual(rc, 0, err)
        self.assertIn("-- resposta (HTTP 200) --\naccepted\n", out)
        body = FakeHandler.requests[0]["body"]
        self.assertEqual(body, '{"type":"PAYLOAD","timestamp":"2026-05-29T13:35:59.223Z","service":"foundation/item",'
                               '"uuid":"u-1","environment":"rgbu-rex-brxs-par1-mfcs","since":"2026-05-29T02:27:59.838Z",'
                               '"payload":{"items":[{"action":"UPDATE","item":"1","status":"A","itemDescription":"sim 1"},'
                               '{"action":"UPDATE","item":"2","status":"A","itemDescription":"sim 2"},'
                               '{"action":"UPDATE","item":"3","status":"A","itemDescription":"sim 3"}],'
                               '"hasMore":false,"limit":1000,"count":4}}')

    def test_simulate_event_unexpected_status_exit_1(self):
        rc, out, _err = self.run_script("simulate-webhook.py", "--listener", self.base + "/listener-500",
                                        "--mode", "event")
        self.assertEqual(rc, 1)
        self.assertIn("esperado ^(200|207)$", out)
        self.assertNotIn("payload", FakeHandler.requests[0]["body"])

    def test_simulate_connection_refused_is_warn_exit_0(self):
        rc, out, _err = self.run_script("simulate-webhook.py", "--listener", "http://127.0.0.1:9/x")
        self.assertEqual(rc, 0)
        self.assertIn("HTTP 000 (cold start)", out)
        self.assertIn("WARN=1", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
