#!/usr/bin/env python3
"""obs_common.py - shared helpers for the AWS observability validators.

IMPORT this module from another script of this folder; do not execute it. Needs Python 3 (standard
library only) and AWS CLI v2. AWS facts behind the helpers: ../SKILL.md and ../blueprints/ (CLI reference
2.39.0, docs read 2026-10-28). Representative scripts: the author could not run them against AWS;
offline tests use a fake aws (VAO_AWS_CMD).
"""
import functools
import json
import math
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
import traceback

if __name__ == "__main__":
    print("obs_common.py is a library: import it from another script", file=sys.stderr)
    sys.exit(2)

# A1 deterministic CLI environment. An empty AWS_PAGER disables the interactive pager that CLI v2
# uses by default. The retry mode is set explicitly because two AWS pages disagree on its default
# (register I6); override it by exporting AWS_RETRY_MODE before the call.
os.environ["AWS_PAGER"] = ""
os.environ["AWS_RETRY_MODE"] = os.environ.get("AWS_RETRY_MODE") or "standard"

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass


class ParseError(Exception):
    """Raised when AWS output does not have the expected JSON shape (exit 3)."""


# ---- jq-compatible value helpers -----------------------------------------------------------------
def parse(text):
    """Parses CLI stdout as JSON. Empty output is read as an empty object; malformed JSON raises."""
    if text is None or text.strip() == "":
        return {}
    return json.loads(text)


def get(obj, *keys):
    """jq-style .a.b: missing keys and null give None; indexing a non-object raises ParseError."""
    for k in keys:
        if obj is None:
            return None
        if not isinstance(obj, dict):
            raise ParseError("cannot index %s with %r" % (type(obj).__name__, k))
        obj = obj.get(k)
    return obj


def alt(v, default):
    """jq `v // default`: default when v is null or false."""
    return default if v is None or v is False else v


def items(v):
    """jq `.[]?`: list elements, object values, nothing otherwise."""
    if isinstance(v, list):
        return list(v)
    if isinstance(v, dict):
        return list(v.values())
    return []


def length(v):
    """jq length."""
    if v is None:
        return 0
    if isinstance(v, bool):
        raise ParseError("boolean has no length")
    if isinstance(v, (int, float)):
        return abs(v)
    return len(v)


def idx(v, k):
    """jq .[k] for an integer k: null for null or out of range; raises for non-arrays."""
    if v is None:
        return None
    if not isinstance(v, list):
        raise ParseError("cannot index %s with a number" % type(v).__name__)
    return v[k] if -len(v) <= k < len(v) else None


def num(x):
    """Formats a number the way jq prints it (integral values without a decimal point)."""
    if isinstance(x, bool):
        return "true" if x else "false"
    if isinstance(x, int):
        return str(x)
    if isinstance(x, float):
        if math.isfinite(x) and x.is_integer() and abs(x) < 1e17:
            return str(int(x))
        return repr(x)
    return str(x)


def tojson(v):
    return json.dumps(v, separators=(",", ":"), ensure_ascii=False)


def text(v):
    """jq -r / string interpolation of one value."""
    if v is None:
        return "null"
    if isinstance(v, str):
        return v
    if isinstance(v, (bool, int, float)):
        return num(v)
    return tojson(v)


_RANK = {type(None): 0, bool: 1, int: 3, float: 3, str: 4, list: 5, dict: 6}


def _rank(v):
    if v is False:
        return 1
    if v is True:
        return 2
    return _RANK.get(type(v), 7)


def jq_cmp(a, b):
    """jq ordering: null < false < true < numbers < strings < arrays < objects."""
    ra, rb = _rank(a), _rank(b)
    if ra != rb:
        return -1 if ra < rb else 1
    if ra in (0, 1, 2):
        return 0
    if ra in (3, 4):
        return (a > b) - (a < b)
    if ra == 5:
        for x, y in zip(a, b):
            c = jq_cmp(x, y)
            if c:
                return c
        return (len(a) > len(b)) - (len(a) < len(b))
    ka, kb = sorted(a), sorted(b)
    c = jq_cmp(ka, kb)
    if c:
        return c
    for k in ka:
        c = jq_cmp(a[k], b[k])
        if c:
            return c
    return 0


def jq_sorted(values):
    return sorted(values, key=functools.cmp_to_key(jq_cmp))


def jq_unique(values):
    out = []
    for v in jq_sorted(values):
        if not out or jq_cmp(out[-1], v) != 0:
            out.append(v)
    return out


def split_csv(value):
    """bash `IFS=',' read -r -a ARR <<<"$value"`: one trailing empty field is dropped."""
    value = value.split("\n", 1)[0]
    if value == "":
        return []
    parts = value.split(",")
    if parts[-1] == "":
        parts.pop()
    return parts


def floor_uint(x):
    """Integer floor of an aggregate; anything that is not a non-negative integer becomes 0."""
    try:
        f = math.floor(x)
    except (TypeError, ValueError, OverflowError):
        return 0
    return f if f >= 0 else 0


COMMON_USAGE = """
Common options:
  --region REGION        AWS Region (default: $AWS_REGION, then $AWS_DEFAULT_REGION; one is required)
  --profile NAME         AWS CLI profile (default: the CLI's own resolution)
  --function NAME        Lambda function name
  --start-s EPOCH        smoke-test start in epoch SECONDS (default: now minus --window-min)
  --window-min N         look-back window in minutes when --start-s is absent (default 15)
  --max-polls N          maximum polls of an asynchronous query (default 30)
  --poll-seconds N       seconds between polls (default 2)
  --wait-seconds N       total seconds to keep re-checking for late data (default 0)
  --retry-seconds N      pause between those re-checks (default 15)
  -h, --help             show this help

Output: one PASS/FAIL/WARN line per check, then one SUMMARY line. WARN means inconclusive.
Exit codes: 0 all checks passed (WARN allowed) | 1 at least one check failed |
            2 usage error or missing tool | 3 AWS CLI error (CLI exit 252-255, 130 or other)
Environment: VAO_AWS_CMD overrides the AWS CLI command (default aws; split like a shell command line).
"""

_UINT = re.compile(r"[0-9]+")
_FN_OK = re.compile(r"[A-Za-z0-9_.:-]*")

_MEANING = {
    252: "invalid syntax, unknown parameter or bad value",
    253: "invalid environment or configuration (for example missing credentials): stop, do not retry",
    254: "the service returned an error",
    255: "the command failed (errors generated by the CLI or by the service)",
    130: "interrupted (SIGINT)",
}


def aws_command():
    """The AWS CLI command as a list: $VAO_AWS_CMD (shell-split) or ['aws']."""
    raw = os.environ.get("VAO_AWS_CMD") or "aws"
    if os.name == "nt":
        parts = []
        for p in shlex.split(raw, posix=False):
            if len(p) >= 2 and p[0] == p[-1] and p[0] in "\"'":
                p = p[1:-1]
            parts.append(p)
    else:
        parts = shlex.split(raw)
    return parts or ["aws"]


class Ctx:
    """State of one validator run: options, counters, AWS calls."""

    def __init__(self, script_file):
        self.script = os.path.basename(script_file)
        self.dir = os.path.dirname(os.path.abspath(script_file))
        self.pass_n = 0
        self.fail_n = 0
        self.warn_n = 0
        self.region = ""
        self.profile = ""
        self.fn = ""
        self.start_s = None
        self.window_min = 15
        self.max_polls = 30
        self.poll_s = 2
        self.wait_s = 0
        self.retry_s = 15
        self.now_s = None
        self.end_s = None
        self.m_start = None
        self.m_end = None
        self.aws = None

    # ---- result lines -----------------------------------------------------------------------
    def _line(self, kind, name, detail):
        sys.stdout.write("%s  %-26s %s\n" % (kind, name, detail))
        sys.stdout.flush()

    def pass_(self, name, detail):
        self.pass_n += 1
        self._line("PASS", name, detail)

    def fail(self, name, detail):
        self.fail_n += 1
        self._line("FAIL", name, detail)

    def warn(self, name, detail):
        self.warn_n += 1
        self._line("WARN", name, detail)

    def finish(self):
        base = self.script[:-3] if self.script.endswith(".py") else self.script
        print("SUMMARY %s pass=%d fail=%d warn=%d" % (base, self.pass_n, self.fail_n, self.warn_n))
        sys.stdout.flush()
        sys.exit(1 if self.fail_n > 0 else 0)

    # ---- option parsing ---------------------------------------------------------------------
    def usage_err(self, msg):
        sys.stdout.flush()
        sys.stderr.write("ERROR: %s\n" % msg)
        sys.stderr.write("Run '%s --help' for usage.\n" % self.script)
        sys.stderr.flush()
        sys.exit(2)

    def need_value(self, args, i):
        if i + 1 >= len(args):
            self.usage_err("option %s needs a value" % args[i])
        return args[i + 1]

    def uint(self, args, i):
        v = self.need_value(args, i)
        if not _UINT.fullmatch(v):
            self.usage_err("%s needs a non-negative integer, got '%s'" % (args[i], v))
        return int(v)

    def common_opt(self, args, i):
        """Handles an option shared by every script. Returns the words consumed (2) or 0."""
        o = args[i]
        if o == "--region":
            self.region = self.need_value(args, i)
        elif o == "--profile":
            self.profile = self.need_value(args, i)
        elif o == "--function":
            self.fn = self.need_value(args, i)
        elif o == "--start-s":
            self.start_s = self.uint(args, i)
        elif o == "--window-min":
            self.window_min = self.uint(args, i)
        elif o == "--max-polls":
            self.max_polls = self.uint(args, i)
        elif o == "--poll-seconds":
            self.poll_s = self.uint(args, i)
        elif o == "--wait-seconds":
            self.wait_s = self.uint(args, i)
        elif o == "--retry-seconds":
            self.retry_s = self.uint(args, i)
        else:
            return 0
        return 2

    # ---- environment ------------------------------------------------------------------------
    def require_tools(self):
        cmd = aws_command()
        exe = shutil.which(cmd[0])
        if not exe:
            self.usage_err("aws CLI not found on PATH (AWS CLI v2 required)")
        self.aws = [exe] + cmd[1:]
        ver = ""
        try:
            r = subprocess.run(self.aws + ["--version"], stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            ver = r.stdout.decode("utf-8", "replace").splitlines()[0] if r.stdout else ""
        except OSError:
            ver = ""
        if not ver.startswith("aws-cli/2."):
            self.usage_err("AWS CLI v2 required, found: %s" % (ver or "nothing"))

    def init_env(self):
        """Tools, Region, time window. Call after option parsing."""
        self.require_tools()
        if not self.region:
            self.region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or ""
        if not self.region:
            self.usage_err("no Region: pass --region or set AWS_REGION")
        if self.fn and not _FN_OK.fullmatch(self.fn):
            self.usage_err("--function contains unexpected characters")
        if self.window_min <= 0:
            self.usage_err("--window-min must be greater than 0")
        self.now_s = int(time.time())
        self.end_s = self.now_s
        if self.start_s is None:
            self.start_s = self.now_s - self.window_min * 60
        if not self.start_s < self.end_s:
            self.usage_err("--start-s must be earlier than now")
        # CloudWatch metrics: align to the 60 s period (start rounds down to the minute).
        self.m_start = self.start_s // 60 * 60
        self.m_end = (self.end_s // 60 + 1) * 60
        if os.environ.get("MSYSTEM"):
            sys.stderr.write("NOTE: Git Bash/MSYS detected. AWS does not document argument path conversion "
                             "for log group names such as /aws/lambda/x (register I5); confirm that "
                             "describe-log-groups returns your group.\n")

    # ---- AWS calls --------------------------------------------------------------------------
    def aws_fatal(self, rc, what, err):
        meaning = _MEANING.get(rc, "unexpected exit code")
        sys.stdout.flush()
        sys.stderr.write("ERROR: aws %s exited %s: %s\n" % (what, rc, meaning))
        for line in err.splitlines()[:3]:
            sys.stderr.write(line + "\n")
        sys.stderr.flush()
        sys.exit(3)

    def _call(self, region, args, cwd=None):
        """Always --output json (the --query filter of text output runs per page); stdin closed."""
        full = self.aws + ["--output", "json", "--no-cli-pager", "--region", region]
        if self.profile:
            full += ["--profile", self.profile]
        full += [str(a) for a in args]
        r = subprocess.run(full, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, cwd=cwd)
        out = r.stdout.decode("utf-8", "replace")
        err = r.stderr.decode("utf-8", "replace")
        return r.returncode, out, err

    def run_aws_in(self, region, *args, cwd=None):
        """Runs aws in REGION; any non-zero CLI exit becomes exit 3. Returns stdout."""
        rc, out, err = self._call(region, args, cwd)
        if rc != 0:
            self.aws_fatal(rc, " ".join(str(a) for a in args[:2]), err)
        return out

    def run_aws(self, *args, cwd=None):
        """Runs aws in --region / $AWS_REGION."""
        return self.run_aws_in(self.region, *args, cwd=cwd)

    def run_aws_try(self, *args):
        """Like run_aws but returns (rc, stdout, stderr) instead of exiting, so a caller can apply a
        documented fallback (for example an unknown parameter, exit 252)."""
        return self._call(self.region, args)


def run(main, script_file, on_exit=None):
    """Runs main(); maps any unexpected failure (typically malformed JSON) to exit 3, never a code
    of its own. on_exit(rc) runs before the process exits."""
    rc = 0
    try:
        main()
    except SystemExit as e:
        rc = e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
    except KeyboardInterrupt:
        rc = 130
    except Exception:  # noqa: BLE001 - the exit-code contract maps every unexpected failure to 3
        tb = traceback.extract_tb(sys.exc_info()[2])
        line = "?"
        for fr in tb:
            if os.path.basename(fr.filename) == os.path.basename(script_file):
                line = fr.lineno
        sys.stdout.flush()
        sys.stderr.write("ERROR: unexpected command failure at line %s of %s (malformed AWS output "
                         "or parse error?); exit 3\n" % (line, os.path.basename(script_file)))
        rc = 3
    if on_exit is not None:
        on_exit(rc)
    sys.stdout.flush()
    sys.stderr.flush()
    sys.exit(rc)
