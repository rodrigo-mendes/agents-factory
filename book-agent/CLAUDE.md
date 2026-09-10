# Book Agent — CLAUDE.md

Self-contained multi-agent system for generating complete technical books from a topic, audience, and market context. Produces prose, code examples, Mermaid diagrams, expert and skeptical reviews, EPUB 3.0 output for KDP, and pt-BR/es translations.

## How to Activate

Copy agents and skills into the root `.claude/` to make slash commands available:

```bash
cp -r book-agent/.claude/agents/* .claude/agents/
cp -r book-agent/.claude/skills/*  .claude/skills/
```

## Commands

| Command | When to Use |
|---------|-------------|
| `/writing-technical-book "<topic>" audience="..." context="..."` | Full pipeline from scratch |
| `/writing-book-toc "<topic>" audience="..."` | Generate and approve TOC before committing to full pipeline |
| `/rewriting-book-chapter <slug> chapter=<N>` | Regenerate one chapter after narrative review or edits |
| `/rewriting-book-introduction <slug> [reason="..."]` | Regenerate just the book introduction |
| `/switching-book-language <slug> language=<lang> [style=...] [additional=...]` | Switch or unify code language across all chapters of a completed book |
| `/enriching-book-chapter <path/to/chapter.md> slug=<slug> [chapter=<N>]` | Infer injection points in external prose and run P4.2+P4.3 to produce a fully assembled chapter |
| `/translating-book <path/to/book.md> target=pt-BR\|es` | Translate a completed book |
| `/formatting-book-epub <path/to/book.md>` | Format a completed book to EPUB 3.0 for KDP |
| `/repairing-book-epub <path/to/kindle/>` | Validate and repair generated EPUBs (path separators, XHTML escaping) |

## Pipeline Overview

```
P1: init + traceability_matrix.md (all assets PLANNED)
P2: TOC research (hybrid: model + web) → toc.md
P3: user approval gate (EnterPlanMode/ExitPlanMode)
P3.5: introduction writing → introduction.md (800–1200 words, prose only)
P4: [per chapter, sequential]:
    chapter-writer → prose.md
    [PARALLEL]: code-illustrator + diagram-illustrator + expert-reviewer + skeptic-reviewer
    [SEQUENTIAL, skip if code_style=pseudocode-only]: code-validator → code.md (validated)
    chapter-assembler → chapter.md
    traceability update per asset (PLANNED → CREATED → VERIFIED/FAILED/SKIPPED)
P5: narrative validation → narrative_report.md + book.md
P5.matrix-check: validate all assets VERIFIED/SKIPPED; retry FAILED; halt on PLANNED
P6: [PARALLEL]: book-translator pt-BR + book-translator es
P7: kdp_metadata.md + [PARALLEL]: book-formatter × 3 → EPUB src trees
    Bash: build-epub.py each epub-src → book.epub
```

## Agents

| Agent | Model | Role |
|-------|-------|------|
| `book-orchestrator` | opus | Full pipeline orchestrator |
| `chapter-writer` | opus | Chapter prose + [CODE:]/[DIAGRAM:] markers |
| `code-illustrator` | sonnet | Code examples, algorithms, pseudocode |
| `diagram-illustrator` | sonnet | Mermaid diagrams |
| `expert-reviewer` | sonnet | Expert annotations (💡) |
| `skeptic-reviewer` | sonnet | Skeptical critique (⚠️) |
| `code-validator` | sonnet | Consistency check, missing-language generation, compilation validation of code.md |
| `chapter-enricher` | sonnet | Injection-point inference on external prose — inserts [CODE:]/[DIAGRAM:] markers verbatim-preserving |
| `chapter-assembler` | sonnet | Merges all 6 chapter assets (including validated code.md) |
| `book-translator` | sonnet | Translates book.md (pt-BR or es) |
| `book-formatter` | sonnet | EPUB 3.0 source tree generator |
| `epub-repairer` | sonnet | EPUB validator + repairer (path separators, XHTML escaping) |

## Output Structure

```
Books/{topic-slug}/
├── traceability_matrix.md
├── toc.md
├── book_metadata.md
├── introduction.md
├── chapters/ch{N}/
│   ├── prose.md
│   ├── code.md
│   ├── diagrams.md
│   ├── expert_notes.md
│   ├── skeptic_notes.md
│   └── chapter.md
├── book.md
├── book_pt-BR.md
├── book_es.md
├── narrative_report.md
└── kindle/
    ├── kdp_metadata.md
    └── {en,pt-BR,es}/book.epub
```

## Principles

- **No phase advances without DoD** — each phase has explicit completion criteria
- **Traceability first** — every asset tracked from PLANNED → CREATED → VERIFIED/FAILED/SKIPPED
- **Parallel within chapter** — steps 3–6 (code, diagrams, expert, skeptic) always parallel
- **Sequential chapters** — ch(N+1) never starts before ch(N) chapter.md is VERIFIED
- **EPUB 3.0 only** — MOBI deprecated March 2025; never generate MOBI
- **Writing style blueprint** — place user's style rules in `blueprints/writing-style-guide.md`

