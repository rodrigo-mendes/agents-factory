#!/usr/bin/env python3
"""
render-mermaid.py  <book_md_path> <output_dir>

Extracts every ```mermaid block from book_md_path, renders each to PNG via
mmdc (Mermaid CLI, installed on demand via npx), saves the PNGs to output_dir,
and rewrites book_md_path in-place replacing each block with a Markdown image
reference.

Exit codes: 0 = all rendered, 1 = partial failure (some blocks kept as source),
            2 = mmdc unavailable (no changes made).
"""

import os
import re
import subprocess
import sys
import tempfile

MERMAID_PATTERN = re.compile(r"```mermaid\n(.*?)```", re.DOTALL)


def mmdc_available():
    try:
        result = subprocess.run(
            ["npx", "--yes", "@mermaid-js/mermaid-cli", "--version"],
            capture_output=True, text=True, timeout=60
        )
        return result.returncode == 0
    except Exception:
        return False


def render_block(mmd_content: str, output_path: str) -> bool:
    with tempfile.NamedTemporaryFile(suffix=".mmd", mode="w",
                                    delete=False, encoding="utf-8") as f:
        f.write(mmd_content)
        tmp_path = f.name
    try:
        result = subprocess.run(
            [
                "npx", "--yes", "@mermaid-js/mermaid-cli",
                "mmdc",
                "-i", tmp_path,
                "-o", output_path,
                "-b", "white",
                "--width", "1200",
            ],
            capture_output=True, text=True, timeout=120
        )
        return result.returncode == 0 and os.path.exists(output_path)
    except Exception:
        return False
    finally:
        os.unlink(tmp_path)


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <book_md_path> <output_dir>", file=sys.stderr)
        sys.exit(2)

    book_path = sys.argv[1]
    output_dir = sys.argv[2]

    if not os.path.exists(book_path):
        print(f"ERROR: {book_path} not found", file=sys.stderr)
        sys.exit(2)

    print("Checking mmdc availability...")
    if not mmdc_available():
        print("WARNING: mmdc (Mermaid CLI) not available via npx. Skipping P5.5.")
        print("Install with: npm install -g @mermaid-js/mermaid-cli")
        sys.exit(2)

    os.makedirs(output_dir, exist_ok=True)

    with open(book_path, "r", encoding="utf-8") as f:
        content = f.read()

    matches = list(MERMAID_PATTERN.finditer(content))
    total = len(matches)
    if total == 0:
        print("No Mermaid blocks found. Nothing to do.")
        sys.exit(0)

    print(f"Found {total} Mermaid block(s). Rendering...")

    rendered = 0
    failed = 0
    replacements = []

    for idx, match in enumerate(matches, start=1):
        mmd_content = match.group(1)
        png_filename = f"diag{idx:03d}.png"
        png_path = os.path.join(output_dir, png_filename)
        # relative path for Markdown reference (assets/diagrams/diagN.png)
        rel_path = os.path.relpath(png_path, os.path.dirname(book_path)).replace("\\", "/")

        print(f"  [{idx}/{total}] Rendering {png_filename}...", end=" ")
        if render_block(mmd_content, png_path):
            print("OK")
            replacements.append((match.start(), match.end(),
                                  f"![Diagrama {idx}]({rel_path})"))
            rendered += 1
        else:
            print("FAILED")
            replacements.append((match.start(), match.end(),
                                  f"<!-- MERMAID_RENDER_FAILED diag{idx:03d} -->\n"
                                  f"```mermaid\n{mmd_content}```"))
            failed += 1

    # Apply replacements in reverse order to preserve offsets
    new_content = content
    for start, end, replacement in reversed(replacements):
        new_content = new_content[:start] + replacement + new_content[end:]

    with open(book_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"\nDone: {rendered} rendered, {failed} failed.")
    print(f"PNGs saved to: {output_dir}")
    print(f"book.md updated in-place: {book_path}")

    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
