#!/usr/bin/env python3
"""Fake `oci` CLI for the validating-oci-observability tests. Never touches the network.

Env:
  FAKE_OCI_FIXTURES  directory with <word>_<word>....json fixtures (one per command)
  FAKE_OCI_LOG       file; each call appends one JSON line {"cmd": "...", "argv": [...]}
  FAKE_OCI_SESSION   "valid" (default) | "expired"  -> `session validate --local`
  FAKE_OCI_LIVE_RC   rc of the live probe `iam region list` (default 0)

A fixture is either a plain JSON document (printed, rc 0) or an object with
"__rules__": [{"contains": ["str", ...], "stdout": <json|string>, "rc": 0}, ...]
and optional "__default__": {"stdout": ..., "rc": ...}. The first rule whose
strings all appear in the joined argv wins. Commands outside READ_ONLY exit 99
(the tests assert none of the scripts calls a mutating OCI command).
"""
import json
import os
import sys

GLOBAL_OPTS = {"--profile", "--auth", "--region", "--connection-timeout", "--read-timeout"}
READ_ONLY = {
    "session validate", "session refresh", "iam region list",
    "logging-search search-logs",
    "monitoring metric-data summarize-metrics-data",
    "monitoring alarm list", "monitoring alarm-status list-alarms-status",
    "ons subscription list", "fn application get",
    "management-dashboard dashboard list", "management-dashboard saved-search list",
}


def main(argv):
    words, rest, i = [], [], 0
    while i < len(argv):
        a = argv[i]
        if a in GLOBAL_OPTS:
            i += 2
            continue
        if a.startswith("--") or rest:
            rest.append(a)
        else:
            words.append(a)
        i += 1
    cmd = " ".join(words)
    log = os.environ.get("FAKE_OCI_LOG")
    if log:
        with open(log, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"cmd": cmd, "argv": argv}) + "\n")

    if cmd not in READ_ONLY:
        print(f"FAKE OCI: unexpected (non read-only) command: {cmd}", file=sys.stderr)
        return 99
    if cmd == "session validate":
        return 0 if os.environ.get("FAKE_OCI_SESSION", "valid") == "valid" else 1
    if cmd == "session refresh":
        return 0
    if cmd == "iam region list":
        rc = int(os.environ.get("FAKE_OCI_LIVE_RC", "0"))
        if rc == 0:
            print(json.dumps({"data": [{"name": "sa-saopaulo-1"}]}))
        return rc

    path = os.path.join(os.environ.get("FAKE_OCI_FIXTURES", ""), cmd.replace(" ", "_") + ".json")
    if not os.path.isfile(path):
        print(f"ServiceError: fake fixture missing for '{cmd}'", file=sys.stderr)
        return 1
    with open(path, encoding="utf-8") as fh:
        fx = json.load(fh)

    resp = {"stdout": fx, "rc": 0}
    if isinstance(fx, dict) and "__rules__" in fx:
        joined = " ".join(argv)
        resp = fx.get("__default__", {"stdout": "", "rc": 1})
        for rule in fx["__rules__"]:
            if all(s in joined for s in rule.get("contains", [])):
                resp = rule
                break
    out = resp.get("stdout", "")
    if out != "":
        print(out if isinstance(out, str) else json.dumps(out, indent=2))
    return int(resp.get("rc", 0))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
