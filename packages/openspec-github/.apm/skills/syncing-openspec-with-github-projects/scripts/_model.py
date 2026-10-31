"""Pure model of the OpenSpec -> GitHub Projects mirror (Python 3.8+, standard library only).

No network, no subprocess, no file writes. Inputs are texts and handoff records already loaded
by the caller; outputs are plain dicts. Git stays canonical: everything here derives the
*desired* GitHub state from the files and compares it with the cached or observed state.

Contents
  * handoff-core library lookup (``_handoff_lib``, ``_mini_yaml``), see ``handoff_scripts_dir``
  * tracker resolution: profile ``tracker:`` block, overridden key by key by
    ``openspec/github-tracker.yaml`` (same keys; an outer ``tracker:`` wrapper is accepted)
  * tasks.md parsing, stage computation, desired issues/comments per change
  * the state file ``handoff/github.yaml`` (mini-yaml subset writer + reader)
  * the gate command grammar, its evaluation and the decision block used by ``pull``

Every body this module renders starts with ``BOT_MARKER`` and carries a key marker
``<!-- openspec-github:key <change>/<object> -->`` used to adopt objects when the state file
is missing (e.g. on a fresh Actions runner).
"""
import datetime
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ENV_HANDOFF = "OPENSPEC_GITHUB_HANDOFF_SCRIPTS"


def handoff_scripts_dir():
    """Locate coordinating-agent-handoffs/scripts (env, vendored copy, sibling skill)."""
    env = os.environ.get(ENV_HANDOFF)
    if env:
        if os.path.isfile(os.path.join(env, "_handoff_lib.py")):
            return os.path.abspath(env)
        raise RuntimeError("%s=%s does not contain _handoff_lib.py" % (ENV_HANDOFF, env))
    candidates = [HERE, os.path.join(HERE, "..", "..", "coordinating-agent-handoffs", "scripts")]
    for cand in candidates:
        if os.path.isfile(os.path.join(cand, "_handoff_lib.py")):
            return os.path.abspath(cand)
    raise RuntimeError("handoff-core scripts not found: install the coordinating-agent-handoffs "
                       "skill next to this one (.claude/skills/coordinating-agent-handoffs/scripts), "
                       "vendor them with bootstrap --vendor, or set %s" % ENV_HANDOFF)


_LIB_DIR = handoff_scripts_dir()
if _LIB_DIR not in sys.path:
    sys.path.insert(0, _LIB_DIR)

import _handoff_lib as lib  # noqa: E402
import _mini_yaml  # noqa: E402

BOT_MARKER = "<!-- openspec-github:bot v1 -->"
SCHEMA = 1
BODY_LIMIT = 60000                       # GitHub body limit is (unverified) 65,536 characters
GATES = ("E1", "E2", "E3", "E5", "E7", "E9")
STATUS_VALUES = ("Todo", "In progress", "Blocked", "Done")
KIND_VALUES = ("change", "task", "adr", "escalation")
STAGE_VALUES = tuple("E%d" % n for n in range(1, 10))
FIELD_SPECS = (                          # name, data type, options (bootstrap creates the missing ones)
    ("Stage", "SINGLE_SELECT", STAGE_VALUES),
    ("Kind", "SINGLE_SELECT", KIND_VALUES),
    ("Change", "TEXT", ()),
    ("Gate", "TEXT", ()),
)
BUILTIN_FIELDS = ("Status",)             # exists in every project; options are checked, not created
LABELS = (                               # name, colour, description
    ("openspec", "0E8A16", "Mirrored from openspec/ (git is canonical)"),
    ("openspec:change", "1D76DB", "OpenSpec change"),
    ("openspec:task", "C5DEF5", "OpenSpec task"),
    ("openspec:adr", "5319E7", "Architecture decision record"),
    ("blocked", "B60205", "Waiting for an answer"),
) + tuple(("gate:%s:%s" % (g, v), "0E8A16" if v == "approved" else "D93F0B",
           "Gate %s %s" % (g, v)) for g in GATES for v in ("approved", "rejected"))
DELTA_LABEL_COLOR = "FBCA04"
WO_STATUS = {"pending": "Todo", "in-progress": "In progress", "blocked": "Blocked",
             "done": "Done", "completed": "Done", "cancelled": "Done"}

_KEY_RE = re.compile(r"<!-- openspec-github:key ([A-Za-z0-9._-]+)/([A-Za-z0-9:._-]+) -->")
_DELTA_STATUS_RE = re.compile(r"<!-- openspec-github:delta status=([a-z-]+) -->")
_GROUP_RE = re.compile(r"^##\s+(\d+)[.)]?\s+(.*?)\s*$")
_ITEM_RE = re.compile(r"^\s*[-*]\s+\[([ xX])\]\s+(\d+)(?:\.(\d+))?\.?\s+(.*?)\s*$")
_ADR_FILE_RE = re.compile(r"^(\d{3,})-.*\.md$")
_ADR_REF_RE = re.compile(r"\bADR[-_ ]?0*(\d+)\b", re.I)
_SIMPLE_KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_CHANGE_TITLE_RE = re.compile(r"^change: ([a-z0-9][a-z0-9._-]*)$")
CHANGE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


# ============================================================ tracker

def resolve_tracker(profile_tracker, project_doc):
    """Merge the profile block with openspec/github-tracker.yaml (the project file wins)."""
    merged = dict(profile_tracker or {})
    if isinstance(project_doc, dict):
        block = project_doc.get("tracker") if isinstance(project_doc.get("tracker"), dict) \
            else project_doc
        merged.update(block)
    if not merged:
        merged = {"kind": "none"}
    return merged, lib.validate_tracker(merged)


def trusted_author(login, tracker):
    """Authors whose openspec-github objects may be adopted / referenced.

    Fails closed: with neither ``approvers`` nor ``bot_login`` configured nobody is
    trusted (family rule 12), so a marker planted by a stranger is never adopted.
    """
    trusted = set(tracker.get("approvers") or [])
    if tracker.get("bot_login"):
        trusted.add(tracker["bot_login"])
    return bool(login) and login in trusted


# ============================================================ small helpers

def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def body_sha(title, body):
    text = (title or "") + "\0" + (body or "")
    return hashlib.sha256(text.replace("\r\n", "\n").encode("utf-8")).hexdigest()[:16]


def key_marker(change, obj):
    return "<!-- openspec-github:key %s/%s -->" % (change, obj)


def parse_key_marker(body):
    """Return (change, object_key) from a body, or (None, None)."""
    m = _KEY_RE.search(body or "")
    return (m.group(1), m.group(2)) if m else (None, None)


def blob_url(repo, path):
    return "https://github.com/%s/blob/HEAD/%s" % (repo, path.replace("\\", "/"))


def truncate(body, link, limit=BODY_LIMIT):
    if len(body) <= limit:
        return body
    note = "\n\n(truncated at %d characters; full text: %s)" % (limit, link)
    return body[:limit - len(note)] + note


def section(sections, name):
    for heading, text in sections:
        if heading.strip().lower() == name.lower():
            return text.strip("\n")
    return None


def frontmatter_split(text):
    """(frontmatter dict, body) when the text has '---' frontmatter, else ({}, text)."""
    if text.lstrip("\ufeff").startswith("---"):
        try:
            return _mini_yaml.parse_frontmatter(text)
        except _mini_yaml.YamlError:
            pass
    return {}, text


def first_line(text):
    for line in (text or "").splitlines():
        line = line.strip().lstrip("#").strip()
        if line:
            return line
    return ""


def header(change, obj):
    return "%s\n%s\n" % (BOT_MARKER, key_marker(change, obj))


# ============================================================ tasks.md, ADRs, stage

def parse_tasks(text):
    """Parse OpenSpec tasks.md: '## N. Title' groups with '- [ ] N.M text' items -> T<N> tasks."""
    groups = {}
    order = []

    def group(n, title=None):
        if n not in groups:
            groups[n] = {"id": "T%d" % n, "n": n, "title": title, "items": []}
            order.append(n)
        elif title and not groups[n]["title"]:
            groups[n]["title"] = title
        return groups[n]

    current = None
    for line in (text or "").splitlines():
        m = _GROUP_RE.match(line)
        if m:
            current = group(int(m.group(1)), m.group(2))
            continue
        m = _ITEM_RE.match(line)
        if m:
            n = int(m.group(2))
            g = group(n) if m.group(3) else (current or group(n))
            label = "%s.%s" % (m.group(2), m.group(3)) if m.group(3) else m.group(2)
            g["items"].append({"id": label, "done": m.group(1) in "xX", "text": m.group(4)})
    out = []
    for n in sorted(order):
        g = groups[n]
        if not g["title"]:
            g["title"] = g["items"][0]["text"] if g["items"] else "group %d" % n
        out.append(g)
    return out


def checkbox_status(items):
    if items and all(i["done"] for i in items):
        return "Done"
    if any(i["done"] for i in items):
        return "In progress"
    return "Todo"


def work_order_status(work_orders):
    """Mirror of the board rule: blocked > all done > in-progress > pending (cancelled ignored)."""
    states = [str(w.fm.get("status")) for w in work_orders]
    live = [s for s in states if s != "cancelled"]
    if not live:
        return "cancelled"
    if "blocked" in live:
        return "blocked"
    if all(s in lib.DONE_STATUSES for s in live):
        return "done"
    if "in-progress" in live:
        return "in-progress"
    return "pending"


def adr_info(filename, text):
    """Return {num, title, status} for an ADR file, or None when the name is not NNN-*.md."""
    m = _ADR_FILE_RE.match(filename)
    if not m:
        return None
    fm, body = frontmatter_split(text)
    status = fm.get("status")
    if not status:
        sm = re.search(r"^\W*status\W*:\s*\**\s*([A-Za-z-]+)", body, re.I | re.M)
        if sm:
            status = sm.group(1)
    if not status:
        st = section(lib.split_sections(body), "Status")
        status = first_line(st) if st else None
    title = fm.get("title") or ""
    if not title:
        for line in body.splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                break
    title = re.sub(r"^(ADR[-_ ]?)?0*%d[:.\s-]*" % int(m.group(1)), "", str(title), flags=re.I).strip()
    return {"num": m.group(1), "title": title or filename[:-3], "status": str(status or "").lower(),
            "file": filename}


def referenced_adrs(adrs, texts):
    """Keep the ADRs mentioned (ADR-003, ADR 3, adr_003) in any of the change's texts."""
    wanted = set()
    for t in texts:
        for m in _ADR_REF_RE.finditer(t or ""):
            wanted.add(int(m.group(1)))
    return [a for a in adrs if int(a["num"]) in wanted]


def stage_of(records, override=None):
    """(stage, finished): --stage wins; else highest verify E<n> with outcome pass, +1 (E1 if none)."""
    best = 0
    for r in records:
        if r.error is None and r.kind == "verify" and str(r.fm.get("outcome")) == "pass":
            m = re.match(r"^E(\d+)$", str(r.fm.get("stage") or ""))
            if m:
                best = max(best, int(m.group(1)))
    if override:
        return override, best >= 9
    return "E%d" % min(best + 1, 9), best >= 9


# ============================================================ desired state

def _records(inputs):
    return [r for r in inputs["records"] if r.error is None and r.kind not in (None, "status")]


def _open_needs_input(recs):
    referenced = set()
    for r in recs:
        referenced.update(lib.refs_of(r))
    return [r for r in recs if r.kind in lib.REPORT_KINDS
            and str(r.fm.get("outcome")) == "needs-input" and r.id not in referenced], referenced


def _issue(key, title, body, labels, fields, state="open", reason=None, parent=None):
    return {"key": key, "title": title, "body": body, "labels": list(labels), "fields": fields,
            "state": state, "reason": reason, "parent": parent}


def _change_issue(inputs, stage, status):
    change, repo = inputs["change"], inputs["repo"]
    rel = "openspec/changes/%s/proposal.md" % change
    sections = lib.split_sections(inputs.get("proposal") or "")
    parts = [header(change, "change"),
             "> Mirror of `openspec/changes/%s/` - git is canonical; edit the files, not this issue."
             % change]
    for name in ("Why", "What Changes"):
        text = section(sections, name)
        parts.append("## %s\n\n%s" % (name, text if text else "(not found in proposal.md)"))
    parts.append("Source: %s" % blob_url(repo, rel))
    body = truncate("\n\n".join(parts) + "\n", blob_url(repo, rel))
    gate = "%s pending" % stage if stage in GATES else "-"
    fields = {"Kind": "change", "Change": change, "Stage": stage, "Status": status, "Gate": gate}
    state = "closed" if inputs.get("closing") else "open"
    return _issue("change", "change: %s" % change, body, ["openspec", "openspec:change"], fields,
                  state, "completed" if state == "closed" else None)


def _task_issues(inputs, recs):
    change, repo = inputs["change"], inputs["repo"]
    by_id = {r.id: r for r in recs}
    wos = {}
    for r in recs:
        if r.kind == "work-order":
            wos.setdefault(lib.task_of(r, by_id), []).append(r)
    groups = {g["id"]: g for g in parse_tasks(inputs.get("tasks") or "")}
    out = []
    for tid in sorted(set(groups) | {t for t in wos if t}, key=_task_sort):
        g = groups.get(tid)
        orders = wos.get(tid, [])
        if orders:
            wstat = work_order_status(orders)
            status = WO_STATUS[wstat]
            state, reason = ("closed", "not_planned") if wstat == "cancelled" else \
                (("closed", "completed") if wstat == "done" else ("open", None))
        else:
            status = checkbox_status(g["items"])
            state, reason = ("closed", "completed") if status == "Done" else ("open", None)
        title_text = g["title"] if g else first_line(section(orders[0].sections, "Scope") or orders[0].id)
        lines = [header(change, "task:" + tid),
                 "Task %s of change `%s` (from `tasks.md` and the work-orders)." % (tid, change), ""]
        for item in (g["items"] if g else []):
            lines.append("- [%s] %s %s" % ("x" if item["done"] else " ", item["id"], item["text"]))
        if orders:
            lines += ["", "Work-orders: " + ", ".join("%s (%s)" % (w.id, w.fm.get("status"))
                                                     for w in orders)]
        link = blob_url(repo, "openspec/changes/%s/tasks.md" % change)
        lines += ["", "Source: %s" % link]
        if inputs.get("closing") and state == "open":
            state, reason, status = "closed", "completed", "Done"
        fields = {"Kind": "task", "Change": change, "Status": status}
        out.append(_issue("task:" + tid, "task: %s %s" % (tid, title_text),
                          truncate("\n".join(lines) + "\n", link),
                          ["openspec", "openspec:task"], fields, state, reason, "change"))
    return out


def _task_sort(tid):
    m = re.match(r"^T(\d+)$", str(tid))
    return (0, int(m.group(1)), "") if m else (1, 0, str(tid))


def _adr_issues(inputs):
    change, repo = inputs["change"], inputs["repo"]
    out = []
    for a in inputs.get("adrs") or []:
        path = "%s/%s" % (inputs.get("adr_dir", "openspec/specs/architecture/adr"), a["file"])
        link = blob_url(repo, path)
        body = "%s\nADR %s (status: %s), referenced by change `%s`.\n\nSource: %s\n" % (
            header(change, "adr:" + a["num"]), a["num"], a["status"] or "unknown", change, link)
        status = "Done" if a["status"] == "accepted" else "Todo"
        state = "closed" if inputs.get("closing") else "open"
        out.append(_issue("adr:" + a["num"], "adr: %s %s" % (a["num"], a["title"]), body,
                          ["openspec", "openspec:adr"],
                          {"Kind": "adr", "Change": change, "Status": status}, state,
                          "completed" if state == "closed" else None, "change"))
    return out


def _escalation_issues(inputs, recs):
    change = inputs["change"]
    needs, referenced = _open_needs_input(recs)
    out = []
    for r in recs:
        is_esc = r.kind == "escalation"
        is_ni = r.kind in lib.REPORT_KINDS and str(r.fm.get("outcome")) == "needs-input"
        if not (is_esc or is_ni):
            continue
        open_ = str(r.fm.get("status")) == "open" if is_esc else r in needs
        if is_esc:
            text = section(r.sections, "Options") or "(no ## Options section)"
            reply = ("Answer on this issue with one line: `/answer %s <text>` (only listed "
                     "approvers are recorded)." % r.id) if open_ else "Answered."
            title = "escalation: %s %s" % (r.id, r.fm.get("limit") or r.fm.get("task") or "")
        else:
            text = section(r.sections, "Questions") or section(r.sections, "Suggested next step") \
                or "\n\n".join("## %s\n\n%s" % s for s in r.sections)
            reply = ("Answer the orchestrator in chat; this issue closes when a later record refers "
                     "to `%s`." % r.id) if open_ else "Answered by a later record."
            title = "needs-input: %s" % r.id
        body = "%s\n## Options\n\n%s\n\n%s\n" % (header(change, "escalation:" + r.id), text, reply)
        if inputs.get("closing"):
            open_ = False
        labels = ["openspec", "blocked"] if open_ else ["openspec"]
        fields = {"Kind": "escalation", "Change": change, "Status": "Blocked" if open_ else "Done"}
        out.append(_issue("escalation:" + r.id, title.strip(), truncate(body, ""), labels, fields,
                          "open" if open_ else "closed", None if open_ else "completed", "change"))
    return out, bool(needs) or any(r.kind == "escalation" and str(r.fm.get("status")) == "open"
                                   for r in recs)


def delta_number(record_id):
    m = re.search(r"(\d+)$", record_id)
    return m.group(1) if m else record_id


def _delta_comments(inputs, recs):
    change, repo = inputs["change"], inputs["repo"]
    out = []
    for r in recs:
        if r.kind != "spec-delta":
            continue
        status = str(r.fm.get("status"))
        nn = delta_number(r.id)
        parts = [header(change, "delta:" + r.id).rstrip("\n"),
                 "<!-- openspec-github:delta status=%s -->" % status,
                 "### %s - status: %s" % (r.id, status)]
        for heading, text in r.sections:
            if heading.lower() in lib.DELTA_HEADINGS or heading.lower() == "questions":
                parts.append("## %s\n%s" % (heading, text.rstrip()))
        if status in ("proposed", "revise"):
            parts.append("Reply with one line (approvers only): `/accept delta-%s`, "
                         "`/reject delta-%s <reason>` or `/revise delta-%s <answer>`." % (nn, nn, nn))
        link = blob_url(repo, "openspec/changes/%s/handoff/%s" % (change, r.name))
        out.append({"key": "delta:" + r.id, "issue": "change",
                    "body": truncate("\n\n".join(parts) + "\n", link)})
    return out


def _summary_comment(inputs, stage):
    change = inputs["change"]
    text = inputs.get("status_md") or ""
    _, body = frontmatter_split(text)
    sections = lib.split_sections(body)
    parts = [header(change, "summary").rstrip("\n"), "### OpenSpec status - `%s`" % change,
             "Stage: **%s**" % stage]
    if stage in GATES and inputs.get("approval_source", "chat") != "chat":
        parts.append("Gate %s waits for an approver: reply `/approve %s` or `/reject %s <reason>`."
                     % (stage, stage, stage))
    found = False
    for name in ("Next action", "Counters", "State"):
        sec = section(sections, name)
        if sec is not None:
            found = True
            parts.append("## %s\n\n%s" % (name, sec.strip()))
    if not found:
        parts.append("(no board yet: run board.py to create handoff/status.md)")
    return {"key": "summary", "issue": "change", "body": truncate("\n\n".join(parts) + "\n", "")}


def desired_state(inputs):
    """Derive the desired GitHub objects of one change.

    inputs: change, repo, proposal, tasks, records (handoff Record objects), adrs (adr_info
    dicts, already filtered), adr_dir, status_md, stage (optional override), closing (bool),
    approval_source.
    Returns {"stage", "issues": [issue dicts in creation order], "comments": [comment dicts]}.
    """
    recs = _records(inputs)
    stage, finished = stage_of(recs, inputs.get("stage"))
    escalations, blocked = _escalation_issues(inputs, recs)
    if inputs.get("closing") or finished:
        status = "Done"
    elif blocked:
        status = "Blocked"
    elif recs:
        status = "In progress"
    else:
        status = "Todo"
    issues = [_change_issue(inputs, stage, status)] + _task_issues(inputs, recs) \
        + _adr_issues(inputs) + escalations
    for issue in issues:
        issue["sha"] = body_sha(issue["title"], issue["body"])
    comments = _delta_comments(inputs, recs) + [_summary_comment(inputs, stage)]
    for c in comments:
        c["sha"] = body_sha("", c["body"])
    return {"stage": stage, "issues": issues, "comments": comments}


# ============================================================ state file (github.yaml)

SECTIONS = {"task": "tasks", "adr": "adrs", "escalation": "escalations", "delta": "deltas"}


def new_state(tracker):
    t = {k: tracker[k] for k in ("owner", "owner_type", "project_number", "repo") if k in tracker}
    return {"schema": SCHEMA, "tracker": t, "project_id": None, "fields": {}, "change": {},
            "tasks": {}, "adrs": {}, "escalations": {}, "deltas": {}, "summary_comment_id": None,
            "summary_sha": None, "pulled": {}}


def get_entry(state, key):
    """Return the (mutable) cache entry of an object key, creating empty ones on demand."""
    if key == "change":
        state.setdefault("change", {})
        if state["change"] is None:
            state["change"] = {}
        return state["change"]
    if key == "summary":
        return {"comment_id": state.get("summary_comment_id"), "sha": state.get("summary_sha")}
    kind, _, sid = key.partition(":")
    sec = state.setdefault(SECTIONS[kind], {})
    if sec is None:
        sec = state[SECTIONS[kind]] = {}
    return sec.setdefault(sid, {})


def set_summary(state, entry):
    state["summary_comment_id"] = entry.get("comment_id")
    state["summary_sha"] = entry.get("sha")


def _q(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    s = str(value).replace("\r", "")
    return '"%s"' % s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\t", "\\t")


def _k(key):
    key = str(key)
    return key if _SIMPLE_KEY.match(key) else _q(key)


def _flow(value):
    if isinstance(value, dict):
        return "{" + ", ".join("%s: %s" % (_k(k), _flow(v)) for k, v in value.items()) + "}"
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(_flow(v) for v in value) + "]"
    return _q(value)


def dump_state(state):
    """Render github.yaml: top-level block mapping, one flow mapping per object (mini-yaml subset)."""
    lines = ["# Written by gh_projects_sync.py (openspec-github) - do not edit by hand.",
             "# GitHub ids cache of one change; git stays canonical."]
    for key, value in state.items():
        if isinstance(value, dict) and value and key not in ("tracker", "vendor") \
                and all(isinstance(v, dict) for v in value.values()):
            lines.append("%s:" % _k(key))
            for sub, entry in value.items():
                lines.append("  %s: %s" % (_k(sub), _flow(entry)))
        else:
            lines.append("%s: %s" % (_k(key), _flow(value)))
    return "\n".join(lines) + "\n"


def load_state(text, tracker):
    state = new_state(tracker)
    if text:
        data = _mini_yaml.load(text)
        if not isinstance(data, dict):
            raise ValueError("github.yaml must be a mapping")
        if data.get("schema") not in (None, SCHEMA):
            raise ValueError("github.yaml schema %r is not supported (expected %d)"
                             % (data.get("schema"), SCHEMA))
        for k, v in data.items():
            state[k] = v
        for sec in ("tasks", "adrs", "escalations", "deltas", "pulled", "fields"):
            if not isinstance(state.get(sec), dict):
                state[sec] = {}
    return state


def tracker_mismatch(state, tracker):
    """Names of tracker keys that differ between github.yaml and the configured tracker."""
    cached = state.get("tracker") or {}
    return [k for k in ("owner", "owner_type", "project_number", "repo")
            if k in cached and cached.get(k) != tracker.get(k)]


# ============================================================ diffs

def field_edits(desired_fields, current_fields):
    """Return [(name, value)] to set; a Gate already answered for this stage is kept."""
    current = current_fields or {}
    out = []
    for name, value in desired_fields.items():
        have = current.get(name)
        if name == "Gate" and isinstance(have, str) and value.endswith(" pending") \
                and have.startswith(value.split(" ")[0] + " "):
            continue
        if have is None or str(have).strip().lower() != str(value).strip().lower():
            out.append((name, value))      # option names compare case-insensitively
    return out


def label_edits(desired_labels, current_labels):
    """(add, remove): remove only 'blocked', never labels this tool does not own."""
    have = set(current_labels or [])
    add = [l for l in desired_labels if l not in have]
    remove = ["blocked"] if "blocked" in have and "blocked" not in desired_labels else []
    return add, remove


def option_id(field, value):
    """Case-insensitive option lookup (the built-in Status uses 'In Progress')."""
    for name, oid in (field.get("options") or {}).items():
        if name.strip().lower() == str(value).strip().lower():
            return oid
    return None


def compare_issue(desired, observed):
    """Differences between a desired issue and the observed one (status command)."""
    diffs = []
    if observed is None:
        return ["missing on GitHub"]
    if body_sha(observed.get("title"), observed.get("body")) != desired["sha"]:
        diffs.append("title/body differ")
    if observed.get("state") != desired["state"]:
        diffs.append("state %s, want %s" % (observed.get("state"), desired["state"]))
    add, remove = label_edits(desired["labels"], observed.get("labels"))
    if add or remove:
        diffs.append("labels: add %s remove %s" % (add, remove))
    for name, value in field_edits(desired["fields"], observed.get("fields")):
        diffs.append("field %s=%r, want %r" % (name, (observed.get("fields") or {}).get(name), value))
    return diffs


# ============================================================ gate commands

COMMAND_PATTERNS = (
    ("gate", "approved", re.compile(r"^/approve (E[1-9])$")),
    ("gate", "rejected", re.compile(r"^/reject (E[1-9]) (\S.*)$")),
    ("delta", "accepted", re.compile(r"^/accept delta-(\d{2,})$")),
    ("delta", "rejected", re.compile(r"^/reject delta-(\d{2,}) (\S.*)$")),
    ("delta", "revise", re.compile(r"^/revise delta-(\d{2,}) (\S.*)$")),
    ("escalation", "answered", re.compile(r"^/answer escalation-(\d{2,}) (\S.*)$")),
)
VERBS = ("/approve", "/reject", "/accept", "/revise", "/answer")
GRAMMAR = ("/approve E<n> | /reject E<n> <reason> | /accept delta-<nn> | /reject delta-<nn> "
           "<reason> | /revise delta-<nn> <answer> | /answer escalation-<nn> <text>")


class CommandError(ValueError):
    """A known verb with malformed arguments."""


def parse_command(body):
    """Parse the FIRST line of a comment. None = not a command (ignore); CommandError = malformed.

    The rest of the body is never interpreted; it is only quoted back verbatim.
    """
    line = (body or "").split("\n", 1)[0].rstrip("\r")
    verb = line.split(" ", 1)[0]
    if verb not in VERBS:
        return None
    for kind, verdict, pattern in COMMAND_PATTERNS:
        m = pattern.match(line)
        if m:
            target = m.group(1)
            return {"kind": kind, "verdict": verdict, "target": target,
                    "text": m.group(2) if m.lastindex and m.lastindex >= 2 else "", "line": line}
    raise CommandError("malformed command %r; expected exactly one of: %s" % (line[:120], GRAMMAR))


def _after(a, b):
    ta, tb = lib.parse_ts(a), lib.parse_ts(b)
    return ta is not None and tb is not None and ta > tb


def evaluate(cmd, ctx):
    """Decide whether a parsed command is recorded.

    ctx: author, body, created_at, tracker, issue {change, obj, trusted, labels, state,
    created_at, stage, stage_updated_at}, delta {status, updated_at} or None.
    Returns {"ok": bool, "reason": str, "silent": bool, "label": str|None}.
    """
    t = ctx["tracker"]
    author = ctx["author"]

    def no(reason, silent=False):
        return {"ok": False, "reason": reason, "silent": silent, "label": None}

    if t.get("bot_login") and author == t["bot_login"]:
        return no("comment author is the bot login", silent=True)
    if author not in (t.get("approvers") or []):
        # silent: never answer strangers (spam / rate-limit guard, audit F6)
        return no("%s is not in tracker.approvers" % author, silent=True)
    if BOT_MARKER in (ctx.get("body") or ""):
        return no("the comment carries the bot marker")
    issue = ctx.get("issue") or {}
    if not issue.get("change") or not issue.get("trusted"):
        return no("this issue is not an openspec-github issue created by a trusted author")
    if cmd["kind"] == "gate":
        return _evaluate_gate(cmd, ctx, issue, no)
    if cmd["kind"] == "delta":
        return _evaluate_delta(cmd, ctx, issue, no)
    return _evaluate_escalation(cmd, ctx, issue, no)


def _evaluate_gate(cmd, ctx, issue, no):
    gate = cmd["target"]
    if issue.get("obj") != "change":
        return no("gate commands are accepted only on the change issue")
    if gate not in GATES:
        return no("%s is not a gate (gates: %s)" % (gate, ", ".join(GATES)))
    if issue.get("stage") != gate:
        return no("out of order: the change is at Stage %s, not %s" % (issue.get("stage"), gate))
    if not issue.get("stage_updated_at"):
        return no("cannot tell when Stage was set (no updatedAt on the Stage value)")
    if not _after(ctx["created_at"], issue["stage_updated_at"]):
        return no("the comment is older than the current Stage value")
    for verdict in ("approved", "rejected"):
        if "gate:%s:%s" % (gate, verdict) in (issue.get("labels") or []):
            return no("gate %s is already %s" % (gate, verdict))
    return {"ok": True, "reason": "", "silent": False, "label": "gate:%s:%s" % (gate, cmd["verdict"])}


def _evaluate_delta(cmd, ctx, issue, no):
    if issue.get("obj") != "change":
        return no("delta commands are accepted only on the change issue")
    delta = ctx.get("delta")
    if not delta:
        return no("no spec-delta-%s comment from a trusted author on this issue" % cmd["target"])
    if delta.get("status") not in ("proposed", "revise"):
        return no("spec-delta-%s is %s, not open for answers" % (cmd["target"], delta.get("status")))
    if not _after(ctx["created_at"], delta.get("updated_at")):
        return no("the comment is older than the current spec-delta-%s text" % cmd["target"])
    return {"ok": True, "reason": "", "silent": False,
            "label": "delta:%s:%s" % (cmd["target"], cmd["verdict"])}


def _evaluate_escalation(cmd, ctx, issue, no):
    if issue.get("obj") != "escalation:escalation-%s" % cmd["target"]:
        return no("/answer escalation-%s is accepted only on that escalation's issue" % cmd["target"])
    if issue.get("state") != "open":
        return no("the escalation issue is closed")
    if not _after(ctx["created_at"], issue.get("created_at")):
        return no("the comment is older than the escalation issue")
    return {"ok": True, "reason": "", "silent": False, "label": None}


def decision_of(cmd, ctx):
    d = {"change": ctx["issue"]["change"], cmd["kind"]: _target_name(cmd), "verdict": cmd["verdict"],
         "by": ctx["author"], "comment_url": ctx["comment_url"], "comment_id": int(ctx["comment_id"]),
         "created_at": ctx["created_at"]}
    return d


def _target_name(cmd):
    return {"gate": cmd["target"], "delta": "delta-" + cmd["target"],
            "escalation": "escalation-" + cmd["target"]}[cmd["kind"]]


def quote_text(body):
    return "\n".join("> " + line if line else ">" for line in (body or "").replace("\r", "").split("\n"))


def confirmation_body(decision, body):
    kind = "gate" if "gate" in decision else "delta" if "delta" in decision else "escalation"
    return ("%s\nRecorded **%s** for %s `%s` of change `%s` (by %s). The orchestrator re-checks it "
            "before anything is written to git.\n\n```yaml\ndecision: %s\n```\n\n%s\n"
            % (BOT_MARKER, decision["verdict"], kind, decision[kind], decision["change"],
               decision["by"], _flow(decision), quote_text(body)))


def refusal_body(reason, author):
    return ("%s\nNot recorded (%s): %s.\n\nAccepted grammar (first line only): %s\n"
            % (BOT_MARKER, author, reason, GRAMMAR))


def parse_decision(body):
    """Return the decision dict of a confirmation comment, or None."""
    text = body or ""
    if not text.startswith(BOT_MARKER):
        return None
    m = re.search(r"```yaml\n(.*?)\n```", text, re.S)
    if not m:
        return None
    try:
        doc = _mini_yaml.load(m.group(1))
    except _mini_yaml.YamlError:
        return None
    d = doc.get("decision") if isinstance(doc, dict) else None
    return d if isinstance(d, dict) else None


def issue_api_suffix(repo, number):
    return "/repos/%s/issues/%s" % (repo, number)


def recheck_user_comment(decision, user_comment, confirmation_created_at, tracker, expected_issue=None):
    """Pull-side re-check of the user comment a confirmation refers to. Returns a reason or None.

    ``expected_issue`` = (repo, number): the user comment must belong to that issue (the issue the
    confirmation was found on), so a confirmation cannot point at a comment elsewhere (audit F12).
    """
    if user_comment is None:
        return "user comment not found"
    if expected_issue is not None:
        suffix = issue_api_suffix(*expected_issue)
        if not str(user_comment.get("issue_url") or "").endswith(suffix):
            return "the user comment is not on issue #%s" % expected_issue[1]
    login = ((user_comment.get("user") or {}).get("login"))
    body = user_comment.get("body") or ""
    if login != decision.get("by"):
        return "author %r differs from the recorded %r" % (login, decision.get("by"))
    if login not in (tracker.get("approvers") or []) or login == tracker.get("bot_login"):
        return "%s is not an approver" % login
    if BOT_MARKER in body:
        return "user comment carries the bot marker"
    if str(user_comment.get("created_at")) != str(decision.get("created_at")):
        return "created_at differs from the recorded one"
    if not _after(confirmation_created_at, user_comment.get("created_at")) and \
            str(confirmation_created_at) != str(user_comment.get("created_at")):
        return "confirmation is older than the user comment"
    try:
        cmd = parse_command(body)
    except CommandError:
        cmd = None
    kind = "gate" if "gate" in decision else "delta" if "delta" in decision else "escalation"
    if cmd is None or cmd["kind"] != kind or _target_name(cmd) != decision.get(kind) \
            or cmd["verdict"] != decision.get("verdict"):
        return "the user comment no longer holds the recorded command (edited?)"
    return None


def recheck_gate(gate, confirmations, fetch_user_comment, tracker, issue, repo, number):
    """Re-check that ``gate`` of the change issue ``number`` holds a valid, bot-confirmed approval.

    confirmations: comments on the issue (REST dicts); fetch_user_comment(id) -> REST dict or None;
    issue: {change, obj, trusted, stage, stage_updated_at}. Returns (ok, [reasons]). Used by
    ``gate_command.py recheck`` before the archive workflow acts on a label (audit F5).
    """
    if not issue.get("change") or issue.get("obj") != "change" or not issue.get("trusted"):
        return False, ["issue #%s is not a change issue created by a trusted author" % number]
    if issue.get("stage") != gate:
        return False, ["the change is at Stage %s, not %s" % (issue.get("stage"), gate)]
    if not issue.get("stage_updated_at"):
        return False, ["cannot tell when Stage was set (no updatedAt on the Stage value)"]
    reasons = []
    for conf in confirmations:
        if not isinstance(conf, dict) or (conf.get("user") or {}).get("login") != tracker.get("bot_login"):
            continue
        d = parse_decision(conf.get("body"))
        if not d or d.get("change") != issue["change"] or d.get("gate") != gate                 or d.get("verdict") != "approved":
            continue
        user = fetch_user_comment(d.get("comment_id"))
        why = recheck_user_comment(d, user, conf.get("created_at"), tracker, (repo, number))
        if why is None and not _after((user or {}).get("created_at"), issue["stage_updated_at"]):
            why = "the approval is older than the current Stage value"
        if why is None:
            return True, ["approved by %s at %s (%s)" % (d.get("by"), d.get("created_at"), d.get("comment_url"))]
        reasons.append("confirmation %s: %s" % (conf.get("id"), why))
    return False, reasons or ["no confirmation of %s by %s on issue #%s" % (gate, tracker.get("bot_login"), number)]


def approval_line(decision, subject_url, user_body):
    lines = (user_body or "").replace("\r", "").split("\n")
    said = lines[0] + ("" if len(lines) == 1 else " " + " ".join(l.strip() for l in lines[1:] if l.strip()))
    said = said.replace("\\", "\\\\").replace('"', '\\"')
    return '- %s | gate=%s | subject=%s | source=github %s login=%s | user said: "%s"' % (
        decision["created_at"], decision["gate"], subject_url, decision["comment_url"],
        decision["by"], said)


def append_approval(status_text, line):
    """Insert ``line`` at the end of '## Approvals' (replacing '(none recorded)'); add the section if absent."""
    lines = (status_text or "").split("\n")
    start = None
    for i, l in enumerate(lines):
        if re.match(r"^##\s+Approvals\s*$", l):
            start = i
            break
    if start is None:
        base = (status_text or "").rstrip("\n")
        return (base + "\n\n" if base else "") + "## Approvals\n\n" + line + "\n"
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("## "):
            end = j
            break
    body = [l for l in lines[start + 1:end] if l.strip() not in ("(none recorded)",)]
    while body and not body[-1].strip():
        body.pop()
    while body and not body[0].strip():
        body.pop(0)
    new = [""] + body + [line, ""]
    return "\n".join(lines[:start + 1] + new + lines[end:])


def change_id_from_issue(title, body):
    """Change id of an issue: the key marker wins, else the 'change: <id>' title."""
    change, obj = parse_key_marker(body)
    if change and obj == "change" and CHANGE_ID_RE.match(change):
        return change
    m = _CHANGE_TITLE_RE.match((title or "").strip())
    return m.group(1) if m else None


_DIFF_HDR = re.compile(r"^diff --git (\S+) (\S+)$")
_MODE_LINE = re.compile(r"^(new file mode|deleted file mode|old mode|new mode) (\d+)$")
_SIDE_LINE = re.compile(r"^(rename from|rename to|copy from|copy to) (.+)$")
_INDEX_MODE = re.compile(r"^index [0-9a-f]+\.\.[0-9a-f]+ (\d+)$")
_REGULAR_MODES = ("100644", "100755")


def _inside(path, root):
    return path.startswith(root) and ".." not in path.split("/") and "\\" not in path


def check_patch(text, root="openspec/"):
    """Problems of a `git diff --binary` patch before it is applied (archive publish job, audit N2).

    Both sides of every file pair must be under ``root``; renames/copies from outside are refused;
    mode changes, symlinks (120000) and submodules (160000) are refused; quoted (escaped) paths
    are refused. Returns a list of problems (empty = safe). Pure: no git needed.
    """
    problems = []
    files = 0
    for n, line in enumerate((text or "").split("\n"), 1):
        if line.startswith("diff --git "):
            files += 1
            m = _DIFF_HDR.match(line)
            if not m or '"' in line:
                problems.append("line %d: unparsable or quoted diff header" % n)
                continue
            for side, prefix in ((m.group(1), "a/"), (m.group(2), "b/")):
                if not side.startswith(prefix) or not _inside(side[2:], root):
                    problems.append("line %d: path %s is outside %s" % (n, side, root))
            continue
        m = _SIDE_LINE.match(line)
        if m:
            if '"' in m.group(2) or not _inside(m.group(2), root):
                problems.append("line %d: %s %s is outside %s" % (n, m.group(1), m.group(2), root))
            continue
        m = _MODE_LINE.match(line)
        if m:
            if m.group(1) in ("old mode", "new mode"):
                problems.append("line %d: mode change refused" % n)
            elif m.group(2) not in _REGULAR_MODES:
                problems.append("line %d: %s %s refused (symlink/submodule/special)" % (n, m.group(1), m.group(2)))
            continue
        m = _INDEX_MODE.match(line)
        if m and m.group(1) not in _REGULAR_MODES:
            problems.append("line %d: file mode %s refused (symlink/submodule/special)" % (n, m.group(1)))
    if files == 0:
        problems.append("the patch contains no file")
    return problems


def to_json(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False)
