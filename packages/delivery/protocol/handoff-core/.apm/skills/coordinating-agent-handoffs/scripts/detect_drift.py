#!/usr/bin/env python3
"""Detect code drift: files changed since the last synced SHA that no report accounts for.

Usage:
  python detect_drift.py <repo> --change <handoff-dir> [--include-worktree]

Reads lastSyncedSha from <handoff-dir>/status.md, runs `git diff --name-only <sha>..HEAD`
and lists changed files that are not mentioned in the "## Spec impact", "## Files",
"## Files changed" or "## What changed" sections of any report / deploy-report /
diagnosis-report in <handoff-dir> (records are recognised by their `kind`; a legacy file-name
prefix is only a fallback for records without `kind`), and in the
same sections of every ACCEPTED spec-delta (proposed, revise and rejected deltas cover nothing).
A path counts as mentioned only on an exact match (a backticked path or a whole token);
mentioning a directory does NOT cover the files under it.
Files under the handoff directory and under openspec/ are never reported (spec side).

Only COMMITTED changes (<sha>..HEAD) are seen by default: an uncommitted hand edit is invisible
until it is committed. Use --include-worktree to also check uncommitted and untracked files, e.g.
before archiving or at the final gate while edits are still in the working tree.

Exit codes: 0 = no drift, 2 = drift (one 'DRIFT: <path>' line each), 1 = error
(git missing, no synced SHA, git failure).
Python 3.8+ (unverified, register U1), standard library only.
"""
import argparse
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import _handoff_lib as lib  # noqa: E402
from _mini_yaml import YamlError, parse_frontmatter  # noqa: E402

FILE_SECTIONS = ("spec impact", "files", "files changed", "what changed")
REPORT_KINDS = ("report", "deploy-report", "diagnosis-report")


class DriftError(Exception):
    pass


def _git(repo, git_args):
    cmd = ["git", "-c", "core.quotepath=off", "-C", repo] + git_args
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              encoding="utf-8", errors="replace")
    except FileNotFoundError:
        raise DriftError("git executable not found")
    if proc.returncode != 0:
        raise DriftError("git %s failed: %s" % (" ".join(git_args), proc.stderr.strip()))
    return [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]


def _mentioned_text(change_dir):
    chunks = []
    for name in sorted(os.listdir(change_dir)):
        path = os.path.join(change_dir, name)
        if not name.lower().endswith(".md") or name == "status.md" or not os.path.isfile(path):
            continue
        try:
            with open(path, encoding="utf-8") as fh:
                fm, body = parse_frontmatter(fh.read())
        except (OSError, UnicodeDecodeError, YamlError):
            continue
        kind = str(fm.get("kind", ""))
        # An ACCEPTED spec-delta also covers the paths in these sections (e.g. a hand edit the user
        # accepted into the spec but has not committed yet); proposed/revise/rejected cover nothing.
        accepted_delta = kind == "spec-delta" and str(fm.get("status", "")) == "accepted"
        if (kind not in REPORT_KINDS and not accepted_delta
                and not name.lower().startswith(("report", "deploy-report", "diagnosis"))):
            continue
        for heading, text in lib.split_sections(body):
            if heading.lower() in FILE_SECTIONS:
                chunks.append(text)
    return "\n".join(chunks).replace("\\", "/")


_TOKEN_SPLIT = re.compile(r"[\s,;()\[\]<>\"']+")


def _clean_token(tok):
    tok = tok.strip("`*").rstrip(".:")
    if tok.startswith("./"):
        tok = tok[2:]
    return tok


def mentioned_paths(text):
    """Return the set of paths a report names: backticked spans and whole tokens.

    Matching is exact: `src/App.java` does not cover `src/App.javascript` or `xsrc/App.java.bak`,
    and a mentioned directory does not cover the files under it.
    """
    found = set()
    for span in re.findall(r"`([^`\n]+)`", text):
        found.add(_clean_token(span.strip()))
    for tok in _TOKEN_SPLIT.split(text):
        found.add(_clean_token(tok))
    found.discard("")
    return found


def find_drift(repo, change_dir, include_worktree=False):
    """Return the sorted list of drifted paths. Raises DriftError on failure."""
    fm, _ = lib.read_status(os.path.join(change_dir, "status.md"))
    sha = str(fm.get("lastSyncedSha") or "").strip()
    if not sha or sha.lower() == "none":
        raise DriftError("no lastSyncedSha in %s (run board.py --sync-sha <sha> first)"
                         % os.path.join(change_dir, "status.md"))
    changed = set(_git(repo, ["diff", "--name-only", "%s..HEAD" % sha]))
    if include_worktree:
        changed.update(_git(repo, ["diff", "--name-only", "HEAD"]))
        changed.update(_git(repo, ["ls-files", "--others", "--exclude-standard"]))
    try:
        change_rel = os.path.relpath(os.path.abspath(change_dir), os.path.abspath(repo))
    except ValueError as exc:  # e.g. different Windows drives
        raise DriftError("cannot relate --change %s to repo %s: %s" % (change_dir, repo, exc))
    change_rel = change_rel.replace("\\", "/").rstrip("/") + "/"
    mentioned = mentioned_paths(_mentioned_text(change_dir))
    drift = []
    for path in sorted(changed):
        norm = path.replace("\\", "/")
        if norm.startswith("openspec/") or norm.startswith(change_rel):
            continue
        if norm not in mentioned:
            drift.append(norm)
    return drift


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="detect_drift.py",
        description="List files changed since the last synced SHA that no report mentions. "
                    "Exit 0 = no drift, 2 = drift, 1 = error.")
    ap.add_argument("repo", help="git repository root")
    ap.add_argument("--change", required=True, help="handoff directory holding status.md and reports")
    ap.add_argument("--include-worktree", action="store_true",
                    help="also check uncommitted and untracked files (without it, only "
                         "committed changes since the synced SHA are seen)")
    args = ap.parse_args(argv)
    if not os.path.isdir(args.change):
        sys.stderr.write("error: %s is not a directory\n" % args.change)
        return 1
    try:
        drift = find_drift(args.repo, args.change, args.include_worktree)
    except DriftError as exc:
        sys.stderr.write("error: %s\n" % exc)
        return 1
    for path in drift:
        print("DRIFT: %s" % path)
    if drift:
        print("%d file(s) changed since the last synced SHA are not covered by any report" % len(drift))
        return 2
    print("NO DRIFT")
    return 0


if __name__ == "__main__":
    sys.exit(main())
