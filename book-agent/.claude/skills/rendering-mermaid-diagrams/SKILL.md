---
name: rendering-mermaid-diagrams
description: Renders all Mermaid diagram blocks in a completed book.md to PNG images and rewrites the file with Markdown image references, making diagrams visible in EPUB/Kindle readers.
version: "1.0"
model: claude-sonnet-5
context: fork
disable-model-invocation: true
---

# Skill: rendering-mermaid-diagrams

Converts raw ` ```mermaid ``` ` blocks in a completed `book.md` into rendered PNG images using the Mermaid CLI (`mmdc` via `npx`), then rewrites `book.md` in-place with `![Diagrama N](assets/diagrams/diagN.png)` references.

This is **P5.5** in the full pipeline — run after `book.md` is assembled (P5) and before EPUB formatting (P7).

## Usage

```
/rendering-mermaid-diagrams <path/to/book.md>
```

**Example:**
```
/rendering-mermaid-diagrams Books/arquitetura-baseada-em-eventos/book.md
```

## Pre-requisites

- Node.js + npx available in PATH
- (`mmdc` is installed on demand via `npx --yes @mermaid-js/mermaid-cli`)

## What it does

1. Checks `mmdc` availability via npx
2. Extracts every ` ```mermaid ``` ` block from `book.md`
3. Renders each block to `PNG` (1200px wide, white background) using `mmdc`
4. Saves PNGs to `{book_dir}/assets/diagrams/diag001.png`, `diag002.png`, …
5. Rewrites `book.md` in-place: each block → `![Diagrama N](assets/diagrams/diagN.png)`
6. Prints a summary: N rendered, M failed

Blocks that fail to render are kept as-is with a `<!-- MERMAID_RENDER_FAILED -->` comment so the book is never silently broken.

## Fallback

If `mmdc` is unavailable (exit 2), `book.md` is **not modified**. The `book-formatter` still handles raw Mermaid blocks via the `<pre class="mermaid-source">` fallback.

## Output structure

```
Books/{slug}/
├── book.md                    ← rewritten with ![...](assets/...) references
└── assets/diagrams/
    ├── diag001.png
    ├── diag002.png
    └── ...
```

## Next step

After this skill completes, run:
- `/translating-book Books/{slug}/book.md target=pt-BR` (optional)
- `/formatting-book-epub Books/{slug}/book.md` — the formatter detects image references and embeds them in `OEBPS/images/`
