#!/usr/bin/env python3
"""check-logs.py - Logs pillar, read-only. Detail: ../blueprints/pillar-logs.md"""
import os
import re
import sys
import time

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import obs_common as oc  # noqa: E402

USAGE = """Usage: check-logs.py (--function NAME | --log-group NAME) [options]

Read-only. Checks that the Lambda log group exists, has retention set, and that the smoke window
holds at least --min-events JSON log lines carrying every required field (Logs Insights ispresent()).
Prints counts only, never log messages. Logs Insights discovers fields for the Standard log class only.

Options:
  --log-group NAME       log group (default: LoggingConfig.LogGroup of --function, else /aws/lambda/NAME)
  --fields A,B           required JSON fields; the FIRST one identifies application lines
                         (default requestId,tenantId; application-defined names)
  --min-events N         minimum number of lines carrying the first field (default 1)
  --allow-no-retention   WARN instead of FAIL when retentionInDays is absent
  --i-have-logs-insights-approval
                         required for the billable Logs Insights queries (steps 2-3); give it only when the
                         caller holds a relayed 'approval: logs-insights scope=<log-group>' line. Without it
                         only the retention check runs and the field checks are WARN (not verified)
"""

FIELD_OK = re.compile(r"[A-Za-z_@][A-Za-z0-9_.@]*")
LOG_GROUP_OK = re.compile(r"[A-Za-z0-9_/#.-]*")


def main():
    c = oc.Ctx(__file__)
    log_group = ""
    fields = "requestId,tenantId"
    min_events = 1
    allow_no_retention = False
    billable_ok = False

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("-h", "--help"):
            sys.stdout.write(USAGE + oc.COMMON_USAGE)
            sys.exit(0)
        elif a == "--log-group":
            log_group = c.need_value(args, i)
            i += 2
        elif a == "--fields":
            fields = c.need_value(args, i)
            i += 2
        elif a == "--min-events":
            min_events = c.uint(args, i)
            i += 2
        elif a == "--allow-no-retention":
            allow_no_retention = True
            i += 1
        elif a == "--i-have-logs-insights-approval":
            billable_ok = True
            i += 1
        else:
            n = c.common_opt(args, i)
            if not n:
                c.usage_err("unknown option: %s" % a)
            i += n

    if not c.fn and not log_group:
        c.usage_err("give --function or --log-group")
    farr = oc.split_csv(fields)
    if not farr:
        c.usage_err("--fields is empty")
    for f in farr:
        if not FIELD_OK.fullmatch(f):
            c.usage_err("invalid field name '%s' (letters, digits, _ . @ only)" % f)
    if not LOG_GROUP_OK.fullmatch(log_group):
        c.usage_err("--log-group contains unexpected characters")

    c.init_env()

    lg = log_group
    if not lg:
        cfg = oc.parse(c.run_aws("lambda", "get-function-configuration", "--function-name", c.fn))
        v = oc.alt(oc.get(cfg, "LoggingConfig", "LogGroup"), None)
        lg = oc.text(v) if v is not None else ""
        if not lg:
            lg = "/aws/lambda/%s" % c.fn

    def run_count(qs):
        """Runs a Logs Insights query; returns (rc, count, error). rc 0 ok, 1 query failed,
        2 still running after --max-polls. Time unit: epoch SECONDS."""
        sq = oc.parse(c.run_aws("logs", "start-query", "--log-group-name", lg,
                                "--start-time", c.start_s, "--end-time", c.end_s,
                                "--query-language", "CWLI", "--query-string", qs))
        qid_v = oc.alt(oc.get(sq, "queryId"), None)
        qid = oc.text(qid_v) if qid_v is not None else ""
        if not qid:
            return 1, 0, "start-query returned no queryId"
        n = 0
        while n < c.max_polls:
            n += 1
            qr = oc.parse(c.run_aws("logs", "get-query-results", "--query-id", qid))
            st = oc.text(oc.alt(oc.get(qr, "status"), "Unknown"))
            if st == "Complete":
                # no result row (no match) is read as 0
                vals = [oc.get(cell, "value") for row in oc.items(oc.get(qr, "results"))
                        for cell in oc.items(row) if oc.get(cell, "field") == "n"]
                first = oc.alt(vals[0] if vals else None, "0")
                count = oc.text(first).split(".", 1)[0]
                if not re.fullmatch(r"[0-9]+", count):
                    return 1, 0, "non-numeric count in query result"
                return 0, int(count), ""
            if st in ("Scheduled", "Running"):
                time.sleep(c.poll_s)
            else:
                return 1, 0, "query status %s" % st
        return 2, 0, "query still running after %s polls" % c.max_polls

    # 1. log group and retention
    lgr = oc.parse(c.run_aws("logs", "describe-log-groups", "--log-group-name-prefix", lg))
    grp = [g for g in oc.items(oc.get(lgr, "logGroups")) if oc.get(g, "logGroupName") == lg]
    grp = oc.alt(grp[0] if grp else None, None)
    if grp is None:
        c.fail("logs.group", "log group %s not found" % lg)
        c.finish()
    c.pass_("logs.group", lg)
    ret = oc.alt(oc.get(grp, "retentionInDays"), None)
    if ret is not None:
        c.pass_("logs.retention", "retentionInDays=%s" % oc.text(ret))
    elif allow_no_retention:
        c.warn("logs.retention", "retentionInDays not set (whether that means never expire is unverified)")
    else:
        c.fail("logs.retention", "retentionInDays not set (repo policy: retention must be set)")

    # Gate: Logs Insights start-query is billable; run it only with the caller's relayed approval.
    if not billable_ok:
        c.warn("logs.query", "not verified: Logs Insights needs a relayed logs-insights approval "
                             "(--i-have-logs-insights-approval); no query started")
        c.finish()

    # 2. lines carrying the anchor field (first of --fields), re-checked until --wait-seconds
    f1 = farr[0]
    waited = 0
    while True:
        rc, count, qerr = run_count("filter ispresent(%s) | stats count(*) as n" % f1)
        if rc != 0:
            break
        if count >= min_events or waited >= c.wait_s:
            break
        time.sleep(c.retry_s)
        waited += c.retry_s
    if rc == 1:
        c.fail("logs.query", qerr)
        c.finish()
    if rc == 2:
        c.warn("logs.query", "INCONCLUSIVE: %s" % qerr)
        c.finish()
    if count == 0 and min_events > 0:
        c.warn("logs.events", "INCONCLUSIVE: no line carries %s yet (ingestion-to-query delay is "
                              "undocumented); retry with --wait-seconds" % f1)
        c.finish()
    elif count >= min_events:
        c.pass_("logs.events", "%d line(s) carry %s in the window" % (count, f1))
    else:
        c.fail("logs.events", "only %d line(s) carry %s, expected at least %d" % (count, f1, min_events))

    # 3. every other required field must be present on every line that carries the anchor field
    for f in farr[1:]:
        rc, count, qerr = run_count("filter ispresent(%s) and not ispresent(%s) | stats count(*) as n" % (f1, f))
        if rc == 1:
            c.fail("logs.field.%s" % f, qerr)
        elif rc == 2:
            c.warn("logs.field.%s" % f, "INCONCLUSIVE: %s" % qerr)
        elif count == 0:
            c.pass_("logs.field.%s" % f, "every line carrying %s also carries %s" % (f1, f))
        else:
            c.fail("logs.field.%s" % f, "%d line(s) carry %s but not %s" % (count, f1, f))

    c.finish()


if __name__ == "__main__":
    oc.run(main, __file__)
