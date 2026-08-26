# Evaluation Scenarios Template

> Replace ALL `[PLACEHOLDERS]`. Each skill must define all 4 scenario types.
> Scenarios are run by the `evaluating-skill-scenarios` prompt → `skill-evaluator` agent.

---

## Scenario 1 — Canonical Path

```json
{
  "id": 1,
  "name": "canonical-[skill-name]",
  "description": "Standard successful invocation with well-formed inputs",
  "query": "[A typical, complete user request that this skill is designed to handle]",
  "must_pass": [
    "Response addresses [primary deliverable]",
    "Response cites at least one official source",
    "Response uses the correct output format (§N section headers present)",
    "No fabricated version numbers or API names"
  ],
  "must_not": [
    "Invent facts not in official docs",
    "Use deprecated APIs from previous versions",
    "Skip the mandatory [key section] section"
  ]
}
```

## Scenario 2 — Edge Case

```json
{
  "id": 2,
  "name": "edge-[skill-name]",
  "description": "Sparse or ambiguous input — skill must handle gracefully or ask a clarifying question",
  "query": "[A request with missing version, ambiguous technology name, or unusual integration target]",
  "must_pass": [
    "Response either asks a specific clarifying question OR proceeds with stated assumptions",
    "If assumptions are made, they are listed explicitly",
    "Response does not invent missing information silently"
  ],
  "must_not": [
    "Fabricate a version number that was not provided",
    "Proceed as if ambiguity does not exist",
    "Return an empty or generic response"
  ]
}
```

## Scenario 3 — Misuse Rejection

```json
{
  "id": 3,
  "name": "misuse-rejection-[skill-name]",
  "description": "Request that is outside this skill's scope — must decline and route correctly",
  "query": "[A request that clearly belongs to a different skill, e.g. asking a researcher to write code, or asking an auditor to generate a skill]",
  "must_pass": [
    "Response explicitly states the request is out of scope",
    "Response names the correct skill/prompt to use instead",
    "Response does NOT attempt to fulfill the out-of-scope request"
  ],
  "must_not": [
    "Attempt to fulfill a request outside scope",
    "Silently ignore the mismatch",
    "Give a vague 'I can't help with that' without routing guidance"
  ]
}
```

## Scenario 4 — Anti-Pattern Trap

```json
{
  "id": 4,
  "name": "anti-pattern-trap-[skill-name]",
  "description": "Input contains an embedded 🚫 Never-Do violation — skill must detect and reject it",
  "query": "[A request that contains or implies a known forbidden pattern, e.g. using an undated source, mixing versions, skipping version pinning]",
  "must_pass": [
    "Response identifies the forbidden pattern by name",
    "Response explains why it is forbidden",
    "Response provides the correct alternative approach"
  ],
  "must_not": [
    "Proceed with the forbidden pattern without comment",
    "Accept an undated or community-only source as authoritative",
    "Mix version patterns from different releases"
  ]
}
```
