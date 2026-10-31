#!/usr/bin/env python3
"""check-metrics.py - Metrics pillar, read-only. Detail: ../blueprints/pillar-metrics.md"""
import os
import sys
import tempfile
import time

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import obs_common as oc  # noqa: E402

USAGE = """Usage: check-metrics.py --function NAME [options]

Read-only. Reads AWS/Lambda Invocations, Errors, Throttles (Sum, period 60) and Duration (Maximum)
for the function with one get-metric-data call over the smoke window, and asserts every
StatusCode is Complete. Optionally reads custom (for example EMF) metrics on their EXACT dimension set.

Options:
  --min-invocations N    Invocations Sum must be at least N (default 1); Sum 0 is INCONCLUSIVE (WARN)
  --max-errors N         Errors Sum must not exceed N (default 0)
  --custom-namespace NS  namespace of the custom metrics (needed with --custom)
  --custom SPEC          custom metric, repeatable: Name or Name:Dim=Value,Dim2=Value2
                         (the dimension set must equal the published one; no guessing)
  --custom-stat STAT     Sum (default), Average, Minimum, Maximum or SampleCount; the datapoints of the
                         window are aggregated by that statistic (Sum, SampleCount add; Maximum takes the
                         largest; Minimum the smallest; Average is the mean of the per-period averages)
"""

STATS = ("Sum", "Average", "Minimum", "Maximum", "SampleCount")


def dims_of(dimstr):
    """'Dim=Value,Dim2=Value2' -> [{Name, Value}] (a value may contain '=')."""
    if dimstr == "":
        return []
    out = []
    for piece in dimstr.split(","):
        parts = piece.split("=") if piece != "" else []
        out.append({"Name": parts[0] if parts else None, "Value": "=".join(parts[1:])})
    return out


def agg_for(stat):
    """The read_metric aggregation matching a CloudWatch statistic name."""
    return {"Maximum": "max", "Minimum": "min", "Average": "avg"}.get(stat, "add")


def stat_label(stat):
    """Label of the aggregate, honest about what an Average aggregate is."""
    return "Average(mean of per-period averages)" if stat == "Average" else stat


def main():
    c = oc.Ctx(__file__)
    custom_ns = ""
    custom_stat = "Sum"
    custom = []
    min_inv = 1
    max_err = 0

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("-h", "--help"):
            sys.stdout.write(USAGE + oc.COMMON_USAGE)
            sys.exit(0)
        elif a == "--min-invocations":
            min_inv = c.uint(args, i)
            i += 2
        elif a == "--max-errors":
            max_err = c.uint(args, i)
            i += 2
        elif a == "--custom-namespace":
            custom_ns = c.need_value(args, i)
            i += 2
        elif a == "--custom":
            custom.append(c.need_value(args, i))
            i += 2
        elif a == "--custom-stat":
            custom_stat = c.need_value(args, i)
            i += 2
        else:
            n = c.common_opt(args, i)
            if not n:
                c.usage_err("unknown option: %s" % a)
            i += n

    if not c.fn:
        c.usage_err("--function is required")
    if custom_stat not in STATS:
        c.usage_err("--custom-stat must be Sum, Average, Minimum, Maximum or SampleCount")
    if custom and not custom_ns:
        c.usage_err("--custom needs --custom-namespace")

    c.init_env()

    # Query ids start with a lowercase letter. Invocation metrics use the Sum statistic.
    def lambda_query(qid, metric, stat):
        return {"Id": qid,
                "MetricStat": {"Metric": {"Namespace": "AWS/Lambda", "MetricName": metric,
                                          "Dimensions": [{"Name": "FunctionName", "Value": c.fn}]},
                               "Period": 60, "Stat": stat}}

    q = [lambda_query(m.lower(), m, "Sum") for m in ("Invocations", "Errors", "Throttles")]
    q.append(lambda_query("dur", "Duration", "Maximum"))
    for n, spec in enumerate(custom):
        name, sep, dimstr = spec.partition(":")
        q.append({"Id": "c%d" % n,
                  "MetricStat": {"Metric": {"Namespace": custom_ns, "MetricName": name,
                                            "Dimensions": dims_of(dimstr if sep else "")},
                                 "Period": 60, "Stat": custom_stat}})

    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, "q.json"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(oc.tojson(q))

        # file:// relative to the current directory (the research documents fileb:// that way)
        def fetch_metrics():
            return oc.parse(c.run_aws("cloudwatch", "get-metric-data",
                                      "--metric-data-queries", "file://q.json",
                                      "--start-time", c.m_start, "--end-time", c.m_end, cwd=tmp))

        md = fetch_metrics()

        def read_metric(qid, agg="add"):
            """Aggregates the per-period Values of one query by the statistic that was asked.
            AGG is add (Sum, SampleCount), max (Maximum), min (Minimum) or avg (Average: the mean of
            the per-period averages, not a weighted average, because the sample counts are not
            requested). Returns (status or MISSING, datapoints, aggregate label text, integer floor)."""
            r = [x for x in oc.items(oc.get(md, "MetricDataResults")) if oc.get(x, "Id") == qid]
            if not r:
                return "MISSING", 0, "0", 0
            v = oc.items(oc.get(r[0], "Values"))
            if not v:
                a = 0
            elif agg == "max":
                a = max(v)
            elif agg == "min":
                a = min(v)
            elif agg == "avg":
                a = sum(v) / len(v)
            else:
                a = sum(v)
            st = oc.text(oc.alt(oc.get(r[0], "StatusCode"), "Unknown"))
            return st, len(v), oc.num(a), oc.floor_uint(a)

        def usable(label, st):
            """True when the current result can be asserted on, False after reporting why not."""
            if st == "Complete":
                return True
            if st == "PartialData":
                c.warn("metrics.%s" % label, "StatusCode=PartialData: re-run the check")
            elif st == "MISSING":
                c.fail("metrics.%s" % label, "no result for this query id in the response")
            else:
                c.fail("metrics.%s" % label, "StatusCode=%s" % st)
            return False

        waited = 0
        while True:
            _, _, _, val = read_metric("invocations")
            if val > 0 or waited >= c.wait_s:
                break
            time.sleep(c.retry_s)
            waited += c.retry_s
            md = fetch_metrics()

    st, _, _, val = read_metric("invocations")
    if usable("invocations", st):
        if val == 0:
            c.warn("metrics.invocations", "INCONCLUSIVE: Sum=0 (Lambda sends metrics in 1-minute intervals); "
                                          "retry with --wait-seconds")
        elif val >= min_inv:
            c.pass_("metrics.invocations", "Sum=%d" % val)
        else:
            c.fail("metrics.invocations", "Sum=%d, expected at least %d" % (val, min_inv))

    st, _, _, val = read_metric("errors")
    if usable("errors", st):
        if val <= max_err:
            c.pass_("metrics.errors", "Sum=%d (allowed %d)" % (val, max_err))
        else:
            c.fail("metrics.errors", "Sum=%d, allowed %d" % (val, max_err))

    st, _, _, val = read_metric("throttles")
    if usable("throttles", st):
        if val == 0:
            c.pass_("metrics.throttles", "Sum=0")
        else:
            c.fail("metrics.throttles", "Sum=%d (throttles do not count as Invocations or Errors)" % val)

    # Duration is queried with the Maximum statistic: the aggregate is the largest per-period maximum.
    st, _, raw, _ = read_metric("dur", "max")
    if usable("duration", st):
        c.pass_("metrics.duration", "Maximum=%s ms (largest per-period maximum)" % raw)

    for n, spec in enumerate(custom):
        name = spec.partition(":")[0]
        st, cnt, raw, _ = read_metric("c%d" % n, agg_for(custom_stat))
        if usable("custom.%s" % name, st):
            if cnt > 0:
                c.pass_("metrics.custom.%s" % name,
                        "%s=%s over %d datapoint(s) in %s" % (stat_label(custom_stat), raw, cnt, custom_ns))
            else:
                c.warn("metrics.custom.%s" % name,
                       "no datapoints yet (statistics of a new custom metric can take up to 2 minutes)")

    c.finish()


if __name__ == "__main__":
    oc.run(main, __file__)
