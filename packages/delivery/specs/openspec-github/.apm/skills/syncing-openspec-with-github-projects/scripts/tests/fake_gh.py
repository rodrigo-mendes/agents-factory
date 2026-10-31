#!/usr/bin/env python3
"""Offline stand-in for the GitHub CLI used by the tests (no network, no real gh).

Run as an executable: ``python fake_gh.py <gh args...>``. Environment:

  FAKE_GH_LOG     JSON-lines file; every call appends {"argv": [...], "stdin": "..."}
  FAKE_GH_SCRIPT  JSON file: {"overrides": [{match, contains, stdout, stderr, code}], "sim": {...}}
                  * overrides are tried first: ``match`` is a list of regexes that must fullmatch
                    the leading argv items, ``contains`` substrings that must all occur in the
                    joined argv + stdin; ``stdout`` (string or JSON value), ``stderr``, ``code``.
                  * otherwise a tiny in-memory GitHub simulates the REST/GraphQL calls the scripts
                    make (issues, labels, comments, sub-issues, a Project v2 with fields and items).
                    Its state is persisted in ``<FAKE_GH_SCRIPT>.state.json`` between calls.

The module also offers helpers for the tests: ``FakeGh`` (sets the environment, reads the log,
edits the simulated state) and ``write_wrappers`` (a ``gh.cmd`` / ``gh`` launcher so the fake can
be put first on PATH, as a real executable would be).
"""
import datetime
import json
import os
import re
import sys

HERE = os.path.abspath(__file__)
MUTATING_GH = (("project", "item-edit"), ("project", "field-create"), ("label", "create"),
               ("issue", "create"), ("issue", "edit"), ("issue", "close"), ("issue", "comment"))


# ============================================================ simulator

def _now(sim):
    sim["clock"] = sim.get("clock", 0) + 1
    base = datetime.datetime(2026, 11, 5, 10, 0, 0) + datetime.timedelta(seconds=sim["clock"])
    return base.strftime("%Y-%m-%dT%H:%M:%SZ")


def _repo_issue_path(path):
    m = re.match(r"^repos/([^/]+/[^/?]+)/issues(?:/(\d+))?(?:/(labels|comments|sub_issues)(?:/([^?]+))?)?(?:\?.*)?$", path)
    return m.groups() if m else None


def _issue_json(sim, iss):
    return {"number": iss["number"], "id": iss["id"], "node_id": iss["node_id"],
            "html_url": "https://github.com/%s/issues/%d" % (sim["repo"], iss["number"]),
            "title": iss["title"], "body": iss["body"], "state": iss["state"],
            "state_reason": iss.get("state_reason"), "user": {"login": iss["author"]},
            "labels": [{"name": l} for l in iss["labels"]], "created_at": iss["created_at"]}


def _comment_json(sim, c):
    return {"id": c["id"], "body": c["body"], "user": {"login": c["author"]},
            "created_at": c["created_at"], "updated_at": c["updated_at"],
            "issue_url": "https://api.github.com/repos/%s/issues/%d" % (sim["repo"], c["issue"]),
            "html_url": "https://github.com/%s/issues/%d#issuecomment-%d" % (sim["repo"], c["issue"], c["id"])}


def _rest(sim, method, path, body):
    parts = _repo_issue_path(path)
    if path.startswith("repos/") and "/labels?" in path and "/issues" not in path:
        return [[{"name": l} for l in sim["labels"]]]
    if parts is None:
        return None, "fake gh: unsupported REST path %s" % path, 1
    _, number, sub, extra = parts
    issues = sim["issues"]
    if number is None and sub is None and method == "POST":
        n = sim["next_issue"]
        sim["next_issue"] += 1
        iss = {"number": n, "id": 5000 + n, "node_id": "I_%d" % n, "title": body["title"],
               "body": body.get("body", ""), "state": "open", "labels": list(body.get("labels", [])),
               "author": sim["viewer"], "created_at": _now(sim), "parent": None}
        issues[str(n)] = iss
        return _issue_json(sim, iss)
    if number is None and sub == "comments" and extra and method in ("GET", "PATCH"):
        c = sim["comments"].get(extra)
        if c is None:
            return None, "gh: Not Found (HTTP 404)", 1
        if method == "PATCH":
            if c["author"] != sim["viewer"]:
                return None, "gh: Resource not accessible (HTTP 403)", 1
            c["body"] = body["body"]
            c["updated_at"] = _now(sim)
        return _comment_json(sim, c)
    if number is None and method == "GET":
        label = re.search(r"labels=([^&]+)", path)
        found = [_issue_json(sim, i) for _, i in sorted(issues.items(), key=lambda kv: int(kv[0]))
                 if not label or label.group(1) in i["labels"]]
        return [found]
    iss = issues.get(number)
    if iss is None:
        return None, "gh: Not Found (HTTP 404)", 1
    if sub is None and method == "PATCH":
        for k in ("title", "body", "state", "state_reason"):
            if k in body:
                iss[k] = body[k]
        return _issue_json(sim, iss)
    if sub is None and method == "GET":
        return _issue_json(sim, iss)
    if sub == "labels" and method == "POST":
        for l in body["labels"]:
            if l not in iss["labels"]:
                iss["labels"].append(l)
        return [{"name": l} for l in iss["labels"]]
    if sub == "labels" and method == "DELETE":
        iss["labels"] = [l for l in iss["labels"] if l != extra]
        return [{"name": l} for l in iss["labels"]]
    if sub == "sub_issues" and method == "POST":
        child = [i for i in issues.values() if i["id"] == body["sub_issue_id"]]
        if not child:
            return None, "gh: sub_issue_id not found (HTTP 422)", 1
        child[0]["parent"] = iss["number"]
        return _issue_json(sim, iss)
    if sub == "sub_issues" and method == "GET":
        return [[_issue_json(sim, i) for i in issues.values() if i.get("parent") == iss["number"]]]
    if sub == "comments" and method == "POST":
        cid = sim["next_comment"]
        sim["next_comment"] += 1
        ts = _now(sim)
        c = {"id": cid, "issue": iss["number"], "body": body["body"], "author": sim["viewer"],
             "created_at": ts, "updated_at": ts}
        sim["comments"][str(cid)] = c
        return _comment_json(sim, c)
    if sub == "comments" and method == "GET":
        return [[_comment_json(sim, c) for _, c in sorted(sim["comments"].items(), key=lambda kv: int(kv[0]))
                 if c["issue"] == iss["number"]]]
    return None, "fake gh: unsupported %s %s" % (method, path), 1


def _graphql(sim, query, vars_):
    proj = sim["project"]
    if "addProjectV2ItemById" in query:
        content = vars_["content"]
        for item in sim["items"].values():
            if item["content"] == content:
                return {"data": {"addProjectV2ItemById": {"item": {"id": item["id"]}}}}
        iid = "PVTI_%d" % (len(sim["items"]) + 1)
        sim["items"][iid] = {"id": iid, "content": content, "values": {}}
        return {"data": {"addProjectV2ItemById": {"item": {"id": iid}}}}
    if "projectV2(number" in query:
        root = "organization" if "organization(login" in query else "user"
        if sim.get("project_missing") or vars_.get("owner") != sim["owner"]                 or root != sim.get("owner_type", "organization"):
            return {"data": {root: {"projectV2": None}}}
        nodes = []
        for f in proj["fields"]:
            node = {"id": f["id"], "name": f["name"]}
            if f.get("options") is not None:
                node["options"] = [{"id": o[0], "name": o[1]} for o in f["options"]]
            nodes.append(node)
        return {"data": {root: {"projectV2": {"id": proj["id"], "title": "Board", "fields": {"nodes": nodes}}}}}
    if "repository(owner" in query:
        iss = sim["issues"].get(str(vars_["number"]))
        if iss is None:
            return {"data": {"repository": {"issue": None}},
                    "errors": [{"message": "Could not resolve to an issue"}]}
        items = []
        for item in sim["items"].values():
            if item["content"] != iss["node_id"]:
                continue
            values = []
            for fid, v in item["values"].items():
                field = [f for f in proj["fields"] if f["id"] == fid][0]
                node = {"field": {"id": fid, "name": field["name"]}}
                if "updatedAt" in query:
                    node["updatedAt"] = v["updatedAt"]
                if field.get("options") is not None:
                    node["name"] = [o[1] for o in field["options"] if o[0] == v["value"]][0]
                else:
                    node["text"] = v["value"]
                values.append(node)
            items.append({"id": item["id"], "project": {"id": proj["id"]}, "fieldValues": {"nodes": values}})
        node = {"id": iss["node_id"], "databaseId": iss["id"], "number": iss["number"],
                "url": "https://github.com/%s/issues/%d" % (sim["repo"], iss["number"]),
                "title": iss["title"], "body": iss["body"], "state": iss["state"].upper(),
                "createdAt": iss["created_at"], "author": {"login": iss["author"]},
                "labels": {"nodes": [{"name": l} for l in iss["labels"]]},
                "projectItems": {"nodes": items}}
        return {"data": {"repository": {"issue": node}}}
    return None


def _flag(argv, name):
    return argv[argv.index(name) + 1] if name in argv else None


def _project_cmd(sim, argv):
    if argv[1] == "item-edit":
        item = sim["items"][_flag(argv, "--id")]
        value = _flag(argv, "--single-select-option-id") or _flag(argv, "--text")
        item["values"][_flag(argv, "--field-id")] = {"value": value, "updatedAt": _now(sim)}
        return ""
    if argv[1] == "field-create":
        name = _flag(argv, "--name")
        opts = _flag(argv, "--single-select-options")
        fid = "F_%s" % name
        field = {"id": fid, "name": name}
        if opts:
            field["options"] = [["O_%s_%s" % (name, o), o] for o in opts.split(",")]
        sim["project"]["fields"].append(field)
        return {"id": fid, "name": name}
    return None


def simulate(sim, argv, stdin):
    """Return (stdout, stderr, code)."""
    if argv[:1] == ["--version"]:
        return "gh version %s (2026-10-26)\nhttps://github.com/cli/cli/releases/tag/v%s\n" % (
            sim.get("version", "2.103.3"), sim.get("version", "2.103.3")), "", 0
    if argv[:2] == ["auth", "status"]:
        return "", "", 0
    if argv[:2] == ["label", "create"]:
        if argv[2] not in sim["labels"]:
            sim["labels"].append(argv[2])
        return "", "", 0
    if argv[:1] == ["project"]:
        res = _project_cmd(sim, argv)
        return (json.dumps(res) if isinstance(res, dict) else ""), "", 0
    if argv[:2] == ["api", "user"]:
        if sim.get("viewer_is_app"):
            return "", "gh: Resource not accessible by integration (HTTP 403)", 1
        if "--jq" in argv:
            return sim["viewer"] + "\n", "", 0
        return json.dumps({"login": sim["viewer"]}), "", 0
    if argv[:2] == ["api", "graphql"] and any("viewer" in a for a in argv if a.startswith("query=")):
        if sim.get("viewer_is_app"):
            return json.dumps({"errors": [{"message": "not available"}]}), "gh: not available\n", 1
        return json.dumps({"data": {"viewer": {"login": sim["viewer"]}}}), "", 0
    if argv[:2] == ["api", "graphql"]:
        query = [a[6:] for a in argv if a.startswith("query=")][0]
        vars_ = {}
        for i, a in enumerate(argv):
            if a in ("-f", "-F") and not argv[i + 1].startswith("query="):
                k, _, v = argv[i + 1].partition("=")
                vars_[k] = int(v) if a == "-F" else v
        doc = _graphql(sim, query, vars_)
        if doc is None:
            return "", "fake gh: unsupported GraphQL", 1
        if doc.get("errors"):
            return json.dumps(doc), "gh: %s\n" % doc["errors"][0]["message"], 1
        return json.dumps(doc), "", 0
    if argv[:1] == ["api"]:
        method = _flag(argv, "-X") or "GET"
        path = [a for a in argv[1:] if not a.startswith("-") and a not in (method,)][0]
        body = json.loads(stdin) if stdin else None
        res = _rest(sim, method, path, body)
        if isinstance(res, tuple):
            return "", res[1], res[2]
        if "--slurp" not in argv and isinstance(res, list) and res and isinstance(res[0], list):
            res = res[0]
        return json.dumps(res), "", 0
    return "", "fake gh: unsupported command %s" % " ".join(argv), 1


def _match(entry, argv, stdin):
    pats = entry.get("match") or []
    if len(pats) > len(argv):
        return False
    for pat, arg in zip(pats, argv):
        if not re.fullmatch(pat, arg, re.S):
            return False
    joined = " ".join(argv) + "\n" + (stdin or "")
    return all(s in joined for s in entry.get("contains") or [])


def main(argv):
    stdin = "" if sys.stdin is None or sys.stdin.isatty() else sys.stdin.read()
    log = os.environ.get("FAKE_GH_LOG")
    if log:
        with open(log, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"argv": argv, "stdin": stdin}) + "\n")
    script_path = os.environ.get("FAKE_GH_SCRIPT")
    script = {}
    if script_path and os.path.isfile(script_path):
        with open(script_path, encoding="utf-8") as fh:
            script = json.load(fh)
    for entry in script.get("overrides") or []:
        if _match(entry, argv, stdin):
            out = entry.get("stdout", "")
            sys.stdout.write(out if isinstance(out, str) else json.dumps(out))
            sys.stderr.write(entry.get("stderr", ""))
            return int(entry.get("code", 0))
    state_path = (script_path or "fake_gh") + ".state.json"
    if os.path.isfile(state_path):
        with open(state_path, encoding="utf-8") as fh:
            sim = json.load(fh)
    else:
        sim = script.get("sim") or default_sim()
    out, err, code = simulate(sim, argv, stdin)
    with open(state_path, "w", encoding="utf-8") as fh:
        json.dump(sim, fh)
    sys.stdout.write(out)
    sys.stderr.write(err)
    return code


# ============================================================ helpers for the tests

def default_sim(viewer="openspec-bot[bot]", status_options=("Todo", "In Progress", "Blocked", "Done"),
                with_fields=True):
    fields = [{"id": "F_Status", "name": "Status",
               "options": [["O_Status_%d" % i, n] for i, n in enumerate(status_options)]},
              {"id": "F_Title", "name": "Title"}]
    if with_fields:
        fields += [{"id": "F_Stage", "name": "Stage", "options": [["O_Stage_E%d" % n, "E%d" % n] for n in range(1, 10)]},
                   {"id": "F_Kind", "name": "Kind", "options": [["O_Kind_%s" % k, k] for k in
                                                                ("change", "task", "adr", "escalation")]},
                   {"id": "F_Change", "name": "Change"}, {"id": "F_Gate", "name": "Gate"}]
    return {"repo": "acme/shop", "owner": "acme", "viewer": viewer, "version": "2.103.3",
            "project": {"id": "PVT_1", "fields": fields}, "issues": {}, "comments": {}, "items": {},
            "labels": [], "next_issue": 101, "next_comment": 9001, "clock": 0}


def is_mutating(call):
    argv = call["argv"]
    if tuple(argv[:2]) in MUTATING_GH:
        return True
    if argv[:2] == ["api", "graphql"]:
        return any(a.startswith("query=mutation") for a in argv)
    if argv[:1] == ["api"]:
        return (_flag(argv, "-X") or "GET") != "GET"
    return False


class FakeGh(object):
    """Point the scripts at this fake for one test (use as ``with FakeGh(tmp) as fake:``)."""

    def __init__(self, tmpdir, sim=None, overrides=None):
        self.dir = tmpdir
        self.script = os.path.join(tmpdir, "fake_gh_script.json")
        self.log = os.path.join(tmpdir, "fake_gh_log.jsonl")
        self.state = self.script + ".state.json"
        with open(self.script, "w", encoding="utf-8") as fh:
            json.dump({"overrides": overrides or [], "sim": sim or default_sim()}, fh)
        self._saved = {}

    def env(self):
        return {"OPENSPEC_GITHUB_GH": HERE, "FAKE_GH_SCRIPT": self.script, "FAKE_GH_LOG": self.log,
                "OPENSPEC_GITHUB_WRITE_DELAY": "0", "OPENSPEC_GITHUB_BACKOFF_BASE": "0",
                "GH_TOKEN": "fake-token-value-123456"}

    def __enter__(self):
        for k, v in self.env().items():
            self._saved[k] = os.environ.get(k)
            os.environ[k] = v
        return self

    def __exit__(self, *exc):
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def calls(self):
        if not os.path.isfile(self.log):
            return []
        with open(self.log, encoding="utf-8") as fh:
            return [json.loads(l) for l in fh if l.strip()]

    def mutations(self):
        return [c for c in self.calls() if is_mutating(c)]

    def reset_log(self):
        if os.path.isfile(self.log):
            os.remove(self.log)

    def sim(self):
        if os.path.isfile(self.state):
            with open(self.state, encoding="utf-8") as fh:
                return json.load(fh)
        with open(self.script, encoding="utf-8") as fh:
            return json.load(fh)["sim"]

    def save_sim(self, sim):
        with open(self.state, "w", encoding="utf-8") as fh:
            json.dump(sim, fh)

    def set_overrides(self, overrides):
        with open(self.script, encoding="utf-8") as fh:
            doc = json.load(fh)
        doc["overrides"] = overrides
        with open(self.script, "w", encoding="utf-8") as fh:
            json.dump(doc, fh)


    def add_comment(self, issue, author, body):
        """Insert a comment into the simulated GitHub; returns (id, created_at)."""
        sim = self.sim()
        cid = sim["next_comment"]
        sim["next_comment"] += 1
        ts = _now(sim)
        sim["comments"][str(cid)] = {"id": cid, "issue": issue, "body": body, "author": author,
                                     "created_at": ts, "updated_at": ts}
        self.save_sim(sim)
        return cid, ts

    def set_viewer(self, login):
        sim = self.sim()
        sim["viewer"] = login
        self.save_sim(sim)


# ------------------------------------------------------------------ test support

TESTS = os.path.dirname(HERE)
SCRIPTS = os.path.dirname(TESTS)
FIXTURES = os.path.join(TESTS, "fixtures")
PROFILE = os.path.join(FIXTURES, "profiles", "quarkus-aws.yaml")
CHANGE = "list-tenant-items"
_DEFAULT_HANDOFF = os.path.normpath(os.path.join(
    SCRIPTS, "..", "..", "..", "..", "..", "handoff-core", ".apm", "skills",
    "coordinating-agent-handoffs", "scripts"))


def prepare_imports():
    """Make the scripts importable; default OPENSPEC_GITHUB_HANDOFF_SCRIPTS to the repo layout."""
    if not os.environ.get("OPENSPEC_GITHUB_HANDOFF_SCRIPTS") and             os.path.isfile(os.path.join(_DEFAULT_HANDOFF, "_handoff_lib.py")):
        os.environ["OPENSPEC_GITHUB_HANDOFF_SCRIPTS"] = _DEFAULT_HANDOFF
    if SCRIPTS not in sys.path:
        sys.path.insert(0, SCRIPTS)


def run_main(module, argv):
    """Run module.main(argv) in-process; return (code, stdout, stderr)."""
    import contextlib
    import io
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = module.main(argv)
        except SystemExit as exc:
            code = exc.code
    return code, out.getvalue(), err.getvalue()


def write_wrappers(bin_dir, python=None):
    """Create ``gh.cmd`` (Windows) and ``gh`` (POSIX) launchers for this fake in ``bin_dir``."""
    python = python or sys.executable
    os.makedirs(bin_dir, exist_ok=True)
    with open(os.path.join(bin_dir, "gh.cmd"), "w", encoding="utf-8", newline="\r\n") as fh:
        fh.write('@echo off\r\n"%s" "%s" %%*\r\n' % (python, HERE))
    posix = os.path.join(bin_dir, "gh")
    with open(posix, "w", encoding="utf-8", newline="\n") as fh:
        fh.write('#!/bin/sh\nexec "%s" "%s" "$@"\n' % (python, HERE))
    os.chmod(posix, 0o755)
    return bin_dir


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
