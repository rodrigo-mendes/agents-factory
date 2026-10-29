#!/usr/bin/env python3
"""Vendor the bridge scripts into a target repository (Python 3.8+, standard library only).

The workflows in assets/workflows/ run the scripts from ``.github/openspec-github/`` of the
target repository, because an Actions runner has no ``.claude/skills/``. This module copies:

  * this skill's scripts: gh_projects_sync.py, _gh.py, _model.py, gate_command.py, _vendor.py
  * the handoff-core scripts: _handoff_lib.py, _mini_yaml.py, check_records.py,
    detect_drift.py, board.py (located like _model.handoff_scripts_dir)
  * the family profile given with --profile, as handoff-profile.yaml

and writes ``MANIFEST.sha256`` (one ``<sha256>  <file>`` line per file, hashes taken over the
content with CRLF normalised to LF so a Windows checkout and a Linux runner agree). The
digest of the manifest itself is what ``gh_projects_sync.py bootstrap --vendor`` records in
github.yaml as ``vendor: {version, sha256}``.

Usage:
  python _vendor.py install <repo-root> --profile <yaml> [--apply]   # dry-run by default
  python _vendor.py verify <vendored-dir>                             # exit 0 ok, 1 mismatch
"""
import argparse
import hashlib
import os
import sys

VERSION = "1.0.0"
TARGET = os.path.join(".github", "openspec-github")
MANIFEST = "MANIFEST.sha256"
OWN = ("gh_projects_sync.py", "_gh.py", "_model.py", "gate_command.py", "_vendor.py")
HANDOFF = ("_handoff_lib.py", "_mini_yaml.py", "check_records.py", "detect_drift.py", "board.py")
PROFILE_NAME = "handoff-profile.yaml"
HERE = os.path.dirname(os.path.abspath(__file__))


def normalized_sha(data):
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def sources(profile_path, handoff_dir):
    """[(source path, vendored file name)] in manifest order."""
    out = [(os.path.join(HERE, n), n) for n in OWN]
    out += [(os.path.join(handoff_dir, n), n) for n in HANDOFF]
    out.append((profile_path, PROFILE_NAME))
    return out


def build_manifest(entries):
    """entries: [(name, bytes)] -> (manifest text, digest)."""
    lines = ["# openspec-github vendor %s" % VERSION]
    lines += ["%s  %s" % (normalized_sha(data), name) for name, data in entries]
    text = "\n".join(lines) + "\n"
    return text, normalized_sha(text.encode("utf-8"))


def install(repo_root, profile_path, apply, handoff_dir, out=print):
    """Copy the files; return {"version", "sha256"}. Dry-run prints PLAN lines and writes nothing."""
    target = os.path.join(repo_root, TARGET)
    entries = []
    for src, name in sources(profile_path, handoff_dir):
        if not os.path.isfile(src):
            raise OSError("vendor source missing: %s" % src)
        with open(src, "rb") as fh:
            entries.append((name, fh.read()))
    manifest, digest = build_manifest(entries)
    if not apply:
        for name, _ in entries:
            out("PLAN write %s" % os.path.join(TARGET, name).replace("\\", "/"))
        out("PLAN write %s (sha256 %s)" % (os.path.join(TARGET, MANIFEST).replace("\\", "/"), digest))
        return {"version": VERSION, "sha256": digest}
    os.makedirs(target, exist_ok=True)
    for name, data in entries + [(MANIFEST, manifest.encode("utf-8"))]:
        with open(os.path.join(target, name), "wb") as fh:
            fh.write(data.replace(b"\r\n", b"\n"))
        out("WROTE %s" % os.path.join(TARGET, name).replace("\\", "/"))
    return {"version": VERSION, "sha256": digest}


def verify(directory):
    """Return a list of problems (empty when every file matches MANIFEST.sha256)."""
    path = os.path.join(directory, MANIFEST)
    if not os.path.isfile(path):
        return ["%s not found" % path]
    problems = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            want, _, name = line.partition("  ")
            fpath = os.path.join(directory, name)
            if os.path.basename(name) != name:
                problems.append("unexpected path in manifest: %r" % name)
                continue
            if not os.path.isfile(fpath):
                problems.append("missing %s" % name)
                continue
            with open(fpath, "rb") as fh2:
                if normalized_sha(fh2.read()) != want:
                    problems.append("modified %s (sha256 differs from the manifest)" % name)
    return problems


def main(argv=None):
    ap = argparse.ArgumentParser(prog="_vendor.py", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd")
    p_inst = sub.add_parser("install", help="copy the scripts into <repo>/.github/openspec-github/")
    p_inst.add_argument("repo_root")
    p_inst.add_argument("--profile", required=True, help="family handoff profile to vendor")
    p_inst.add_argument("--apply", action="store_true", help="write the files (default: dry-run)")
    p_ver = sub.add_parser("verify", help="check the vendored files against MANIFEST.sha256")
    p_ver.add_argument("directory")
    args = ap.parse_args(argv)
    if args.cmd == "verify":
        problems = verify(args.directory)
        for p in problems:
            sys.stderr.write("vendor: %s\n" % p)
        if not problems:
            print("vendor OK")
        return 1 if problems else 0
    if args.cmd == "install":
        sys.path.insert(0, HERE)
        try:
            import _model
            result = install(args.repo_root, args.profile, args.apply, _model.handoff_scripts_dir())
        except (RuntimeError, OSError) as exc:
            sys.stderr.write("error: %s\n" % exc)
            return 1
        print("vendor %s sha256 %s" % (result["version"], result["sha256"]))
        return 0
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
