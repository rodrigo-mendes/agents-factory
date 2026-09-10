# Book Agent

Self-contained multi-agent system for generating complete, publication-ready technical books from a topic, target audience, and market context. Produces English prose, code examples, Mermaid diagrams, expert and skeptical review annotations, pt-BR and es translations, and EPUB 3.0 output for Amazon KDP — all from a single slash command.

---

## Installation

Copy agents and skills into the root `.claude/` of your project:

```bash
cp -r book-agent/.claude/agents/* .claude/agents/
cp -r book-agent/.claude/skills/*  .claude/skills/
```

---

## Quick Start

```bash
# Generate a complete book (full pipeline, pseudocode, 10 chapters)
/writing-technical-book "Event-Driven Architecture with Kafka" \
  audience="senior backend engineers" \
  context="cloud-native microservices at enterprise scale"
```

The pipeline stops at Phase 3 to show you the TOC for approval before writing any prose.

---

## Usage Scenarios

Real end-to-end workflows organized by intent.

---

### Scenario 1 — Brand new book, fastest possible run

You want a complete book quickly without worrying about language specifics.

```bash
/writing-technical-book "Distributed Systems" \
  audience="senior backend engineers" \
  context="cloud-native" \
  chapters=10
```

Uses all defaults: `pseudocode-only`, `standard` depth, 10 chapters. Produces `book.md` + pt-BR/es translations + EPUB 3.0 for all three languages.

---

### Scenario 2 — Validate the TOC before committing to the full pipeline

You want to review and refine the chapter structure before spending time on prose generation.

```bash
# Step 1: generate TOC only, review and approve it
/writing-book-toc "Machine Learning in Production" \
  audience="ML engineers" \
  chapters=12 \
  depth=exhaustive

# Step 2: once approved, run the full pipeline reusing the same slug
/writing-technical-book "Machine Learning in Production" \
  audience="ML engineers" \
  context="production ML systems at scale" \
  chapters=12
```

The orchestrator detects the existing `toc.md` and skips re-researching.

---

### Scenario 3 — Working code book, single language

You want real compilable code throughout, not pseudocode.

```bash
/writing-technical-book "Kafka Internals" \
  audience="data engineers" \
  context="real-time data pipelines" \
  chapters=8 \
  code_style=working-code \
  code_language=java
```

Activates `code-validator` per chapter: compiles each Java block with `javac`, retries up to 3 times, annotates failures inline rather than silently dropping them.

---

### Scenario 4 — Multi-language code: concept + multiple implementations

You want pseudocode to explain the concept, then real implementations in two languages side-by-side.

```bash
/writing-technical-book "Microservices Patterns" \
  audience="senior backend engineers" \
  context="cloud-native enterprise" \
  code_style=pseudocode-first \
  code_language=java \
  additional_languages=go,typescript
```

Each `[CODE:]` marker produces three blocks: pseudocode concept → Java implementation → Go implementation → TypeScript implementation.

---

### Scenario 5 — Exhaustive research for a niche or fast-moving topic

You want maximum research depth and are willing to confirm before the pipeline starts.

```bash
/writing-technical-book "WebAssembly for Backend Systems" \
  audience="platform engineers" \
  context="edge computing and serverless" \
  depth=exhaustive \
  chapters=8 \
  code_style=working-code \
  code_language=go
```

The orchestrator asks for confirmation before starting exhaustive web research (can produce many more chapters than expected for some topics).

---

### Scenario 6 — Fix one chapter after narrative review

The narrative validator flagged a coherence issue in chapter 5, or you want to improve a specific chapter without regenerating everything.

```bash
/rewriting-book-chapter distributed-systems \
  chapter=5 \
  reason="narrative validator: missing conceptual bridge from ch4 consensus algorithms"
```

Regenerates all 6 assets for chapter 5 only. `book.md`, translations, and EPUBs are not automatically updated — re-run downstream commands when ready.

**After a rewrite, refresh the book and downstream outputs:**

```bash
# Re-translate if needed
/translating-book Books/distributed-systems/book.md target=pt-BR
/translating-book Books/distributed-systems/book.md target=es

# Re-format EPUBs
/formatting-book-epub Books/distributed-systems/book.md language=en author="Jane Doe"
/formatting-book-epub Books/distributed-systems/book_pt-BR.md language=pt-BR author="Jane Doe"
/formatting-book-epub Books/distributed-systems/book_es.md language=es author="Jane Doe"
```

---

### Scenario 7 — Switch code language after delivery (publisher or audience change)

The book was written in Java but your publisher wants Python examples, or you're repurposing it for a different audience.

```bash
/switching-book-language distributed-systems \
  language=python \
  style=working-code
```

Regenerates all `code.md` files and reassembles `chapter.md` and `book.md`. Prose, diagrams, and reviewer annotations are preserved. Translations and EPUBs are re-run automatically (pass `translate=no epub=no` to skip).

**Switch language but skip re-translating:**

```bash
/switching-book-language kafka-internals \
  language=go \
  style=pseudocode-first \
  additional=typescript \
  translate=no \
  epub=no
```

---

### Scenario 8 — Integrate external prose chapters into the pipeline

You have chapters written outside the pipeline (no `[CODE:]` / `[DIAGRAM:]` markers) and want to enrich them with generated assets.

```bash
# Enrich a single external chapter into slot 3 of an existing book
/enriching-book-chapter external/ch03.md \
  slug=event-driven-arch \
  chapter=3 \
  toc=Books/event-driven-arch/toc.md \
  audience="senior backend engineers" \
  code_style=working-code \
  code_language=java

# Enrich multiple external chapters (run sequentially)
/enriching-book-chapter drafts/chapter-01.md slug=my-book chapter=1
/enriching-book-chapter drafts/chapter-02.md slug=my-book chapter=2
/enriching-book-chapter drafts/chapter-03.md slug=my-book chapter=3
```

The enricher preserves every word of original prose and only inserts `[CODE:]` / `[DIAGRAM:]` markers at inferred injection points. It then runs the full P4.2 + P4.3 sub-pipeline to produce `code.md`, `diagrams.md`, `expert_notes.md`, `skeptic_notes.md`, and `chapter.md`.

---

### Scenario 9 — Hybrid book: some chapters external, some pipeline-written

You have 3 pre-written chapters and want the pipeline to write the remaining 7.

```bash
# Step 1: generate the TOC
/writing-book-toc "Platform Engineering" audience="SREs and platform engineers" chapters=10

# Step 2: enrich your pre-written chapters into slots 1, 4, 7
/enriching-book-chapter drafts/intro.md slug=platform-engineering chapter=1
/enriching-book-chapter drafts/networking.md slug=platform-engineering chapter=4
/enriching-book-chapter drafts/observability.md slug=platform-engineering chapter=7

# Step 3: run the full pipeline — orchestrator detects existing chapter.md files
# and skips those slots, writing only the missing chapters
/writing-technical-book "Platform Engineering" \
  audience="SREs and platform engineers" \
  context="internal developer platforms at scale" \
  chapters=10
```

---

### Scenario 10 — Translate a completed book (standalone)

You have a `book.md` produced outside the pipeline and want translations only.

```bash
/translating-book Books/my-book/book.md target=pt-BR slug=my-book
/translating-book Books/my-book/book.md target=es slug=my-book
```

Code fences, Mermaid blocks, framework names, CLI commands, and URLs are preserved in English.

---

### Scenario 11 — Format to EPUB standalone (book written outside the pipeline)

You have a `book.md` not produced by this pipeline and want a KDP-ready EPUB.

```bash
/formatting-book-epub my-content/book.md \
  slug=my-external-book \
  language=en \
  author="Jane Doe"
```

Upload the resulting `Books/my-external-book/kindle/en/book.epub` to kdp.amazon.com. Validate with Kindle Previewer before submitting. Cover image (2560×1600 px minimum) must be provided separately.

---

### Scenario 12 — Rapid prototype / quick draft

You want a fast draft to evaluate structure and coverage before investing in a full run.

```bash
/writing-technical-book "GraphQL at Scale" \
  audience="backend engineers" \
  context="API platform teams" \
  chapters=6 \
  depth=quick \
  code_style=pseudocode-only
```

`depth=quick` uses model knowledge only (no web searches). `pseudocode-only` skips `code-validator`. Fastest possible complete run.

---

### Scenario 13 — EPUB file won't open in a reader / fails KDP upload

The generated `.epub` opens fine on some devices but not others, or Amazon KDP rejects it at upload, or `extract-text` / Calibre reports a broken file.

```bash
# Validate and repair all 3 language EPUBs for a book
/repairing-book-epub Books/my-book/kindle/

# Repair only the English EPUB
/repairing-book-epub Books/my-book/kindle/ languages=en

# Target a single file
/repairing-book-epub Books/my-book/kindle/pt-BR/book.epub
```

The agent runs `validate-epub.py` first (checks ZIP integrity, `mimetype` placement, forward-slash paths, XHTML well-formedness) then calls `build-epub.py` to repack any failing file from its `epub-src/` tree.

**Common causes this fixes:**
- Backslash paths in ZIP entries (`META-INF\container.xml` instead of `META-INF/container.xml`) — caused by `zip` on Windows
- XHTML parse errors from unescaped `<` in code blocks (e.g., Python f-string format specifiers `:<30}`)
- `mimetype` not first or not `ZIP_STORED`

---

### Scenario 14 — Production book with full validation and multi-language code

Maximum quality: exhaustive research, pseudocode + two working-code implementations, full validation, translations, EPUB.

```bash
/writing-technical-book "Designing Data-Intensive Applications with AWS" \
  audience="senior backend engineers" \
  context="cloud-native data platforms at enterprise scale" \
  chapters=12 \
  depth=exhaustive \
  code_style=pseudocode-first \
  code_language=java \
  additional_languages=python
```

Each chapter goes through: `chapter-writer` (opus) → [parallel: `code-illustrator` + `diagram-illustrator` + `expert-reviewer` + `skeptic-reviewer`] → `code-validator` (compiles Java + Python) → `chapter-assembler`. Total agents spawned: ~7 per chapter + 2 translators + 3 formatters.

---

## Commands Reference

### `/writing-technical-book` — Full Book Pipeline

Runs the complete 7-phase pipeline: TOC research → user approval → per-chapter prose + code + diagrams + reviews → narrative validation → translations → EPUB 3.0.

**Syntax:**

```
/writing-technical-book "<topic>" audience="<audience>" context="<context>"
  [chapters=10]
  [depth=standard|exhaustive|quick]
  [code_language=pseudocode|java|go|typescript|python]
  [code_style=pseudocode-only|working-code|pseudocode-first]
  [additional_languages=go,typescript]
  [decision_diagrams=flowchart]
```

**Parameters:**

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `topic` | YES | — | Be specific: "Event-Driven Architecture with Kafka", not "Kafka" |
| `audience` | YES | — | Reader profile: "senior backend engineers", "junior data scientists" |
| `context` | YES | — | Market/industry context: "cloud-native microservices at enterprise scale" |
| `chapters` | no | `10` | Number of chapters; warns if > 15 |
| `depth` | no | `standard` | `quick` (model only) / `standard` (model + 2–4 web searches) / `exhaustive` (confirms before starting) |
| `code_language` | no | `pseudocode` | `java` / `go` / `typescript` / `python` / `pseudocode` |
| `code_style` | no | `pseudocode-only` | See table below |
| `additional_languages` | no | _(none)_ | Extra languages per code example, e.g. `go,typescript`. Requires `code_style ≠ pseudocode-only` |
| `decision_diagrams` | no | `flowchart` | Forces decision diagrams to `flowchart TD` decision trees. Only `flowchart` supported. |

**`code_style` options:**

| Value | Meaning |
|-------|---------|
| `pseudocode-only` | Conceptual pseudocode only; no runtime dependency; `code-validator` skipped |
| `working-code` | Real compilable code in `code_language` (+ `additional_languages` if set) |
| `pseudocode-first` | Pseudocode concept block followed by implementation in `code_language`. Requires `code_language ≠ pseudocode` |

**Pipeline phases:**

| Phase | What happens |
|-------|-------------|
| P0 | Validate inputs, derive slug, load style guide |
| P1 | Initialize directory tree, `book_metadata.md`, `traceability_matrix.md` |
| P2 | TOC research (model + web) → `toc.md` |
| P3 | **User approval gate** — stops here until you approve the TOC |
| P3.5 | Introduction writing → `introduction.md` (800–1200 words: scope, audience, chapter overview, conventions) |
| P4 | Per-chapter: `chapter-writer` → [parallel: `code-illustrator` + `diagram-illustrator` + `expert-reviewer` + `skeptic-reviewer`] → `code-validator` (if applicable) → `chapter-assembler` |
| P5 | Narrative validation → `narrative_report.md`; prepend introduction + concatenate chapters → `book.md`; matrix-check gate |
| P6 | Parallel translations → `book_pt-BR.md` + `book_es.md` |
| P7 | KDP metadata + 3 parallel `book-formatter` instances → EPUB src trees → zip → `.epub` |

**Output files:**

```
Books/{slug}/
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

---

### `/writing-book-toc` — TOC Generation Only

Runs phases P0–P3 only. Generates and presents a structured table of contents for approval without writing any prose, code, or diagrams. Useful for validating the book outline before committing to the full pipeline.

**Syntax:**

```
/writing-book-toc "<topic>" audience="<audience>" [chapters=10] [depth=standard|exhaustive]
```

**Parameters:**

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `topic` | YES | — | Book topic |
| `audience` | YES | — | Reader profile |
| `chapters` | no | `10` | Number of chapters |
| `depth` | no | `standard` | Research depth |

Note: `context` is optional here; if provided, it is stored in `book_metadata.md` for a subsequent full pipeline run.

**Output files:**

```
Books/{slug}/
├── book_metadata.md
├── traceability_matrix.md
└── toc.md
```

**Examples:**

```bash
/writing-book-toc "Distributed Systems" audience="senior backend engineers" chapters=12

/writing-book-toc "Machine Learning in Production" audience="ML engineers" depth=exhaustive
```

**To continue to the full pipeline after TOC approval:**

```bash
# Re-use the same topic — orchestrator picks up the existing toc.md
/writing-technical-book "Distributed Systems" \
  audience="senior backend engineers" \
  context="cloud-native" \
  chapters=12
```

---

### `/rewriting-book-chapter` — Single Chapter Regeneration

Re-runs phase P4 for a single chapter. Use after narrative validation flags issues, or when you want to improve a specific chapter without regenerating the whole book.

**Syntax:**

```
/rewriting-book-chapter <book-slug> chapter=<N> [reason="..."] [depth=standard]
```

**Parameters:**

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `slug` | YES | — | Folder name under `Books/` |
| `chapter` | YES | — | Chapter number to regenerate (integer, 1-based) |
| `reason` | no | — | Reason logged in the traceability matrix |
| `depth` | no | `standard` | Passed to `chapter-writer` for research awareness |

**Prerequisites:** `Books/{slug}/toc.md` and `traceability_matrix.md` must exist. Chapter N must be within range.

**What is updated:** All 6 assets for chapter N (`prose.md`, `code.md`, `diagrams.md`, `expert_notes.md`, `skeptic_notes.md`, `chapter.md`) plus the traceability matrix. `book.md`, translations, and EPUBs are **not** automatically updated.

**Examples:**

```bash
/rewriting-book-chapter distributed-systems \
  chapter=5 \
  reason="narrative validator: missing bridge from ch4"

/rewriting-book-chapter kafka-internals \
  chapter=3 \
  reason="expert reviewer: consumer group explanation too brief"
```

---

### `/rewriting-book-introduction` — Introduction Regeneration

Regenerates only `introduction.md` without re-running any chapter or downstream phase. Use when the TOC changes, the audience scope is updated, or the introduction needs a full rewrite after narrative review.

**Syntax:**

```
/rewriting-book-introduction <book-slug> [reason="..."]
```

**Parameters:**

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `slug` | YES | — | Folder name under `Books/` |
| `reason` | no | — | Reason logged in the traceability matrix |

**Prerequisites:** `Books/{slug}/toc.md` and `traceability_matrix.md` must exist.

**What is updated:** Only `Books/{slug}/introduction.md` and the traceability matrix row. `book.md`, translations, and EPUBs are **not** automatically updated.

**Examples:**

```bash
/rewriting-book-introduction distributed-systems \
  reason="TOC restructured after narrative review"

/rewriting-book-introduction kafka-internals \
  reason="audience scope updated to include junior engineers"
```

---

### `/switching-book-language` — Code Language Switch

Regenerates all `code.md` files across every chapter using a new primary language, then reassembles `chapter.md` and `book.md`. Optionally re-runs translations and EPUB formatting.

**Syntax:**

```
/switching-book-language <book-slug> language=<lang>
  [style=working-code|pseudocode-first|pseudocode-only]
  [additional=go,typescript]
  [translate=yes|no]
  [epub=yes|no]
```

**Parameters:**

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `slug` | YES | — | Folder name under `Books/` |
| `language` | YES | — | New primary language: `python` / `go` / `java` / `typescript` / `pseudocode` |
| `style` | no | keeps current | Override `code_style` |
| `additional` | no | keeps current | Extra languages per example; ignored when `style=pseudocode-only` |
| `translate` | no | `yes` | Re-run translations if they previously existed |
| `epub` | no | `yes` | Re-run EPUB formatting if EPUBs previously existed |

**What is regenerated vs. preserved:**

| Asset | Action |
|-------|--------|
| `chapters/ch{N}/code.md` | Regenerated |
| `chapters/ch{N}/chapter.md` | Reassembled with new code |
| `book.md` | Regenerated |
| `book_pt-BR.md` / `book_es.md` | Conditional (`translate=yes` + existed) |
| `kindle/{lang}/book.epub` | Conditional (`epub=yes` + existed) |
| `chapters/ch{N}/prose.md` | **Preserved** |
| `chapters/ch{N}/diagrams.md` | **Preserved** |
| `chapters/ch{N}/expert_notes.md` | **Preserved** |
| `chapters/ch{N}/skeptic_notes.md` | **Preserved** |

**Examples:**

```bash
# Switch entire book to Python working code
/switching-book-language event-driven-architecture \
  language=python \
  style=working-code

# Switch to Go with TypeScript alternatives, skip re-translating
/switching-book-language kafka-internals \
  language=go \
  style=pseudocode-first \
  additional=typescript \
  translate=no

# Collapse to pseudocode-only, skip everything downstream
/switching-book-language my-book \
  language=java \
  style=pseudocode-only \
  translate=no \
  epub=no
```

---

### `/translating-book` — Standalone Translation

Translates a completed `book.md` to pt-BR or es. Code fences, Mermaid blocks, and technical term names are preserved in English. Can be run standalone or re-run after a chapter rewrite.

**Syntax:**

```
/translating-book <path/to/book.md> target=<pt-BR|es> [slug=<book-slug>]
```

**Parameters:**

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `book_path` | YES | — | Absolute or relative path to `book.md` |
| `target` | YES | — | `pt-BR` or `es` |
| `slug` | no | derived from path | Determines output directory |

**What is translated / preserved:**

| Element | Action |
|---------|--------|
| Prose, headings, list items | Translated |
| Code blocks (` ``` ` fences) | Preserved in English |
| Mermaid blocks | Preserved in English |
| Technical term names (framework names, CLI commands, URLs) | Kept in English |
| Callout labels (Expert Note, Critical Note, Key Takeaways, What's Next) | Translated per built-in table |
| First use of a translatable technical term | Parenthetical translation appended |

**Output files:**

```
Books/{slug}/book_pt-BR.md    (if target=pt-BR)
Books/{slug}/book_es.md       (if target=es)
```

**Examples:**

```bash
/translating-book Books/distributed-systems/book.md target=pt-BR

/translating-book Books/kafka-internals/book.md target=es slug=kafka-internals

# Translate to both languages (two separate invocations):
/translating-book Books/distributed-systems/book.md target=pt-BR
/translating-book Books/distributed-systems/book.md target=es
```

---

### `/formatting-book-epub` — Standalone EPUB 3.0 Formatting

Converts a `book.md` into a valid EPUB 3.0 source tree ready for zip and upload to Amazon KDP. Produces one language's EPUB per invocation.

**Syntax:**

```
/formatting-book-epub <path/to/book.md>
  [slug=<book-slug>]
  [toc=<path/to/toc.md>]
  [language=en|pt-BR|es]
  [author="Author Name"]
```

**Parameters:**

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `book_path` | YES | — | Path to `book.md` (or translated variant) |
| `slug` | no | derived from path | Output directory under `Books/` |
| `toc` | no | `Books/{slug}/toc.md` | Path to `toc.md` for navigation generation |
| `language` | no | `en` | `en` / `pt-BR` / `es` |
| `author` | no | `Author Name` | Book author name for EPUB metadata |

**What it produces:**

```
Books/{slug}/kindle/{language}/epub-src/
├── mimetype
├── META-INF/container.xml
└── OEBPS/
    ├── content.opf
    ├── nav.xhtml
    ├── toc.ncx
    ├── styles.css
    └── ch{N:02d}.xhtml

Books/{slug}/kindle/{language}/book.epub   ← final zipped EPUB
```

Mermaid diagrams are converted to text captions + `<pre>` blocks (Kindle cannot render Mermaid). Code blocks are HTML-escaped. Format is EPUB 3.0 reflowable. **MOBI is never generated** (deprecated March 2025).

**Examples:**

```bash
/formatting-book-epub Books/distributed-systems/book.md \
  slug=distributed-systems \
  language=en \
  author="Jane Doe"

/formatting-book-epub Books/distributed-systems/book_pt-BR.md \
  slug=distributed-systems \
  language=pt-BR \
  author="Jane Doe"
```

**After running:** Upload `book.epub` to kdp.amazon.com → New Title → eBook. Validate with Kindle Previewer first. Cover image (2560×1600 px minimum) must be provided separately.

---

### `/enriching-book-chapter` — Enrich External Chapter

Takes a `chapter.md` written outside the pipeline (without `[CODE:]` / `[DIAGRAM:]` markers), infers injection points using heuristic rules, writes an enriched `prose.md`, then runs the standard P4.2 + P4.3 sub-pipeline to produce fully assembled chapter assets.

Use this when you have existing prose you want to integrate into the book agent pipeline without rewriting it from scratch.

**Syntax:**

```
/enriching-book-chapter <path/to/chapter.md> slug=<book-slug>
  [chapter=<N>]
  [toc=<path/to/toc.md>]
  [audience="..."]
  [code_style=working-code|pseudocode-first|pseudocode-only]
  [code_language=java|go|typescript|python|pseudocode]
  [additional_languages=go,typescript]
```

**Parameters:**

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `chapter.md path` | YES | — | Path to the external chapter file (first positional argument) |
| `slug` | YES | — | Output book folder under `Books/` |
| `chapter` | no | `1` | Chapter slot number; determines `ch{N:02d}/` subfolder |
| `toc` | no | `Books/{slug}/toc.md` if exists | Path to `toc.md` for chapter objective and key concept context |
| `audience` | no | inferred | Reader profile; passed to `expert-reviewer` and `skeptic-reviewer` |
| `code_style` | no | `working-code` | `pseudocode-only` / `working-code` / `pseudocode-first` |
| `code_language` | no | `pseudocode` | Primary code language for `code-illustrator` |
| `additional_languages` | no | _(none)_ | Extra code languages, comma-separated. Requires `code_style ≠ pseudocode-only` |

**Pipeline stages (mode=enrich-chapter):**

| Stage | What happens |
|-------|-------------|
| E1 | Load `injection-heuristics.md`; optionally load TOC context |
| E2 | Spawn `chapter-enricher` → enriched `prose.md` (original prose preserved verbatim; markers inserted) |
| E3 | [PARALLEL] `code-illustrator` + `diagram-illustrator` + `expert-reviewer` + `skeptic-reviewer` |
| E4 | `code-validator` → validated `code.md` (skipped if `code_style=pseudocode-only`) |
| E5 | `chapter-assembler` → final `chapter.md` |

**Injection heuristics — what the enricher detects:**

`[CODE:]` triggers:
- Named algorithms or computational steps ("the idempotent consumer checks the message ID before processing")
- Data structure or schema definitions ("the event store table has three columns")
- API contracts or method signatures ("the function takes a userId and returns a list of orders")
- Anti-pattern contrasts ("the right approach is X; the anti-pattern is Y")
- "Your Turn" / exercise sections
- Named library or framework usage with specific API ("using Lambda Powertools, annotate with @Tracer")
- Configuration as key-value pairs or environment variables

`[DIAGRAM:]` triggers:
- Multi-actor flows with named components ("Service A sends to broker; consumer group reads")
- Side-by-side architecture comparisons ("on one side… on the other side")
- Decision criteria ("use X when… use Y when…") → always uses `flowchart |` prefix
- State machine or lifecycle transitions ("moves from PENDING → PROCESSING → COMPLETE")
- Architectural topology with named nodes
- Trade-off matrices described in prose

**Sections that never receive markers:** `Key Takeaways`, `What's Next` (summary/transition sections).

**Output files:**

```
Books/{slug}/chapters/ch{N:02d}/
├── prose.md           (enriched — original prose + [CODE:]/[DIAGRAM:] markers)
├── code.md
├── diagrams.md
├── expert_notes.md
├── skeptic_notes.md
└── chapter.md
```

`book.md`, translations, and EPUBs are **not** automatically updated after this command.

**Examples:**

```bash
# Enrich an intro chapter into slot 1 (all defaults)
/enriching-book-chapter draft-chapters/intro.md slug=my-book chapter=1

# Full context: TOC + audience + working Java code
/enriching-book-chapter external/ch03.md \
  slug=event-driven-arch \
  chapter=3 \
  toc=Books/event-driven-arch/toc.md \
  audience="senior backend engineers" \
  code_style=working-code \
  code_language=java

# Pseudocode-first + Go alternative
/enriching-book-chapter raw/chapter-five.md \
  slug=kafka-internals \
  chapter=5 \
  code_style=pseudocode-first \
  code_language=java \
  additional_languages=go

# Pseudocode-only (no code validation, no runtime dependency)
/enriching-book-chapter drafts/overview.md \
  slug=platform-engineering \
  chapter=2 \
  code_style=pseudocode-only \
  audience="platform engineers"
```

---

## Pipeline Architecture

```
/writing-technical-book
    └── book-orchestrator (opus)
         │
         ├── P1: init directory tree + traceability_matrix.md
         │
         ├── P2: TOC research (model + web searches) → toc.md
         │
         ├── P3: ★ USER APPROVAL GATE ★ (EnterPlanMode/ExitPlanMode)
         │
         ├── P3.5: introduction writing → introduction.md
         │
         ├── P4: [per chapter, strictly sequential]
         │    ├── chapter-writer → prose.md
         │    ├── [PARALLEL]
         │    │    ├── code-illustrator    → code.md
         │    │    ├── diagram-illustrator → diagrams.md
         │    │    ├── expert-reviewer     → expert_notes.md
         │    │    └── skeptic-reviewer    → skeptic_notes.md
         │    ├── code-validator → code.md (validated)
         │    │    (skipped when code_style=pseudocode-only)
         │    └── chapter-assembler → chapter.md
         │
         ├── P5: narrative validation → narrative_report.md
         │    book.md assembled; matrix-check gate (0 PLANNED, 0 FAILED required)
         │
         ├── P6: [PARALLEL]
         │    ├── book-translator (pt-BR) → book_pt-BR.md
         │    └── book-translator (es)    → book_es.md
         │
         └── P7: kdp_metadata.md
              [PARALLEL]
              ├── book-formatter (en)    → epub-src/ → book.epub
              ├── book-formatter (pt-BR) → epub-src/ → book.epub
              └── book-formatter (es)    → epub-src/ → book.epub

/enriching-book-chapter
    └── book-orchestrator (opus) [mode=enrich-chapter]
         │
         ├── E1: load injection-heuristics.md + optional TOC context
         ├── E2: chapter-enricher → prose.md (markers inserted; original text preserved)
         ├── E3: [PARALLEL] code-illustrator + diagram-illustrator + expert-reviewer + skeptic-reviewer
         ├── E4: code-validator → code.md (skipped if pseudocode-only)
         └── E5: chapter-assembler → chapter.md
```

**Traceability lifecycle for every asset:**
`PLANNED` → `CREATED` (before agent spawn) → `VERIFIED` (after Glob-confirm) / `FAILED` (file not found) / `SKIPPED` (not applicable)

---

## Agents Reference

| Agent | Model | Role |
|-------|-------|------|
| `book-orchestrator` | opus | Full pipeline orchestrator; maintains traceability matrix; spawns all other agents |
| `chapter-writer` | opus | Writes audience-calibrated English prose; inserts `[CODE:]` and `[DIAGRAM:]` markers |
| `chapter-enricher` | sonnet | Infers `[CODE:]` and `[DIAGRAM:]` injection points in external unstructured prose; preserves original text verbatim |
| `code-illustrator` | sonnet | Resolves `[CODE:]` markers; generates code examples per `code_style` and `additional_languages` |
| `diagram-illustrator` | sonnet | Resolves `[DIAGRAM:]` markers; generates valid Mermaid diagrams |
| `expert-reviewer` | sonnet | Reviews prose as a 10+ year practitioner; produces up to 8 `💡 Expert Note` annotations |
| `skeptic-reviewer` | sonnet | Reviews prose as a rigorous skeptic; produces up to 8 `⚠️ Critical Note` annotations |
| `code-validator` | sonnet | Language consistency check; missing-language generation; compilation/execution validation |
| `chapter-assembler` | sonnet | Merges all 5 chapter assets; resolves markers; integrates callouts; writes `chapter.md` |
| `book-translator` | sonnet | Translates `book.md` to pt-BR or es; preserves code, Mermaid, and technical terms |
| `book-formatter` | sonnet | Converts `book.md` to EPUB 3.0 source tree (XHTML, OPF, nav, NCX, CSS) |

### Diagram type selection (diagram-illustrator)

| Marker description contains | Diagram type |
|-----------------------------|-------------|
| "flow", "process", "steps", "pipeline" | `flowchart TD` or `flowchart LR` |
| "sequence", "interaction", "request/response" | `sequenceDiagram` |
| "class", "structure", "inheritance" | `classDiagram` |
| "data model", "entity", "relationship" | `erDiagram` |
| "state", "transition", "lifecycle" | `stateDiagram-v2` |
| "timeline", "history", "evolution" | `timeline` |
| "graph", "network", "topology" | `graph LR` |
| "architecture", "components", "layers" | `C4Context` or `flowchart TD` with subgraphs |
| prefixed with `flowchart \|` | `flowchart TD` decision tree (override) |

### Code validation strategies (code-validator)

| Language | Validation method |
|----------|------------------|
| Python | `python -c "{code}"` or temp `.py` file |
| Go | temp `main.go` + `go build` |
| Java | temp `{ClassName}.java` + `javac` |
| TypeScript | temp `.ts` + `npx tsc --noEmit --strict` |
| JavaScript | `node --check {file}` |
| Other | LLM-as-judge review |

Up to 3 retry attempts per block. Persistent failures are annotated with `// ⚠️ VALIDATION:` prefix rather than silently dropped.

---

## Writing Style Blueprint

Rules applied by `chapter-writer` on every chapter (from `blueprints/writing-style-guide.md`):

- **Voice:** Direct, conversational, confident, instructional — a senior professional sharing hard-won lessons, not academic prose or marketing copy.
- **Tone:** Solution-oriented; encourages the reader; assumes beginner level on the subject matter.
- **Explanation methods:** Decomposition (numbered steps) → Analogy (concrete everyday examples) → Comparison (what it IS and IS NOT).
- **Structure per concept:** Definition → Contextualization → Review and connection.
- **Code placement:** Immediately after each concept, not grouped at the end.
- **Lists:** Numbered for sequential procedures; tables for comparisons.
- **Recurring elements:** Pro Tips callout, "Your Turn to Try!" exercise, Summary (3–5 bullets), What's Next (1–2 sentences) — all mandatory per chapter.
- **Avoid:** Long sentences, assumed expert knowledge, redundant code blocks, excessively formal language.

### Callout priority levels

| Reviewer | Priority | Integration |
|----------|----------|-------------|
| Expert Note | `high` | Inline blockquote in `chapter.md` |
| Expert Note | `medium` | Collapsed `<details>` block |
| Expert Note | `low` | `expert_notes.md` only |
| Critical Note | `blocking` | Inline blockquote in `chapter.md` |
| Critical Note | `important` | Collapsed `<details>` block |
| Critical Note | `minor` | `skeptic_notes.md` only |

---

## Limits and Constraints

| Constraint | Value |
|------------|-------|
| Max chapters before warning | 15 |
| Target words per chapter (introductory) | 1800–2500 |
| Target words per chapter (intermediate/senior) | 1500–2000 |
| Target words per chapter (expert/advanced) | 1200–1800 |
| Target words per section | 300–600 |
| Max Mermaid nodes per diagram | 20 |
| Max Expert / Critical Note annotations per chapter | 8 each |
| Code validator retry attempts per block | 3 |
| Translation languages | pt-BR, es (always included in full pipeline) |
| EPUB format | EPUB 3.0 reflowable only |
| MOBI | Never generated (deprecated March 2025) |
| Chapter ordering | ch(N+1) never starts before ch(N) `chapter.md` is VERIFIED |
| Phase 6 gate | P6 (translations) never starts if any asset is PLANNED or FAILED |

---

## Output Structure (full pipeline)

```
Books/{topic-slug}/
├── traceability_matrix.md          ← asset lifecycle tracker
├── toc.md                          ← approved table of contents
├── book_metadata.md                ← topic, audience, context, parameters
├── introduction.md                 ← book introduction (scope, audience, chapter overview, conventions)
├── narrative_report.md             ← cross-chapter coherence analysis
├── book.md                         ← complete assembled book (English, introduction + all chapters)
├── book_pt-BR.md                   ← Brazilian Portuguese translation
├── book_es.md                      ← Spanish translation
├── chapters/
│   ├── ch01/
│   │   ├── prose.md                ← raw chapter prose with [CODE:] / [DIAGRAM:] markers
│   │   ├── code.md                 ← code examples (validated)
│   │   ├── diagrams.md             ← Mermaid diagrams
│   │   ├── expert_notes.md         ← expert annotations
│   │   ├── skeptic_notes.md        ← skeptical critique annotations
│   │   └── chapter.md             ← final assembled chapter
│   └── ch{N}/...
└── kindle/
    ├── kdp_metadata.md             ← KDP upload metadata
    ├── en/
    │   ├── epub-src/               ← EPUB 3.0 source tree
    │   └── book.epub
    ├── pt-BR/
    │   ├── epub-src/
    │   └── book.epub
    └── es/
        ├── epub-src/
        └── book.epub
```
