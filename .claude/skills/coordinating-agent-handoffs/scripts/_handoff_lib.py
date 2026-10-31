"""Shared logic for the handoff scripts (Python 3.8+, standard library only).

Used by check_records.py, board.py and detect_drift.py. Protocol v1.
"""
import datetime
import os
import re
import sys

from _mini_yaml import YamlError, load as yaml_load, parse_frontmatter, scalar as yaml_scalar

PROTOCOL_VERSION = 1

KINDS = ("work-order", "report", "review", "deploy-report", "diagnosis-report",
         "spec-delta", "escalation", "verify", "status")

REPORT_KINDS = ("report", "deploy-report", "diagnosis-report")
REPORT_OUTCOMES = ("success", "partial", "failed", "needs-input")
DONE_STATUSES = ("done", "completed")
DRIFT_IMPACTS = ("divergence", "ambiguity")
DELTA_HEADINGS = ("added requirements", "modified requirements",
                  "removed requirements", "renamed requirements")

DEFAULT_SECTIONS = {
    "work-order": ["Scope", "Skills", "Requirements", "Constraints", "Acceptance criteria"],
    "report": ["Done", "Evidence", "Spec impact", "Suggested next step"],
    "review": ["Findings", "ADR check"],
    "deploy-report": ["Deployed", "Validation", "Next step"],
    "diagnosis-report": ["Symptom", "Root cause", "Evidence", "Exact fix",
                         "Classification", "Next step"],
    "spec-delta": ["Questions"],
    "escalation": ["Attempts", "Evidence", "Hypothesis", "Options"],
    "verify": ["Criteria", "Evidence"],
    "status": [],
}

# kind -> {field: allowed values}; the profile `values:` map overrides per kind/field.
DEFAULT_ENUMS = {
    "work-order": {"status": ["pending", "in-progress", "done", "blocked", "cancelled"]},
    "report": {"outcome": list(REPORT_OUTCOMES)},
    "review": {"outcome": ["approved", "changes-requested"]},
    # report family (report, deploy-report, diagnosis-report) shares one outcome vocabulary
    "deploy-report": {"outcome": list(REPORT_OUTCOMES)},
    "diagnosis-report": {"outcome": list(REPORT_OUTCOMES)},
    "spec-delta": {"status": ["proposed", "accepted", "rejected", "revise"]},
    "escalation": {"status": ["open", "answered"]},
    "verify": {"outcome": ["pass", "fail"]},
}

# the field that every record of a kind must carry
REQUIRED_ENUM_FIELD = {
    "work-order": "status", "spec-delta": "status", "escalation": "status",
    "report": "outcome", "review": "outcome", "deploy-report": "outcome",
    "diagnosis-report": "outcome", "verify": "outcome",
}

DEFAULT_COUNTERS = {
    "build_attempts": {"kind": "report", "outcome": ["failed", "partial"], "scope": "task"},
    "review_rounds": {"kind": "review", "outcome": "changes-requested", "scope": "task"},
    "deploy_cycles": {"kind": "deploy-report", "outcome": "failed", "scope": "change"},
    "delta_revisions": {"kind": "spec-delta", "status": "revise", "scope": "change"},
    "record_rejections": {"max_field": "rejections", "scope": "task"},
}

MATCHERS = ("kind", "role", "outcome", "limit_reached", "drift", "all_tasks", "pending_deltas")
COUNTER_KEYS = ("kind", "role", "outcome", "status", "scope", "max_field")
SPECIAL_ACTIONS = ("escalate", "final-gate")
_CMP_RE = re.compile(r"^\s*(>=|<=|==|>|<)?\s*(\d+)\s*$")
ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:?\d{2})?)?$")
_TS_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})(?:T(\d{2}):(\d{2})(?::(\d{2})(?:\.(\d+))?)?"
                    r"(Z|[+-]\d{2}:?\d{2})?)?$")


def parse_ts(value):
    """Parse an ISO 8601 timestamp to a naive UTC datetime; None when unparseable.

    A timestamp without offset is read as UTC; a bare date is midnight UTC.
    (datetime.fromisoformat cannot read 'Z' before Python 3.11, so this is hand-rolled.)
    """
    m = _TS_RE.match(str(value or "").strip())
    if not m:
        return None
    year, month, day, hour, minute, sec, frac, tz = m.groups()
    try:
        micro = int((frac or "0")[:6].ljust(6, "0"))
        dt = datetime.datetime(int(year), int(month), int(day), int(hour or 0), int(minute or 0),
                               int(sec or 0), micro)
        if tz and tz != "Z":
            digits = tz[1:].replace(":", "")
            delta = datetime.timedelta(hours=int(digits[:2]), minutes=int(digits[2:]))
            dt = dt - delta if tz[0] == "+" else dt + delta
    except (ValueError, OverflowError):
        return None
    return dt


def make_clock(values):
    """Return a function mapping a timestamp string to a sortable value.

    Uses datetimes when every non-empty value parses; otherwise falls back to plain string
    comparison for all of them and prints one warning on stderr.
    """
    bad = sorted({str(v) for v in values if v not in (None, "") and parse_ts(v) is None})
    if bad:
        sys.stderr.write("warning: unparseable timestamp(s) %s; ordering falls back to string "
                         "comparison\n" % ", ".join(repr(b) for b in bad))
        return lambda v: str(v or "")
    return lambda v: parse_ts(v) or datetime.datetime.min


# ---------------------------------------------------------------- small helpers

def norm_agent(value):
    return str(value).strip().lstrip("@")


def as_list(value):
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    return [str(value)]


def norm_ref(ref):
    ref = str(ref).strip()
    if ref.lower().endswith(".md"):
        ref = ref[:-3]
    return ref


def is_str_or_list(value):
    if isinstance(value, str):
        return value != ""
    return isinstance(value, list) and bool(value) and all(isinstance(x, str) and x for x in value)


def value_in(want, have):
    """True when `have` equals `want` (scalar) or is one of `want` (list)."""
    if have is None:
        return False
    if isinstance(want, list):
        return str(have) in [str(w) for w in want]
    return str(have) == str(want)


def cmp_spec(spec, value):
    if isinstance(spec, int) and not isinstance(spec, bool):
        return value == spec
    m = _CMP_RE.match(str(spec))
    if not m:
        return False
    op, num = m.group(1) or "==", int(m.group(2))
    return {">": value > num, ">=": value >= num, "<": value < num,
            "<=": value <= num, "==": value == num}[op]


def split_sections(body):
    """Return [(heading, text)] for level-2 ('## ') headings, ignoring fenced code."""
    sections = []
    current = None
    buf = []
    fence = False
    for line in body.splitlines():
        st = line.lstrip()
        if st.startswith("```") or st.startswith("~~~"):
            fence = not fence
            if current is not None:
                buf.append(line)
            continue
        m = None if fence else re.match(r"^##\s+(.+?)\s*#*\s*$", line)
        if m:
            if current is not None:
                sections.append((current, "\n".join(buf)))
            current = m.group(1).strip()
            buf = []
        elif current is not None:
            buf.append(line)
    if current is not None:
        sections.append((current, "\n".join(buf)))
    return sections


def count_top_items(text):
    n = 0
    for line in text.splitlines():
        if re.match(r"^ {0,1}(?:[-*]|\d+[.)])\s+\S", line):
            n += 1
    return n


# -------------------------------------------------------------------- profile

def _check_matcher(key, value, limit_names):
    if key in ("kind", "role", "outcome"):
        return None if is_str_or_list(value) else "must be a string or a list of strings"
    if key == "limit_reached":
        if value is True or value is False or value == "any":
            return None
        names = value if isinstance(value, list) else [value]
        for name in names:
            if name not in limit_names:
                return "unknown limit %r (use 'any' or one of: %s)" % (
                    name, ", ".join(sorted(limit_names)) or "none")
        return None
    if key == "drift":
        return None if isinstance(value, bool) else "must be true or false"
    if key == "all_tasks":
        return None if value in ("done", "open") else "must be 'done' or 'open'"
    if key == "pending_deltas":
        if isinstance(value, int) and not isinstance(value, bool):
            return None
        return None if isinstance(value, str) and _CMP_RE.match(value) else \
            "must be an integer or a quoted comparison such as \">0\""
    return "unknown matcher"


TRACKER_KINDS = ("none", "github-projects")
TRACKER_OWNER_TYPES = ("organization", "user")
TRACKER_APPROVAL_SOURCES = ("chat", "github", "both")
_REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def validate_tracker(t):
    """Shape check of the optional `tracker:` block (profile-format.md#tracker).

    The protocol scripts never talk to a tracker; this only rejects malformed
    blocks early so a bridge (for example openspec-github) can rely on them.
    """
    if t is None:
        return []
    if not isinstance(t, dict):
        return ["'tracker' must be a mapping"]
    errs = []
    kind = t.get("kind")
    if kind not in TRACKER_KINDS:
        return ["tracker.kind must be one of: %s" % ", ".join(TRACKER_KINDS)]
    if kind == "none":
        return []
    for key in ("owner", "owner_type", "project_number", "repo"):
        if key not in t:
            errs.append("tracker.%s is required when tracker.kind is github-projects" % key)
    if "owner_type" in t and t["owner_type"] not in TRACKER_OWNER_TYPES:
        errs.append("tracker.owner_type must be 'organization' or 'user'")
    pn = t.get("project_number")
    if pn is not None and (isinstance(pn, bool) or not isinstance(pn, int) or pn < 1):
        errs.append("tracker.project_number must be an integer >= 1")
    repo = t.get("repo")
    if repo is not None and not (isinstance(repo, str) and _REPO_RE.match(repo)):
        errs.append("tracker.repo must be 'owner/name'")
    source = t.get("approval_source", "chat")
    if source not in TRACKER_APPROVAL_SOURCES:
        errs.append("tracker.approval_source must be one of: %s" % ", ".join(TRACKER_APPROVAL_SOURCES))
    elif source != "chat":
        approvers = t.get("approvers")
        if not (isinstance(approvers, list) and approvers
                and all(isinstance(a, str) and a for a in approvers)):
            errs.append("tracker.approvers must be a non-empty list of logins when approval_source is not 'chat'")
    approvers = t.get("approvers")
    if isinstance(approvers, list) and t.get("bot_login") in approvers:
        errs.append("tracker.bot_login must not be one of tracker.approvers")
    # The bridge adopts mirrored objects only from bot_login (or an approver),
    # so the automation identity is needed even when approvals stay in chat.
    if not (isinstance(t.get("bot_login"), str) and t.get("bot_login")):
        errs.append("tracker.bot_login is required when tracker.kind is github-projects")
    return errs


def validate_profile(p):
    """Return a list of error strings (empty when the profile is valid)."""
    errs = []
    for key in ("profile", "mode", "root", "spec", "roles", "next"):
        if key not in p or p[key] in (None, "", [], {}):
            errs.append("missing required key '%s'" % key)
    if p.get("protocol_version", PROTOCOL_VERSION) != PROTOCOL_VERSION:
        errs.append("protocol_version must be %d" % PROTOCOL_VERSION)
    if "mode" in p and p["mode"] not in ("orchestrated", "user-mediated"):
        errs.append("mode must be 'orchestrated' or 'user-mediated'")
    if p.get("scope_key", "change") not in ("change", "capability"):
        errs.append("scope_key must be 'change' or 'capability'")
    spec = p.get("spec")
    if spec is not None and not isinstance(spec, dict):
        errs.append("'spec' must be a mapping")
    elif isinstance(spec, dict) and spec.get("kind") not in ("openspec", "none"):
        errs.append("spec.kind must be 'openspec' or 'none'")
    errs.extend(validate_tracker(p.get("tracker")))

    roles = p.get("roles")
    role_names = set()
    if isinstance(roles, dict):
        for name, agents in roles.items():
            if not is_str_or_list(agents):
                errs.append("roles.%s must be an agent name or a list of agent names" % name)
            role_names.add(name)
    elif roles is not None:
        errs.append("'roles' must be a mapping role -> agent(s)")

    limits = p.get("limits")
    if limits is not None and not isinstance(limits, dict):
        errs.append("'limits' must be a mapping")
        limits = None
    limit_names = set(limits or {})

    counters = p.get("counters")
    if counters is not None:
        if not isinstance(counters, dict):
            errs.append("'counters' must be a mapping")
        else:
            for name, spec_c in counters.items():
                if not isinstance(spec_c, dict) or not spec_c:
                    errs.append("counters.%s must be a non-empty mapping" % name)
                    continue
                for k in spec_c:
                    if k not in COUNTER_KEYS:
                        errs.append("counters.%s: unknown key '%s'" % (name, k))
                if spec_c.get("scope", "task") not in ("task", "change"):
                    errs.append("counters.%s.scope must be 'task' or 'change'" % name)

    secs = p.get("required_sections")
    if secs is not None:
        if not isinstance(secs, dict):
            errs.append("'required_sections' must be a mapping")
        else:
            for kind, names in secs.items():
                if kind not in KINDS:
                    errs.append("required_sections: unknown kind '%s'" % kind)
                elif not isinstance(names, list) or not all(isinstance(x, str) for x in names):
                    errs.append("required_sections.%s must be a list of strings" % kind)

    vals = p.get("values")
    if vals is not None:
        if not isinstance(vals, dict):
            errs.append("'values' must be a mapping")
        else:
            for kind, fields in vals.items():
                if kind not in KINDS or not isinstance(fields, dict):
                    errs.append("values.%s must be a known kind with a field mapping" % kind)
                    continue
                for field, allowed in fields.items():
                    if not is_str_or_list(allowed) or not isinstance(allowed, list):
                        errs.append("values.%s.%s must be a list of strings" % (kind, field))

    ko = p.get("kind_overrides")
    if ko is not None:
        if not isinstance(ko, dict) or any(v not in KINDS for v in ko.values()):
            errs.append("'kind_overrides' must map file names to known kinds")

    fb = p.get("fallback", "none")
    if fb != "none" and fb not in role_names:
        errs.append("fallback must be 'none' or a role name (got %r)" % (fb,))

    rules = p.get("next")
    if isinstance(rules, list):
        for i, rule in enumerate(rules):
            tag = "next[%d]" % i
            if (not isinstance(rule, dict) or "when" not in rule or "then" not in rule
                    or set(rule) - {"when", "then"}):
                errs.append("%s: each rule needs exactly 'when' (mapping) and 'then'" % tag)
                continue
            when, then = rule["when"], rule["then"]
            if not isinstance(when, dict) or not when:
                errs.append("%s.when must be a non-empty mapping" % tag)
                continue
            for k, v in when.items():
                if k not in MATCHERS:
                    errs.append("%s.when: unknown matcher '%s' (allowed: %s)"
                                % (tag, k, ", ".join(MATCHERS)))
                    continue
                msg = _check_matcher(k, v, limit_names)
                if msg:
                    errs.append("%s.when.%s: %s" % (tag, k, msg))
            if "limit_reached" in when and i != 0:
                errs.append("%s: a 'limit_reached' rule must be the first rule" % tag)
            if not isinstance(then, str) or (then not in role_names and then not in SPECIAL_ACTIONS):
                errs.append("%s.then must be a role name, 'escalate' or 'final-gate' (got %r)"
                            % (tag, then))
        if limit_names:
            first = rules[0] if rules else None
            if not (isinstance(first, dict) and isinstance(first.get("when"), dict)
                    and "limit_reached" in first["when"]):
                errs.append("next[0]: the profile defines limits, so the first rule must be "
                            "a 'limit_reached' rule")
    elif rules is not None:
        errs.append("'next' must be a list of rules")
    return errs


def normalize_profile(p):
    n = dict(p)
    n["protocol_version"] = PROTOCOL_VERSION
    n["scope_key"] = p.get("scope_key", "change")
    n["limits"] = dict(p.get("limits") or {})
    n["quality"] = dict(p.get("quality") or {})
    counters = dict(DEFAULT_COUNTERS)
    counters.update(p.get("counters") or {})
    n["counters"] = counters
    secs = dict(DEFAULT_SECTIONS)
    secs.update(p.get("required_sections") or {})
    n["required_sections"] = secs
    enums = {k: dict(v) for k, v in DEFAULT_ENUMS.items()}
    for kind, fields in (p.get("values") or {}).items():
        enums.setdefault(kind, {}).update(fields)
    n["enums"] = enums
    n["kind_overrides"] = dict(p.get("kind_overrides") or {})
    n["fallback"] = p.get("fallback", "none")
    n["roles"] = {k: (list(v) if isinstance(v, list) else [v]) for k, v in p["roles"].items()}
    n["limits_zero_confirmed"] = p.get("limits_zero_confirmed") is True
    return n


def load_profile(path):
    """Return (profile, errors). profile is None when errors is non-empty."""
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        return None, ["cannot read profile: %s" % exc]
    try:
        data = yaml_load(text)
    except YamlError as exc:
        return None, ["invalid YAML: %s" % exc]
    if not isinstance(data, dict):
        return None, ["profile must be a mapping"]
    errors = validate_profile(data)
    if errors:
        return None, errors
    return normalize_profile(data), []


# -------------------------------------------------------- effective parameters

def parse_arg_pairs(pairs):
    """Parse ['limits.x=4', 'drift=true', ...] -> (sections, drift, zero_confirmed, ignored, errors)."""
    sections = {"limits": {}, "quality": {}}
    drift = None
    zero = False
    ignored = []
    errors = []
    for pair in pairs or []:
        if "=" not in pair:
            errors.append(("args", "expected key=value, got %r" % pair))
            continue
        key, raw = pair.split("=", 1)
        key = key.strip()
        try:
            value = yaml_scalar(raw)
        except YamlError as exc:
            errors.append(("args", "%s: %s" % (key, exc)))
            continue
        if key == "drift":
            if isinstance(value, bool):
                drift = value
            else:
                errors.append(("args", "drift must be true or false"))
        elif key == "limits_zero_confirmed":
            zero = value is True
        elif "." in key and key.split(".", 1)[0] in sections:
            section, name = key.split(".", 1)
            sections[section][name] = value
        else:
            ignored.append(key)
    return sections, drift, zero, ignored, errors


def effective_params(profile, override_path=None, arg_pairs=None):
    """Resolve limits/quality with precedence profile < override file < args."""
    res = {"limits": {}, "quality": {}, "sources": {}, "errors": [], "drift": None, "ignored": []}
    known = set(profile.get("limits") or {})

    def apply(section, mapping, source, zero_ok):
        if mapping is None:
            return
        if not isinstance(mapping, dict):
            res["errors"].append((source, "'%s' must be a mapping" % section))
            return
        for name, value in mapping.items():
            if section == "limits":
                if name not in known:
                    res["errors"].append((source, "unknown limit '%s' (profile defines: %s)"
                                          % (name, ", ".join(sorted(known)) or "none")))
                    continue
                if isinstance(value, bool) or not isinstance(value, int):
                    res["errors"].append((source, "limits.%s must be an integer >= 1 (got %r)"
                                          % (name, value)))
                    continue
                if value < 0 or (value == 0 and not zero_ok):
                    res["errors"].append((source, "limits.%s must be an integer >= 1 (got %d); "
                                          "0 needs 'limits_zero_confirmed: true' in the same source"
                                          % (name, value)))
                    continue
            res[section][name] = value
            res["sources"]["%s.%s" % (section, name)] = source

    apply("limits", profile.get("limits"), "profile", profile.get("limits_zero_confirmed") is True)
    apply("quality", profile.get("quality"), "profile", False)

    if override_path:
        source = "override (%s)" % os.path.basename(override_path)
        try:
            with open(override_path, encoding="utf-8") as fh:
                data = yaml_load(fh.read())
        except (OSError, YamlError) as exc:
            res["errors"].append((source, "cannot load override file: %s" % exc))
            data = None
        if data is not None:
            if not isinstance(data, dict):
                res["errors"].append((source, "override file must be a mapping"))
            else:
                zero_ok = data.get("limits_zero_confirmed") is True
                apply("limits", data.get("limits"), source, zero_ok)
                apply("quality", data.get("quality"), source, False)

    if arg_pairs:
        sections, drift, zero, ignored, errs = parse_arg_pairs(arg_pairs)
        res["errors"].extend(errs)
        res["drift"] = drift
        res["ignored"] = ignored
        apply("limits", sections["limits"], "args", zero)
        apply("quality", sections["quality"], "args", False)
    return res


# --------------------------------------------------------------------- records

class Record(object):
    def __init__(self, path):
        self.path = path
        self.name = os.path.basename(path)
        self.stem = self.name[:-3] if self.name.lower().endswith(".md") else self.name
        self.fm = {}
        self.body = ""
        self.sections = []
        self.kind = None
        self.id = self.stem
        self.role = None
        self.created = ""
        self.error = None


def load_records(dirpath, profile):
    agent_role = {}
    for role, agents in profile["roles"].items():
        for agent in agents:
            agent_role.setdefault(norm_agent(agent), role)
    out = []
    for name in sorted(os.listdir(dirpath)):
        path = os.path.join(dirpath, name)
        if (not name.lower().endswith(".md") or name.startswith("_")
                or name.lower() == "readme.md" or not os.path.isfile(path)):
            continue
        rec = Record(path)
        try:
            with open(path, encoding="utf-8") as fh:
                rec.fm, rec.body = parse_frontmatter(fh.read())
        except (OSError, UnicodeDecodeError, YamlError) as exc:
            rec.error = str(exc)
            out.append(rec)
            continue
        rec.sections = split_sections(rec.body)
        rec.kind = profile["kind_overrides"].get(name, rec.fm.get("kind"))
        if rec.fm.get("id") not in (None, ""):
            rec.id = str(rec.fm["id"])
        rec.created = str(rec.fm.get("createdAt") or "")
        if rec.fm.get("role"):
            rec.role = str(rec.fm["role"])
        else:
            party = rec.fm.get("to") if rec.kind == "work-order" else rec.fm.get("from")
            if party not in (None, ""):
                rec.role = agent_role.get(norm_agent(party))
        out.append(rec)
    return out


def refs_of(rec):
    return [norm_ref(r) for r in as_list(rec.fm.get("refs"))]


def task_of(rec, by_id, depth=0):
    task = rec.fm.get("task")
    if task not in (None, ""):
        return str(task)
    if rec.kind == "work-order":
        return rec.id
    if depth < 6:
        for ref in refs_of(rec):
            target = by_id.get(ref)
            if target is not None and target is not rec:
                found = task_of(target, by_id, depth + 1)
                if found:
                    return found
    return None


# ----------------------------------------------------------------------- board

def _task_status(work_orders):
    states = [str(w.fm.get("status")) for w in work_orders if str(w.fm.get("status")) != "cancelled"]
    if not states:
        return "cancelled"
    if "blocked" in states:
        return "blocked"
    if all(s in DONE_STATUSES for s in states):
        return "done"
    if "in-progress" in states:
        return "in-progress"
    return "pending"


def _counter_matches(spec, rec):
    for key in ("kind", "role", "outcome", "status"):
        if key in spec:
            have = rec.kind if key == "kind" else rec.role if key == "role" else rec.fm.get(key)
            if not value_in(spec[key], have):
                return False
    return True


def compute_state(records, profile, params, ext_drift=False):
    recs = [r for r in records if r.error is None and r.kind not in (None, "status")]
    by_id = {r.id: r for r in recs}
    task_of_rec = {r.id: task_of(r, by_id) for r in recs}

    tasks = {}
    for r in recs:
        if r.kind == "work-order":
            tasks.setdefault(task_of_rec[r.id], []).append(r)
    task_rows = []
    for tid in sorted(tasks):
        wos = tasks[tid]
        task_rows.append({"task": tid, "status": _task_status(wos),
                          "work_orders": [w.id for w in wos],
                          "roles": sorted({w.role for w in wos if w.role})})
    active = [t for t in task_rows if t["status"] != "cancelled"]
    all_done = bool(active) and all(t["status"] == "done" for t in active)

    resets = []
    for r in recs:
        if r.kind == "escalation" and str(r.fm.get("status")) == "answered":
            resets.append((task_of_rec[r.id], r.fm.get("limit"),
                           str(r.fm.get("answeredAt") or r.created)))

    clock = make_clock([r.created for r in recs] + [w for _, _, w in resets])

    def reset_time(name, task, scope):
        best = ""
        for rtask, rlimit, when in resets:
            if rlimit not in (None, "", name):
                continue
            if scope == "task" and rtask != task:
                continue
            if not best or clock(when) > clock(best):
                best = when
        return best

    task_ids = sorted(set(tasks) | {t for t in task_of_rec.values() if t})
    counters = []
    for name in profile["limits"]:
        limit = params["limits"].get(name)
        spec = profile["counters"].get(name)
        if spec is None:
            counters.append({"name": name, "scope": "-", "task": "-", "count": 0,
                             "limit": limit, "reached": False})
            continue
        scope = spec.get("scope", "task")
        instances = [None] if scope == "change" else (task_ids or [None])
        for task in instances:
            since = reset_time(name, task, scope)
            count = 0
            for r in recs:
                if since and clock(r.created) <= clock(since):
                    continue
                if scope == "task" and task_of_rec[r.id] != task:
                    continue
                if "max_field" in spec:
                    try:
                        count = max(count, int(r.fm.get(spec["max_field"]) or 0))
                    except (TypeError, ValueError):
                        pass
                elif _counter_matches(spec, r):
                    count += 1
            counters.append({"name": name, "scope": scope, "task": task or "-",
                             "count": count, "limit": limit,
                             # limit 0 (confirmed) means "escalate on the first failure", not "always"
                             "reached": limit is not None and count >= max(limit, 1)})
    reached = [c for c in counters if c["reached"]]

    delta_refs = set()
    for r in recs:
        if r.kind == "spec-delta":
            delta_refs.update(refs_of(r))
    uncovered = [r.id for r in recs
                 if r.kind in ("report", "diagnosis-report")
                 and str(r.fm.get("spec_impact", "none")) in DRIFT_IMPACTS
                 and r.id not in delta_refs]
    pending = len([r for r in recs if r.kind == "spec-delta"
                   and str(r.fm.get("status")) in ("proposed", "revise")])

    latest = None
    for r in sorted(recs, key=lambda x: (clock(x.created), x.name)):
        latest = r
    event = None
    if latest is not None:
        event = {"id": latest.id, "kind": latest.kind, "role": latest.role,
                 "outcome": latest.fm.get("outcome")}

    state = {"tasks": task_rows, "all_done": all_done, "counters": counters, "reached": reached,
             "uncovered": uncovered, "drift": bool(ext_drift) or bool(uncovered),
             "pending_deltas": pending, "event": event}
    state["next"] = next_action(profile, state)
    return state


def _rule_matches(when, state):
    event = state["event"]
    for key, want in when.items():
        if key in ("kind", "role", "outcome"):
            if event is None or not value_in(want, event.get(key)):
                return False
        elif key == "limit_reached":
            names = [c["name"] for c in state["reached"]]
            if want is True or want == "any":
                ok = bool(names)
            elif want is False:
                ok = not names
            else:
                ok = any(n in names for n in (want if isinstance(want, list) else [want]))
            if not ok:
                return False
        elif key == "drift":
            if bool(want) != state["drift"]:
                return False
        elif key == "all_tasks":
            if (want == "done") != state["all_done"]:
                return False
        elif key == "pending_deltas":
            if not cmp_spec(want, state["pending_deltas"]):
                return False
    return True


def _resolve(profile, then, rule, state):
    if then == "escalate":
        limit = None
        if state["reached"]:
            c = state["reached"][0]
            limit = {"name": c["name"], "task": c["task"]}
        return {"action": "escalate", "rule": rule, "limit": limit, "agents": []}
    if then == "final-gate":
        return {"action": "final-gate", "rule": rule, "limit": None, "agents": []}
    return {"action": then, "rule": rule, "limit": None, "agents": profile["roles"][then]}


def next_action(profile, state):
    for idx, rule in enumerate(profile["next"], 1):
        if _rule_matches(rule["when"], state):
            return _resolve(profile, rule["then"], idx, state)
    if profile["fallback"] != "none":
        return _resolve(profile, profile["fallback"], "fallback", state)
    return {"action": "none", "rule": None, "limit": None, "agents": []}


def format_next(nxt):
    action = nxt["action"]
    if action == "escalate":
        extra = ""
        if nxt["limit"]:
            extra = " limit=%s task=%s" % (nxt["limit"]["name"], nxt["limit"]["task"])
        return "NEXT: escalate%s rule=%s" % (extra, nxt["rule"])
    if action == "final-gate":
        return "NEXT: final-gate rule=%s" % nxt["rule"]
    if action == "none":
        return "NEXT: none (no rule matched)"
    return "NEXT: role=%s agent=%s rule=%s" % (action, ",".join(nxt["agents"]), nxt["rule"])


# ---------------------------------------------------------------------- status

def read_status(path):
    """Return (frontmatter, approvals_text_or_None); ({}, None) when absent/unreadable."""
    if not os.path.isfile(path):
        return {}, None
    try:
        with open(path, encoding="utf-8") as fh:
            fm, body = parse_frontmatter(fh.read())
    except (OSError, UnicodeDecodeError, YamlError):
        return {}, None
    for name, text in split_sections(body):
        if name.lower() == "approvals":
            return fm, text.strip("\n")
    return fm, None


def render_status(profile, state, params, sha, approvals, now):
    out = ["---", "kind: status", "id: status", 'profile: "%s"' % profile["profile"],
           'lastSyncedSha: "%s"' % sha, 'updatedAt: "%s"' % now, "---", "",
           "# Handoff status (generated by board.py - do not edit, except ## Approvals)", "",
           "## Tasks", "", "| Task | Status | Work orders | Roles |", "|---|---|---|---|"]
    if state["tasks"]:
        for t in state["tasks"]:
            out.append("| %s | %s | %s | %s |" % (t["task"], t["status"],
                                                 ", ".join(t["work_orders"]),
                                                 ", ".join(t["roles"])))
    else:
        out.append("| - | - | - | - |")
    out += ["", "## Counters", "", "| Counter | Scope | Task | Count | Limit | Reached |",
            "|---|---|---|---|---|---|"]
    for c in state["counters"]:
        out.append("| %s | %s | %s | %s | %s | %s |" % (
            c["name"], c["scope"], c["task"], c["count"],
            "-" if c["limit"] is None else c["limit"], "yes" if c["reached"] else "no"))
    if not state["counters"]:
        out.append("| - | - | - | - | - | - |")
    out += ["", "## Effective limits", "", "| Parameter | Value | Source |", "|---|---|---|"]
    for section in ("limits", "quality"):
        for name in sorted(params[section]):
            out.append("| %s.%s | %s | %s |" % (section, name, params[section][name],
                                                 params["sources"]["%s.%s" % (section, name)]))
    out += ["", "## State", "",
            "- drift: %s" % ("true" if state["drift"] else "false"),
            "- uncovered spec impacts: %s" % (", ".join(state["uncovered"]) or "none"),
            "- pending spec-deltas: %d" % state["pending_deltas"],
            "- all tasks done: %s" % ("yes" if state["all_done"] else "no"),
            "", "## Next action", "", format_next(state["next"]), "",
            "## Approvals", "", approvals if approvals else "(none recorded)", "",
            "## Last synced SHA", "", "`%s`" % sha, ""]
    return "\n".join(out)
