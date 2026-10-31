#!/usr/bin/env python3
"""Fake git / terraform / bash for the tests: `fake_tool.py <tool> <args...>`.

git        `rev-parse --show-toplevel` prints $FAKE_GIT_TOPLEVEL, or exits 128 if unset.
terraform  `output -json` prints the file $FAKE_TF_OUTPUTS (rc 1 if unset);
           `-chdir=X output -raw NAME` prints that output's value;
           `plan ...` / `apply ...` exit $FAKE_TF_PLAN_RC / $FAKE_TF_APPLY_RC (default 0).
bash       exits $FAKE_BASH_RC (default 0).
Every call is appended to $FAKE_TOOL_LOG as one JSON line {"tool", "argv", "cwd"}.
"""
import json
import os
import sys


def main(argv):
    tool, args = argv[0], argv[1:]
    log = os.environ.get("FAKE_TOOL_LOG")
    if log:
        with open(log, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"tool": tool, "argv": args, "cwd": os.getcwd()}) + "\n")
    if tool == "git":
        top = os.environ.get("FAKE_GIT_TOPLEVEL")
        if not top:
            return 128
        print(top)
        return 0
    if tool == "terraform":
        args = [a for a in args if not a.startswith("-chdir=")]
        if args[:1] == ["output"]:
            path = os.environ.get("FAKE_TF_OUTPUTS")
            if not path:
                return 1
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
            if "-raw" in args:
                name = args[-1]
                if name not in data:
                    return 1
                sys.stdout.write(str(data[name]["value"]))
                return 0
            print(json.dumps(data))
            return 0
        if args[:1] == ["plan"]:
            return int(os.environ.get("FAKE_TF_PLAN_RC", "0"))
        if args[:1] == ["apply"]:
            return int(os.environ.get("FAKE_TF_APPLY_RC", "0"))
        return 1
    if tool == "bash":
        return int(os.environ.get("FAKE_BASH_RC", "0"))
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
