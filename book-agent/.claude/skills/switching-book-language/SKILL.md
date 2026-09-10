---
name: switching-book-language
description: Troca ou unifica a linguagem de código de um livro técnico já gerado, regenerando os artefatos de código em todos os capítulos e remontando book.md, traduções e EPUBs.
argument-hint: "<book-slug> language=<lang> [style=working-code|pseudocode-first|pseudocode-only] [additional=go,typescript] [translate=yes|no] [epub=yes|no]"
context: fork
agent: book-orchestrator
disable-model-invocation: true
---

## Function

Runs the `book-orchestrator` in `mode=switch-language`. Reads the existing book structure at `Books/{slug}/`, detects the current code language settings, then regenerates only the code-related assets across all chapters before reassembling the book.

Pipeline executed:

1. **SL-P1 — Detect state:** reads `Books/{slug}/book_metadata.md` for `Code Language`, `Code Style`, `Additional Languages`; falls back to scanning `chapters/ch*/code.md` fence labels if fields are absent
2. **SL-P2 — Update metadata:** writes new language fields to `book_metadata.md`
3. **SL-P3 — Reset traceability:** sets `code.md` and `chapter.md` rows to PLANNED for each chapter; conditionally resets P5/P6/P7 rows
4. **SL-P4 — Per-chapter regeneration (parallel code-illustrator batch):**
   - Spawns `code-illustrator` for all chapters in parallel
   - Runs `code-validator` per chapter if `style ≠ pseudocode-only`
   - Runs `chapter-assembler` per chapter (reuses existing prose, diagrams, expert/skeptic notes)
5. **SL-P5 — Reassemble book.md** from updated `chapter.md` files
6. **SL-P6 — Re-translate (conditional):** pt-BR and es in parallel if translations existed and `translate=yes`
7. **SL-P7 — Re-format EPUBs (conditional):** 3 formatters in parallel + zip if EPUBs existed and `epub=yes`
8. **SL-P8 — Report:** prints per-chapter status table and updates traceability timestamp

## Prerequisites

- `Books/{slug}/toc.md` must exist
- `Books/{slug}/traceability_matrix.md` must exist
- `Books/{slug}/chapters/ch*/prose.md` must all exist (prose is not regenerated)

## Input Parameters

| Parameter | Required | Default | Notes |
|-----------|----------|---------|-------|
| `slug` | ✅ | — | Book slug (folder name under `Books/`) |
| `language` | ✅ | — | New primary code language: `python`, `go`, `java`, `typescript`, `pseudocode` |
| `style` | ⚠️ | keeps current | `working-code` / `pseudocode-first` / `pseudocode-only` |
| `additional` | ⚠️ | keeps current | Comma-separated extra languages (e.g., `go,typescript`); ignored when `style=pseudocode-only` |
| `translate` | ⚠️ | `yes` | Re-run translations if they previously existed |
| `epub` | ⚠️ | `yes` | Re-run EPUB formatting if EPUBs previously existed |

## What is Regenerated

| Asset | Regenerated | Notes |
|-------|-------------|-------|
| `chapters/ch{N}/code.md` | ✅ Yes | New language via code-illustrator |
| `chapters/ch{N}/chapter.md` | ✅ Yes | Reassembled with new code |
| `book.md` | ✅ Yes | Concatenation of updated chapters |
| `book_pt-BR.md` / `book_es.md` | Conditional | Only if existed AND `translate=yes` |
| `kindle/{lang}/book.epub` | Conditional | Only if existed AND `epub=yes` |
| `chapters/ch{N}/prose.md` | 🚫 No | Prose is preserved |
| `chapters/ch{N}/diagrams.md` | 🚫 No | Diagrams are preserved |
| `chapters/ch{N}/expert_notes.md` | 🚫 No | Expert notes are preserved |
| `chapters/ch{N}/skeptic_notes.md` | 🚫 No | Skeptical notes are preserved |

## Usage

```
/switching-book-language event-driven-architecture language=python style=working-code
/switching-book-language kafka-internals language=go style=pseudocode-first additional=typescript
/switching-book-language my-book language=java style=pseudocode-only translate=no epub=no
```
