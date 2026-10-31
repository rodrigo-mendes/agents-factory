"""Thin, non-interactive wrapper around the GitHub CLI (gh 2.103.x; minimum 2.94.0).

Contract (Python 3.8+, standard library only):

  * Every call is ``subprocess.run([<gh>, *args])`` with an argument list - never
    ``shell=True`` - and the environment ``GH_PROMPT_DISABLED=1``, ``NO_COLOR=1``,
    ``GH_NO_UPDATE_NOTIFIER=1`` added to the caller's environment (``GH_TOKEN`` is
    inherited and never printed).
  * ``run(args, json=True)`` returns parsed JSON (or text with ``json=False``) and raises
    ``GhError(cmd, code, stderr)`` on a non-zero exit, a timeout or invalid JSON.
    gh exit codes: 0 ok, 1 failure, 2 cancelled, 4 authentication required.
  * Rate limits: a failure whose stderr looks like a primary/secondary rate limit
    (matching stderr text is a fallback, (unverified)) is retried at most 3 times with
    exponential backoff (base ``OPENSPEC_GITHUB_BACKOFF_BASE`` seconds, default 60).
  * Writes (``mutating=True``) are serial and followed by a pause of
    ``OPENSPEC_GITHUB_WRITE_DELAY`` seconds (default 1.0, the REST best-practice minimum).
  * The executable is ``OPENSPEC_GITHUB_GH`` when set (a ``.py`` file there is run with the
    current Python - this is how the offline tests inject ``tests/fake_gh.py``), otherwise
    ``shutil.which("gh")`` (which honours PATHEXT on Windows).
  * ``redact()`` masks the value of GH_TOKEN / GITHUB_TOKEN in any text before it is shown.
"""
import json as _json
import os
import re
import shutil
import subprocess
import sys
import time

MIN_VERSION = (2, 94, 0)       # sub-issue flags and Issues 2.0 (family fact F5, rule 9)
PIN_MINOR = (2, 103)           # family pin 2.103.x (F1)
MAX_RETRIES = 3

_RATE_RE = re.compile(r"rate limit|secondary rate|abuse detection|HTTP 429|retry-after", re.I)
_VERSION_RE = re.compile(r"gh version (\d+)\.(\d+)\.(\d+)")


class GhError(Exception):
    """A gh invocation failed. ``cmd`` is the argument list (no secrets), ``code`` the exit code."""

    def __init__(self, cmd, code, stderr):
        self.cmd = list(cmd)
        self.code = code
        self.stderr = redact(stderr or "")
        Exception.__init__(self, "gh %s failed (exit %s): %s"
                           % (format_args(cmd), code, self.stderr.strip()))


def redact(text):
    """Mask token values that might appear in text (defence in depth; gh does not print them)."""
    text = str(text)
    for name in ("GH_TOKEN", "GITHUB_TOKEN"):
        value = os.environ.get(name)
        if value and len(value) >= 8:
            text = text.replace(value, "***")
    return text


def format_args(args, limit=300):
    """Render an argument list for PLAN lines and errors (whitespace collapsed, long args cut)."""
    out = []
    for a in args:
        a = " ".join(str(a).split())
        if len(a) > limit:
            a = a[:limit] + "...(%d chars)" % len(a)
        if a == "" or re.search(r"[\s\"'$`\\|&;<>(){}*?!#]", a):
            a = "'" + a.replace("'", "'\"'\"'") + "'"
        out.append(a)
    return " ".join(out)


def gh_command():
    """Return the argv prefix used to start gh."""
    override = os.environ.get("OPENSPEC_GITHUB_GH")
    if override:
        if override.lower().endswith(".py"):
            return [sys.executable, override]
        return [override]
    found = shutil.which("gh")
    if not found:
        raise GhError(["--version"], 127, "gh executable not found on PATH (install gh 2.103.x)")
    return [found]


def _env():
    env = dict(os.environ)
    env.update({"GH_PROMPT_DISABLED": "1", "NO_COLOR": "1", "GH_NO_UPDATE_NOTIFIER": "1"})
    return env


def _float_env(name, default):
    try:
        return float(os.environ.get(name, default))
    except ValueError:
        return default


def _invoke(args, stdin, timeout):
    try:
        return subprocess.run(gh_command() + list(args), input=stdin if stdin is not None else "",
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=_env(),
                              encoding="utf-8", errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired:
        raise GhError(args, -1, "timed out after %ss" % timeout)
    except OSError as exc:
        raise GhError(args, 127, "cannot start gh: %s" % exc)


def run(args, *, json=True, timeout=60, stdin=None, mutating=False):
    """Run gh with ``args``; return parsed JSON (``json=True``) or stdout text."""
    base = _float_env("OPENSPEC_GITHUB_BACKOFF_BASE", 60.0)
    for attempt in range(MAX_RETRIES + 1):
        proc = _invoke(args, stdin, timeout)
        if proc.returncode == 0:
            break
        if proc.returncode == 4:
            raise GhError(args, 4, "authentication required: set GH_TOKEN to the credential "
                                   "matching tracker.owner_type. " + proc.stderr)
        if attempt < MAX_RETRIES and _RATE_RE.search(proc.stderr or ""):
            time.sleep(base * (2 ** attempt))
            continue
        raise GhError(args, proc.returncode, proc.stderr)
    if mutating:
        time.sleep(_float_env("OPENSPEC_GITHUB_WRITE_DELAY", 1.0))
    if not json:
        return proc.stdout
    text = proc.stdout.strip()
    if not text:
        return None
    try:
        return _json.loads(text)
    except ValueError:
        raise GhError(args, 0, "expected JSON on stdout, got: %s" % text[:200])


# ------------------------------------------------------------------ preflight helpers

def parse_version(text):
    m = _VERSION_RE.search(text or "")
    return tuple(int(x) for x in m.groups()) if m else None


def check_version():
    """Return (version_tuple, warning_or_None); raise GhError when gh is older than 2.94.0."""
    text = run(["--version"], json=False, timeout=30)
    version = parse_version(text)
    if version is None:
        raise GhError(["--version"], 0, "cannot parse gh version from %r" % text[:80])
    if version < MIN_VERSION:
        raise GhError(["--version"], 1, "gh %s is older than the required %s (sub-issues); "
                                        "upgrade to 2.103.x" % (".".join(map(str, version)),
                                                                 ".".join(map(str, MIN_VERSION))))
    warning = None
    if version[:2] != PIN_MINOR:
        warning = ("gh %s is not the family pin 2.103.x; behaviour was verified only on 2.103.x"
                   % ".".join(map(str, version)))
    return version, warning


def check_auth():
    """Raise GhError when gh has no usable credential. Output is never printed (no tokens)."""
    try:
        run(["auth", "status"], json=False, timeout=30)
    except GhError as exc:
        raise GhError(["auth", "status"], exc.code,
                      "gh auth status failed; set GH_TOKEN (App installation token for an "
                      "organization project, classic PAT with project + repo for a user project)")


# ------------------------------------------------------------------ REST / GraphQL

def graphql_args(query, variables=None):
    """Argument list of one GraphQL call (query on one line). Ints use -F, everything else -f."""
    args = ["api", "graphql", "-f", "query=" + " ".join(query.split())]
    for name, value in sorted((variables or {}).items()):
        flag = "-F" if isinstance(value, int) and not isinstance(value, bool) else "-f"
        args += [flag, "%s=%s" % (name, value)]
    return args


def graphql_data(args, doc):
    if not isinstance(doc, dict):
        raise GhError(args, 0, "unexpected GraphQL response: %r" % (doc,))
    if doc.get("errors"):
        raise GhError(args, 0, "GraphQL errors: %s" % _json.dumps(doc["errors"])[:500])
    return doc.get("data") or {}


def graphql(query, variables=None, mutating=False):
    """Run one GraphQL document; return its ``data`` (raises GhError on GraphQL errors)."""
    args = graphql_args(query, variables)
    return graphql_data(args, run(args, mutating=mutating))


def rest_args(method, path, body=None, paginate=False):
    args = ["api", "-X", method, path]
    if paginate:
        args += ["--paginate", "--slurp"]
    if body is not None:
        args += ["--input", "-"]
    return args


def rest(method, path, body=None, paginate=False, mutating=None):
    """Call a REST endpoint; JSON bodies go through stdin (``--input -``), never argv."""
    if mutating is None:
        mutating = method != "GET"
    stdin = _json.dumps(body) if body is not None else None
    doc = run(rest_args(method, path, body, paginate), stdin=stdin, mutating=mutating)
    if paginate:
        return flatten_pages(doc)
    return doc


def flatten_pages(doc):
    """``--paginate --slurp`` yields a list of pages; tolerate a flat list as well."""
    if doc is None:
        return []
    if isinstance(doc, list) and all(isinstance(p, list) for p in doc):
        return [item for page in doc for item in page]
    if isinstance(doc, list):
        return doc
    return [doc]
