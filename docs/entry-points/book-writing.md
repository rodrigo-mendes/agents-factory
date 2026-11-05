# Book-writing commands

The book pipeline writes a technical book from a topic and an audience, in phases: table of
contents, introduction, chapters, assets (code, diagrams), assembly, validation, translation and
EPUB output. Output goes to `Books/{slug}/`, which is git-ignored.

Most commands are thin entry points. They route to the `book-orchestrator`, which runs the phases.
The [package manual](../../packages/content-generation/book-writing/README.md) has the full pipeline, every parameter and 14 usage scenarios; this page shows what to run for each job.

## Start a new book

```
/writing-book-toc <topic> audience=<audience> [chapters=10] [depth=standard|exhaustive]
```
Creates only the table of contents. Review it before you write chapters.

```
/writing-technical-book <topic> audience=<audience> context=<market-context> [chapters=10] \
  [code_style=pseudocode-only|pseudocode-first|working-code] [code_language=...] \
  [additional_languages=go,typescript] [decision_diagrams=flowchart]
```
Runs the full pipeline from topic to EPUB.

## Change part of a book

| Job | Command | Example |
|---|---|---|
| Rewrite one chapter | [`/rewriting-book-chapter`](../../packages/content-generation/book-writing/README.md#rewriting-book-chapter) | `/rewriting-book-chapter my-book chapter=4 reason="narrative issue: jumps ahead"` |
| Rewrite the introduction | [`/rewriting-book-introduction`](../../packages/content-generation/book-writing/README.md#rewriting-book-introduction) | `/rewriting-book-introduction my-book reason="too long"` |
| Add code and diagrams to a chapter you wrote yourself | [`/enriching-book-chapter`](../../packages/content-generation/book-writing/README.md#enriching-book-chapter) | `/enriching-book-chapter drafts/ch3.md slug=my-book chapter=3` |
| Change the language | [`/switching-book-language`](../../packages/content-generation/book-writing/README.md#switching-book-language) | `/switching-book-language my-book language=pt-BR translate=yes epub=yes` |

## Output and packaging

| Job | Command | Example |
|---|---|---|
| Translate a finished book | [`/translating-book`](../../packages/content-generation/book-writing/README.md#translating-book) | `/translating-book Books/my-book/book.md target=es` |
| Render Mermaid diagrams to PNG | [`/rendering-mermaid-diagrams`](../../packages/content-generation/book-writing/README.md#rendering-mermaid-diagrams) | `/rendering-mermaid-diagrams Books/my-book/book.md` |
| Build the EPUB source | [`/formatting-book-epub`](../../packages/content-generation/book-writing/README.md#formatting-book-epub) | `/formatting-book-epub Books/my-book/book.md slug=my-book language=en` |
| Repair or rebuild an EPUB | [`/repairing-book-epub`](../../packages/content-generation/book-writing/README.md#repairing-book-epub) | `/repairing-book-epub Books/my-book/kindle/` |

## Which order?

1. `/writing-book-toc`, then review the table of contents.
2. `/writing-technical-book` to produce the draft.
3. `/rendering-mermaid-diagrams` on the draft.
4. `/translating-book` for each target language, if you need one.
5. `/formatting-book-epub` per language, then `/repairing-book-epub` if validation fails.

## Common mistakes

- Running `/writing-technical-book` without a clear audience. The audience drives the depth of
  every chapter, so state it.
- Rewriting a chapter without a `reason=`. The pipeline needs the problem to fix.

## Related

- Package: [`book-writing`](../../packages/content-generation/book-writing/README.md).
- Agents: `book-orchestrator` and its workers ([subagents](../agents/README.md)).
