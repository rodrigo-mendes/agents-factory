# Chapter Structure Template

Reference for `chapter-writer`. This defines the canonical structure of every chapter and the exact marker syntax for asset injection.

---

## Canonical Chapter Structure

```markdown
# Chapter {N}: {Title}

## Opening Problem Statement
[1 paragraph, 150–250 words]
[Poses the question or problem this chapter answers. Explains why it matters to the target audience.]
[If not the first chapter: opens with a reference connecting to the previous chapter's conclusion.]

## {Section title derived from Key Concept 1}
[Prose, 300–600 words]
[Introduces and explains the concept clearly]

[CODE: brief description of what should be illustrated]

[Prose continuing the explanation]

[DIAGRAM: brief description of what diagram type and content]

[Prose wrapping up the concept]

## {Section title derived from Key Concept 2}
[Prose, 300–600 words]
[Same pattern: prose → marker → prose]

[... repeat for each key concept from TOC ...]

## Pro Tips
- [Pro Tip 1: practical advice or deeper insight on a concept from this chapter]
- [Pro Tip 2 — optional]
- [Pro Tip 3 — optional]

## Your Turn to Try!
[1–3 hands-on exercises with detailed instructions the reader can run on their computer. For each exercise: describe the task, the expected result, and optionally provide the answer/solution code.]

## Summary
- [Bullet 1: most important thing learned]
- [Bullet 2]
- [Bullet 3]
- [Bullet 4 — optional]
- [Bullet 5 — optional]

## What's Next
[1–2 sentences bridging to the next chapter. For the final chapter: "This concludes [BOOK TITLE]. [Final reflective sentence.]"]
```

---

## Marker Syntax Reference

### Code Marker
```
[CODE: brief description of what code/algorithm/pseudocode should illustrate]
```

Rules:
- Place on its own line
- The description tells `code-illustrator` what to generate
- Include the concept being illustrated and optionally the preferred artifact type: `[CODE: Python example of exponential backoff retry logic]`, `[CODE: pseudocode for binary search algorithm]`
- Do NOT place two markers back-to-back without intervening prose
- Each marker needs at least one context sentence before and after it

### Diagram Marker
```
[DIAGRAM: brief description of what the diagram should show and what type (flowchart/sequence/class/ER/state)]
```

Rules:
- Place on its own line
- Include what the diagram depicts and optionally the Mermaid type: `[DIAGRAM: sequence diagram of HTTP request-response between client and load balancer]`, `[DIAGRAM: flowchart of consumer group rebalancing process]`
- If no specific type mentioned, `diagram-illustrator` will choose the most appropriate type

---

## Word Count Targets

| Audience | Target per chapter | Per section |
|----------|-------------------|-------------|
| Introductory / junior | 1800–2500 words | 400–600 |
| Intermediate / senior | 1500–2000 words | 300–500 |
| Expert / advanced | 1200–1800 words | 250–400 |

---

## What NOT to Include in Prose

| ❌ Don't | ✅ Do instead |
|----------|--------------|
| Actual code blocks (``` fences) | `[CODE: description]` markers |
| Mermaid diagram blocks | `[DIAGRAM: description]` markers |
| Two consecutive markers | Separate with at least one prose sentence |
| Placeholder text ("TBD", "TODO") | Leave the section out; write what you know |
| Self-referential meta-text ("In this section we will...") | Start directly with the content |
