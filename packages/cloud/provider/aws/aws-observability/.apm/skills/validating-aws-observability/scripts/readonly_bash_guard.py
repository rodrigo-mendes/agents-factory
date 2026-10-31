#!/usr/bin/env python3
"""PreToolUse hook for the Bash tool: allow ONLY an explicit read-only command allowlist.

Wired from the frontmatter of a subagent (`hooks: PreToolUse: matcher Bash`), so the guard is
technical, not just prose. Fails CLOSED: any parsing or runtime error denies the call.

  python readonly_bash_guard.py [--profile static-site]

Reads the hook JSON from stdin, prints a PreToolUse permission decision (allow | deny) and
exits 0. Standard library only; works the same on Windows (Git Bash), macOS and Linux.

Rules common to every profile: no shell syntax at all (no ; & | ` < > ( ) $ backslash or
newline: no chaining, pipes, redirects, substitution or expansion), the program must be on the
profile allowlist, and each allowed program has its own strict argument check.
"""
import json
import re
import shlex
import sys

SHELL_SYNTAX = re.compile(r"[;&|`<>()$\\\n\r]")

# ---- curl: GET/HEAD to one https URL, no output files, no request body, no config files ----
CURL_LONG_NO_VALUE = {"--silent", "--show-error", "--head", "--fail", "--location"}
CURL_LONG_WITH_VALUE = {"--max-time", "--header"}
CURL_SHORT_NO_VALUE = set("sSIfL")
CURL_SHORT_WITH_VALUE = {"-m", "-H"}
URL = re.compile(r"https://[A-Za-z0-9.-]+(?::\d+)?(?:/[^\s]*)?")


def check_curl(args):
    urls, i = 0, 0
    while i < len(args):
        a = args[i]
        if a.startswith("--"):
            name = a.split("=", 1)[0]
            if name in CURL_LONG_NO_VALUE and "=" not in a:
                pass
            elif name in CURL_LONG_WITH_VALUE:
                if "=" not in a:
                    i += 1
            else:
                return False
        elif a.startswith("-"):
            if a in CURL_SHORT_WITH_VALUE:
                i += 1
            elif len(a) > 1 and set(a[1:]) <= CURL_SHORT_NO_VALUE:
                pass
            else:
                return False
        else:
            if not URL.fullmatch(a):
                return False
            urls += 1
        i += 1
    return urls == 1


# ---- aws: a closed list of read-only service/operation pairs ----
AWS_GLOBAL_WITH_VALUE = {"--profile", "--region", "--output", "--query"}
AWS_GLOBAL_NO_VALUE = {"--no-paginate", "--no-cli-pager"}
AWS_READ_OPS = {
    ("s3", "ls"),
    ("s3api", "head-object"),
    ("s3api", "get-bucket-policy"),
    ("s3api", "get-public-access-block"),
    ("s3api", "get-bucket-encryption"),
    ("cloudfront", "get-distribution"),
    ("cloudfront", "get-distribution-config"),
    ("cloudfront", "list-distributions"),
    ("cloudfront", "list-invalidations"),
    ("cloudfront", "get-invalidation"),
    ("wafv2", "get-web-acl"),
    ("wafv2", "get-web-acl-for-resource"),
    ("sts", "get-caller-identity"),
}
AWS_ARG = re.compile(r"[A-Za-z0-9_./:@=+,\-]+")


def check_aws(args):
    rest, i = [], 0
    while i < len(args):
        a = args[i]
        if a in AWS_GLOBAL_WITH_VALUE:
            if i + 1 >= len(args):
                return False
            i += 2
            continue
        if a in AWS_GLOBAL_NO_VALUE:
            i += 1
            continue
        rest.append(a)
        i += 1
    if len(rest) < 2 or (rest[0], rest[1]) not in AWS_READ_OPS:
        return False
    # remaining tokens: plain values and long options only, never an input-file flag
    return all(AWS_ARG.fullmatch(t) for t in rest[2:]) and not any(
        t in ("--cli-input-json", "--cli-input-yaml", "--generate-cli-skeleton") for t in rest[2:])


# ---- python: only the shared read-only helper scripts/portable.py now|sha256|dirhash ----
PORTABLE = re.compile(r"(?:[A-Za-z0-9_.:/\-]*/)?coordinating-agent-handoffs/scripts/portable\.py")


def check_python(args):
    if not args or not PORTABLE.fullmatch(args[0]) or ".." in args[0].split("/"):
        return False
    sub = args[1:]
    if sub == ["now"]:
        return True
    return (len(sub) == 2 and sub[0] in ("sha256", "dirhash")
            and not sub[1].startswith("-") and ".." not in sub[1].split("/"))


PROFILES = {
    "static-site": {"curl": check_curl, "aws": check_aws,
                    "python": check_python, "python3": check_python, "py": check_python},
}


def decide(command, profile):
    if SHELL_SYNTAX.search(command):
        return "deny", "shell chaining, pipes, redirects, substitution and backslashes are not allowed"
    argv = shlex.split(command, posix=True)
    if not argv:
        return "deny", "empty command"
    check = PROFILES[profile].get(argv[0])
    if check and check(argv[1:]):
        return "allow", "allowlisted read-only command: " + argv[0]
    return "deny", "not on the read-only allowlist: " + argv[0]


def emit(decision, reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": decision,
        "permissionDecisionReason": reason,
    }}))
    return 0


def main(argv):
    profile = "static-site"
    if "--profile" in argv:
        profile = argv[argv.index("--profile") + 1]
    try:
        if profile not in PROFILES:
            return emit("deny", "unknown profile")
        payload = json.load(sys.stdin)
        if payload.get("tool_name") != "Bash":
            return emit("deny", "this hook only accepts Bash")
        decision, reason = decide(payload["tool_input"]["command"], profile)
    except Exception as exc:  # fail closed
        decision, reason = "deny", "hook error, denied: " + type(exc).__name__
    return emit(decision, reason)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
