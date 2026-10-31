#!/usr/bin/env python3
"""Gate command handler run by the openspec-gate workflow (the ONLY interpreter of user commands).

Usage (<repo-root> defaults to the current directory):
  gate_command.py evaluate [<repo-root>] --profile <yaml> [--apply]
      reads the issue_comment payload from the environment only - never from argv:
      COMMENT_BODY, COMMENT_AUTHOR, COMMENT_URL, COMMENT_ID, ISSUE_NUMBER, CREATED_AT
  gate_command.py recheck [<repo-root>] --profile <yaml> --gate E<n>
      reads ISSUE_NUMBER; exit 0 only when that change issue holds a confirmation by
      tracker.bot_login for the gate whose user comment still passes every check (approver,
      no bot marker, same issue, newer than the Stage value, Stage equals the gate); read-only
  gate_command.py check-patch <patch-file>
      exit 0 only when every path of a `git diff --binary` patch - both sides of renames/copies -
      is under openspec/, with no mode change, symlink or submodule (archive publish job)
  gate_command.py resolve-change [<repo-root>]
      reads ISSUE_TITLE and ISSUE_BODY; prints ``change=<id>`` (append it to $GITHUB_OUTPUT)

Grammar (first line of the comment, exact; the rest is quoted back verbatim, never interpreted):
  /approve E<n> | /reject E<n> <reason> | /accept delta-<nn> | /reject delta-<nn> <reason>
  /revise delta-<nn> <answer> | /answer escalation-<nn> <text>

A command is recorded only when: the author is in tracker.approvers and is not tracker.bot_login;
the body has no bot marker; the issue carries this tool's key marker and was created by a trusted
author (bot_login or an approver); a gate equals the change's current Stage field and the comment
is newer than that Stage value; a delta is proposed/revise and the comment is newer than its text;
an escalation is answered on its own open issue. On accept (with --apply) it adds the label
(gate:E<n>:approved|rejected or delta:<nn>:<verdict>), sets the Gate field (gates) and posts a
confirmation (bot marker + fenced YAML ``decision:`` + the user's text quoted). Otherwise it posts
a refusal with the reason - except for comments by the bot itself (loop guard), by anyone not in
tracker.approvers, and comments whose first word is not a known verb: those are ignored silently. Dry-run by default: writes print PLAN lines.

Exit codes: 0 handled (recorded, refused or ignored); 1 error; 3 tracker disabled.
Python 3.8+, standard library only. This script reads approvals for the workflow; agents never run it.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import _model as model  # noqa: E402
except RuntimeError as _exc:
    sys.stderr.write("error: %s\n" % _exc)
    sys.exit(1)
import _gh as gh  # noqa: E402
import gh_projects_sync as sync  # noqa: E402

lib = model.lib
ENV_KEYS = ("COMMENT_BODY", "COMMENT_AUTHOR", "COMMENT_URL", "COMMENT_ID", "ISSUE_NUMBER", "CREATED_AT")


class GateContext(object):
    """Minimal context compatible with the gh_projects_sync helpers."""

    def __init__(self, repo_root, profile_path, apply):
        self.repo_root = os.path.abspath(repo_root)
        self.apply = apply
        profile, errs = lib.load_profile(profile_path)
        if errs:
            raise sync.Failure("%s: %s" % (profile_path, "; ".join(errs)))
        self.profile = profile
        self.tracker = sync.load_tracker(self.repo_root, profile)
        self.repo = self.tracker["repo"]
        self.state = {}
        self.project = None

    def out(self, line):
        print(gh.redact(line))

    def warn(self, line):
        sys.stderr.write(gh.redact("warning: %s\n" % line))


def read_payload():
    missing = [k for k in ENV_KEYS if os.environ.get(k) in (None, "")]
    if missing:
        raise sync.Failure("missing environment variable(s): %s" % ", ".join(missing))
    p = {k.lower(): os.environ[k] for k in ENV_KEYS}
    if not p["issue_number"].isdigit() or not p["comment_id"].isdigit():
        raise sync.Failure("ISSUE_NUMBER and COMMENT_ID must be integers")
    return p


def issue_context(ctx, number):
    obs = sync.observe_issue(ctx, number, with_times=True)
    if obs is None:
        return {}, None
    change, obj = model.parse_key_marker(obs["body"])
    issue = {"change": change, "obj": obj, "labels": obs["labels"], "state": obs["state"],
             "created_at": obs["created_at"], "stage": obs["fields"].get("Stage"),
             "stage_updated_at": obs["times"].get("Stage"),
             "trusted": bool(change) and model.trusted_author(obs["author"], ctx.tracker)
             and bool(obs["author"])}
    return issue, obs


def delta_context(ctx, number, change, nn):
    key = "delta:spec-delta-%s" % nn
    for c in gh.rest("GET", "repos/%s/issues/%s/comments?per_page=100" % (ctx.repo, number),
                     paginate=True):
        cchange, obj = model.parse_key_marker((c or {}).get("body"))
        if cchange != change or obj != key:
            continue
        if not model.trusted_author((c.get("user") or {}).get("login"), ctx.tracker):
            continue
        m = model._DELTA_STATUS_RE.search(c.get("body") or "")
        return {"status": m.group(1) if m else None, "updated_at": c.get("updated_at")}
    return None


def record(ctx, w, cmd, payload, issue, obs, decision):
    """Apply an accepted command: label, Gate field, confirmation comment."""
    number = payload["issue_number"]
    label = decision["label"]
    if label and cmd["kind"] == "delta":
        w.call(["label", "create", label, "-R", ctx.repo, "--color", model.DELTA_LABEL_COLOR,
                "--description", "spec-delta answer recorded by openspec-github", "--force"],
               json_out=False)
    if label:
        w.rest("POST", "repos/%s/issues/%s/labels" % (ctx.repo, number), {"labels": [label]})
    if cmd["kind"] == "gate" and obs and obs.get("item_id") and obs["field_ids"].get("Gate") is None:
        gate_field = ((ctx.project or {}).get("fields") or {}).get("Gate")
        obs["field_ids"]["Gate"] = gate_field.get("id") if gate_field else None
    if cmd["kind"] == "gate" and obs and obs.get("item_id") and obs["field_ids"].get("Gate"):
        w.call(["project", "item-edit", "--id", obs["item_id"], "--project-id", ctx.project["id"],
                "--field-id", obs["field_ids"]["Gate"], "--text",
                "%s %s" % (cmd["target"], cmd["verdict"])], json_out=False)
    ctx_eval = {"issue": issue, "author": payload["comment_author"], "comment_url": payload["comment_url"],
                "comment_id": payload["comment_id"], "created_at": payload["created_at"]}
    body = model.confirmation_body(model.decision_of(cmd, ctx_eval), payload["comment_body"])
    w.rest("POST", "repos/%s/issues/%s/comments" % (ctx.repo, number), {"body": body})


def refuse(ctx, w, payload, reason):
    ctx.out("REFUSED: %s" % reason)
    body = model.refusal_body(reason, payload["comment_author"])
    w.rest("POST", "repos/%s/issues/%s/comments" % (ctx.repo, payload["issue_number"]), {"body": body})
    return sync.EXIT_OK


def cmd_evaluate(args):
    ctx = GateContext(args.repo_root, args.profile, args.apply)
    payload = read_payload()
    t = ctx.tracker
    if t.get("approval_source", "chat") == "chat":
        ctx.out("IGNORED: approval_source is chat")
        return sync.EXIT_OK
    if t.get("bot_login") and payload["comment_author"] == t["bot_login"]:
        ctx.out("IGNORED: comment by the bot login")
        return sync.EXIT_OK
    if payload["comment_author"] not in (t.get("approvers") or []):
        ctx.out("IGNORED: %s is not in tracker.approvers" % payload["comment_author"])
        return sync.EXIT_OK
    try:
        cmd = model.parse_command(payload["comment_body"])
    except model.CommandError as exc:
        cmd = exc
    if cmd is None:
        ctx.out("IGNORED: first line is not a gate command")
        return sync.EXIT_OK
    sync.preflight(ctx)
    w = sync.Writer(ctx)
    if isinstance(cmd, model.CommandError):
        return refuse(ctx, w, payload, str(cmd))
    ctx.project = sync.resolve_project(ctx)
    if ctx.project is None:
        raise sync.Failure("project %s/%s not found" % (t["owner"], t["project_number"]))
    issue, obs = issue_context(ctx, payload["issue_number"])
    delta = None
    if cmd["kind"] == "delta" and issue.get("change"):
        delta = delta_context(ctx, payload["issue_number"], issue["change"], cmd["target"])
    decision = model.evaluate(cmd, {"author": payload["comment_author"], "body": payload["comment_body"],
                                    "created_at": payload["created_at"], "tracker": t,
                                    "issue": issue, "delta": delta})
    if not decision["ok"]:
        if decision["silent"]:
            ctx.out("IGNORED: %s" % decision["reason"])
            return sync.EXIT_OK
        return refuse(ctx, w, payload, decision["reason"])
    record(ctx, w, cmd, payload, issue, obs, decision)
    ctx.out("ACCEPTED: %s %s by %s" % (cmd["verdict"], cmd["target"], payload["comment_author"]))
    return sync.EXIT_OK


def cmd_recheck(args):
    """Re-verify a gate approval before acting on its label (archive workflow, audit F5/F12)."""
    ctx = GateContext(args.repo_root, args.profile, False)
    number = os.environ.get("ISSUE_NUMBER", "")
    if not number.isdigit():
        raise sync.Failure("ISSUE_NUMBER must be set to the issue number")
    if ctx.tracker.get("approval_source", "chat") == "chat":
        raise sync.Failure("approval_source is chat: a GitHub label is not an approval")
    sync.preflight(ctx)
    ctx.project = sync.resolve_project(ctx)
    if ctx.project is None:
        raise sync.Failure("project %s/%s not found" % (ctx.tracker["owner"], ctx.tracker["project_number"]))
    issue, _ = issue_context(ctx, number)
    comments = gh.rest("GET", "repos/%s/issues/%s/comments?per_page=100" % (ctx.repo, number), paginate=True)
    ok, reasons = model.recheck_gate(args.gate, comments, lambda cid: sync.fetch_comment(ctx, cid),
                                     ctx.tracker, issue, ctx.repo, int(number))
    for reason in reasons:
        ctx.out("%s: %s" % ("RECHECK OK" if ok else "RECHECK FAILED", reason))
    return sync.EXIT_OK if ok else sync.EXIT_ERROR


def cmd_check_patch(args):
    """Refuse an archive patch that leaves openspec/, renames from outside or changes modes (N2)."""
    with open(args.patch, encoding="utf-8", errors="replace") as fh:
        problems = model.check_patch(fh.read())
    for p in problems:
        print("PATCH REFUSED: %s" % p)
    if not problems:
        print("PATCH OK")
    return sync.EXIT_ERROR if problems else sync.EXIT_OK


def cmd_resolve_change(args):
    change = model.change_id_from_issue(os.environ.get("ISSUE_TITLE", ""), os.environ.get("ISSUE_BODY", ""))
    if not change:
        raise sync.Failure("the issue is not an openspec-github change issue")
    if not os.path.isdir(os.path.join(os.path.abspath(args.repo_root), "openspec", "changes", change)):
        raise sync.Failure("openspec/changes/%s does not exist on this ref" % change)
    print("change=%s" % change)
    return sync.EXIT_OK


def main(argv=None):
    ap = sync.HintingParser(prog="gate_command.py",
                            description="Evaluate one gate command from an issue comment (Actions).")
    sub = ap.add_subparsers(dest="command", parser_class=sync.HintingParser)
    root_help = "repository root containing openspec/ (default: the current directory)"
    p = sub.add_parser("evaluate", help="evaluate the comment in COMMENT_* / ISSUE_NUMBER / CREATED_AT",
                       epilog=sync.PROFILE_HINT)
    p.add_argument("repo_root", nargs="?", default=".", help=root_help)
    p.add_argument("--profile", required=True)
    p.add_argument("--apply", action="store_true", help="post labels/comments (default: dry-run)")
    c = sub.add_parser("recheck", help="exit 0 only when gate --gate of the change issue ISSUE_NUMBER has a "
                       "bot-confirmed approval that still passes every check (read-only)",
                       epilog=sync.PROFILE_HINT)
    c.add_argument("repo_root", nargs="?", default=".", help=root_help)
    c.add_argument("--profile", required=True)
    c.add_argument("--gate", required=True, choices=model.GATES)
    k = sub.add_parser("check-patch", help="exit 0 only when every path of a git diff patch (both sides "
                       "of renames/copies) is under openspec/ with regular file modes")
    k.add_argument("patch")
    r = sub.add_parser("resolve-change", help="print change=<id> from ISSUE_TITLE / ISSUE_BODY")
    r.add_argument("repo_root", nargs="?", default=".", help=root_help)
    args = ap.parse_args(argv)
    if not args.command:
        ap.print_help()
        return sync.EXIT_ERROR
    handlers = {"evaluate": cmd_evaluate, "recheck": cmd_recheck, "resolve-change": cmd_resolve_change,
                "check-patch": cmd_check_patch}
    try:
        return handlers[args.command](args)
    except sync.Disabled:
        print("tracker disabled")
        return sync.EXIT_DISABLED
    except sync.Failure as exc:
        sys.stderr.write(gh.redact("error: %s\n" % exc))
        return sync.EXIT_ERROR
    except gh.GhError as exc:
        sys.stderr.write("error: %s\n" % exc)
        return sync.EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
