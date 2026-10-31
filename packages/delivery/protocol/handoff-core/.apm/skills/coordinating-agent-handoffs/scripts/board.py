#!/usr/bin/env python3
"""Compute counters, effective limits and the next action; write <dir>/status.md.

Usage:
  python board.py <dir> --profile <yaml> [--override <yaml>] [--sync-sha <sha>] [--args k=v ...]

--args (keep it last; it consumes every following token):
  limits.<name>=<int>      per-run limit (precedence: profile < --override file < --args)
  quality.<name>=<value>   per-run quality parameter
  limits_zero_confirmed=true   allow 0 in --args (only with explicit user confirmation)
  drift=true|false         drift flag from detect_drift.py (exit 2 = true)
  other keys (change=..., capability=...) are ignored.

Prints one line on stdout:
  NEXT: role=<role> agent=<a>[,<b>] rule=<n|fallback>
  NEXT: escalate [limit=<name> task=<id>] rule=<n>
  NEXT: final-gate rule=<n>
  NEXT: none (no rule matched)
Exit codes: 0 ok, 1 invalid profile / limits / directory.
Python 3.8+, standard library only.
"""
import argparse
import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import _handoff_lib as lib  # noqa: E402


def _fail(items):
    for name, message in items:
        sys.stderr.write("%s: %s\n" % (name, message))
    return 1


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="board.py",
        description="Compute handoff counters, effective limits and the next action; "
                    "writes <dir>/status.md and prints the next action.")
    ap.add_argument("dir", help="handoff directory containing the records (*.md)")
    ap.add_argument("--profile", required=True, help="handoff-profile.yaml of the family")
    ap.add_argument("--override", help="optional project override YAML (limits/quality)")
    ap.add_argument("--sync-sha", help="record this commit SHA as the last synced one")
    ap.add_argument("--args", nargs="*", default=[], metavar="k=v",
                    help="per-run parameters, e.g. limits.review_rounds=4 drift=true")
    args = ap.parse_args(argv)

    profile, perrs = lib.load_profile(args.profile)
    if perrs:
        return _fail([(os.path.basename(args.profile), e) for e in perrs])
    params = lib.effective_params(profile, args.override, args.args)
    if params["errors"]:
        return _fail(params["errors"])
    if not os.path.isdir(args.dir):
        return _fail([(args.dir, "not a directory")])

    records = lib.load_records(args.dir, profile)
    for rec in records:
        if rec.error is not None and rec.name != "status.md":
            sys.stderr.write("warning: %s: %s (skipped)\n" % (rec.name, rec.error))
    state = lib.compute_state(records, profile, params, bool(params["drift"]))

    status_path = os.path.join(args.dir, "status.md")
    old_fm, approvals = lib.read_status(status_path)
    sha = args.sync_sha or str(old_fm.get("lastSyncedSha") or "none")
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    text = lib.render_status(profile, state, params, sha, approvals, now)
    with open(status_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)

    if params["ignored"]:
        sys.stderr.write("note: ignored --args keys: %s\n" % ", ".join(params["ignored"]))
    print(lib.format_next(state["next"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
