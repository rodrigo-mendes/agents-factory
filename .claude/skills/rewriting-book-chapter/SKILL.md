---
name: rewriting-book-chapter
description: Regenerates a single chapter (prose, code examples, Mermaid diagrams, expert review, skeptical review, and assembly) for an existing book without re-running the full pipeline. Use when narrative validation or editing flags issues with a specific chapter.
argument-hint: "<book-slug> chapter=<N> [reason=\"narrative issue: ...\"] [depth=standard]"
context: fork
agent: book-orchestrator
disable-model-invocation: true
---

## Function

Runs the `book-orchestrator` in `mode=rewrite-chapter chapter=N`. Reads the existing `toc.md` and `traceability_matrix.md` for context, then runs only the P4 sub-pipeline for chapter N:

1. **Loads context:** reads `Books/{slug}/toc.md` for chapter title, objective, key concepts; reads `traceability_matrix.md` for previous chapter summary if stored
2. **Runs P4.1:** spawns `chapter-writer` for chapter N
3. **Runs P4.2:** spawns `code-illustrator`, `diagram-illustrator`, `expert-reviewer`, `skeptic-reviewer` in parallel
4. **Runs P4.3:** spawns `chapter-assembler`
5. **Updates matrix:** marks all 6 chapter N rows as VERIFIED; logs the reason for rewrite

## Prerequisites

- `Books/{slug}/toc.md` must exist (run `/writing-book-toc` or `/writing-technical-book` first)
- `Books/{slug}/traceability_matrix.md` must exist
- Chapter number must be valid (1 ≤ N ≤ NUM_CHAPTERS from the TOC)

## Input Parameters

| Parameter | Required | Default | Notes |
|-----------|----------|---------|-------|
| `slug` | ✅ | — | Book slug (folder name under `Books/`) |
| `chapter` | ✅ | — | Chapter number to regenerate (integer) |
| `reason` | ⚠️ | — | Why the chapter is being rewritten (logged in traceability matrix) |
| `depth` | ⚠️ | standard | Passed to chapter-writer for research depth awareness |

## Output

Overwrites only the 6 files for chapter N:
```
Books/{slug}/chapters/ch{N:02d}/
├── prose.md           (overwritten)
├── code.md            (overwritten)
├── diagrams.md        (overwritten)
├── expert_notes.md    (overwritten)
├── skeptic_notes.md   (overwritten)
└── chapter.md         (overwritten)
```

`traceability_matrix.md` updated with new VERIFIED timestamps and the `reason` in the Notes column.

`book.md`, `narrative_report.md`, translations, and EPUBs are NOT automatically updated — run `/writing-technical-book` from P5 onward, or re-run the full pipeline, to regenerate them.

## Usage

```
/rewriting-book-chapter distributed-systems chapter=5 reason="narrative validator flagged missing bridge from ch4"
/rewriting-book-chapter kafka-internals chapter=3 reason="expert reviewer: consumer group explanation too brief"
```
