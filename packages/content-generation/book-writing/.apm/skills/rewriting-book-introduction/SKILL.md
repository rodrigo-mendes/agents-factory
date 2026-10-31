---
name: rewriting-book-introduction
description: Regenerates only the book introduction for an existing book without re-running the full pipeline. Use when the introduction needs updating after TOC changes, narrative review, or audience adjustments.
argument-hint: "<book-slug> [reason=\"...\"]"
context: fork
agent: book-orchestrator
disable-model-invocation: true
---

## Function

Runs the `book-orchestrator` in `mode=rewrite-introduction`. Reads the existing `toc.md` and `book_metadata.md`, then regenerates `Books/{slug}/introduction.md` only:

1. **Loads context:** reads `Books/{slug}/toc.md` for all chapter titles and objectives; reads `Books/{slug}/book_metadata.md` for audience and market context
2. **Runs P3.5:** orchestrator writes a fresh `introduction.md` (800–1200 words) covering what the book covers, who it's for, how to read it, a chapter overview, and conventions used
3. **Updates matrix:** marks the introduction row VERIFIED; logs the reason in the Notes column

## Prerequisites

- `Books/{slug}/toc.md` must exist (run `/writing-book-toc` or `/writing-technical-book` first)
- `Books/{slug}/traceability_matrix.md` must exist

## Input Parameters

| Parameter | Required | Notes |
|-----------|----------|-------|
| `slug` | ✅ | Book slug (folder name under `Books/`) |
| `reason` | ⚠️ | Why the introduction is being rewritten (logged in traceability matrix) |

## Output

Overwrites only `Books/{slug}/introduction.md`.

`traceability_matrix.md` updated with new VERIFIED timestamp and the `reason` in the Notes column.

`book.md`, translations, and EPUBs are NOT automatically updated — run `/writing-technical-book` from P5 onward to regenerate them.

## Usage

```
/rewriting-book-introduction distributed-systems reason="TOC changed after chapter review"
/rewriting-book-introduction kafka-internals reason="audience scope updated to include junior engineers"
/rewriting-book-introduction event-driven-architecture reason="added conventions section for new callout types"
```
