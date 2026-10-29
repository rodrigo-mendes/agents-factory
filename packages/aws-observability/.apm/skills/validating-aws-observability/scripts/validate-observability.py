#!/usr/bin/env python3
"""validate-observability.py - runs the five READ-ONLY pillar checks and aggregates the result.
It never calls trigger-alarm-test.py (the only mutating script). Detail: ../SKILL.md
"""
import os
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import obs_common as oc  # noqa: E402

USAGE = """Usage: validate-observability.py --function NAME [pillar options] [common options]

Runs check-logs.py, check-metrics.py, check-traces.py, check-alarms.py and check-dashboards.py with the
options below, prints each script's lines, then a pillar table. alarms and dashboards are SKIPPED
unless you give their selectors. Nothing here changes AWS state; billable reads need the flags below.

Pillar options are forwarded to the script that owns them (see each script's --help):
  logs:       --log-group --fields --min-events --allow-no-retention
  metrics:    --custom-namespace --custom --custom-stat --min-invocations --max-errors
  traces:     --api-type --trace-ids --max-traces --expect-aws-call
  alarms:     --alarm-prefix | --alarm-names, --fail-on-insufficient-data
  dashboards: --dashboard (repeatable) | --dashboard-prefix
  --wait-seconds and --retry-seconds go to logs and metrics; the other common options go to all five.
  --skip LIST            comma list of pillars to skip: logs,metrics,traces,alarms,dashboards
  --i-have-logs-insights-approval    forwarded to logs: allows the billable Logs Insights queries
  --i-have-trace-retrieval-approval  forwarded to traces: allows start-trace-retrieval (Transaction Search)
  Give each flag only when the caller holds the matching relayed approval line (scope=<log-group> /
  scope=xray). Without them no billable call is made: those checks report WARN (not verified).

Exit codes: 0 every run pillar passed (WARN allowed) | 1 a pillar reported FAIL |
            2 usage error or missing tool (also when a pillar script exits 2) |
            3 a pillar could not run because of an AWS CLI error (and none failed a check)
"""

PILLARS = ("logs", "metrics", "traces", "alarms", "dashboards")
COMMON_VALUE_OPTS = ("--region", "--profile", "--start-s", "--window-min", "--max-polls", "--poll-seconds")


def main():
    c = oc.Ctx(__file__)
    common, logs, metrics, traces, alarms, dash = [], [], [], [], [], []
    skip = ""
    have_alarm = False
    have_dash = False

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("-h", "--help"):
            sys.stdout.write(USAGE + oc.COMMON_USAGE)
            sys.exit(0)
        elif a == "--skip":
            skip = c.need_value(args, i)
            i += 2
        elif a == "--function":
            c.fn = c.need_value(args, i)
            common += [a, c.fn]
            i += 2
        elif a in COMMON_VALUE_OPTS:
            common += [a, c.need_value(args, i)]
            i += 2
        elif a in ("--wait-seconds", "--retry-seconds"):
            v = c.need_value(args, i)
            logs += [a, v]
            metrics += [a, v]
            i += 2
        elif a in ("--log-group", "--fields", "--min-events"):
            logs += [a, c.need_value(args, i)]
            i += 2
        elif a in ("--allow-no-retention", "--i-have-logs-insights-approval"):
            logs.append(a)
            i += 1
        elif a == "--i-have-trace-retrieval-approval":
            traces.append(a)
            i += 1
        elif a in ("--custom-namespace", "--custom", "--custom-stat", "--min-invocations", "--max-errors"):
            metrics += [a, c.need_value(args, i)]
            i += 2
        elif a in ("--api-type", "--trace-ids", "--max-traces", "--expect-aws-call"):
            traces += [a, c.need_value(args, i)]
            i += 2
        elif a in ("--alarm-prefix", "--alarm-names"):
            alarms += [a, c.need_value(args, i)]
            have_alarm = True
            i += 2
        elif a == "--fail-on-insufficient-data":
            alarms.append(a)
            i += 1
        elif a in ("--dashboard", "--dashboard-prefix"):
            dash += [a, c.need_value(args, i)]
            have_dash = True
            i += 2
        else:
            c.usage_err("unknown option: %s" % a)

    if not c.fn:
        c.usage_err("--function is required")
    c.require_tools()

    # --skip accepts only the five pillar names; a typo must not silently run (or skip) the wrong pillar.
    skip_list = oc.split_csv(skip)
    for s in skip_list:
        if s not in PILLARS:
            c.usage_err("--skip: unknown pillar '%s' (allowed: logs, metrics, traces, alarms, dashboards)" % s)

    rows = []
    n = {"PASS": 0, "FAIL": 0, "WARN": 0, "ERROR": 0, "USAGE": 0, "SKIPPED": 0}

    def run_one(pillar, script, extra):
        sys.stdout.flush()
        r = subprocess.run([sys.executable, os.path.join(c.dir, script)] + extra,
                           stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                           env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        out = r.stdout.decode("utf-8", "replace").replace("\r\n", "\n").rstrip("\n")
        sys.stdout.write(out + "\n")
        sys.stdout.flush()
        rc = r.returncode
        if rc == 0:
            status = "WARN" if any(l.startswith("WARN") for l in out.split("\n")) else "PASS"
        elif rc == 1:
            status = "FAIL"
        elif rc == 2:
            status = "USAGE"
        else:
            status = "ERROR"
        n[status] += 1
        rows.append("%-12s %-8s exit=%s" % (pillar, status, rc))

    def skip_row(pillar, reason):
        n["SKIPPED"] += 1
        rows.append("%-12s %-8s %s" % (pillar, "SKIPPED", reason))

    if "logs" in skip_list:
        skip_row("logs", "--skip")
    else:
        run_one("logs", "check-logs.py", common + logs)
    if "metrics" in skip_list:
        skip_row("metrics", "--skip")
    else:
        run_one("metrics", "check-metrics.py", common + metrics)
    if "traces" in skip_list:
        skip_row("traces", "--skip")
    else:
        run_one("traces", "check-traces.py", common + traces)
    if "alarms" in skip_list:
        skip_row("alarms", "--skip")
    elif not have_alarm:
        skip_row("alarms", "no --alarm-prefix or --alarm-names")
    else:
        run_one("alarms", "check-alarms.py", common + alarms)
    if "dashboards" in skip_list:
        skip_row("dashboards", "--skip")
    elif not have_dash:
        skip_row("dashboards", "no --dashboard or --dashboard-prefix")
    else:
        run_one("dashboards", "check-dashboards.py", common + dash)

    print()
    print("%-12s %-8s %s" % ("PILLAR", "STATUS", "DETAIL"))
    for row in rows:
        print(row)
    print("SUMMARY validate-observability pass=%d fail=%d warn=%d error=%d usage=%d skipped=%d"
          % (n["PASS"], n["FAIL"], n["WARN"], n["ERROR"], n["USAGE"], n["SKIPPED"]))

    if n["USAGE"] > 0:
        sys.exit(2)
    if n["FAIL"] > 0:
        sys.exit(1)
    if n["ERROR"] > 0:
        sys.exit(3)
    sys.exit(0)


if __name__ == "__main__":
    oc.run(main, __file__)
