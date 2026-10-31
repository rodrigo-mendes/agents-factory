#!/usr/bin/env python3
"""Mirror one OpenSpec change into a GitHub Project v2 and read approvals back (gh 2.103.x).

Git is canonical; GitHub is a mirror plus an approval channel. Python 3.8+, stdlib only.

Usage (<repo-root> defaults to the current directory; --profile is required, see the hint in --help):
  gh_projects_sync.py bootstrap [<repo-root>] --change <id> --profile <yaml> [--apply]
                                [--install-workflows] [--vendor]
  gh_projects_sync.py push      [<repo-root>] --change <id> --profile <yaml> [--stage E<n>] [--apply]
  gh_projects_sync.py pull      [<repo-root>] --change <id> --profile <yaml> [--apply]   # ORCHESTRATOR ONLY
  gh_projects_sync.py close     [<repo-root>] --change <id> --profile <yaml> [--apply]
  gh_projects_sync.py status    [<repo-root>] --change <id> --profile <yaml>            # read-only

Contract
  * Dry-run by default: every planned write prints ``PLAN gh <args>`` (bodies go through stdin,
    shown as ``< stdin(N chars)``) and nothing is written - neither GitHub nor local files.
    ``--apply`` runs the writes (``APPLIED gh <args>``) and saves
    ``openspec/changes/<id>/handoff/github.yaml`` (ids cache, written only by this script).
    Read-only gh calls (queries, lists) run in both modes.
  * Tracker = profile ``tracker:`` block, overridden key by key by ``openspec/github-tracker.yaml``.
  * Preflight on every command: tracker valid; gh >= 2.94.0 (warning when not 2.103.x);
    ``gh auth status`` succeeds (its output is never printed, ``--show-token`` is never used);
    ``owner_type: user`` prints the classic-PAT risk warning. When ``approval_source`` is
    ``github`` or ``both``, the token's login (``gh api user``) must NOT be in
    ``tracker.approvers`` (family rule 13): use a machine-user or App token locally and approve in
    the browser. A login that cannot be read is refused, except inside GitHub Actions
    (``GITHUB_ACTIONS=true``, App installation tokens cannot call ``/user``).
  * Idempotent: ids come from github.yaml, or are adopted from existing issues/comments that carry
    this tool's key marker (fresh runners); a second ``push --apply`` with no git change issues no
    write. ``pull`` reads only confirmation comments authored by ``tracker.bot_login`` and
    re-checks the user comment each one refers to (author, approver list, bot marker, timestamps,
    same issue as the confirmation; gate and delta decisions only on the change issue); it is for
    the orchestrator, never for agents. ``pull`` refuses when the profile or
    ``openspec/github-tracker.yaml`` is not committed unchanged at HEAD, and prints the effective
    trust anchors as ``TRUST approvers=... bot_login=...``.
  * Exit codes: 0 ok; 1 error (stderr, with gh's stderr); 2 ``status`` found divergence;
    3 tracker disabled (``kind: none``).
"""
import argparse
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import _model as model  # noqa: E402
except RuntimeError as _exc:  # handoff-core scripts not found
    sys.stderr.write("error: %s\n" % _exc)
    sys.exit(1)
import _gh as gh  # noqa: E402
import _vendor  # noqa: E402

lib = model.lib
EXIT_OK, EXIT_ERROR, EXIT_DIVERGED, EXIT_DISABLED = 0, 1, 2, 3
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRACKER_FILE = os.path.join("openspec", "github-tracker.yaml")
USER_PAT_WARNING = (
    "WARNING: tracker.owner_type is 'user'. A user-owned project needs a classic personal access "
    "token with the 'project' and 'repo' scopes (fine-grained tokens cannot access user-owned "
    "projects). 'repo' grants broad access to every repository the user can reach; store it only "
    "as the OPENSPEC_PROJECT_PAT secret of a machine user and prefer an organization-owned project "
    "with a GitHub App.")

PROJECT_QUERY = """query($owner:String!,$number:Int!){ %s(login:$owner){ projectV2(number:$number){
  id title fields(first:50){ nodes{ ... on ProjectV2FieldCommon { id name }
  ... on ProjectV2SingleSelectField { options { id name } } } } } } }"""

ISSUE_QUERY = """query($owner:String!,$name:String!,$number:Int!){ repository(owner:$owner,name:$name){
  issue(number:$number){ id databaseId number url title body state createdAt author{ login }
  labels(first:100){ nodes{ name } }
  projectItems(first:20){ nodes{ id project{ id }
    fieldValues(first:30){ nodes{
      ... on ProjectV2ItemFieldSingleSelectValue { name %(ts)s field{ ... on ProjectV2FieldCommon { id name } } }
      ... on ProjectV2ItemFieldTextValue { text %(ts)s field{ ... on ProjectV2FieldCommon { id name } } }
  } } } } } } }"""

ADD_ITEM = """mutation($project:ID!,$content:ID!){ addProjectV2ItemById(input:{projectId:$project,
  contentId:$content}){ item{ id } } }"""


class Failure(Exception):
    """A user-facing error: printed on stderr, exit 1."""


class Disabled(Exception):
    """tracker.kind is none: exit 3."""


# ===================================================================== context

class Context(object):
    def __init__(self, args):
        self.args = args
        self.apply = bool(getattr(args, "apply", False))
        self.repo_root = os.path.abspath(args.repo_root)
        self.change = args.change
        if not model.CHANGE_ID_RE.match(self.change or ""):
            raise Failure("invalid change id %r" % self.change)
        self.change_dir = os.path.join(self.repo_root, "openspec", "changes", self.change)
        if not os.path.isdir(self.change_dir):
            raise Failure("change folder not found: %s" % self.change_dir)
        self.handoff_dir = os.path.join(self.change_dir, "handoff")
        self.profile_path = args.profile
        self.profile, errs = lib.load_profile(args.profile)
        if errs:
            raise Failure("%s: %s" % (args.profile, "; ".join(errs)))
        self.tracker = load_tracker(self.repo_root, self.profile)
        self.repo = self.tracker["repo"]
        self.state_path = os.path.join(self.handoff_dir, "github.yaml")
        text = read_text(self.state_path)
        try:
            self.state = model.load_state(text, self.tracker)
        except (ValueError, model._mini_yaml.YamlError) as exc:
            raise Failure("%s: %s" % (self.state_path, exc))
        mismatch = model.tracker_mismatch(self.state, self.tracker)
        if mismatch:
            raise Failure("github.yaml was written for another tracker (%s differ); move it away "
                          "before re-pointing the change" % ", ".join(mismatch))
        self.state["tracker"] = model.new_state(self.tracker)["tracker"]
        self.project = None

    def out(self, line):
        print(gh.redact(line))

    def warn(self, line):
        sys.stderr.write(gh.redact("warning: %s\n" % line))

    def save(self):
        if not self.apply:
            return
        os.makedirs(self.handoff_dir, exist_ok=True)
        tmp = self.state_path + ".tmp"
        with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(model.dump_state(self.state))
        os.replace(tmp, self.state_path)


def read_text(path):
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def load_tracker(repo_root, profile):
    """Resolve and validate the tracker; raise Disabled for kind none."""
    doc = None
    text = read_text(os.path.join(repo_root, TRACKER_FILE))
    if text is not None:
        try:
            doc = model._mini_yaml.load(text)
        except model._mini_yaml.YamlError as exc:
            raise Failure("%s: %s" % (TRACKER_FILE, exc))
    tracker, errs = model.resolve_tracker(profile.get("tracker"), doc)
    if tracker.get("kind") == "none":
        raise Disabled()
    if errs:
        raise Failure("tracker: %s" % "; ".join(errs))
    return tracker


APPROVER_LOGIN_ERROR = (
    "the gh login %r is in tracker.approvers while approval_source is %s: the bridge refuses to run "
    "with an approver's credential (an agent could post an approval in that person's name). Use a "
    "machine-user or GitHub App token in GH_TOKEN for the scripts, and approve in the browser")


def local_login():
    """Login of the credential gh uses, or None when it cannot be told (App installation tokens)."""
    try:
        login = gh.run(["api", "user", "--jq", ".login"], json=False, timeout=30).strip()
        if login:
            return login
    except gh.GhError:
        pass
    try:
        data = gh.graphql("query{ viewer{ login } }")
        return ((data.get("viewer") or {}).get("login")) or None
    except gh.GhError:
        return None


def check_operator(ctx):
    """Family rule 13: with GitHub approvals, never run under an approver's login (audit F1)."""
    source = ctx.tracker.get("approval_source", "chat")
    if source == "chat":
        return
    login = local_login()
    if login is None:
        # Spoofing GITHUB_ACTIONS=true locally is harmless here: only a token whose login
        # cannot be read (an App installation token) reaches this branch, and such a token
        # can never be one of tracker.approvers, so it cannot forge an approval (audit L1).
        if os.environ.get("GITHUB_ACTIONS") == "true":
            ctx.warn("cannot read the token's login (GitHub App installation token?); continuing in Actions")
            return
        raise Failure("cannot determine the gh login (gh api user failed); refusing to run while "
                      "approval_source is %s" % source)
    if login in (ctx.tracker.get("approvers") or []):
        raise Failure(APPROVER_LOGIN_ERROR % (login, source))


def preflight(ctx):
    _, warning = gh.check_version()
    if warning:
        ctx.warn(warning)
    gh.check_auth()
    check_operator(ctx)
    if ctx.tracker.get("owner_type") == "user":
        sys.stderr.write(USER_PAT_WARNING + "\n")


# ===================================================================== gh I/O helpers

class Writer(object):
    """Runs (``--apply``) or prints (dry-run) every mutating gh call."""

    def __init__(self, ctx):
        self.ctx = ctx
        self.count = 0

    def call(self, args, stdin=None, placeholder=None, json_out=True):
        self.count += 1
        shown = "gh %s%s" % (gh.format_args(args), " < stdin(%d chars)" % len(stdin) if stdin else "")
        if not self.ctx.apply:
            self.ctx.out("PLAN " + shown)
            return placeholder
        result = gh.run(args, stdin=stdin, mutating=True, json=json_out)
        self.ctx.out("APPLIED " + shown)
        return result

    def rest(self, method, path, body=None, placeholder=None):
        stdin = model.json.dumps(body) if body is not None else None
        return self.call(gh.rest_args(method, path, body), stdin, placeholder)

    def graphql(self, query, variables, placeholder=None):
        args = gh.graphql_args(query, variables)
        doc = self.call(args, placeholder=placeholder)
        return doc if not self.ctx.apply else gh.graphql_data(args, doc)


def owner_root(tracker):
    return "organization" if tracker["owner_type"] == "organization" else "user"


def resolve_project(ctx):
    """Query the project id, fields and options (read-only). Returns None when not found."""
    query = PROJECT_QUERY % owner_root(ctx.tracker)
    data = gh.graphql(query, {"owner": ctx.tracker["owner"], "number": ctx.tracker["project_number"]})
    node = ((data.get(owner_root(ctx.tracker)) or {}).get("projectV2"))
    if not node:
        return None
    fields = {}
    for f in ((node.get("fields") or {}).get("nodes") or []):
        if not f or not f.get("name"):
            continue
        entry = {"id": f.get("id")}
        if f.get("options") is not None:
            entry["options"] = {o.get("name"): o.get("id") for o in f["options"] if o}
        fields[f["name"]] = entry
    return {"id": node.get("id"), "fields": fields}


def ensure_project(ctx):
    if ctx.project is None:
        if ctx.state.get("project_id") and ctx.state.get("fields"):
            ctx.project = {"id": ctx.state["project_id"], "fields": ctx.state["fields"]}
        else:
            ctx.project = resolve_project(ctx)
            if ctx.project is None:
                raise Failure("project %s/%s not found (check tracker.owner, project_number, "
                              "owner_type and the token's project scope)"
                              % (ctx.tracker["owner"], ctx.tracker["project_number"]))
            ctx.state["project_id"] = ctx.project["id"]
            ctx.state["fields"] = ctx.project["fields"]
    return ctx.project


def observe_issue(ctx, number, with_times=False):
    """Observed issue state (title, body, labels, project item and its field values), or None."""
    owner, name = ctx.repo.split("/", 1)
    query = ISSUE_QUERY % {"ts": "updatedAt" if with_times else ""}
    try:
        data = gh.graphql(query, {"owner": owner, "name": name, "number": int(number)})
    except gh.GhError as exc:
        if "Could not resolve" in exc.stderr:
            return None
        raise
    node = ((data.get("repository") or {}).get("issue"))
    if not node:
        return None
    project_id = ctx.project["id"] if ctx.project else ctx.state.get("project_id")
    obs = {"issue": node.get("number"), "id": node.get("databaseId"), "node_id": node.get("id"),
           "url": node.get("url"), "title": node.get("title") or "", "body": node.get("body") or "",
           "state": str(node.get("state") or "").lower(), "created_at": node.get("createdAt"),
           "author": (node.get("author") or {}).get("login"),
           "labels": [l.get("name") for l in ((node.get("labels") or {}).get("nodes") or []) if l],
           "item_id": None, "fields": {}, "times": {}, "field_ids": {}}
    for item in ((node.get("projectItems") or {}).get("nodes") or []):
        if not item or (item.get("project") or {}).get("id") != project_id:
            continue
        obs["item_id"] = item.get("id")
        for v in ((item.get("fieldValues") or {}).get("nodes") or []):
            fname = ((v or {}).get("field") or {}).get("name")
            if not fname:
                continue
            obs["fields"][fname] = v.get("name") if "name" in v else v.get("text")
            obs["times"][fname] = v.get("updatedAt")
            obs["field_ids"][fname] = (v.get("field") or {}).get("id")
    return obs


def entry_from_observed(obs):
    return {"issue": obs["issue"], "id": obs["id"], "node_id": obs["node_id"], "url": obs["url"],
            "sha": model.body_sha(obs["title"], obs["body"]), "state": obs["state"],
            "labels": obs["labels"], "item_id": obs["item_id"], "fields": dict(obs["fields"])}


class Adopter(object):
    """Finds existing objects by key marker when github.yaml has no id (read-only calls)."""

    def __init__(self, ctx):
        self.ctx = ctx
        self._issues = None
        self._comments = {}
        self._subs = {}

    def _trusted(self, login):
        return model.trusted_author(login, self.ctx.tracker)

    def issue(self, key):
        if self._issues is None:
            self._issues = {}
            items = gh.rest("GET", "repos/%s/issues?labels=openspec&state=all&per_page=100"
                            % self.ctx.repo, paginate=True)
            for it in items:
                if not isinstance(it, dict) or it.get("pull_request"):
                    continue
                change, obj = model.parse_key_marker(it.get("body"))
                if change == self.ctx.change and self._trusted((it.get("user") or {}).get("login")):
                    self._issues.setdefault(obj, it.get("number"))
        number = self._issues.get(key)
        return observe_issue(self.ctx, number) if number else None

    def comment(self, issue_number, key):
        if issue_number not in self._comments:
            found = {}
            items = gh.rest("GET", "repos/%s/issues/%s/comments?per_page=100"
                            % (self.ctx.repo, issue_number), paginate=True)
            for c in items:
                change, obj = model.parse_key_marker((c or {}).get("body"))
                if change == self.ctx.change and self._trusted((c.get("user") or {}).get("login")):
                    found.setdefault(obj, c)
            self._comments[issue_number] = found
        return self._comments[issue_number].get(key)

    def is_sub_issue(self, parent_number, child_number):
        if parent_number not in self._subs:
            items = gh.rest("GET", "repos/%s/issues/%s/sub_issues?per_page=100"
                            % (self.ctx.repo, parent_number), paginate=True)
            self._subs[parent_number] = {i.get("number") for i in items if isinstance(i, dict)}
        return child_number in self._subs[parent_number]


# ===================================================================== inputs

def load_inputs(ctx, closing=False):
    texts = {}
    for name in ("proposal.md", "design.md", "tasks.md"):
        texts[name] = read_text(os.path.join(ctx.change_dir, name)) or ""
    records = lib.load_records(ctx.handoff_dir, ctx.profile) if os.path.isdir(ctx.handoff_dir) else []
    for rec in records:
        if rec.error is not None and rec.name != "status.md":
            ctx.warn("%s: %s (skipped)" % (rec.name, rec.error))
    adr_dir = str((ctx.profile.get("spec") or {}).get("adr_dir") or "openspec/specs/architecture/adr")
    adrs = []
    adr_path = os.path.join(ctx.repo_root, adr_dir)
    if os.path.isdir(adr_path):
        for name in sorted(os.listdir(adr_path)):
            info = model.adr_info(name, read_text(os.path.join(adr_path, name)) or "")
            if info:
                adrs.append(info)
    mentions = list(texts.values()) + [r.body + " " + str(r.fm) for r in records if r.error is None]
    return {"change": ctx.change, "repo": ctx.repo, "proposal": texts["proposal.md"],
            "tasks": texts["tasks.md"], "records": records,
            "adrs": model.referenced_adrs(adrs, mentions), "adr_dir": adr_dir.replace("\\", "/"),
            "status_md": read_text(os.path.join(ctx.handoff_dir, "status.md")) or "",
            "stage": getattr(ctx.args, "stage", None), "closing": closing,
            "approval_source": ctx.tracker.get("approval_source", "chat")}


# ===================================================================== push / close

def placeholder_issue(key):
    tag = "<%s>" % key
    return {"number": tag + "#", "id": tag + ".id", "node_id": tag + ".node_id",
            "html_url": tag + ".url"}


def sync_issue(ctx, w, adopt, desired):
    key = desired["key"]
    entry = model.get_entry(ctx.state, key)
    if not entry.get("issue"):
        obs = adopt.issue(key)
        if obs:
            entry.update(entry_from_observed(obs))
            parent = model.get_entry(ctx.state, desired["parent"]) if desired["parent"] else None
            if parent and isinstance(parent.get("issue"), int):
                entry["parent_linked"] = adopt.is_sub_issue(parent["issue"], entry["issue"])
            ctx.out("ADOPT %s -> #%s" % (key, entry["issue"]))
    if not entry.get("issue"):
        create_issue(ctx, w, desired, entry)
    else:
        update_issue(ctx, w, desired, entry)
    sync_state(ctx, w, desired, entry)
    link_parent(ctx, w, desired, entry)
    sync_item(ctx, w, desired, entry)


def create_issue(ctx, w, desired, entry):
    body = {"title": desired["title"], "body": desired["body"], "labels": desired["labels"]}
    res = w.rest("POST", "repos/%s/issues" % ctx.repo, body, placeholder_issue(desired["key"])) or {}
    entry.update({"issue": res.get("number"), "id": res.get("id"), "node_id": res.get("node_id"),
                  "url": res.get("html_url"), "sha": desired["sha"], "state": "open",
                  "labels": list(desired["labels"]), "fields": {}})


def update_issue(ctx, w, desired, entry):
    path = "repos/%s/issues/%s" % (ctx.repo, entry["issue"])
    if entry.get("sha") != desired["sha"]:
        w.rest("PATCH", path, {"title": desired["title"], "body": desired["body"]})
        entry["sha"] = desired["sha"]
    add, remove = model.label_edits(desired["labels"], entry.get("labels"))
    if add:
        w.rest("POST", path + "/labels", {"labels": add})
    for label in remove:
        w.call(["api", "-X", "DELETE", "%s/labels/%s" % (path, label)], json_out=False)
    if add or remove:
        entry["labels"] = sorted((set(entry.get("labels") or []) | set(add)) - set(remove))


def sync_state(ctx, w, desired, entry):
    if entry.get("state") == desired["state"]:
        return
    body = {"state": desired["state"]}
    if desired["state"] == "closed" and desired.get("reason"):
        body["state_reason"] = desired["reason"]
    w.rest("PATCH", "repos/%s/issues/%s" % (ctx.repo, entry["issue"]), body)
    entry["state"] = desired["state"]


def link_parent(ctx, w, desired, entry):
    if not desired["parent"] or entry.get("parent_linked"):
        return
    parent = model.get_entry(ctx.state, desired["parent"])
    w.rest("POST", "repos/%s/issues/%s/sub_issues" % (ctx.repo, parent.get("issue")),
           {"sub_issue_id": entry.get("id")})
    entry["parent_linked"] = True


def sync_item(ctx, w, desired, entry):
    project = ensure_project(ctx)
    if not entry.get("item_id"):
        data = w.graphql(ADD_ITEM, {"project": project["id"], "content": entry.get("node_id")},
                         placeholder={"addProjectV2ItemById": {"item": {"id": "<%s.item>" % desired["key"]}}})
        entry["item_id"] = (((data or {}).get("addProjectV2ItemById") or {}).get("item") or {}).get("id")
    current = entry.setdefault("fields", {})
    for name, value in model.field_edits(desired["fields"], current):
        flag = field_flag(ctx, project, name, value)
        if flag is None:
            continue
        w.call(["project", "item-edit", "--id", str(entry["item_id"]), "--project-id",
                str(project["id"]), "--field-id", str(project["fields"][name]["id"])] + flag,
               json_out=False)
        current[name] = value


def field_flag(ctx, project, name, value):
    field = project["fields"].get(name)
    if not field:
        ctx.warn("project has no field %r; run bootstrap (value %r not set)" % (name, value))
        return None
    if "options" in field:
        oid = model.option_id(field, value)
        if oid is None:
            ctx.warn("field %s has no option %r; add it in the project settings (value not set)"
                     % (name, value))
            return None
        return ["--single-select-option-id", str(oid)]
    return ["--text", str(value)]


def sync_comment(ctx, w, adopt, desired):
    key = desired["key"]
    entry = model.get_entry(ctx.state, key)
    issue_number = model.get_entry(ctx.state, desired["issue"]).get("issue")
    if not entry.get("comment_id"):
        found = adopt.comment(issue_number, key) if isinstance(issue_number, int) else None
        if found:
            entry.update({"comment_id": found.get("id"), "sha": model.body_sha("", found.get("body"))})
            ctx.out("ADOPT %s -> comment %s" % (key, entry["comment_id"]))
    if not entry.get("comment_id"):
        res = w.rest("POST", "repos/%s/issues/%s/comments" % (ctx.repo, issue_number),
                     {"body": desired["body"]}, {"id": "<%s.comment>" % key}) or {}
        entry.update({"comment_id": res.get("id"), "sha": desired["sha"]})
    elif entry.get("sha") != desired["sha"]:
        w.rest("PATCH", "repos/%s/issues/comments/%s" % (ctx.repo, entry["comment_id"]),
               {"body": desired["body"]})
        entry["sha"] = desired["sha"]
    if key == "summary":
        model.set_summary(ctx.state, entry)


def cmd_push(ctx, closing=False):
    ensure_project(ctx)
    desired = model.desired_state(load_inputs(ctx, closing))
    w = Writer(ctx)
    adopt = Adopter(ctx)
    try:
        for issue in desired["issues"]:
            sync_issue(ctx, w, adopt, issue)
        for comment in desired["comments"]:
            sync_comment(ctx, w, adopt, comment)
    finally:
        ctx.save()
    verb = "applied" if ctx.apply else "planned"
    ctx.out("%s %d write(s); stage %s" % (verb, w.count, desired["stage"]))
    return EXIT_OK


# ===================================================================== status

def cmd_status(ctx):
    ensure_project(ctx)
    desired = model.desired_state(load_inputs(ctx))
    adopt = Adopter(ctx)
    diverged = 0
    for issue in desired["issues"]:
        entry = model.get_entry(ctx.state, issue["key"])
        obs = observe_issue(ctx, entry["issue"]) if entry.get("issue") else adopt.issue(issue["key"])
        for diff in model.compare_issue(issue, obs):
            diverged += 1
            ctx.out("DIVERGE %s: %s" % (issue["key"], diff))
    change_number = model.get_entry(ctx.state, "change").get("issue")
    for c in desired["comments"]:
        entry = model.get_entry(ctx.state, c["key"])
        found = None
        if entry.get("comment_id"):
            found = fetch_comment(ctx, entry["comment_id"])
        elif change_number:
            found = adopt.comment(change_number, c["key"])
        if found is None:
            diverged += 1
            ctx.out("DIVERGE %s: missing on GitHub" % c["key"])
        elif model.body_sha("", found.get("body")) != c["sha"]:
            diverged += 1
            ctx.out("DIVERGE %s: body differs" % c["key"])
    if diverged:
        ctx.out("%d divergence(s) between git and GitHub" % diverged)
        return EXIT_DIVERGED
    ctx.out("IN SYNC (stage %s)" % desired["stage"])
    return EXIT_OK


def fetch_comment(ctx, comment_id):
    try:
        return gh.rest("GET", "repos/%s/issues/comments/%s" % (ctx.repo, comment_id))
    except gh.GhError as exc:
        if "404" in exc.stderr or "Not Found" in exc.stderr:
            return None
        raise


# ===================================================================== pull

def uncommitted_reason(path):
    """None when ``path`` is committed and unchanged at HEAD; else why not (git status --porcelain)."""
    folder, name = os.path.split(os.path.abspath(path))
    try:
        proc = subprocess.run(["git", "-C", folder, "status", "--porcelain", "--", name],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8",
                              errors="replace", timeout=60)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return "cannot run git: %s" % exc
    if proc.returncode != 0:
        return "is not inside a git work tree (%s)" % proc.stderr.strip()
    if proc.stdout.strip():
        return "has uncommitted changes or is not committed (git status: %s)" % proc.stdout.strip().split()[0]
    return None


def check_trust_anchors(ctx):
    """Audit F7: pull reads approvers / bot_login only from committed, unmodified files."""
    files = [os.path.abspath(ctx.profile_path)]
    tracker_file = os.path.join(ctx.repo_root, TRACKER_FILE)
    if os.path.exists(tracker_file):
        files.append(tracker_file)
    for path in files:
        why = uncommitted_reason(path)
        if why:
            raise Failure("%s %s: pull reads its trust anchors (approvers, bot_login) only from files "
                          "committed at HEAD" % (path, why))
    ctx.out("TRUST approvers=%s bot_login=%s (from %s)" % (
        ",".join(ctx.tracker.get("approvers") or []), ctx.tracker.get("bot_login"),
        ", ".join(p.replace("\\", "/") for p in files)))


def cmd_pull(ctx):
    t = ctx.tracker
    if t.get("approval_source", "chat") == "chat":
        raise Failure("approval_source is chat: approvals are taken in chat, pull refuses")
    check_trust_anchors(ctx)
    change = model.get_entry(ctx.state, "change")
    if not change.get("issue"):
        ensure_project(ctx)
        obs = Adopter(ctx).issue("change")
        if obs:
            change.update(entry_from_observed(obs))
    if not change.get("issue"):
        raise Failure("change issue not found; run push first")
    numbers = [change["issue"]] + [e.get("issue") for e in (ctx.state.get("escalations") or {}).values()
                                   if isinstance(e, dict) and isinstance(e.get("issue"), int)]
    status_path = os.path.join(ctx.handoff_dir, "status.md")
    status_text = read_text(status_path) or ""
    new_lines = []
    pulled = ctx.state.setdefault("pulled", {})
    for number in numbers:
        for conf in gh.rest("GET", "repos/%s/issues/%s/comments?per_page=100" % (ctx.repo, number),
                            paginate=True):
            line = pull_one(ctx, conf, change, status_text, pulled, number)
            if line:
                new_lines.append(line)
                status_text = model.append_approval(status_text, line)
    if new_lines and ctx.apply:
        with open(status_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(status_text)
    for line in new_lines:
        ctx.out(("APPROVAL " if ctx.apply else "PLAN append status.md ## Approvals: ") + line)
    ctx.save()
    ctx.out("pull: %d approval line(s) %s" % (len(new_lines), "written" if ctx.apply else "planned"))
    return EXIT_OK


def pull_one(ctx, conf, change, status_text, pulled, number):
    """Handle one comment found on issue ``number``; return an approval line to append, or None."""
    t = ctx.tracker
    if not isinstance(conf, dict) or (conf.get("user") or {}).get("login") != t.get("bot_login"):
        return None
    decision = model.parse_decision(conf.get("body"))
    if not decision or decision.get("change") != ctx.change:
        return None
    cid = str(conf.get("id"))
    if cid in pulled:
        return None
    user = fetch_comment(ctx, decision.get("comment_id"))
    reason = model.recheck_user_comment(decision, user, conf.get("created_at"), t, (ctx.repo, number))
    if reason is None and "escalation" not in decision and number != change.get("issue"):
        reason = "gate and delta decisions are valid only on the change issue"
    if reason:
        ctx.out("REFUSED confirmation %s: %s" % (cid, reason))
        return None
    if "gate" in decision and decision.get("verdict") == "approved":
        pulled[cid] = "gate=%s" % decision["gate"]
        if str(decision.get("comment_url")) in status_text:
            ctx.out("SKIP confirmation %s: already in status.md" % cid)
            return None
        return model.approval_line(decision, change.get("url"), user.get("body"))
    kind = "gate" if "gate" in decision else "delta" if "delta" in decision else "escalation"
    pulled[cid] = "%s:%s" % (decision.get(kind), decision.get("verdict"))
    out = dict(decision)
    out["user_said"] = user.get("body")
    out["confirmation_id"] = conf.get("id")
    ctx.out("DECISION " + model.to_json(out))
    return None


# ===================================================================== bootstrap

def cmd_bootstrap(ctx):
    w = Writer(ctx)
    project = resolve_project(ctx)
    if project is None:
        raise Failure("project %s/%s not found (check tracker.owner, project_number, owner_type and "
                      "the token's project scope)" % (ctx.tracker["owner"], ctx.tracker["project_number"]))
    created = create_fields(ctx, w, project)
    if created and ctx.apply:
        project = resolve_project(ctx) or project
    check_options(ctx, project)
    create_labels(ctx, w)
    ctx.state["project_id"] = project["id"]
    ctx.state["fields"] = project["fields"]
    try:
        if ctx.args.vendor:
            ctx.state["vendor"] = _vendor.install(ctx.repo_root, ctx.profile_path, ctx.apply,
                                                  model.handoff_scripts_dir(), ctx.out)
        if ctx.args.install_workflows:
            install_workflows(ctx)
    finally:
        ctx.save()
    ctx.out("bootstrap: %d write(s) %s" % (w.count, "applied" if ctx.apply else "planned"))
    return EXIT_OK


def create_fields(ctx, w, project):
    created = 0
    for name, dtype, options in model.FIELD_SPECS:
        if name in project["fields"]:
            continue
        args = ["project", "field-create", str(ctx.tracker["project_number"]), "--owner",
                ctx.tracker["owner"], "--name", name, "--data-type", dtype, "--format", "json"]
        if options:
            args += ["--single-select-options", ",".join(options)]
        w.call(args)
        created += 1
    return created


def check_options(ctx, project):
    wanted = {"Status": model.STATUS_VALUES}
    wanted.update({name: opts for name, _, opts in model.FIELD_SPECS if opts})
    for name, values in wanted.items():
        field = project["fields"].get(name)
        if not field or "options" not in field:
            if ctx.apply or name == "Status":
                ctx.warn("project field %s is missing or not single-select" % name)
            continue
        for value in values:
            if model.option_id(field, value) is None:
                ctx.warn("field %s has no option %r: add it in the project settings (the gh CLI "
                         "cannot add options to an existing field)" % (name, value))


def create_labels(ctx, w):
    existing = {l.get("name") for l in gh.rest("GET", "repos/%s/labels?per_page=100" % ctx.repo,
                                                paginate=True) if isinstance(l, dict)}
    for name, color, desc in model.LABELS:
        if name not in existing:
            w.call(["label", "create", name, "-R", ctx.repo, "--color", color, "--description",
                    desc, "--force"], json_out=False)


def install_workflows(ctx):
    src_dir = os.path.join(SKILL_DIR, "assets", "workflows")
    if not os.path.isdir(src_dir):
        raise Failure("workflow templates not found in %s (vendored copies cannot install them)" % src_dir)
    if not os.path.isdir(os.path.join(ctx.repo_root, _vendor.TARGET)) and not ctx.args.vendor:
        ctx.warn("the workflows run %s/*.py: also pass --vendor" % _vendor.TARGET.replace("\\", "/"))
    dest_dir = os.path.join(ctx.repo_root, ".github", "workflows")
    plan, conflicts = [], []
    for name in sorted(os.listdir(src_dir)):
        if not name.endswith(".yml"):
            continue
        with open(os.path.join(src_dir, name), "rb") as fh:
            data = fh.read().replace(b"\r\n", b"\n")
        dest = os.path.join(dest_dir, name)
        if os.path.isfile(dest):
            with open(dest, "rb") as fh:
                if fh.read().replace(b"\r\n", b"\n") == data:
                    continue
            conflicts.append(name)
            continue
        plan.append((name, dest, data))
    if conflicts:  # checked before any write: never leave a partial install
        raise Failure("existing workflow files differ from the templates (nothing written): %s"
                      % ", ".join(conflicts))
    for name, dest, data in plan:
        if ctx.apply:
            os.makedirs(dest_dir, exist_ok=True)
            with open(dest, "wb") as fh:
                fh.write(data)
            ctx.out("WROTE .github/workflows/%s" % name)
        else:
            ctx.out("PLAN write .github/workflows/%s" % name)


# ===================================================================== main

PROFILE_HINT = ("hint: pass --profile .claude/skills/<family profile skill>/assets/handoff-profile.yaml "
                "(e.g. coordinating-quarkus-aws-handoffs), or --profile "
                ".github/openspec-github/handoff-profile.yaml in a vendored repository")


class HintingParser(argparse.ArgumentParser):
    """Appends the --profile hint to argparse's 'required argument' error."""

    def error(self, message):
        if "--profile" in message:
            message = "%s\n%s" % (message, PROFILE_HINT)
        argparse.ArgumentParser.error(self, message)


def build_parser():
    ap = HintingParser(
        prog="gh_projects_sync.py",
        description="Mirror an OpenSpec change into a GitHub Project v2 (git canonical). Dry-run by "
                    "default; --apply writes. Exit 0 ok, 1 error, 2 divergence (status), "
                    "3 tracker disabled.")
    sub = ap.add_subparsers(dest="command", parser_class=HintingParser)
    helps = {
        "bootstrap": "create missing project fields and labels, cache ids; optionally vendor the "
                     "scripts and install the workflow templates",
        "push": "create or update the change issue, task/ADR/escalation sub-issues, project fields, "
                "spec-delta comments and the summary comment",
        "pull": "ORCHESTRATOR ONLY - agents never run it. Read gate/delta/escalation confirmations "
                "posted by tracker.bot_login, re-check each user comment and (with --apply) append "
                "gate approvals to handoff/status.md ## Approvals; delta and escalation decisions "
                "are printed as DECISION <json> for the orchestrator to apply",
        "close": "close every mirrored issue of the change and set Status=Done",
        "status": "read-only: report divergence between git and GitHub (exit 2 when diverged)",
    }
    for name in ("bootstrap", "push", "pull", "close", "status"):
        p = sub.add_parser(name, help=helps[name], description=helps[name], epilog=PROFILE_HINT)
        p.add_argument("repo_root", nargs="?", default=".",
                       help="repository root containing openspec/ (default: the current directory)")
        p.add_argument("--change", required=True, help="change id (openspec/changes/<id>)")
        p.add_argument("--profile", required=True, help="family handoff profile (YAML)")
        if name != "status":
            p.add_argument("--apply", action="store_true", help="perform the writes (default: dry-run)")
        if name == "push":
            p.add_argument("--stage", choices=model.STAGE_VALUES, help="override the computed Stage")
        if name == "bootstrap":
            p.add_argument("--install-workflows", action="store_true",
                           help="copy assets/workflows/*.yml into .github/workflows/")
            p.add_argument("--vendor", action="store_true",
                           help="copy the scripts into .github/openspec-github/ (sha256 manifest)")
    return ap


COMMANDS = {"bootstrap": cmd_bootstrap, "push": cmd_push, "pull": cmd_pull,
            "close": lambda ctx: cmd_push(ctx, closing=True), "status": cmd_status}


def main(argv=None):
    ap = build_parser()
    args = ap.parse_args(argv)
    if not args.command:
        ap.print_help()
        return EXIT_ERROR
    try:
        ctx = Context(args)
        preflight(ctx)
        return COMMANDS[args.command](ctx)
    except Disabled:
        print("tracker disabled")
        return EXIT_DISABLED
    except Failure as exc:
        sys.stderr.write(gh.redact("error: %s\n" % exc))
        return EXIT_ERROR
    except gh.GhError as exc:
        sys.stderr.write("error: %s\n" % exc)
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
