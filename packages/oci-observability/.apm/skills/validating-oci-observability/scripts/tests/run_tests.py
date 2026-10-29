#!/usr/bin/env python3
"""Minimal test runner for the validating-oci-observability Python scripts.

Run:  python scripts/tests/run_tests.py      (exit 0 = all tests passed)

Every external command is faked: `oci` -> fakes/fake_oci.py (fixtures/green|fail),
git/terraform/bash -> fakes/fake_tool.py. HTTP calls go to an in-process server
bound to 127.0.0.1 (loopback only). Nothing reaches OCI or the network.
Standard library only.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
FAKES = os.path.join(HERE, "fakes")
FIXTURES = os.path.join(HERE, "fixtures")
PY = sys.executable

sys.path.insert(0, FAKES)
sys.dont_write_bytecode = True
from fake_oci import READ_ONLY  # noqa: E402

COMPARTMENT = "ocid1.compartment.oc1..testcompartment"
TOPIC = "ocid1.onstopic.oc1..testtopic"


# ------------------------------------------------------------------------------
# Loopback HTTP server (stands in for the API Gateway)
# ------------------------------------------------------------------------------
class Api:
    mode = "ok"
    requests = []


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _reply(self):
        n = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(n).decode("utf-8") if n else ""
        Api.requests.append((self.command, self.path, body, self.headers.get("Content-Type")))
        path = self.path[len("/v1"):] if self.path.startswith("/v1") else self.path
        code = 200
        if path == "/proxy/item/webhook":
            code = 500
        if Api.mode == "fail" and path == "/facade/hello":
            code = 404
        self.send_response(code)
        self.send_header("Content-Length", "2")
        self.end_headers()
        self.wfile.write(b"{}")

    do_GET = do_POST = _reply


# ------------------------------------------------------------------------------
# Harness
# ------------------------------------------------------------------------------
class Ctx:
    def __init__(self, base_url):
        self.tmp = tempfile.mkdtemp(prefix="voo-tests-")
        self.base_url = base_url
        self.repo = os.path.join(self.tmp, "repo")
        self.tf_dir = os.path.join(self.repo, "infra", "environments", "dev")
        os.makedirs(self.tf_dir)
        for d in ("api-handler", "func-api-facade", "func-rr-rest-proxy"):
            os.makedirs(os.path.join(self.repo, "services", d))
            with open(os.path.join(self.repo, "services", d, "func.yaml"), "w", encoding="utf-8") as fh:
                fh.write(f"schema_version: 20180708\nname: {d}\nversion: 1.2.3\n")
        self.tf_outputs = os.path.join(self.tmp, "tf_outputs.json")
        with open(self.tf_outputs, "w", encoding="utf-8") as fh:
            json.dump({
                "compartment_ocid": {"value": COMPARTMENT},
                "api_base_url": {"value": base_url},
                "log_group_id": {"value": "ocid1.loggroup.oc1..testlg"},
                "apm_domain_id": {"value": "ocid1.apmdomain.oc1..testapm"},
                "notification_topic_id": {"value": TOPIC},
            }, fh)
        self.oci_log = os.path.join(self.tmp, "oci.log")
        self.tool_log = os.path.join(self.tmp, "tool.log")

    def env(self, fixtures="green", **extra):
        env = {k: v for k, v in os.environ.items()
               if not (k.startswith(("OCI_", "VOO_", "FAKE_", "ITEM_SET_"))
                       or k.lower().endswith("_proxy")
                       or k in ("TF_DIR","API_BASE_URL", "ROUNDS", "SLEEP", "SIM", "TARGET_PATH",
                                "LOOKBACK_MIN", "ALARM_EMAIL"))}
        env.update({
            "VOO_OCI_CMD": json.dumps([PY, os.path.join(FAKES, "fake_oci.py")]),
            "VOO_TERRAFORM_CMD": json.dumps([PY, os.path.join(FAKES, "fake_tool.py"), "terraform"]),
            "VOO_GIT_CMD": json.dumps([PY, os.path.join(FAKES, "fake_tool.py"), "git"]),
            "VOO_BASH_CMD": json.dumps([PY, os.path.join(FAKES, "fake_tool.py"), "bash"]),
            "VOO_SLEEP_SCALE": "0",
            "VOO_ALLOW_PIPE": "1",
            "FAKE_GIT_TOPLEVEL": self.repo,
            "FAKE_TF_OUTPUTS": self.tf_outputs,
            "FAKE_OCI_FIXTURES": os.path.join(FIXTURES, fixtures),
            "FAKE_OCI_LOG": self.oci_log,
            "FAKE_TOOL_LOG": self.tool_log,
            "PYTHONIOENCODING": "utf-8",
            "PYTHONDONTWRITEBYTECODE": "1",
            "no_proxy": "127.0.0.1,localhost",  # loopback only; never a proxy
        })
        env.update({k: str(v) for k, v in extra.items()})
        return env

    def run(self, script, *args, stdin="", **env_kw):
        for f in (self.oci_log, self.tool_log):
            if os.path.exists(f):
                os.remove(f)
        Api.requests = []
        p = subprocess.run([PY, os.path.join(SCRIPTS, script)] + list(args), input=stdin.encode(),
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=self.env(**env_kw),
                           cwd=self.tmp, timeout=120)
        return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")

    def oci_calls(self):
        if not os.path.exists(self.oci_log):
            return []
        with open(self.oci_log, encoding="utf-8") as fh:
            return [json.loads(line) for line in fh]

    def tool_calls(self, tool):
        if not os.path.exists(self.tool_log):
            return []
        with open(self.tool_log, encoding="utf-8") as fh:
            return [c for c in map(json.loads, fh) if c["tool"] == tool]


def check(cond, msg, out="", errout=""):
    if not cond:
        raise AssertionError(f"{msg}\n--- stdout ---\n{out}\n--- stderr ---\n{errout}")


def expect(ctx, script, args=(), rc=0, out_has=(), err_has=(), out_not=(), fixtures="green", stdin="", **env):
    code, out, err = ctx.run(script, *args, stdin=stdin, fixtures=fixtures, **env)
    check(code == rc, f"{script} {list(args)}: rc={code}, expected {rc}", out, err)
    for s in out_has:
        check(s in out, f"{script}: stdout missing {s!r}", out, err)
    for s in err_has:
        check(s in err, f"{script}: stderr missing {s!r}", out, err)
    for s in out_not:
        check(s not in out, f"{script}: stdout must not contain {s!r}", out, err)
    bad = [c["cmd"] for c in ctx.oci_calls() if c["cmd"] not in READ_ONLY]
    check(not bad, f"{script}: non read-only OCI commands called: {bad}", out, err)
    return out, err


# ------------------------------------------------------------------------------
# Tests
# ------------------------------------------------------------------------------
CHECKS = ("check-logs.py", "check-metrics.py", "check-traces.py", "check-alarms.py", "check-dashboards.py")


def t_logs_green(c):
    expect(c, "check-logs.py", out_has=["PASS Log group tem 2 entradas na janela.",
                                         "PASS Logs contêm campos estruturados",
                                         "PASS Logs de 'api-handler': 1 entradas.",
                                         "RESULTADO: PASS=3  FAIL=0  WARN=5"])


def t_logs_fail(c):
    expect(c, "check-logs.py", rc=1, fixtures="fail",
           out_has=["FAIL Nenhuma entrada de log na janela (invoque as functions antes: smoke-invoke.py)."])


def t_logs_cli_error(c):
    out, _ = expect(c, "check-logs.py", rc=1, fixtures="does-not-exist",
                    out_has=["FAIL logging-search não retornou dados (verifique permissões / janela)."])
    check("search \"" + COMPARTMENT + "/ocid1.loggroup.oc1..testlg\"" in
          " ".join(c.oci_calls()[-1]["argv"]), "search query built from TF outputs", out)


def t_metrics_green(c):
    expect(c, "check-metrics.py", out_has=["PASS oci_faas/FunctionInvocationCount: 1 datapoints",
                                            "applicationId=app -> 1 dp | resourceId=function -> 1 dp",
                                            "PASS rest_proxy_analytics/RestProxyInvocation: 1 datapoints.",
                                            "FAIL=0"])


def t_metrics_fail(c):
    expect(c, "check-metrics.py", rc=1, fixtures="fail",
           out_has=["FAIL oci_faas/FunctionInvocationCount sem datapoints (invoque as functions).",
                    "WARN api-handler: sem datapoints em nenhuma dimensão",
                    "FAIL api_handler_analytics/ApiHandlerInvocation sem datapoints"])


def t_traces_green(c):
    expect(c, "check-traces.py", out_has=["PASS api-handler: APM_DOMAIN_URL + APM_DATA_KEY presentes no config.",
                                           "IngestedBytes=1536 | PayloadRejections=0 (janela 15min)",
                                           "PASS APM ingerindo traces (IngestedBytes=1536).",
                                           "FAIL=0"])


def t_traces_fail(c):
    _, err = expect(c, "check-traces.py", rc=1, fixtures="fail",
                    out_has=["FAIL api-handler: config sem APM_* (keys atuais: LOG_LEVEL) -> traces NÃO fluem.",
                             "FAIL PayloadRejections=5 > 0"],
                    err_has=["[!] Traces não vão aparecer"])


def t_alarms_green(c):
    expect(c, "check-alarms.py", out_has=["PASS Alarmes no compartment: 10 (habilitados: 10).",
                                           "  - alarm-fn-errors-api-handler [CRITICAL] enabled=true",
                                           "[i] 1 alarme(s) em FIRING no momento.",
                                           "  - EMAIL ops@example.invalid: ACTIVE",
                                           "PASS 1 subscription(s), 1 ACTIVE (confirmada).", "FAIL=0"])


def t_alarms_fail(c):
    expect(c, "check-alarms.py", rc=1, fixtures="fail",
           out_has=["FAIL Nenhum alarme encontrado no compartment.",
                    "WARN Esperava >=10 alarmes; encontrei 0.",
                    "FAIL Tópico de alertas SEM subscription"])


def t_dashboards_green(c):
    expect(c, "check-dashboards.py", out_has=["PASS Dashboard ACTIVE: REST Proxy - Operations Overview",
                                               "PASS regionName param OK (metric): Invocations",
                                               "PASS dataSource 'tracesDataSource' OK: Upstream spans",
                                               "PASS ingestão oci_faas OK: api-handler", "FAIL=0"],
           out_not=["Oracle OOB dashboard"])


def t_dashboards_fail(c):
    expect(c, "check-dashboards.py", rc=1, fixtures="fail",
           out_has=["FAIL Dashboard não-ACTIVE (CREATING): REST Proxy - Operations Overview",
                    "FAIL regionName param AUSENTE (metric fica em branco — P10): Invocations",
                    # bash parity: empty widget-template collapses tab fields under IFS=$'\t' read
                    "FAIL dataSource inválido/ausente ('yes'): NoTemplate",
                    "WARN sem datapoints oci_faas p/ api-handler (gere tráfego: scripts/generate-dashboard-traffic.py)"])


def t_dashboards_name_filter(c):
    expect(c, "check-dashboards.py", args=["--name-filter", "Nope"], rc=1,
           out_has=["[i] Filtro de nome: 'Nope'", "FAIL Nenhum dashboard custom encontrado"])


def t_dashboards_usage(c):
    expect(c, "check-dashboards.py", args=["--bogus"], rc=2, err_has=["Argumento desconhecido: --bogus"])
    expect(c, "check-dashboards.py", args=["--name-filter"], rc=127, err_has=["unbound variable"])
    expect(c, "check-dashboards.py", args=["-h"], rc=0, out_has=["Uso: ./check-dashboards.py [--name-filter"])


def t_checks_session_expired(c):
    for s in CHECKS:
        expect(c, s, rc=2, err_has=["inválida/expirada", "oci session authenticate --profile poc"],
               FAKE_OCI_SESSION="expired")


def t_checks_missing_oci(c):
    for s in CHECKS + ("smoke-invoke.py",):
        expect(c, s, rc=1, err_has=["Ferramenta ausente: oci"], VOO_OCI_CMD="voo-no-such-oci-binary")


def t_validate_green_no_smoke(c):
    expect(c, "validate-observability.py", args=["--no-smoke"],
           out_has=["--no-smoke: pulando geração de tráfego.", "  smoke      N/A", "  dashboards PASS",
                    "Observabilidade VALIDADA — todos os pilares OK."])


def t_validate_green_with_smoke(c):
    out, _ = expect(c, "validate-observability.py", args=["--wait", "0"],
                    out_has=["== PILAR: smoke ==", "  smoke      PASS", "Observabilidade VALIDADA"])
    check(any(r[1] == "/v1/health" for r in Api.requests), "smoke hit /v1/health", out)


def t_validate_fail(c):
    expect(c, "validate-observability.py", args=["--no-smoke"], rc=5, fixtures="fail",
           out_has=["  logs       FAIL", "5 pilar(es) com falha — ver detalhes acima."])


def t_validate_session(c):
    expect(c, "validate-observability.py", args=["--no-smoke"], rc=2,
           err_has=["NÃO aceita pelo servidor (rc=1)"], FAKE_OCI_LIVE_RC="1")
    expect(c, "validate-observability.py", rc=2, err_has=["expirada (validação local falhou)"],
           FAKE_OCI_SESSION="expired")
    expect(c, "validate-observability.py", args=["--wait"], rc=127, err_has=["unbound variable"])


def t_smoke_green(c):
    out, _ = expect(c, "smoke-invoke.py", args=["1"],
                    out_has=["SMOKE TEST — " + c.base_url + " (x1 por rota)", "PASS GET /health -> HTTP 200",
                             "PASS POST /hello -> HTTP 200", "RESULTADO: PASS=7  FAIL=0  WARN=0"])
    posts = [r for r in Api.requests if r[0] == "POST"]
    # bash parity: "${body:-{}}" sent body + "}" ; see smoke-invoke.py
    check(posts == [("POST", "/v1/hello", '{"name":"smoke"}}', "application/json")], f"POST body {posts}", out)
    check(c.oci_calls() == [], "smoke-invoke must not call the OCI CLI", out)


def t_smoke_fail(c):
    Api.mode = "fail"
    try:
        expect(c, "smoke-invoke.py", args=["2"], rc=1,
               out_has=["FAIL GET /facade/hello -> HTTP 404 (esperado ^200$)"])
    finally:
        Api.mode = "ok"
    check(len([r for r in Api.requests if r[1] == "/v1/health"]) == 2, "N_REPEAT=2 -> 2 calls per route")


def t_trigger_green(c):
    out, err = expect(c, "trigger-alarm-test.py", args=["--i-have-user-approval", "3", "1"],
                      out_has=["   HTTP 500 x3", "PASS Gerou respostas 5xx", "PASS Alarme(s) em FIRING:",
                               "     - alarm-fn-errors-api-handler", "FAIL=0"],
                      err_has=["Isto injeta erros reais nas métricas de dev"])
    bodies = [r[2] for r in Api.requests]
    check(bodies[0] == '{"__invalid__":true,"trigger":"alarm-test","n":1}' and len(bodies) == 3, f"bodies {bodies}", out)


def t_trigger_fail(c):
    expect(c, "trigger-alarm-test.py", args=["--i-have-user-approval", "1", "0"], rc=1,
           out_has=["FAIL Nenhum alarme de erro/5xx entrou em FIRING dentro de 0min."])


def t_trigger_no_session_no_traffic(c):
    expect(c, "trigger-alarm-test.py", args=["--i-have-user-approval"], rc=2, FAKE_OCI_SESSION="expired")
    check(Api.requests == [], "trigger-alarm-test must not send traffic when the session gate fails")


def t_trigger_refuses_without_approval(c):
    _, err = expect(c, "trigger-alarm-test.py", args=["3", "1"], rc=2)
    check("--i-have-user-approval" in err, "refusal names the approval flag", "", err)
    check(Api.requests == [], "trigger-alarm-test must not send traffic without --i-have-user-approval")


def t_deploy_refuses_without_yes(c):
    for answer in ("no\n", "", "YES\n"):
        _, err = expect(c, "deploy-and-validate.py", args=["--skip-build"], stdin=answer,
                        out_has=["SKIP build de api-handler", "Aplicar? (yes/no):"],
                        err_has=["Apply cancelado pelo usuário."])
        tf = [x["argv"][0] for x in c.tool_calls("terraform") if x["argv"][0] in ("plan", "apply")]
        check(tf == ["plan"], f"answer {answer!r}: terraform calls {tf} (apply must not run)", err)
    plan = [x for x in c.tool_calls("terraform") if x["argv"][0] == "plan"][0]
    check("api_handler_image=gru.ocir.io/gr2o2hdgzoxw/serverless-app/api-handler:1.2.3" in plan["argv"]
          and "-out=tfplan" in plan["argv"], f"plan argv {plan['argv']}")


def t_deploy_piped_yes_refused_without_terminal(c):
    _, err = expect(c, "deploy-and-validate.py", args=["--skip-build"], stdin="yes" + chr(10),
                    err_has=["precisa ser digitado num terminal interativo"], VOO_ALLOW_PIPE="0")
    check([x["argv"][0] for x in c.tool_calls("terraform") if x["argv"][0] == "apply"] == [],
          "a piped yes must not apply without a terminal", err)


def t_deploy_plan_only(c):
    expect(c, "deploy-and-validate.py", args=["--skip-build", "--plan-only"], stdin="yes\n",
           out_has=["--plan-only: parando após o plan."], out_not=["Aplicar?"])
    check([x["argv"][0] for x in c.tool_calls("terraform") if x["argv"][0] in ("plan", "apply")] == ["plan"],
          "plan-only must not apply")


def t_deploy_yes_applies(c):
    expect(c, "deploy-and-validate.py", args=["--skip-build"], stdin="yes\n",
           out_has=["TERRAFORM APPLY (dev)", "PASS Infra aplicada", "Observabilidade VALIDADA"])
    tf = [x["argv"] for x in c.tool_calls("terraform") if x["argv"][0] in ("plan", "apply")]
    check(tf[1] == ["apply", "tfplan"] and len(tf) == 2, f"terraform calls {tf}")


def t_deploy_failures(c):
    expect(c, "deploy-and-validate.py", rc=1, err_has=["preflight falhou em api-handler"], FAKE_BASH_RC="1")
    check(not [x for x in c.tool_calls("terraform") if x["argv"][0] == "plan"], "no plan after preflight failure")
    expect(c, "deploy-and-validate.py", args=["--skip-build"], rc=1, err_has=["terraform plan falhou"],
           FAKE_TF_PLAN_RC="1")
    expect(c, "deploy-and-validate.py", args=["--skip-build"], rc=2, FAKE_OCI_SESSION="expired")
    check(not c.tool_calls("bash") and not [x for x in c.tool_calls("terraform") if x["argv"][0] == "plan"],
          "session gate runs before any build/plan")


def t_generate_green(c):
    out, _ = expect(c, "generate-dashboard-traffic.py", args=["--rounds", "1", "--sleep", "0", "--url", c.base_url],
                    out_has=[f"Target: {c.base_url} | rounds=1 sleep=0s | simulate-webhook: absent",
                             "=== Round 1/1 ===", "  GET  /proxy/health            -> 200",   # printf '  %-4s %-24s -> %s'
                             "  POST /proxy/item/webhook      -> 500", "=== Traffic generation complete ===",
                             "  check-dashboards.py                        # render-readiness (5th pillar)"])
    check([r[0] for r in Api.requests] == ["GET"] * 3 + ["POST"] * 4, f"requests {Api.requests}", out)
    check(Api.requests[5][2] == '{"type":"PAYLOAD","payload":{"items":[ BROKEN JSON', "malformed JSON wave", out)
    check(c.oci_calls() == [], "generate-dashboard-traffic must not call the OCI CLI", out)


def t_generate_url_from_terraform(c):
    expect(c, "generate-dashboard-traffic.py", args=["--rounds", "0"], out_has=[f"Target: {c.base_url} | rounds=0"],
           TF_DIR=c.tf_dir)


def t_generate_usage(c):
    expect(c, "generate-dashboard-traffic.py", args=["--bogus"], rc=2, err_has=["Unknown argument: --bogus"])
    expect(c, "generate-dashboard-traffic.py", args=["--rounds"], rc=127, err_has=["unbound variable"])
    expect(c, "generate-dashboard-traffic.py", rc=1, err_has=["ERROR: API_BASE_URL not resolved."],
           TF_DIR=os.path.join(c.tmp, "missing"))
    check(Api.requests == [], "no traffic without a resolved URL")
    expect(c, "generate-dashboard-traffic.py", args=["-h"], out_has=["Usage (all parameters are optional"])


def t_lib_common_direct(c):
    expect(c, "lib_common.py", rc=0)
    check(c.oci_calls() == [] and not c.tool_calls("terraform"), "running lib_common.py directly does nothing")


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("t_")]


def main():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    ctx = Ctx(f"http://127.0.0.1:{server.server_address[1]}/v1")
    passed, failed = 0, []
    # Optional name filters (substring match), e.g. `run_tests.py validate trigger`, to keep a run
    # under short tool timeouts; no argument runs every test.
    wanted = [a for a in sys.argv[1:] if not a.startswith("-")]
    selected = [t for t in TESTS if not wanted or any(w in t.__name__ for w in wanted)]
    try:
        for t in selected:
            try:
                t(ctx)
                passed += 1
                print(f"ok    {t.__name__}")
            except Exception:  # noqa: BLE001
                failed.append(t.__name__)
                print(f"FAIL  {t.__name__}\n{traceback.format_exc()}")
    finally:
        server.shutdown()
        shutil.rmtree(ctx.tmp, ignore_errors=True)
    print(f"\n{passed} passed, {len(failed)} failed (of {len(selected)})")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
