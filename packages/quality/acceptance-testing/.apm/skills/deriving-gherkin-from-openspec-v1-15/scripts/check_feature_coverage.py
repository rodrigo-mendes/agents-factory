#!/usr/bin/env python3
"""Check that every OpenSpec 1.15 scenario has a matching Gherkin scenario (traceability by script).

Usage:
  python check_feature_coverage.py [--spec-root <dir>] [--change <id>] --features <dir> [--json] [--strict]

Reads Markdown specs (<spec-root>/specs/**/spec.md; with --change also
<spec-root>/changes/<id>/specs/**/spec.md merged over them) and **/*.feature files. It never runs
anything. Spec parsing: `### Requirement: [R<n> ]<title>` and `#### Scenario: <name>` (exactly four #).
Delta files use `## ADDED|MODIFIED|REMOVED|RENAMED Requirements`: ADDED and MODIFIED replace or add a
requirement, REMOVED drops it from the merged set (no coverage required), RENAMED (FROM/TO lines)
moves the base requirement to its new name. A feature scenario (Scenario, Example, Scenario Outline,
Scenario Template) matches a spec scenario when it carries the requirement tag (@R<n>, or
@req-<slug> where slug is the kebab-case title of a requirement without R-id) and the same name
(case-insensitive, whitespace-normalized). Tags are inherited from Feature and Rule lines.

Report: missing (spec scenario without feature scenario), orphans (feature scenario with no
requirement tag or whose tag matches no requirement), covered, and per-requirement coverage.
empty_requirements lists requirements with zero scenarios (reason "no-scenarios"); they count as gaps.
--json prints one object {missing, orphans, covered, summary, parse_errors, empty_requirements}.
--strict also parses each feature with gherkin.parser.Parser (pip gherkin-official) and counts
parse errors as gaps; without that module a warning goes to stderr and the run continues.

Exit codes: 0 = complete, 1 = gaps found, 2 = nothing found (no spec requirements or no features),
3 = usage error.
Python 3.8+, standard library only.
"""
import argparse
import json
import os
import re
import sys

REQ_RE = re.compile(r"^###\s+Requirement:\s*(.+?)\s*#*\s*$")
SCEN_RE = re.compile(r"^####\s+Scenario:\s*(.+?)\s*#*\s*$")
DELTA_RE = re.compile(r"^##\s+(ADDED|MODIFIED|REMOVED|RENAMED)\s+Requirements\s*$", re.I)
H2_RE = re.compile(r"^##\s+")
RENAME_RE = re.compile(r"(FROM|TO):\s*`*\s*(?:###\s*)?(?:Requirement:\s*)?(.+?)\s*`*\s*$", re.I)
RID_RE = re.compile(r"^(R\d+)\b\s*(.*)$")
TAG_REQ_RE = re.compile(r"^@(r\d+|req-.+)$", re.I)
FEATURE_STEP_RE = re.compile(r"^(Scenario Outline|Scenario Template|Scenario|Example):\s*(.*)$")


class Parser3(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write("usage error: %s\n" % message)
        raise SystemExit(3)


def norm(text):
    return re.sub(r"\s+", " ", text.strip()).lower()


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def split_name(name):
    """Return (rid or None, title)."""
    m = RID_RE.match(name.strip())
    if m:
        return m.group(1), (m.group(2) or m.group(1)).strip()
    return None, name.strip()


def req_key(name):
    rid, title = split_name(name)
    return rid.lower() if rid else "req-" + slugify(title)


def req_tag(name):
    rid, title = split_name(name)
    return ("@" + rid) if rid else "@req-" + slugify(title)


def read_lines(path):
    with open(path, encoding="utf-8-sig", errors="replace") as handle:
        return handle.read().splitlines()


def find_files(root, suffix_match):
    found = []
    for base, dirs, files in os.walk(root):
        dirs.sort()
        for name in sorted(files):
            if suffix_match(name):
                found.append(os.path.join(base, name))
    return found


def parse_spec(path, is_delta):
    """Return (requirements by op, renames). requirements: op -> list of dict."""
    ops = {"BASE": [], "ADDED": [], "MODIFIED": [], "REMOVED": []}
    renames = []
    op = "ADDED" if is_delta else "BASE"
    current = None
    fenced = False
    pending_from = None
    for number, raw in enumerate(read_lines(path), 1):
        line = raw.strip()
        if line.startswith("```"):
            fenced = not fenced
            continue
        if fenced:
            continue
        delta = DELTA_RE.match(line)
        if delta:
            op = delta.group(1).upper()
            current = None
            continue
        if H2_RE.match(line):
            op = "ADDED" if is_delta else "BASE"
            current = None
            continue
        if op == "RENAMED":
            m = RENAME_RE.search(line)
            if m and m.group(1).upper() == "FROM":
                pending_from = m.group(2)
            elif m and m.group(1).upper() == "TO" and pending_from:
                renames.append((pending_from, m.group(2)))
                pending_from = None
            continue
        m = REQ_RE.match(line)
        if m:
            current = {"name": m.group(1), "scenarios": [], "file": path, "line": number}
            ops[op].append(current)
            continue
        m = SCEN_RE.match(line)
        if m and current is not None:
            current["scenarios"].append(m.group(1))
    return ops, renames


def capability_of(path, specs_dir):
    rel = os.path.relpath(os.path.dirname(path), specs_dir)
    return rel.replace(os.sep, "/")


def collect_requirements(spec_root, change):
    """Merged requirement list: base specs, then change deltas (RENAMED, REMOVED, MODIFIED, ADDED)."""
    merged = {}
    base_dir = os.path.join(spec_root, "specs")
    for path in find_files(base_dir, lambda n: n == "spec.md") if os.path.isdir(base_dir) else []:
        cap = capability_of(path, base_dir)
        ops, _ = parse_spec(path, False)
        for req in ops["BASE"]:
            merged.setdefault(cap, {})[req_key(req["name"])] = req
    if change:
        delta_dir = os.path.join(spec_root, "changes", change, "specs")
        deltas = find_files(delta_dir, lambda n: n == "spec.md") if os.path.isdir(delta_dir) else []
        for path in deltas:
            cap = capability_of(path, delta_dir)
            table = merged.setdefault(cap, {})
            ops, renames = parse_spec(path, True)
            for old, new in renames:
                req = table.pop(req_key(old), None)
                if req is not None:
                    req = dict(req, name=new)
                    table[req_key(new)] = req
            for req in ops["REMOVED"]:
                table.pop(req_key(req["name"]), None)
            for req in ops["MODIFIED"] + ops["ADDED"]:
                table[req_key(req["name"])] = req
    result = []
    for cap in sorted(merged):
        for req in merged[cap].values():
            rid, title = split_name(req["name"])
            result.append({
                "capability": cap, "id": rid, "title": title, "tag": req_tag(req["name"]),
                "scenarios": list(req["scenarios"]),
                "file": req["file"].replace(os.sep, "/"), "line": req["line"],
            })
    return result


def parse_feature(path, shown):
    scenarios = []
    feature_tags, rule_tags, pending = [], [], []
    rule_name = None
    in_doc = False
    for number, raw in enumerate(read_lines(path), 1):
        line = raw.strip()
        if line.startswith('"""') or line.startswith("```"):
            in_doc = not in_doc
            continue
        if in_doc or not line or line.startswith("#"):
            continue
        if line.startswith("@"):
            for token in line.split():
                if token.startswith("#"):
                    break
                if token.startswith("@"):
                    pending.append(token)
            continue
        if line.startswith("Feature:"):
            feature_tags, pending, rule_tags, rule_name = pending, [], [], None
            continue
        if line.startswith("Rule:"):
            rule_tags, rule_name, pending = pending, line[5:].strip(), []
            continue
        m = FEATURE_STEP_RE.match(line)
        if m:
            tags = feature_tags + rule_tags + pending
            scenarios.append({
                "name": m.group(2).strip(), "kind": m.group(1), "line": number, "file": shown,
                "rule": rule_name, "tags": tags,
            })
        pending = []
    return scenarios


def feature_scenarios(features_dir, strict):
    scenarios, parse_errors = [], []
    files = find_files(features_dir, lambda n: n.endswith(".feature")) if os.path.isdir(features_dir) else []
    gherkin_parser = None
    if strict:
        try:
            from gherkin.parser import Parser as gherkin_parser  # type: ignore
        except ImportError:
            sys.stderr.write("warning: module gherkin not importable (pip install gherkin-official); "
                             "--strict parse check skipped\n")
    for path in files:
        shown = path.replace(os.sep, "/")
        scenarios.extend(parse_feature(path, shown))
        if gherkin_parser is not None:
            try:
                gherkin_parser().parse("\n".join(read_lines(path)))
            except Exception as exc:  # parser raises CompositeParserException or ParserException
                parse_errors.append({"file": shown, "error": " ".join(str(exc).split())})
    return files, scenarios, parse_errors


def analyze(spec_root, change, features_dir, strict=False):
    requirements = collect_requirements(spec_root, change)
    files, scenarios, parse_errors = feature_scenarios(features_dir, strict)
    known_tags = {r["tag"].lower() for r in requirements}
    covered, missing, per_req, empty = [], [], [], []
    for req in requirements:
        done = 0
        for sname in req["scenarios"]:
            cands = [s for s in scenarios
                     if req["tag"].lower() in [t.lower() for t in s["tags"]] and norm(s["name"]) == norm(sname)]
            cands.sort(key=lambda s: os.path.basename(s["file"]) != req["capability"].split("/")[-1] + ".feature")
            entry = {"requirement": req["id"] or req["tag"], "title": req["title"],
                     "capability": req["capability"], "scenario": sname}
            if cands:
                done += 1
                entry.update(feature=cands[0]["file"], line=cands[0]["line"])
                covered.append(entry)
            else:
                entry.update(spec=req["file"], spec_line=req["line"])
                missing.append(entry)
        total = len(req["scenarios"])
        if total == 0:
            empty.append({"requirement": req["id"] or req["tag"], "title": req["title"],
                          "capability": req["capability"], "spec": req["file"],
                          "spec_line": req["line"], "reason": "no-scenarios"})
        per_req.append({"requirement": req["id"] or req["tag"], "title": req["title"],
                        "capability": req["capability"], "scenarios": total, "covered": done,
                        "status": "covered" if done == total and total else "gap"})
    orphans = []
    for s in scenarios:
        req_tags = [t.lower() for t in s["tags"] if TAG_REQ_RE.match(t)]
        if not req_tags:
            reason = "no-requirement-tag"
        elif not any(t in known_tags for t in req_tags):
            reason = "unknown-requirement"
        else:
            continue
        orphans.append({"scenario": s["name"], "feature": s["file"], "line": s["line"], "reason": reason})
    summary = {"requirements": len(requirements), "spec_scenarios": len(covered) + len(missing),
               "covered": len(covered), "missing": len(missing), "orphans": len(orphans),
               "empty_requirements": len(empty), "feature_files": len(files), "feature_scenarios": len(scenarios),
               "parse_errors": len(parse_errors), "per_requirement": per_req}
    return {"missing": missing, "orphans": orphans, "covered": covered, "summary": summary,
            "parse_errors": parse_errors, "empty_requirements": empty}


def print_text(result):
    s = result["summary"]
    print("requirements: %d | spec scenarios: %d | covered: %d | missing: %d | orphans: %d"
          % (s["requirements"], s["spec_scenarios"], s["covered"], s["missing"], s["orphans"]))
    for row in s["per_requirement"]:
        print("  %-6s %s: %d/%d (%s)" % (row["requirement"], row["title"], row["covered"],
                                         row["scenarios"], row["status"]))
    for m in result["missing"]:
        print("MISSING %s '%s' (%s:%d)" % (m["requirement"], m["scenario"], m["spec"], m["spec_line"]))
    for e in result["empty_requirements"]:
        print("EMPTY   %s '%s' has no scenarios (%s:%d): ask the spec owner, do not invent one"
              % (e["requirement"], e["title"], e["spec"], e["spec_line"]))
    for o in result["orphans"]:
        print("ORPHAN '%s' %s:%d (%s)" % (o["scenario"], o["feature"], o["line"], o["reason"]))
    for e in result["parse_errors"]:
        print("PARSE   %s: %s" % (e["file"], e["error"]))


def main(argv=None):
    ap = Parser3(description="OpenSpec scenario to Gherkin coverage check")
    ap.add_argument("--spec-root", default="openspec")
    ap.add_argument("--change")
    ap.add_argument("--features", required=True)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args(argv)
    result = analyze(args.spec_root, args.change, args.features, args.strict)
    s = result["summary"]
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print_text(result)
    if s["requirements"] == 0 or s["feature_files"] == 0:
        if not args.json:
            print("nothing found: need spec requirements and .feature files")
        return 2
    gaps = s["missing"] + s["orphans"] + s["parse_errors"] + s["empty_requirements"]
    return 1 if gaps else 0


if __name__ == "__main__":
    sys.exit(main())
