#!/usr/bin/env python3
"""Fake `aws` for the offline tests: no network, no credentials, no real AWS call.

Selected with VAO_AWS_CMD="<python> <this file>". It returns canned JSON from
../fixtures/<scenario>/<service>_<subcommand>.json and falls back to ../fixtures/green/. Environment:
  FAKE_AWS_SCENARIO    scenario directory (default green)
  FAKE_AWS_LOG         file that receives one line per call: "<service> <subcommand> <args>"
  FAKE_AWS_EXIT        exit code to simulate (for example 255); FAKE_AWS_EXIT_ON limits it to calls whose
                       "<service> <subcommand>" contains that text
  FAKE_AWS_REJECT_ARG  when set, a call whose arguments contain that word exits 252 (unknown parameter);
                       FAKE_AWS_REJECT_ON limits it to calls whose "<service> <subcommand>" contains that text
Special cases: cloudwatch list-metrics applies the --namespace and --metric-name filters like the
service does; logs start-query answers a queryId derived from the query text (q-count, or
q-missing-<field> for "not ispresent(<field>)"); logs get-query-results is chosen by --query-id.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "..", "fixtures")


def out(data):
    sys.stdout.buffer.write(data if isinstance(data, bytes) else data.encode("utf-8"))
    sys.stdout.flush()


def pick(scen, name):
    """Scenario fixture first, then green; None when neither exists."""
    for d in (scen, "green"):
        p = os.path.abspath(os.path.join(FIX, d, name))
        if os.name == "nt" and len(p) >= 248 and not p.startswith("\\\\?\\"):
            p = "\\\\?\\" + p  # long-path prefix: a long checkout path must not silently fall back to green
        if os.path.isfile(p):
            with open(p, "rb") as fh:
                return fh.read()
        if d == scen and d != "green" and os.path.isdir(os.path.dirname(p)) and \
                os.path.basename(p) in os.listdir(os.path.dirname(p)):
            sys.stderr.write("fake_aws: fixture %s exists but cannot be read\n" % p)
            sys.exit(97)
    return None


def main(argv):
    scen = os.environ.get("FAKE_AWS_SCENARIO") or "green"
    if argv[:1] == ["--version"]:
        out("aws-cli/2.39.0 (fake test stub)\n")
        return 0

    svc, sub, rest = "", "", []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("--output", "--region", "--profile"):
            i += 2
            continue
        if a == "--no-cli-pager":
            i += 1
            continue
        if not svc:
            svc = a
        elif not sub:
            sub = a
        else:
            rest.append(a)
        i += 1

    log = os.environ.get("FAKE_AWS_LOG")
    if log:
        with open(log, "a", encoding="utf-8") as fh:
            fh.write("%s %s %s\n" % (svc, sub, " ".join(rest)))

    what = "%s %s" % (svc, sub)
    if os.environ.get("FAKE_AWS_EXIT"):
        if (os.environ.get("FAKE_AWS_EXIT_ON") or "") in what:
            sys.stderr.write("fake aws: simulated failure\n")
            return int(os.environ["FAKE_AWS_EXIT"])

    reject = os.environ.get("FAKE_AWS_REJECT_ARG")
    if reject and (os.environ.get("FAKE_AWS_REJECT_ON") or "") in what:
        if reject in rest:
            sys.stderr.write("fake aws: Unknown options: %s\n" % reject)
            return 252

    if what == "logs start-query":
        m = re.search(r"not ispresent\(([^)]+)\)", " ".join(rest))
        out('{"queryId":"q-missing-%s"}\n' % m.group(1) if m else '{"queryId":"q-count"}\n')
        return 0
    if what == "logs get-query-results":
        qid = ""
        for j, a in enumerate(rest):
            if a == "--query-id":
                qid = rest[j + 1] if j + 1 < len(rest) else ""
        data = pick(scen, "logs_get-query-results.%s.json" % qid)
        out(data if data is not None else '{"status":"Failed"}\n')
        return 0
    if what == "cloudwatch set-alarm-state":
        return 0

    data = pick(scen, "%s_%s.json" % (svc, sub))
    if what == "cloudwatch list-metrics" and data is not None:
        # emulate the server-side --namespace / --metric-name filters of ListMetrics
        flt = {"--namespace": "Namespace", "--metric-name": "MetricName"}
        want = {flt[a]: rest[j + 1] for j, a in enumerate(rest) if a in flt and j + 1 < len(rest)}
        doc = json.loads(data)
        doc["Metrics"] = [m for m in doc.get("Metrics", []) if all(m.get(k) == v for k, v in want.items())]
        data = json.dumps(doc)
    out(data if data is not None else "{}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
