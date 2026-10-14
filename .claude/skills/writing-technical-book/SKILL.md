---
name: writing-technical-book
description: Generates a complete technical book (TOC, introduction, prose, code examples, Mermaid diagrams, expert and skeptical review, chapter assembly, narrative validation, pt-BR and es translations, and EPUB 3.0 for KDP) from a topic, target audience, and market context. Use when generating a full technical book on any technical domain.
argument-hint: "<topic> audience=<audience> context=<market-context> [chapters=10] [depth=standard|exhaustive] [code_language=pseudocode] [code_style=pseudocode-only|pseudocode-first|working-code] [additional_languages=go,typescript] [decision_diagrams=flowchart]"
context: fork
agent: book-orchestrator
disable-model-invocation: true
---

## Function

This skill orchestrates 9 specialized agents across an 8-phase pipeline to produce a publication-ready technical book:

1. **TOC Research** — topic-scoped table of contents with chapter objectives, descriptions, and key concepts; user-approved before any writing begins
2. **Introduction Writing** — 800–1200 word book introduction covering scope, audience, chapter overview, and conventions; written directly by the orchestrator after TOC approval
3. **Chapter Prose** — audience-calibrated narrative with `[CODE:]` and `[DIAGRAM:]` markers for downstream agents
4. **Parallel Asset Generation** — code examples, Mermaid diagrams, expert annotations, and skeptical critique run concurrently per chapter
5. **Chapter Assembly** — markers resolved, callouts integrated at the right priority level, final `chapter.md`
6. **Narrative Validation** — cross-chapter consistency, concept progression, term coherence; `book.md` assembled with introduction prepended
7. **Translation** — pt-BR and es in parallel from the final English `book.md`
8. **EPUB 3.0 Formatting** — one EPUB per language, ready for direct upload to Amazon KDP

## Input Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `topic` | ✅ | — | Book topic — be specific ("Event-Driven Architecture with Kafka", not "Kafka") |
| `audience` | ✅ | — | Target reader profile ("senior backend engineers", "junior data scientists") |
| `context` | ✅ | — | Market/industry context ("cloud-native microservices at enterprise scale") |
| `chapters` | ⚠️ | 10 | Number of chapters (warn if > 15) |
| `depth` | ⚠️ | standard | TOC research depth: `quick` / `standard` / `exhaustive` |
| `code_language` | ⚠️ | `pseudocode` | Primary language for all code examples: `java`, `go`, `typescript`, `python`, `pseudocode` |
| `code_style` | ⚠️ | `pseudocode-only` | `pseudocode-only` · `working-code` · `pseudocode-first` (pseudocode block then implementation) |
| `additional_languages` | ⚠️ | _(none)_ | Extra languages for each code example, comma-separated: `go,typescript`. Requires `code_style` ≠ `pseudocode-only` |
| `decision_diagrams` | ⚠️ | `flowchart` | Force decision-explanation diagrams to use flowchart decision trees. Currently only `flowchart` is supported. |

## Blueprints & Guardrails

### ✅ Always Do
- Require `topic`, `audience`, `context` — abort with clear message if any missing
- Present TOC for user approval before any chapter prose is written
- Write every intermediate asset to disk before spawning the next agent
- Run `code-illustrator`, `diagram-illustrator`, `expert-reviewer`, `skeptic-reviewer` in ONE parallel Agent call per chapter
- Update `traceability_matrix.md` after every agent completes (PLANNED → CREATED → VERIFIED)
- Run the P5.matrix-check validation gate before translations (P6)
- Preserve all code blocks and Mermaid syntax untranslated in both translation outputs
- Apply the writing style guide from `blueprints/writing-style-guide.md` for chapter-writer

### ⚠️ Ask First
- If `chapters` > 15: warn and confirm
- If `depth=exhaustive`: confirm before starting
- If `topic` is too broad ("Python", "Cloud", "AI"): ask to narrow scope before proceeding
- If a chapter title in the TOC appears redundant with another: flag before approval

### 🚫 Never Do
| ❌ Wrong | ✅ Correct |
|----------|-----------|
| Start writing chapters before TOC is approved and introduction is written | Always pause at P3 for user approval; always run P3.5 before P4 |
| Run code/diagram/review agents sequentially per chapter | Always spawn all 4 in a single parallel Agent call |
| Translate code blocks or Mermaid syntax | Preserve code verbatim; translate only prose |
| Leave `[CODE:]` or `[DIAGRAM:]` markers in `chapter.md` | Assembler must resolve all markers; flag unresolved with `<!-- NOT GENERATED -->` |
| Write `book.md` before all `chapter.md` files are verified | Glob-verify all chapters before concatenating |
| Generate MOBI | MOBI deprecated since March 2025 — use EPUB 3.0 |

## Writing Quality Standards

Applied by `chapter-writer` and enforced by `narrative-validator`:

- **Voice:** Third-person authoritative; precise; confident without being dogmatic
- **Sentence length:** Prefer sentences under 25 words; break compound ideas
- **Terminology:** Define each technical term exactly once on first use; use consistently throughout
- **Section length:** Each `## Section`: 300–600 words + associated markers
- **Chapter opener:** Problem statement — the question this chapter answers
- **Chapter closer:** "Key Takeaways" (3–5 bullets) + bridge to next chapter
- **Writing Style Guide:** See `blueprints/writing-style-guide.md` ← *(place user's style rules here)*

## Integration Patterns

```
toc.md → chapter-writer (reads for book context)
prose.md → code-illustrator + diagram-illustrator + expert-reviewer + skeptic-reviewer (parallel)
[prose + code + diagrams + expert_notes + skeptic_notes] → chapter-assembler
introduction.md + all chapter.md files → narrative-validator (via Glob) → book.md
book.md → book-translator (pt-BR) + book-translator (es) (parallel)
book.md / book_pt-BR.md / book_es.md → book-formatter × 3 (parallel) → epub-src trees
orchestrator Bash → zip epub-src → book.epub × 3
```

## Verification Loop

Orchestrator runs after each phase:
```bash
# P2: TOC has correct chapter count
grep -c "^## Chapter" Books/{slug}/toc.md  # must = NUM_CHAPTERS

# P3.5: introduction exists
ls Books/{slug}/introduction.md

# P4: per chapter, all 6 assets present
ls Books/{slug}/chapters/ch{N:02d}/  # must list 6 files

# P5: book.md exists and has correct chapter count
grep -c "^# Chapter" Books/{slug}/book.md  # must = NUM_CHAPTERS

# P7: all 3 EPUBs present
ls Books/{slug}/kindle/en/book.epub Books/{slug}/kindle/pt-BR/book.epub Books/{slug}/kindle/es/book.epub
```

## Quick Reference

```
# Default — pseudocode only (safest, no runtime dependency)
/writing-technical-book "Distributed Systems" audience="senior engineers" context="cloud-native" chapters=10

# Working code in Java only
/writing-technical-book "Kafka Internals" audience="data engineers" context="real-time pipelines" chapters=8 code_style=working-code code_language=java

# Pseudocode first, then Java + Go implementations
/writing-technical-book "Microservices Patterns" audience="senior backend engineers" context="cloud-native" code_style=pseudocode-first code_language=java additional_languages=go

# Exhaustive TOC research, TypeScript code
/writing-technical-book "Node.js Architecture" audience="full-stack engineers" context="serverless" depth=exhaustive code_style=working-code code_language=typescript
```

**`code_style` semantics:**
- `pseudocode-only` (default) — conceptual pseudocode; no runtime dependency; language-agnostic
- `working-code` — real, compilable code in `code_language` (+ `additional_languages` if set)
- `pseudocode-first` — pseudocode concept block followed by implementation in `code_language` (+ `additional_languages`)

| Limit | Value |
|-------|-------|
| Max chapters (before warning) | 15 |
| Target words per chapter | 1500–2500 |
| Target words per section | 300–600 |
| Parallel agents per chapter (steps 4–7) | 4 (+ sequential code-validator at P4.2b when code_style ≠ pseudocode-only) |
| Translation languages | pt-BR, es (always included) |
| EPUB format | EPUB 3.0 reflowable |

## Blueprints Directory

| Blueprint | Content | When to Read |
|-----------|---------|--------------|
| `blueprints/writing-style-guide.md` | User's writing style rules | Before every `chapter-writer` spawn |
| `blueprints/chapter-structure-template.md` | Chapter structure and marker syntax reference | By `chapter-writer` |
| `blueprints/output-format.md` | Full book and chapter file format spec | By `chapter-assembler` and orchestrator |
| `blueprints/evaluation-scenarios.md` | Skill behavioral test cases | By `skill-evaluator` only |
