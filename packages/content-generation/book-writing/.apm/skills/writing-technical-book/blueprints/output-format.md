# Output Format Specification

Defines the canonical format for every output file in the book-agent pipeline. Used by `chapter-assembler`, `book-orchestrator`, and `book-formatter`.

---

## `toc.md` — Table of Contents

```markdown
# {BOOK_TITLE} — Table of Contents

**Topic:** {TOPIC}
**Audience:** {AUDIENCE}
**Market Context:** {MARKET_CONTEXT}
**Chapters:** {NUM_CHAPTERS}
**Generated:** {YYYY-MM-DD}

---

## Chapter 1: {Title}

**Objective:** {one sentence describing what the reader will learn}

**Description:** {2–3 sentences describing the chapter's content and approach}

**Key Concepts:**
- {Concept 1}
- {Concept 2}
- {Concept 3}
- {Concept 4 — optional}
- {Concept 5 — optional}

---

## Chapter 2: {Title}
[... repeat for each chapter ...]
```

---

## `chapter.md` — Assembled Chapter

The final assembled chapter file. Produced by `chapter-assembler` from the 5 source assets.

```markdown
# Chapter {N}: {Title}

## Opening Problem Statement
{prose}

## {Section}
{prose}

> 💡 **Expert Note:** {high-priority expert note, if any}

```{language}
{code block}
```

```mermaid
{mermaid diagram}
```

<details>
<summary>💡 Expert Note</summary>
{medium-priority expert note, if any}
</details>

> ⚠️ **Critical Note:** {blocking skeptic note, if any}

<details>
<summary>⚠️ Critical Note</summary>
{important skeptic note, if any}
</details>

{more sections...}

## Key Takeaways
- {bullet}
- {bullet}

## What's Next
{bridge sentence}

<!-- ASSEMBLY COMPLETE
  Chapter: {CHAPTER_TITLE}
  Code blocks resolved: {N} / {total}
  Diagrams resolved: {N} / {total}
  Expert callouts (inline): {N}
  Expert callouts (collapsed): {N}
  Critical callouts (inline): {N}
  Critical callouts (collapsed): {N}
  Unresolved markers: {N}
-->
```

---

## `introduction.md` — Book Introduction

Produced by `book-orchestrator` at P3.5. Prose only — no `[CODE:]` or `[DIAGRAM:]` markers.

```markdown
# Introduction

## What This Book Covers
{Topic summary and why it matters in the current market/industry context — 2–3 paragraphs}

## Who This Book Is For
{Audience profile; assumed background knowledge and prerequisites — 1–2 paragraphs}

## How to Read This Book
{Cover-to-cover vs. chapter-jumping guidance; which chapters are foundational vs. advanced — 1 paragraph}

## Chapter Overview
- **Chapter 1 — {Title}:** {one sentence derived from toc.md objective}
- **Chapter 2 — {Title}:** {one sentence}
- {...}
- **Chapter N — {Title}:** {one sentence}

## Conventions Used in This Book
- **Code blocks** are labeled with the language name (e.g., ` ```java `).
- **Mermaid diagrams** are labeled with the diagram type (e.g., `flowchart TD`).
- **💡 Expert Note** — practitioner insight from a senior domain expert.
- **⚠️ Critical Note** — common pitfall or misconception to avoid.
```

---

## `book.md` — Final English Book

Introduction prepended, then chapters concatenated with separators:

```markdown
# {TOPIC}

{content of introduction.md}

---

{content of ch01/chapter.md}

---

{content of ch02/chapter.md}

---

{...}

{content of ch{N}/chapter.md}
```

---

## `narrative_report.md` — Narrative Consistency Report

```markdown
# Narrative Consistency Report — {TOPIC}
Date: {YYYY-MM-DD}

## Summary
| Metric | Count |
|--------|-------|
| Chapters reviewed | {N} |
| Concept progression gaps | {N} |
| Term inconsistencies | {N} |
| Audience drift instances | {N} |
| Missing chapter bridges | {N} |

## Overall Assessment
✅ / ⚠️ / 🚫 {overall verdict with 1-paragraph reasoning}

## Per-Chapter Findings

### Chapter 1: {title}
| Check | Result |
|-------|--------|
| Concept progression | ✅ OK / ⚠️ {detail} |
| Term consistency | ✅ OK / ⚠️ {term} used differently than ch{M} |
| Audience alignment | ✅ OK / ⚠️ {detail} |
| Bridge to next chapter | ✅ Present / ⚠️ Missing |

**Notes:** {optional free text}

---

### Chapter 2: {title}
[...]

## Recommended Actions
1. {specific action — reference chapter and section}
2. {...}
```

---

## `traceability_matrix.md` — Asset Traceability Matrix

See the full specification in `book-orchestrator.md` Phase P1 section. The format includes:
- Header with generation timestamp and validation gate status
- Summary table (per-phase asset counts)
- Full Asset Register table (Asset ID, Path, Type, Phase, Created By, Input Assets, Status, Notes)
- Mermaid dependency graph

---

## EPUB Source Tree Structure

```
epub-src/
├── mimetype                         (no trailing newline; content: "application/epub+zip")
├── META-INF/
│   └── container.xml
└── OEBPS/
    ├── content.opf                  (OPF manifest)
    ├── nav.xhtml                    (EPUB3 navigation)
    ├── toc.ncx                      (EPUB2 fallback)
    ├── styles.css                   (KDP-safe stylesheet)
    └── ch{N:02d}.xhtml              (one per chapter)
```

Final output after orchestrator zip:
```
kindle/{language}/book.epub          (zipped with -X mimetype first, then -rg META-INF OEBPS)
```
