---
name: translating-book
description: Translates an existing book.md to a target language (pt-BR or es), preserving all Markdown formatting and leaving code blocks and Mermaid syntax in English. Use when a completed book needs translation without re-running the full pipeline.
argument-hint: "<path/to/book.md> target=<pt-BR|es> [slug=<book-slug>]"
context: fork
agent: book-translator
disable-model-invocation: true
---

## Function

Routes directly to `book-translator`. Translates a completed `book.md` to the specified language.

**Translation rules:**
- Prose, headings, and list items → translated to target language
- Code blocks (` ``` ` fences) → preserved verbatim in English
- Mermaid blocks → preserved verbatim in English
- Technical terms (framework/library names, CLI commands, URLs) → kept in English
- Callout labels (Expert Note, Critical Note) → translated per the translator's built-in table
- On first use of a translatable technical term: provides a parenthetical translation

## Input Parameters

| Parameter | Required | Default | Notes |
|-----------|----------|---------|-------|
| `book_path` | ✅ | — | Absolute or relative path to `book.md` |
| `target` | ✅ | — | `pt-BR` or `es` |
| `slug` | ⚠️ | derived from path | Used to determine output directory |

## Output

```
Books/{slug}/book_pt-BR.md    (if target=pt-BR)
Books/{slug}/book_es.md       (if target=es)
```

If `slug` is not provided, the output is placed next to the input file as `book_{target}.md`.

## Usage

```
/translating-book Books/distributed-systems/book.md target=pt-BR
/translating-book Books/kafka-internals/book.md target=es slug=kafka-internals
```

To translate both languages, run twice (or let `/writing-technical-book` handle both in parallel):
```
/translating-book Books/distributed-systems/book.md target=pt-BR
/translating-book Books/distributed-systems/book.md target=es
```
