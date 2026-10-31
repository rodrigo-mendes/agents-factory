#!/usr/bin/env python3
"""check-traces.py - Traces pillar, read-only. Detail: ../blueprints/pillar-traces.md

Always reads the trace segment destination first: with Transaction Search (CloudWatchLogs)
BatchGetTraces cannot find traces, so the retrieval API is used instead.
"""
import json
import os
import re
import sys
import time

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import obs_common as oc  # noqa: E402

USAGE = """Usage: check-traces.py --function NAME [options]

Read-only. Steps: Lambda TracingConfig.Mode must be Active; read xray get-trace-segment-destination;
find trace ids (get-trace-summaries, or --trace-ids); read them with batch-get-traces (destination
XRay) or start-trace-retrieval + list-retrieved-traces (destination CloudWatchLogs, Transaction
Search); then assert the segment origins for the API type.

Options:
  --api-type T           REST, HTTP or NONE (default NONE). REST expects AWS::ApiGateway::Stage plus the
                         two Lambda origins; HTTP and NONE expect only AWS::Lambda and
                         AWS::Lambda::Function (an HTTP API adds no X-Ray node; a Stage node fails HTTP)
  --trace-ids "ID ID"    use these trace ids (space or comma separated) instead of get-trace-summaries
  --max-traces N         how many trace ids to read, 1-5 (default 5)
  --expect-aws-call NAME require a subsegment with namespace aws and this name (for example DynamoDB)
  --i-have-trace-retrieval-approval
                         required for start-trace-retrieval (destination CloudWatchLogs, Transaction Search);
                         give it only when the caller holds a relayed 'approval: logs-insights scope=xray'
                         line. Without it that path is WARN (not verified) and no retrieval is started
"""

TRACE_IDS_OK = re.compile(r"[0-9A-Za-z, -]*")
CALL_OK = re.compile(r"[A-Za-z0-9_.:-]*")


def documents(resp, key):
    """Parsed Document of every segment/span (each Document is a JSON string); unparsable ones skipped."""
    out = []
    for tr in oc.items(oc.get(resp, "Traces")):
        for seg in oc.items(oc.get(tr, key)):
            doc = oc.get(seg, "Document")
            if not isinstance(doc, str):
                continue
            try:
                out.append(json.loads(doc))
            except ValueError:
                continue
    return out


def walk(v):
    """jq `.. | objects`."""
    if isinstance(v, dict):
        yield v
        for x in v.values():
            yield from walk(x)
    elif isinstance(v, list):
        for x in v:
            yield from walk(x)


def main():
    c = oc.Ctx(__file__)
    api_type = "NONE"
    trace_ids_in = ""
    max_traces = 5
    expect_call = ""
    retrieval_ok = False

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("-h", "--help"):
            sys.stdout.write(USAGE + oc.COMMON_USAGE)
            sys.exit(0)
        elif a == "--api-type":
            api_type = c.need_value(args, i)
            i += 2
        elif a == "--trace-ids":
            trace_ids_in = c.need_value(args, i)
            i += 2
        elif a == "--max-traces":
            max_traces = c.uint(args, i)
            i += 2
        elif a == "--expect-aws-call":
            expect_call = c.need_value(args, i)
            i += 2
        elif a == "--i-have-trace-retrieval-approval":
            retrieval_ok = True
            i += 1
        else:
            n = c.common_opt(args, i)
            if not n:
                c.usage_err("unknown option: %s" % a)
            i += n

    if not c.fn:
        c.usage_err("--function is required")
    if api_type not in ("REST", "HTTP", "NONE"):
        c.usage_err("--api-type must be REST, HTTP or NONE")
    if max_traces < 1 or max_traces > 5:
        c.usage_err("--max-traces must be 1 to 5 (BatchGetTraces takes at most 5 ids)")
    if not TRACE_IDS_OK.fullmatch(trace_ids_in):
        c.usage_err("--trace-ids may only contain letters, digits, hyphens, spaces and commas")
    if not CALL_OK.fullmatch(expect_call):
        c.usage_err("--expect-aws-call contains unexpected characters")

    c.init_env()

    if api_type == "REST":
        need_origins = ["AWS::ApiGateway::Stage", "AWS::Lambda", "AWS::Lambda::Function"]
    else:
        need_origins = ["AWS::Lambda", "AWS::Lambda::Function"]

    # 1. precondition: Lambda must send traces (PassThrough, the default, sends none automatically)
    cfg = oc.parse(c.run_aws("lambda", "get-function-configuration", "--function-name", c.fn))
    mode = oc.text(oc.alt(oc.get(cfg, "TracingConfig", "Mode"), "unknown"))
    if mode != "Active":
        c.fail("traces.lambda-mode", "TracingConfig.Mode=%s; PassThrough does not send traces automatically" % mode)
        c.finish()
    c.pass_("traces.lambda-mode", "Active")

    # 2. destination first (N4): decides which API can read the traces
    dst = oc.parse(c.run_aws("xray", "get-trace-segment-destination"))
    dest = oc.text(oc.alt(oc.get(dst, "Destination"), "unknown"))
    dstat = oc.text(oc.alt(oc.get(dst, "Status"), "unknown"))
    if dest == "XRay":
        c.pass_("traces.destination", "XRay (%s): X-Ray APIs read the traces" % dstat)
    elif dest == "CloudWatchLogs":
        c.pass_("traces.destination", "CloudWatchLogs (%s): Transaction Search, BatchGetTraces cannot find traces" % dstat)
    else:
        c.fail("traces.destination", "unexpected Destination '%s'" % dest)
        c.finish()
    if dest == "CloudWatchLogs" and dstat != "ACTIVE":
        c.warn("traces.transaction-search", "Status=%s: spans can take 10 minutes to become available; INCONCLUSIVE" % dstat)
        c.finish()

    # 3. trace ids
    if trace_ids_in:
        ids = trace_ids_in.replace(",", " ")
    else:
        ts = oc.parse(c.run_aws("xray", "get-trace-summaries", "--start-time", c.start_s, "--end-time", c.end_s,
                                "--filter-expression",
                                'service(id(name: "%s", type: "AWS::Lambda::Function"))' % c.fn))
        found = [oc.get(s, "Id") for s in oc.items(oc.get(ts, "TraceSummaries"))][:max_traces]
        ids = " ".join("" if x is None else oc.text(x) for x in found)
    if ids.rstrip("\n") == "":
        if dest == "XRay":
            c.fail("traces.summaries", "no trace summary for %s in the window" % c.fn)
        else:
            c.warn("traces.summaries", "INCONCLUSIVE: no summary (only an indexed share of spans becomes trace "
                                       "summaries); pass --trace-ids or ask for a higher indexing percentage")
        c.finish()
    idarr = ids.split()
    c.pass_("traces.summaries", "%d trace id(s)" % len(idarr))

    # 4. read the traces on the path that matches the destination
    if dest == "XRay":
        rx = oc.parse(c.run_aws("xray", "batch-get-traces", "--trace-ids", *idarr))
        segkey = "Segments"
        level = c.fail
    else:
        if not retrieval_ok:
            c.warn("traces.retrieval", "not verified: start-trace-retrieval needs a relayed 'logs-insights scope=xray' "
                                       "approval (--i-have-trace-retrieval-approval); no retrieval started")
            c.finish()
        st = oc.parse(c.run_aws("xray", "start-trace-retrieval", "--trace-ids", *idarr,
                                "--start-time", c.start_s, "--end-time", c.end_s))
        tok_v = oc.alt(oc.get(st, "RetrievalToken"), None)
        token = oc.text(tok_v) if tok_v is not None else ""
        if not token:
            c.fail("traces.retrieval", "start-trace-retrieval returned no RetrievalToken")
            c.finish()
        n = 0
        rs = "UNKNOWN"
        lr = {}
        while n < c.max_polls:
            n += 1
            lr = oc.parse(c.run_aws("xray", "list-retrieved-traces", "--retrieval-token", token,
                                    "--trace-format", "XRAY"))
            rs = oc.text(oc.alt(oc.get(lr, "RetrievalStatus"), "UNKNOWN"))
            if rs in ("COMPLETE", "FAILED", "CANCELLED", "TIMEOUT"):
                break
            time.sleep(c.poll_s)
        if rs == "COMPLETE":
            c.pass_("traces.retrieval", "RetrievalStatus=COMPLETE")
        elif rs in ("FAILED", "CANCELLED", "TIMEOUT"):
            c.fail("traces.retrieval", "RetrievalStatus=%s" % rs)
            c.finish()
        else:
            c.warn("traces.retrieval", "INCONCLUSIVE: RetrievalStatus=%s after %s polls" % (rs, c.max_polls))
            c.finish()
        rx = lr
        segkey = "Spans"
        level = c.warn  # the Spans document shape is not confirmed to equal BatchGetTraces documents

    # 5. origins
    docs = documents(rx, segkey)
    origins = []
    for d in docs:
        o = d.get("origin") if isinstance(d, dict) else None
        o = oc.alt(o, None)
        if o is not None:
            origins.append(o)
    origins = [oc.text(o) for o in oc.jq_unique(origins)]
    missing = "".join(" " + o for o in need_origins if o not in origins)
    found_txt = " ".join(origins)
    if missing:
        level("traces.origins", "missing origin(s):%s; found: %s" % (missing, found_txt or "none"))
    elif api_type == "HTTP" and "AWS::ApiGateway::Stage" in origins:
        level("traces.origins", "api-type HTTP but the trace has an AWS::ApiGateway::Stage node (REST API?)")
    else:
        c.pass_("traces.origins", "api-type %s: %s" % (api_type, found_txt))

    if expect_call:
        cnt = sum(1 for d in docs for o in walk(d)
                  if o.get("namespace") == "aws" and o.get("name") == expect_call)
        if cnt > 0:
            c.pass_("traces.aws-call", "%d subsegment(s) named %s" % (cnt, expect_call))
        else:
            level("traces.aws-call", "no subsegment named %s with namespace aws" % expect_call)

    c.finish()


if __name__ == "__main__":
    oc.run(main, __file__)
