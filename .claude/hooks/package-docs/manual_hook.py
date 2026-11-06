#!/usr/bin/env python3
"""
Hook shim for documenting-agent-packages: finds check_manual.py where APM installed the skill and runs it.

APM copies a hook script next to the hook definition, but the checker itself ships inside the skill folder,
whose location depends on the target (.claude/skills, .github/skills, .cursor/skills ...). This shim looks for
it in each known target folder of the project, then in a source checkout (packages/**/.apm/skills), and
forwards the hook JSON on stdin and the exit code. If the checker cannot be found it exits 0 without a word,
so a missing install never blocks editing.

Usage (from a hook definition):  python manual_hook.py post-edit | stop
Exit codes: whatever check_manual.py returns (0 fine, 2 problem); 0 when it is not installed.
Stdlib only.
"""
import os
import subprocess
import sys
from pathlib import Path

SKILL = "documenting-agent-packages"
TARGET_DIRS = (".claude", ".github", ".cursor", ".codex", ".gemini", ".windsurf", ".kiro", ".agents")
EVENT_ARGS = {
    "post-edit": ["--hook", "post-edit"],
    "stop": ["--hook", "stop", "--skip-stale"],
}


def project_root() -> Path:
    for var in ("CLAUDE_PROJECT_DIR", "CURSOR_PROJECT_DIR", "GEMINI_PROJECT_DIR"):
        if os.environ.get(var):
            return Path(os.environ[var])
    return Path.cwd()


def find_checker(root: Path):
    for target in TARGET_DIRS:
        candidate = root / target / "skills" / SKILL / "scripts" / "check_manual.py"
        if candidate.is_file():
            return candidate
    for candidate in sorted(root.glob(f"packages/**/.apm/skills/{SKILL}/scripts/check_manual.py")):
        return candidate
    return None


def main(argv=None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if not args or args[0] not in EVENT_ARGS:
        print(f"usage: manual_hook.py {' | '.join(EVENT_ARGS)}", file=sys.stderr)
        return 0
    root = project_root()
    checker = find_checker(root)
    if checker is None:
        return 0
    payload = sys.stdin.buffer.read()
    done = subprocess.run([sys.executable, str(checker), "--root", str(root), *EVENT_ARGS[args[0]]],
                          input=payload, capture_output=True)
    if done.stderr:
        sys.stderr.buffer.write(done.stderr)
    if done.stdout:
        sys.stdout.buffer.write(done.stdout)
    return done.returncode


if __name__ == "__main__":
    sys.exit(main())
