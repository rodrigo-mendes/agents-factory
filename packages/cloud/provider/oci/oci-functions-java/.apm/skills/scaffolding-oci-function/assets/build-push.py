#!/usr/bin/env python3
# ==============================================================================
# build-push.py — Generic OCI Function build-and-push template
#
# Copy this file to services/<function-name>/build-push.py (Python 3.8+, standard
# library only; Linux, macOS and Windows).
# All values are sourced from services/.env (relative to this script) and
# from func.yaml in the same directory — NO hardcoded values.
#
# Usage:
#   python3 build-push.py [TAG]
#
# Resolution order for the image tag:
#   1. First positional argument
#   2. version: field in ./func.yaml
#
# Required in services/.env (one directory up from this script):
#   OCIR_REGION     OCI region code prefix, e.g. "gru" (sa-saopaulo-1)
#   OCIR_NAMESPACE  Object Storage namespace of the tenancy
#   OCIR_REPO       Repository path under the namespace, e.g. "serverless-app"
#   OCIR_USERNAME   "<namespace>/<iam-user>" or federated IDCS email
#   OCIR_PASSWORD   OCIR auth token (NOT the OCI account password)
#
# services/.env is read as KEY=VALUE lines (optional `export`, quotes, $VAR
# expansion, # comments); it is not executed as shell code.
#
# Optional env var override (not in .env):
#   PLATFORM        Docker --platform value; defaults to "linux/amd64"
#                   Override to "linux/arm64" for local Apple Silicon builds —
#                   always push linux/amd64 to OCI Functions.
#   DOCKER_CMD      Docker CLI command (default: docker), e.g. a fake for tests
#
# Pre-flight: runs ../../scripts/preflight.sh <this dir> first when it exists and
# is executable (on Windows it is run through `bash`).
# ==============================================================================
"""Port of build-push.sh: same inputs (services/.env, func.yaml, PLATFORM), steps, output, exit codes."""

import os
import re
import shlex
import shutil
import subprocess
import sys

REQUIRED = ("OCIR_REGION", "OCIR_NAMESPACE", "OCIR_REPO", "OCIR_USERNAME", "OCIR_PASSWORD")
PROXY_VARS = ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy")
_ASSIGN = re.compile(r"^(export\s+)?([A-Za-z_][A-Za-z0-9_]*)=(.*)$")
_VAR = re.compile(r"\$(?:\{([A-Za-z_][A-Za-z0-9_]*)\}|([A-Za-z_][A-Za-z0-9_]*))")


def say(text=""):
    sys.stdout.write(text + "\n")
    sys.stdout.flush()


def split_cmd(value):
    if os.name == "nt":
        parts = [p[1:-1] if len(p) >= 2 and p[0] == p[-1] == '"' else p for p in shlex.split(value, posix=False)]
    else:
        parts = shlex.split(value)
    if parts:
        resolved = shutil.which(parts[0])
        if resolved:
            parts[0] = resolved
    return parts


def _expand(text, variables):
    return _VAR.sub(lambda m: variables.get(m.group(1) or m.group(2), ""), text)


def _parse_value(raw, variables):
    raw = raw.strip()
    if raw.startswith("'"):
        end = raw.find("'", 1)
        return raw[1:end] if end > 0 else raw[1:]
    if raw.startswith('"'):
        out, i = [], 1
        while i < len(raw) and raw[i] != '"':
            if raw[i] == "\\" and i + 1 < len(raw) and raw[i + 1] in '"\\$`':
                out.append("\x00" if raw[i + 1] == "$" else raw[i + 1])  # \$ stays a literal $
                i += 2
                continue
            out.append(raw[i])
            i += 1
        return _expand("".join(out), variables).replace("\x00", "$")
    value = re.split(r"\s+#", raw, maxsplit=1)[0].rstrip()
    return _expand(value, variables)


def load_env_file(path, base_env):
    """Applies services/.env assignments. Returns (variables, child_env) like `source` would:
    every assignment is visible to the script; it reaches child processes only when exported
    (`export KEY=...`) or when KEY was already in the environment."""
    variables, child_env = dict(base_env), dict(base_env)
    with open(path, encoding="utf-8-sig") as fh:
        for number, line in enumerate(fh, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            match = _ASSIGN.match(stripped)
            if not match:
                sys.stderr.write("WARNING: %s:%d is not a KEY=VALUE line — ignored\n" % (path, number))
                continue
            exported, key, raw = match.groups()
            value = _parse_value(raw, variables)
            variables[key] = value
            if exported or key in base_env:
                child_env[key] = value
    return variables, child_env


def func_field(func_yaml, field):
    """`grep '^<field>:' func.yaml | awk '{print $2}'` with `set -euo pipefail` semantics."""
    try:
        with open(func_yaml, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
    except OSError:
        sys.stderr.write("grep: %s: No such file or directory\n" % func_yaml)
        sys.exit(2)
    values = [(line.split() + [""])[1] for line in lines if line.startswith(field + ":")]
    if not values:
        sys.exit(1)
    return "\n".join(values)


def run_preflight(script_dir):
    preflight = os.path.join(script_dir, "..", "..", "scripts", "preflight.sh")
    if not (os.path.isfile(preflight) and os.access(preflight, os.X_OK)):
        return
    say("==> Running pre-flight checks...")
    if os.name == "nt":
        bash = shutil.which("bash")
        if not bash:
            say("ERROR: %s requires bash, which was not found on PATH." % preflight)
            sys.exit(1)
        cmd = [bash, preflight, script_dir]
    else:
        cmd = [preflight, script_dir]
    rc = subprocess.run(cmd).returncode
    if rc != 0:
        sys.exit(rc)
    say("")


def main(argv):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", newline="\n")
        except (AttributeError, ValueError):
            pass

    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_file = os.path.join(script_dir, "..", ".env")

    # ── Pre-flight (optional, runs if the centralized script is present) ──────
    run_preflight(script_dir)

    # ── Load environment ──────────────────────────────────────────────────────
    if not os.path.isfile(env_file):
        say("ERROR: %s not found." % env_file)
        say("       Copy services/.env.example to services/.env and fill in values.")
        return 1
    variables, child_env = load_env_file(env_file, os.environ)

    # ── Validate required variables ───────────────────────────────────────────
    for var in REQUIRED:
        if not variables.get(var):
            say("ERROR: %s is not set in %s" % (var, env_file))
            return 1
    region, namespace, repo = variables["OCIR_REGION"], variables["OCIR_NAMESPACE"], variables["OCIR_REPO"]
    docker = split_cmd(os.environ.get("DOCKER_CMD") or "docker")

    # ── Docker login (password on stdin, never on the command line) ───────────
    say("==> Logging in to %s.ocir.io" % region)
    login = subprocess.run(docker + ["login", "%s.ocir.io" % region, "-u", variables["OCIR_USERNAME"],
                                     "--password-stdin"],
                           input=(variables["OCIR_PASSWORD"] + "\n").encode("utf-8"), env=child_env)
    if login.returncode != 0:
        return login.returncode

    # ── Resolve function name and tag ─────────────────────────────────────────
    func_yaml = os.path.join(script_dir, "func.yaml")
    func_name = func_field(func_yaml, "name")
    tag = argv[0] if argv and argv[0] else func_field(func_yaml, "version")

    platform = variables.get("PLATFORM") or "linux/amd64"
    image = "%s.ocir.io/%s/%s/%s:%s" % (region, namespace, repo, func_name, tag)

    # ── Build ─────────────────────────────────────────────────────────────────
    say("==> Building %s (platform: %s)" % (image, platform))
    # Unset proxy vars — prevents corporate proxy interference with layer pulls
    # inside the Docker build context.
    build_env = {k: v for k, v in child_env.items() if k not in PROXY_VARS and k.upper() not in PROXY_VARS}
    build = subprocess.run(docker + ["build", "--platform", platform, "-t", image, script_dir], env=build_env)
    if build.returncode != 0:
        return build.returncode

    # ── Push ──────────────────────────────────────────────────────────────────
    say("==> Pushing %s" % image)
    push = subprocess.run(docker + ["push", image], env=child_env)
    if push.returncode != 0:
        return push.returncode

    say("")
    say("Done! Image URI:")
    say("  %s" % image)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        sys.exit(130)
