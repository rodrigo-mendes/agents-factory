#!/usr/bin/env python3
"""Portable helpers for agents on Windows, macOS and Linux (standard library only).

Replaces `date -u`, `sha256sum` and ad-hoc hashing of directories, so every agent
and verifier uses the SAME method and the SAME output on any OS.

Usage:
  python portable.py now                 -> 2026-11-03T14:00:00Z   (UTC, ISO 8601)
  python portable.py sha256 <file>       -> <hex>                  (sha256 of one file)
  python portable.py dirhash <dir>       -> <hex>                  (sha256 of a directory tree)

dirhash method (shared by the front-end integrator, the pipeline artifact check and the
static-site verifier): list every regular file below <dir> with a POSIX relative path,
sort the paths bytewise, compute the sha256 of each file, build one line per file
"<sha256>  <relative path>\n" and print the sha256 of that text (UTF-8). Symlinks and
directories are ignored. Line endings of the files are NOT normalised.

Read-only: it never writes, deletes or runs other programs. Exit 0 on success, 2 on a usage
error or a missing path.
"""
import datetime
import hashlib
import os
import sys


def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def dirhash(root):
    rels = []
    for base, _dirs, files in os.walk(root, followlinks=False):
        for name in files:
            full = os.path.join(base, name)
            if os.path.islink(full) or not os.path.isfile(full):
                continue
            rels.append(os.path.relpath(full, root).replace(os.sep, "/"))
    rels.sort(key=lambda r: r.encode("utf-8"))
    lines = "".join("%s  %s\n" % (_sha256_file(os.path.join(root, r)), r) for r in rels)
    return hashlib.sha256(lines.encode("utf-8")).hexdigest()


def main(argv):
    if len(argv) == 2 and argv[1] == "now":
        print(datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
        return 0
    if len(argv) == 3 and argv[1] == "sha256" and os.path.isfile(argv[2]):
        print(_sha256_file(argv[2]))
        return 0
    if len(argv) == 3 and argv[1] == "dirhash" and os.path.isdir(argv[2]):
        print(dirhash(argv[2]))
        return 0
    sys.stderr.write(__doc__.split("\n\n")[0] + "\nusage: portable.py now | sha256 <file> | dirhash <dir>\n")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
