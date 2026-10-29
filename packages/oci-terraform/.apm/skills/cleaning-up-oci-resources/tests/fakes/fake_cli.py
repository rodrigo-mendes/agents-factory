#!/usr/bin/env python3
"""Fake CLI (oci / terraform / docker) for the script tests. Never touches a network.

Env:
  FAKE_RULES  path to a JSON list of rules: {"match": [contiguous argv tokens], "also": [tokens anywhere],
              "stdout": str, "rc": int}. First matching rule wins; no match -> rc 0, empty stdout.
  FAKE_LOG    path of a JSON-lines file; each call appends {"argv", "stdin", "proxy_env"}.
"""
import json
import os
import sys


def _contains(argv, seq):
    n = len(seq)
    return any(argv[i:i + n] == seq for i in range(len(argv) - n + 1)) if n else True


def main():
    argv = sys.argv[1:]
    stdin = ""
    if not sys.stdin.isatty():
        try:
            stdin = sys.stdin.read()
        except (OSError, ValueError):
            stdin = ""
    log = os.environ.get("FAKE_LOG")
    if log:
        with open(log, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({
                "argv": argv, "stdin": stdin,
                "proxy_env": sorted(k for k in os.environ if k.lower() in ("http_proxy", "https_proxy")),
            }) + "\n")
    rules = []
    if os.environ.get("FAKE_RULES"):
        with open(os.environ["FAKE_RULES"], encoding="utf-8") as fh:
            rules = json.load(fh)
    for rule in rules:
        if _contains(argv, rule.get("match", [])) and all(t in argv for t in rule.get("also", [])):
            sys.stdout.write(rule.get("stdout", ""))
            return int(rule.get("rc", 0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
