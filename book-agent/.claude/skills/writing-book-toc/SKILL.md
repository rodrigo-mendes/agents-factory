---
name: writing-book-toc
description: Researches a technical book topic and generates a structured table of contents (chapters with objectives, descriptions, and key concepts) for user review and approval — without committing to the full writing pipeline. Use when planning a technical book before starting chapter generation.
argument-hint: "<topic> audience=<audience> [chapters=10] [depth=standard|exhaustive]"
context: fork
agent: book-orchestrator
disable-model-invocation: true
---

## Function

Runs the `book-orchestrator` in `mode=toc-only`. Executes only phases P0–P3:

- **P0:** Validates inputs, derives slug, sets `OUTPUT_DIR`
- **P1:** Creates `Books/{slug}/` directory; writes `book_metadata.md`; initializes `traceability_matrix.md` (TOC row only, PLANNED)
- **P2:** Researches topic using hybrid approach (model knowledge + web validation); writes `Books/{slug}/toc.md` with N chapters, each having an objective, description, and key concepts list
- **P3:** Presents TOC to user via EnterPlanMode/ExitPlanMode for approval

Pipeline stops after P3. No chapter prose, code, diagrams, or EPUB is generated.

## Input Parameters

| Parameter | Required | Default |
|-----------|----------|---------|
| `topic` | ✅ | — |
| `audience` | ✅ | — |
| `chapters` | ⚠️ | 10 |
| `depth` | ⚠️ | standard |

Note: `context` is optional for TOC-only runs (no prose is written). If provided, it is stored in `book_metadata.md` for use in a subsequent full pipeline run.

## Output

```
Books/{slug}/
├── book_metadata.md
├── traceability_matrix.md  (toc.md row: VERIFIED; all other rows: not initialized)
└── toc.md                  (N chapters with objectives, descriptions, key concepts)
```

## Usage

```
/writing-book-toc "Distributed Systems" audience="senior backend engineers" chapters=12
/writing-book-toc "Machine Learning in Production" audience="ML engineers" depth=exhaustive
```

To proceed to full book generation after approving the TOC:
```
/writing-technical-book "Distributed Systems" audience="senior backend engineers" context="cloud-native" chapters=12
```
The orchestrator will reuse the approved `toc.md` rather than re-researching.
