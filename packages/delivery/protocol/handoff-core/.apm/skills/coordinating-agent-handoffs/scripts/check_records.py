#!/usr/bin/env python3
"""Validate handoff records against the protocol (v1) and a family profile.

Usage:
  python check_records.py <dir> --profile <yaml> [--override <yaml>]

Prints one line per error as "<file>: <message>" on stdout.
Exit codes: 0 = all records valid, 1 = at least one error.
Python 3.8+, standard library only.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import _handoff_lib as lib  # noqa: E402


def check(dirpath, profile_path, override_path=None):
    """Return (errors, record_count); errors is a list of (file, message)."""
    profile, perrs = lib.load_profile(profile_path)
    if perrs:
        label = os.path.basename(profile_path)
        return [(label, e) for e in perrs], 0
    errors = list(lib.effective_params(profile, override_path)["errors"])
    if not os.path.isdir(dirpath):
        return errors + [(dirpath, "not a directory")], 0

    records = lib.load_records(dirpath, profile)
    scope_key = profile["scope_key"]
    seen = {}
    by_id = {}
    for rec in records:
        if rec.error is None:
            if rec.id in seen:
                errors.append((rec.name, "duplicate id '%s' (also used by %s)" % (rec.id, seen[rec.id])))
            else:
                seen[rec.id] = rec.name
                by_id[rec.id] = rec

    for rec in records:
        if rec.error is not None:
            errors.append((rec.name, rec.error))
            continue
        kind = rec.kind
        if kind in (None, ""):
            errors.append((rec.name, "missing required field 'kind'"))
            continue
        if kind not in lib.KINDS:
            errors.append((rec.name, "unknown kind %r (expected one of: %s)"
                           % (kind, ", ".join(lib.KINDS))))
            continue
        if kind == "status":
            continue
        fm = rec.fm
        for field in ("from", "to", scope_key, "createdAt"):
            if fm.get(field) in (None, ""):
                errors.append((rec.name, "missing required field '%s'" % field))
        created = fm.get("createdAt")
        if created not in (None, "") and not lib.ISO_RE.match(str(created)):
            errors.append((rec.name, "createdAt must be an ISO 8601 timestamp (got %r)" % created))

        enum_field = lib.REQUIRED_ENUM_FIELD.get(kind)
        if enum_field:
            value = fm.get(enum_field)
            allowed = profile["enums"].get(kind, {}).get(enum_field, [])
            if value in (None, ""):
                errors.append((rec.name, "missing required field '%s'" % enum_field))
            elif str(value) not in allowed:
                errors.append((rec.name, "invalid %s %r for kind %s (allowed: %s)"
                               % (enum_field, value, kind, ", ".join(allowed))))
        if kind == "verify" and fm.get("stage") in (None, ""):
            errors.append((rec.name, "missing required field 'stage'"))

        for ref in lib.refs_of(rec):
            target = by_id.get(ref)
            if target is None:
                errors.append((rec.name, "broken ref '%s' (no record with that id)" % ref))
            elif kind == "verify" and lib.norm_agent(target.fm.get("from", "")) == \
                    lib.norm_agent(fm.get("from", "")):
                errors.append((rec.name, "verifier '%s' is the author of '%s' (the producer never "
                               "verifies its own work)" % (fm.get("from"), ref)))

        have = {name.lower() for name, _ in rec.sections}
        for section in profile["required_sections"].get(kind, []):
            if section.lower() not in have:
                errors.append((rec.name, "missing required section '## %s'" % section))

        if kind == "escalation":
            for name, text in rec.sections:
                if name.lower() == "options":
                    n = lib.count_top_items(text)
                    if n < 2 or n > 4:
                        errors.append((rec.name, "section '## Options' must list 2-4 options (found %d)" % n))
        if kind == "spec-delta" and profile["spec"].get("kind") == "openspec":
            if not have.intersection(lib.DELTA_HEADINGS):
                errors.append((rec.name, "spec-delta needs at least one of '## ADDED Requirements', "
                               "'## MODIFIED Requirements', '## REMOVED Requirements', "
                               "'## RENAMED Requirements'"))
    return errors, len(records)


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="check_records.py",
        description="Validate handoff records (protocol v1) against a family profile. "
                    "Exit 0 = valid, 1 = errors (one 'file: message' line each).")
    ap.add_argument("dir", help="handoff directory containing the records (*.md)")
    ap.add_argument("--profile", required=True, help="handoff-profile.yaml of the family")
    ap.add_argument("--override", help="optional project override YAML (limits/quality only)")
    args = ap.parse_args(argv)
    errors, count = check(args.dir, args.profile, args.override)
    for name, message in errors:
        print("%s: %s" % (name, message))
    if errors:
        return 1
    print("OK: %d record(s) valid" % count)
    return 0


if __name__ == "__main__":
    sys.exit(main())
