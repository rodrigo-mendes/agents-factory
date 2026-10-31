#!/usr/bin/env python3
"""run_tests.py - offline tests for the validators.

A fake `aws` (tests/fakes/fake_aws.py) is selected through VAO_AWS_CMD and returns canned JSON from
tests/fixtures. No real AWS call is made anywhere. Needs only Python 3.
Run: python3 scripts/tests/run_tests.py   (Windows: python scripts\\tests\\run_tests.py)   Exit 0 = all passed.
"""
import glob
import os
import re
import shlex
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
S = os.path.dirname(HERE)
FAKE = os.path.join(HERE, "fakes", "fake_aws.py")


def fake_cmd():
    if os.name == "nt":
        return '"%s" "%s"' % (sys.executable, FAKE)
    return shlex.join([sys.executable, FAKE])


BASE_ENV = dict(os.environ)
for k in ("AWS_PROFILE", "AWS_DEFAULT_REGION", "FAKE_AWS_EXIT", "FAKE_AWS_EXIT_ON", "FAKE_AWS_REJECT_ARG",
          "FAKE_AWS_REJECT_ON", "MSYSTEM"):
    BASE_ENV.pop(k, None)
BASE_ENV.update({"AWS_REGION": "eu-west-1", "VAO_AWS_CMD": fake_cmd(), "PYTHONDONTWRITEBYTECODE": "1",
                 "PYTHONIOENCODING": "utf-8"})


class Runner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.out = ""
        self.rc = 0
        fd, self.logf = tempfile.mkstemp(prefix="fake-aws-", suffix=".log")
        os.close(fd)

    def log(self):
        with open(self.logf, encoding="utf-8") as fh:
            return fh.read()

    def run(self, scen, script, *args, **env):
        """Runs SCRIPT -> self.out (stdout+stderr), self.rc, call log in self.logf."""
        open(self.logf, "w").close()
        e = dict(BASE_ENV, FAKE_AWS_SCENARIO=scen, FAKE_AWS_LOG=self.logf)
        e.update(env)
        r = subprocess.run([sys.executable, os.path.join(S, script)] + list(args), env=e,
                           stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self.out = r.stdout.decode("utf-8", "replace").replace("\r\n", "\n")
        self.rc = r.returncode

    def ok(self, msg):
        self.passed += 1
        print("ok   - %s" % msg)

    def bad(self, msg):
        self.failed += 1
        print("FAIL - %s" % msg)
        print("----- output (exit %s) -----" % self.rc)
        print("\n".join(self.out.split("\n")[:40]))
        print("-----")

    def rc_is(self, name, want):
        if self.rc == want:
            self.ok("%s: exit %d" % (name, want))
        else:
            self.bad("%s: expected exit %d, got %s" % (name, want, self.rc))

    def has(self, name, pat):
        if re.search(pat, self.out, re.M):
            self.ok("%s: output has /%s/" % (name, pat))
        else:
            self.bad("%s: output lacks /%s/" % (name, pat))

    def hasnt(self, name, pat):
        if re.search(pat, self.out, re.M):
            self.bad("%s: output must not have /%s/" % (name, pat))
        else:
            self.ok("%s: output has no /%s/" % (name, pat))

    def called(self, name, txt):
        if txt in self.log():
            self.ok("%s: aws call '%s' made" % (name, txt))
        else:
            self.bad("%s: aws call '%s' not made" % (name, txt))

    def notcalled(self, name, txt):
        if txt in self.log():
            self.bad("%s: aws call '%s' must not be made" % (name, txt))
        else:
            self.ok("%s: aws call '%s' not made" % (name, txt))

    def no_call_at_all(self, name):
        if self.log() == "":
            self.ok("%s: no AWS call at all" % name)
        else:
            self.bad("%s: AWS was called" % name)


SCRIPTS = ["check-logs", "check-metrics", "check-traces", "check-alarms", "check-dashboards",
           "trigger-alarm-test", "validate-observability"]
FN = ["--function", "orders-fn"]


def main():
    t = Runner()
    try:
        v =subprocess.run([sys.executable, FAKE, "--version"], stdout=subprocess.PIPE).stdout.decode()
        if "fake test stub" not in v:
            print("fake aws does not answer --version")
            return 2

        print("== syntax and help ==")
        for f in ["obs_common"] + SCRIPTS:
            p = os.path.join(S, f + ".py")
            try:
                with open(p, encoding="utf-8") as fh:
                    compile(fh.read(), p, "exec")
                t.ok("compile %s.py" % f)
            except (OSError, SyntaxError) as e:
                t.out = str(e)
                t.bad("compile %s.py" % f)
        for f in SCRIPTS:
            t.run("green", f + ".py", "--help")
            t.rc_is("%s --help" % f, 0)
            t.has("%s --help" % f, "Usage:")
            t.has("%s --help" % f, "Exit codes")
        t.run("green", "obs_common.py")
        t.rc_is("obs_common.py refuses to run as a script", 2)

        print("== logs ==")
        t.run("green", "check-logs.py", *FN, "--i-have-logs-insights-approval")
        t.rc_is("logs green", 0)
        t.has("logs green", r"^PASS +logs\.retention")
        t.has("logs green", r"^PASS +logs\.field\.tenantId")
        t.run("logs-missing-tenant", "check-logs.py", *FN, "--i-have-logs-insights-approval")
        t.rc_is("logs missing tenantId", 1)
        t.has("logs missing tenantId", r"^FAIL +logs\.field\.tenantId")
        t.run("green", "check-logs.py", *FN, "--i-have-logs-insights-approval", "--fields", "requestId,tenantId,userRole")
        t.rc_is("logs field names are parameters", 0)
        t.run("green", "check-logs.py", *FN, "--fields", "bad field;")
        t.rc_is("logs rejects an unsafe field name", 2)
        t.run("green", "check-logs.py", *FN)
        t.rc_is("logs without the logs-insights approval", 0)
        t.has("logs without the logs-insights approval", r"^WARN +logs\.query")
        t.notcalled("logs without the logs-insights approval", "logs start-query")

        print("== metrics ==")
        t.run("green", "check-metrics.py", *FN)
        t.rc_is("metrics green", 0)
        t.has("metrics green", r"^PASS +metrics\.invocations +Sum=3")
        t.has("metrics green", r"^PASS +metrics\.throttles")
        t.run("green", "check-metrics.py", *FN, "--custom-namespace", "OrdersApp", "--custom", "ordersCreated:Service=orders")
        t.rc_is("metrics custom", 0)
        t.has("metrics custom", r"^PASS +metrics\.custom\.ordersCreated")
        t.run("green", "check-metrics.py", *FN, "--min-invocations", "10")
        t.rc_is("metrics below minimum", 1)
        # aggregation per statistic: Duration is a maximum (largest of 100, 250, 150 = 250, not the sum 500)
        t.run("metric-stats", "check-metrics.py", *FN, "--custom-namespace", "OrdersApp", "--custom", "ordersCreated")
        t.rc_is("metrics aggregation (Sum)", 0)
        t.has("metrics Duration is the largest maximum", r"^PASS +metrics\.duration +Maximum=250 ")
        t.hasnt("metrics Duration is not summed", r"Maximum=500")
        t.has("metrics invocations Sum over two periods", r"^PASS +metrics\.invocations +Sum=3")
        t.has("metrics custom Sum label and value", r"^PASS +metrics\.custom\.ordersCreated +Sum=16 over 3 datapoint")
        t.run("metric-stats", "check-metrics.py", *FN, "--custom-namespace", "OrdersApp", "--custom", "ordersCreated",
              "--custom-stat", "Maximum")
        t.has("metrics custom Maximum takes the largest", r"^PASS +metrics\.custom\.ordersCreated +Maximum=9 ")
        t.run("metric-stats", "check-metrics.py", *FN, "--custom-namespace", "OrdersApp", "--custom", "ordersCreated",
              "--custom-stat", "Minimum")
        t.has("metrics custom Minimum takes the smallest", r"^PASS +metrics\.custom\.ordersCreated +Minimum=2 ")
        t.run("metric-stats", "check-metrics.py", *FN, "--custom-namespace", "OrdersApp", "--custom", "ordersCreated",
              "--custom-stat", "Average")
        t.has("metrics custom Average is labelled as a mean of averages",
              r"^PASS +metrics\.custom\.ordersCreated +Average\(mean of per-period averages\)=5\.33")
        # exit-code contract: malformed JSON from the CLI exits 3, never a code of its own
        t.run("malformed", "check-metrics.py", *FN)
        t.rc_is("metrics with malformed JSON", 3)
        t.has("metrics with malformed JSON", "unexpected command failure")
        t.run("malformed", "check-alarms.py", "--alarm-prefix", "orders-fn")
        t.rc_is("alarms with malformed JSON", 3)

        print("== traces ==")
        t.run("green", "check-traces.py", *FN)
        t.rc_is("traces green (X-Ray)", 0)
        t.has("traces green", r"^PASS +traces\.origins")
        t.called("traces green", "xray batch-get-traces")
        t.run("green", "check-traces.py", *FN, "--api-type", "REST")
        t.rc_is("traces REST without a Stage node", 1)
        t.run("rest-api", "check-traces.py", *FN, "--api-type", "REST")
        t.rc_is("traces REST with a Stage node", 0)
        t.run("rest-api", "check-traces.py", *FN, "--api-type", "HTTP")
        t.rc_is("traces HTTP with a Stage node", 1)
        t.run("green", "check-traces.py", *FN, "--api-type", "HTTP", "--expect-aws-call", "DynamoDB")
        t.rc_is("traces HTTP, DynamoDB subsegment", 0)
        t.run("no-traces", "check-traces.py", *FN)
        t.rc_is("no traces", 1)
        t.has("no traces", r"^FAIL +traces\.summaries")
        t.run("transaction-search", "check-traces.py", *FN, "--i-have-trace-retrieval-approval")
        t.rc_is("traces Transaction Search", 0)
        t.called("traces Transaction Search", "xray start-trace-retrieval")
        t.notcalled("traces Transaction Search", "xray batch-get-traces")
        t.run("transaction-search", "check-traces.py", *FN)
        t.rc_is("traces Transaction Search without approval", 0)
        t.has("traces Transaction Search without approval", r"^WARN +traces\.retrieval")
        t.notcalled("traces Transaction Search without approval", "xray start-trace-retrieval")
        t.run("passthrough", "check-traces.py", *FN)
        t.rc_is("traces Lambda PassThrough", 1)
        t.has("traces Lambda PassThrough", r"^FAIL +traces\.lambda-mode")

        print("== alarms ==")
        t.run("green", "check-alarms.py", "--alarm-prefix", "orders-fn")
        t.rc_is("alarms green", 0)
        t.has("alarms green", r"^PASS +sns\.orders-alerts")
        t.hasnt("alarms green", r"oncall@example\.com")
        t.run("alarm-insufficient", "check-alarms.py", "--alarm-prefix", "orders-fn")
        t.rc_is("alarm in INSUFFICIENT_DATA", 0)
        t.has("alarm in INSUFFICIENT_DATA", r"^WARN +alarm\.orders-fn-errors\.state")
        t.run("alarm-insufficient", "check-alarms.py", "--alarm-prefix", "orders-fn", "--fail-on-insufficient-data")
        t.rc_is("alarm in INSUFFICIENT_DATA with the strict flag", 1)
        t.run("sns-pending", "check-alarms.py", "--alarm-names", "orders-fn-errors")
        t.rc_is("pending SNS subscription", 1)
        t.run("green", "check-alarms.py", "--alarm-names", "missing-alarm")
        t.rc_is("named alarm not found", 1)
        t.notcalled("alarms are read-only", "set-alarm-state")

        print("== dashboards ==")
        t.run("green", "check-dashboards.py", "--dashboard", "orders-dashboard")
        t.rc_is("dashboards green", 0)
        t.has("dashboards green", r"^PASS +dash\.orders-dashboard\.metric")
        t.has("dashboards green", r"^PASS +dash\.orders-dashboard\.log")
        t.has("dashboards green", r"^PASS +dash\.orders-dashboard\.alarm")
        t.has("dashboards green", r"^WARN +dash\.orders-dashboard\.render")
        t.run("dash-missing-metric", "check-dashboards.py", "--dashboard", "orders-dashboard")
        t.rc_is("dashboard widget with a missing metric", 1)
        t.has("dashboard missing metric", r"^FAIL +dash\.orders-dashboard\.metric.*Errors")
        t.run("green", "check-dashboards.py", "--dashboard", "no-such-dashboard")
        t.rc_is("dashboard not found", 1)

        print("== trigger-alarm-test (only mutating script) ==")
        t.run("green", "trigger-alarm-test.py", "--alarm-name", "orders-fn-errors")
        t.rc_is("trigger without the approval flag", 2)
        t.has("trigger without the approval flag", "REFUSED")
        t.notcalled("trigger without the approval flag", "set-alarm-state")
        t.no_call_at_all("trigger without the approval flag")
        t.run("green", "trigger-alarm-test.py", "--alarm-name", "orders-fn-errors", "--i-have-user-approval")
        t.rc_is("trigger with the approval flag", 0)
        t.called("trigger with the approval flag", "cloudwatch set-alarm-state")
        t.has("trigger with the approval flag", r"^PASS +trigger\.action")
        t.called("trigger asks for the metric alarm type", "--alarm-types MetricAlarm --history-item-type Action")
        # composite alarm: refused without --allow-composite; with it the history is read with CompositeAlarm
        t.run("composite", "trigger-alarm-test.py", "--alarm-name", "orders-fn-composite", "--i-have-user-approval")
        t.rc_is("trigger composite without --allow-composite", 2)
        t.notcalled("trigger composite without --allow-composite", "set-alarm-state")
        t.run("composite", "trigger-alarm-test.py", "--alarm-name", "orders-fn-composite", "--i-have-user-approval",
              "--allow-composite")
        t.rc_is("trigger composite with --allow-composite", 0)
        t.called("trigger composite reads composite history", "--alarm-types CompositeAlarm")
        # alarm already in ALARM: refused, nothing sent
        t.run("alarm-in-alarm", "trigger-alarm-test.py", "--alarm-name", "orders-fn-errors", "--i-have-user-approval")
        t.rc_is("trigger on an alarm already in ALARM", 2)
        t.has("trigger on an alarm already in ALARM", "already in ALARM")
        t.notcalled("trigger on an alarm already in ALARM", "set-alarm-state")
        # --alarm-types rejected by the CLI (exit 252): fallback to the default, with a WARN
        t.run("green", "trigger-alarm-test.py", "--alarm-name", "orders-fn-errors", "--i-have-user-approval",
              FAKE_AWS_REJECT_ARG="--alarm-types", FAKE_AWS_REJECT_ON="describe-alarm-history")
        t.rc_is("trigger when describe-alarm-history rejects --alarm-types", 0)
        t.has("trigger fallback", r"^WARN +trigger\.alarm-types")
        t.has("trigger fallback", r"^PASS +trigger\.action")
        # CLI error after the mutation: exit 3 plus a recovery hint
        t.run("green", "trigger-alarm-test.py", "--alarm-name", "orders-fn-errors", "--i-have-user-approval",
              FAKE_AWS_EXIT="255", FAKE_AWS_EXIT_ON="describe-alarm-history")
        t.rc_is("trigger with a CLI error after set-alarm-state", 3)
        t.has("trigger with a CLI error after set-alarm-state", "RECOVERY: set-alarm-state may already have been sent")
        t.called("trigger with a CLI error after set-alarm-state", "cloudwatch set-alarm-state")

        print("== orchestrator ==")
        t.run("green", "validate-observability.py", *FN, "--i-have-logs-insights-approval", "--alarm-prefix",
              "orders-fn", "--dashboard", "orders-dashboard", "--poll-seconds", "0")
        t.rc_is("validate green", 0)
        t.has("validate green", r"^logs +PASS")
        t.has("validate green", r"^dashboards +WARN")
        t.notcalled("validate is read-only", "set-alarm-state")
        t.run("logs-missing-tenant", "validate-observability.py", *FN, "--i-have-logs-insights-approval",
              "--poll-seconds", "0")
        t.rc_is("validate with a failing pillar", 1)
        t.has("validate with a failing pillar", r"^logs +FAIL")
        t.has("validate without selectors", r"^alarms +SKIPPED")
        t.run("green", "validate-observability.py")
        t.rc_is("validate without --function", 2)
        t.run("green", "validate-observability.py", *FN, "--skip", "logs,metrics,traces")
        t.rc_is("validate with valid --skip names", 0)
        t.has("validate with valid --skip names", r"^logs +SKIPPED")
        t.run("green", "validate-observability.py", *FN, "--skip", "logs,metric")
        t.rc_is("validate rejects an unknown --skip name", 2)
        t.has("validate rejects an unknown --skip name", "unknown pillar 'metric'")
        if t.log() == "":
            t.ok("validate rejects an unknown --skip name: no AWS call")
        else:
            t.bad("validate rejects an unknown --skip name: AWS was called")

        print("== AWS CLI errors map to exit 3 ==")
        t.run("green", "check-logs.py", *FN, FAKE_AWS_EXIT="255")
        t.rc_is("aws exit 255 in check-logs", 3)
        t.has("aws exit 255", "exited 255")
        t.run("green", "check-alarms.py", "--alarm-prefix", "x", FAKE_AWS_EXIT="253")
        t.rc_is("aws exit 253 in check-alarms", 3)
        t.has("aws exit 253", "do not retry")
        t.run("green", "check-traces.py", *FN, FAKE_AWS_EXIT="254", FAKE_AWS_EXIT_ON="xray")
        t.rc_is("aws exit 254 in check-traces", 3)
        t.run("green", "validate-observability.py", *FN, "--poll-seconds", "0", FAKE_AWS_EXIT="255")
        t.rc_is("aws exit 255 in the orchestrator", 3)

        print("== static guards (scripts only) ==")
        sources = {}
        for p in sorted(glob.glob(os.path.join(S, "*.py"))):
            with open(p, encoding="utf-8") as fh:
                sources[os.path.basename(p)] = fh.read()
        # AWS subcommands are passed as quoted string literals: "service", "subcommand", ...
        mut = re.compile(r"[\"'](?:(?:put|delete|create|update|enable|disable|associate|confirm|tag|untag)-[a-z-]+"
                         r"|publish|subscribe|invoke)[\"']")
        hits = ["%s: %s" % (n, m.group(0)) for n, src in sources.items() for m in mut.finditer(src)]
        if hits:
            t.out = "\n".join(hits)
            t.bad("no mutating aws subcommand in the scripts")
        else:
            t.ok("no mutating aws subcommand in the scripts")
        sas = [n for n, src in sources.items() if "set-alarm-state" in src]
        if sas == ["trigger-alarm-test.py"]:
            t.ok("set-alarm-state appears only in trigger-alarm-test.py")
        else:
            t.out = " ".join(sas)
            t.bad("set-alarm-state found in: %s" % " ".join(sas))
        # start-* verbs begin a process: only Logs Insights start-query and X-Ray start-trace-retrieval are allowed
        st = re.compile(r"[\"']start-([a-z-]+)[\"']")
        bad_st = ["%s: start-%s" % (n, m.group(1)) for n, src in sources.items() for m in st.finditer(src)
                  if m.group(1) not in ("query", "trace-retrieval")]
        if bad_st:
            t.out = "\n".join(bad_st)
            t.bad("only start-query and start-trace-retrieval among the start-* verbs")
        else:
            t.ok("only start-query and start-trace-retrieval among the start-* verbs")
        if any(re.search(r"--unmask|--interleaved", src) for src in sources.values()):
            t.bad("no --unmask or --interleaved")
        else:
            t.ok("no --unmask or --interleaved")
        if any(re.search(r"--output\"?,? *\"?text", src) for src in sources.values()):
            t.bad("no --output text")
        else:
            t.ok("no --output text")
        if glob.glob(os.path.join(S, "*.sh")):
            t.bad("no bash scripts left in scripts/")
        else:
            t.ok("no bash scripts left in scripts/")
    finally:
        os.remove(t.logf)

    print()
    print("tests passed: %d  failed: %d" % (t.passed, t.failed))
    return 0 if t.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
