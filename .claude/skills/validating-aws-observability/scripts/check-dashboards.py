#!/usr/bin/env python3
"""check-dashboards.py - Dashboards pillar, read-only and only PARTIALLY able to prove anything:
no AWS API reports that a dashboard renders. This script checks structure and references.
Detail: ../blueprints/pillar-dashboards.md
"""
import json
import os
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import obs_common as oc  # noqa: E402

USAGE = """Usage: check-dashboards.py (--dashboard NAME ... | --dashboard-prefix P) [options]

Read-only. For each dashboard: list-dashboards (exists), get-dashboard, parse the DashboardBody JSON
string, then cross-check every reference:
  - metric widgets: each [Namespace, MetricName, DimName, DimValue, ...] row ("." repeats the previous
    row's value) must exist in list-metrics on the exact dimension set; properties.region is required
  - log widgets: every SOURCE '<log-group>' must exist (describe-log-groups); region and query required
  - alarm references (alarm widgets and metric widget annotations) must exist (describe-alarms)
Rows that are not [Namespace, MetricName, ...] are counted and skipped.
It always ends with a WARN: whether the dashboard RENDERS cannot be proven through the API.
list-metrics is not a freshness probe (new metrics can take up to 15 minutes to appear, metrics without
data for two weeks are not listed).

Options:
  --dashboard NAME         dashboard to check, repeatable
  --dashboard-prefix P     check every dashboard whose name starts with P
"""

SOURCE_RE = re.compile(r"SOURCE '([^'\n]*)'")


def metric_refs(body):
    """Metric rows -> unique list of {kind: ref|skipped, ...} (resolves "." against the previous
    resolved row of the same widget)."""
    out = []
    for w in oc.items(oc.get(body, "widgets")):
        if oc.get(w, "type") != "metric":
            continue
        p = oc.get(w, "properties")
        rows = oc.alt(oc.get(p, "metrics"), [])
        acc = []
        for i in range(int(oc.length(rows))):
            r = oc.idx(rows, i)
            if i == 0:
                res = r
            else:
                prev = acc[i - 1]
                res = []
                for k in range(int(oc.length(r))):
                    rk = oc.idx(r, k)
                    if rk == "." and k < oc.length(prev):
                        res.append(oc.idx(prev, k))
                    else:
                        res.append(rk)
            acc.append(res)
        for res in acc:
            if isinstance(oc.idx(res, 0), str) and isinstance(oc.idx(res, 1), str):
                dims = []
                for j in range(2, int(oc.length(res)), 2):
                    if isinstance(res[j], str):
                        dims.append({"Name": res[j], "Value": oc.alt(oc.idx(res, j + 1), "")})
                out.append({"kind": "ref", "region": oc.alt(oc.get(p, "region"), ""),
                            "ns": res[0], "name": res[1], "dims": dims})
            else:
                out.append({"kind": "skipped"})
    return oc.jq_unique(out)


def dim_match(listed, dims):
    """A listed metric matches when it has exactly the widget dimension set."""
    for m in oc.items(oc.get(listed, "Metrics")):
        md = oc.alt(oc.get(m, "Dimensions"), [])
        if oc.length(md) != len(dims):
            continue
        if all(any(oc.get(x, "Name") == d["Name"] and oc.get(x, "Value") == d["Value"] for x in oc.items(md))
               for d in dims):
            return True
    return False


def check_dashboard(c, d):
    gd = oc.parse(c.run_aws("cloudwatch", "get-dashboard", "--dashboard-name", d))
    raw = oc.alt(oc.get(gd, "DashboardBody"), None)
    body = None
    if raw is not None:
        try:
            body = json.loads(oc.text(raw))
        except ValueError:
            body = None
    if not (isinstance(body, dict) and isinstance(body.get("widgets"), list)):
        c.fail("dash.%s.body" % d, "DashboardBody is not JSON with a widgets array")
        return
    nw = len(body["widgets"])
    if nw == 0:
        c.warn("dash.%s.body" % d, "0 widgets")
    else:
        c.pass_("dash.%s.body" % d, "%d widget(s)" % nw)

    # metric references
    nref = 0
    nskip = 0
    for ref in metric_refs(body):
        if ref["kind"] == "skipped":
            nskip += 1
            continue
        nref += 1
        rg = oc.text(ref["region"])
        ns = oc.text(ref["ns"])
        nm = oc.text(ref["name"])
        dtxt = ",".join("%s=%s" % (oc.text(x["Name"]), oc.text(x["Value"])) for x in ref["dims"])
        if not rg:
            c.fail("dash.%s.metric" % d, "%s/%s: metric widget has no properties.region (required)" % (ns, nm))
            continue
        lm = oc.parse(c.run_aws_in(rg, "cloudwatch", "list-metrics", "--namespace", ns, "--metric-name", nm))
        if dim_match(lm, ref["dims"]):
            c.pass_("dash.%s.metric" % d, "%s/%s {%s} is listed" % (ns, nm, dtxt))
        else:
            c.fail("dash.%s.metric" % d, "%s/%s {%s} is not listed in %s (new metrics can take up to 15 minutes "
                                         "to appear)" % (ns, nm, dtxt, rg))
    if nref == 0:
        c.pass_("dash.%s.metric" % d, "no metric rows to check")
    if nskip > 0:
        c.warn("dash.%s.metric" % d, "%d row(s) skipped: not [Namespace, MetricName, ...] rows" % nskip)

    # log widget references
    for w in oc.items(body["widgets"]):
        if oc.get(w, "type") != "log":
            continue
        rg = oc.alt(oc.get(w, "properties", "region"), "")
        q = oc.alt(oc.get(w, "properties", "query"), "")
        rg = oc.text(rg)
        q = oc.text(q)
        if not rg or not q:
            c.fail("dash.%s.log" % d, "log widget needs both region and query")
            continue
        lgs = [g for g in SOURCE_RE.findall(q) if g]
        if not lgs:
            c.warn("dash.%s.log" % d, "no SOURCE '<log-group>' entry found in the widget query")
            continue
        for g in lgs:
            dl = oc.parse(c.run_aws_in(rg, "logs", "describe-log-groups", "--log-group-name-prefix", g))
            if any(oc.get(x, "logGroupName") == g for x in oc.items(oc.get(dl, "logGroups"))):
                c.pass_("dash.%s.log" % d, "log group %s exists" % g)
            else:
                c.fail("dash.%s.log" % d, "log group %s not found in %s" % (g, rg))

    # alarm references (a reference may be an alarm name or an alarm ARN)
    refs = []
    for w in oc.items(body["widgets"]):
        if oc.get(w, "type") not in ("alarm", "metric"):
            continue
        refs += oc.items(oc.alt(oc.get(w, "properties", "alarms"), []))
        refs += oc.items(oc.alt(oc.get(w, "properties", "annotations", "alarms"), []))
    for ref in sorted(set(oc.text(r) for r in refs if oc.text(r) != "")):
        if ref.startswith("arn:") and ":alarm:" in ref[4:]:
            parts = ref.split(":")
            arn_rg = parts[3] if len(parts) > 3 else ""
            anm = ref.split(":alarm:", 1)[1]
        else:
            arn_rg = c.region
            anm = ref
        da = oc.parse(c.run_aws_in(arn_rg, "cloudwatch", "describe-alarms", "--alarm-names", anm,
                                   "--alarm-types", "MetricAlarm", "CompositeAlarm"))
        found = any(oc.get(x, "AlarmName") == anm
                    for x in oc.items(oc.get(da, "MetricAlarms")) + oc.items(oc.get(da, "CompositeAlarms")))
        if found:
            c.pass_("dash.%s.alarm" % d, "alarm %s exists" % anm)
        else:
            c.fail("dash.%s.alarm" % d, "alarm %s not found in %s" % (anm, arn_rg))

    c.warn("dash.%s.render" % d, "NOT PROVABLE VIA API: structure and references checked, console rendering "
                                 "is not verified")


def main():
    c = oc.Ctx(__file__)
    dashes = []
    dprefix = ""

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("-h", "--help"):
            sys.stdout.write(USAGE + oc.COMMON_USAGE)
            sys.exit(0)
        elif a == "--dashboard":
            dashes.append(c.need_value(args, i))
            i += 2
        elif a == "--dashboard-prefix":
            dprefix = c.need_value(args, i)
            i += 2
        else:
            n = c.common_opt(args, i)
            if not n:
                c.usage_err("unknown option: %s" % a)
            i += n

    if not dashes and not dprefix:
        c.usage_err("give --dashboard or --dashboard-prefix")

    c.init_env()

    # resolve the dashboard names
    names = []
    if dprefix:
        ld = oc.parse(c.run_aws("cloudwatch", "list-dashboards", "--dashboard-name-prefix", dprefix))
        for e in oc.items(oc.get(ld, "DashboardEntries")):
            x = oc.text(oc.get(e, "DashboardName"))
            if x:
                names.append(x)
        if not names:
            c.fail("dashboards.found", "no dashboard with prefix %s" % dprefix)
    for d in dashes:
        le = oc.parse(c.run_aws("cloudwatch", "list-dashboards", "--dashboard-name-prefix", d))
        if any(oc.get(e, "DashboardName") == d for e in oc.items(oc.get(le, "DashboardEntries"))):
            names.append(d)
        else:
            c.fail("dash.%s.exists" % d, "dashboard not found")

    for d in names:
        check_dashboard(c, d)

    c.finish()


if __name__ == "__main__":
    oc.run(main, __file__)
