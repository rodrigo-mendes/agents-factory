# Output Format Template — researching-technical-frameworks

Save the research document as `research_{{SYSTEM_NAME}}_v{{TARGET_VERSION}}.md`.

---

## Metadata

```yaml
Full_Name: [Official Name]
Target_Version: [Version]
Release_Date: [Date]
Support_Status: [Active/LTS/EOL]
Primary_Docs: [URL]
Official_Repo: [URL]
Research_Date: [Date]
Domain_Complexity: [Foundational/Standard/Complex]
Research_Depth: [quick/standard/deep/exhaustive]
Max_Iterations: [N]
Gap_Loop_Ran: [true/false]
Iterations_Used: [N of MAX_ITERATIONS]
Triangulated_Count: [N]       # Always-Do patterns with ✓✓ badge
Unverified_Count: [N]         # Claims still marked "unverified" after gap loop
Irresolvable_Count: [N]       # Items marked IRRESOLVABLE
Research_Quality_Score: [N%]  # = (total_claims - unverified - irresolvable) / total_claims * 100
```

---

## Executive Summary

[2-3 paragraphs: what it does, key changes in this version, critical guardrails, domain complexity tier
and why that tier was assigned]

---

## Architectural Guardrails

> Confidence legend: 🟢 High (2+ official sources, dated ≤12mo) | 🟡 Medium (1 source or dated 12–24mo) | 🔴 Low (community source or dated >24mo — verify before use)

### ✅ Mandatory Patterns

**[Pattern Name]**
> Confidence: 🟢 High | [✓✓ Triangulated | Source A (DATE) + Source B (DATE)]
- Why: [Reason]
- Code:
  ```[language]
  [example]
  ```
- Source: [URL] (DATE)

### ⚠️ Conditional Patterns

**[Decision Point]**
> Confidence: 🟡 Medium
- Options: [A, B, C]
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|

- Agent: "Ask user [decision based on factors]"
- Source: [URL] (DATE)

### 🚫 Forbidden Patterns

**[Anti-Pattern Name]**
> Severity: Critical | High | Medium
> Confidence: 🟢 High
- Why: [Reason]
- Impact: [What breaks]
- ❌ Wrong:
  ```[language]
  [bad code]
  ```
- ✅ Correct:
  ```[language]
  [good code]
  ```
- Source: [URL] (DATE)

---

## Migration Guide

> Confidence: 🟢 High | Sources: [changelog URL] (DATE) + [migration guide URL] (DATE)

**Breaking Changes**: [List]

**Upgrade Steps**: [Numbered list with commands]

**Compatibility Matrix**:

| Dependency | Min | Max | Notes |
|------------|-----|-----|-------|

---

## Implementation Blueprint

> Confidence: 🟢 High | [✓✓ Triangulated | official example + official docs]

**Lifecycle**:
```[language]
// Init, Usage, Cleanup
[code]
```

**Integration**: {{SYSTEM_NAME}} ↔ [Partner]
```[language]
[complete example]
```

---

## Quality Control

**Verification Commands**:
```bash
# Representative — adapt to your environment
# Init, Lint, Test, Health
[commands with expected outputs]
```

**Mocking**:
```[language]
[test example with mocking]
```

---

## Production Readiness

- **Performance**: [Latency, throughput, resources]
- **Scalability**: [Vertical/horizontal limits]
- **Monitoring**: [Critical metrics checklist]
- **Security**: [Hardening checklist]

---

## Reference Implementations

- [Official examples with URLs]
- [Canonical patterns]
- [Educational resources]

---

## Source Bibliography

**Primary**: [Official docs, blog, release notes with URLs and dates]
**Validation**: [Stack Overflow, GitHub issues with relevance]
**All Deep-Links**: [Complete organized list]

---

## Research Gaps

> Every gap that survives all gap-loop iterations must also appear as an IRRESOLVABLE row in §7.

```
Gap: [What's missing]
Impact: [Effect on safety]
Workaround: [Temporary approach]
Follow-up: [Where to check]
§7-ref: Iteration [N] — IRRESOLVABLE
```

---

## §7 — Research Iteration Changelog

> Mandatory when `RESEARCH_DEPTH` is `standard`, `deep`, or `exhaustive`. Omit for `quick`.

| Iteration | Section | Item | Action | Source |
|-----------|---------|------|--------|--------|
| 1 | [Section name] | [Claim or pattern] | Added / Resolved / Updated | [URL] (DATE) |
| 2 | [Section name] | [Claim or pattern] | ⚠️ IRRESOLVABLE — [one-line rationale] | — |

> Add one row per gap-loop resolution. Rows are appended in order; do not reorder.
> `IRRESOLVABLE` rows remain in the table permanently as an audit trail.

---

## Completion Checklist

- [ ] Domain complexity tier assessed and documented
- [ ] All scope areas cited
- [ ] Pattern counts driven by domain needs (not template minimums)
- [ ] Every anti-pattern has alternative
- [ ] All CLI commands validated/marked as representative
- [ ] Integration examples complete
- [ ] Sources dated and linked
- [ ] Security documented
- [ ] 1+ copy-paste working example
- [ ] Confidence badge applied to every pattern entry
- [ ] All Always-Do patterns triangulated (deep/exhaustive) or downgraded to 🟡 Medium
- [ ] §7 Iteration Changelog present and complete
- [ ] Research_Quality_Score calculated and added to Metadata
- [ ] Every Research Gap cross-referenced in §7

---

## Agent Operation Notes

- **High Confidence (execute without asking)**: claims marked 🟢 High with ✓✓ Triangulated badge
- **Medium Confidence (validate with user)**: claims marked 🟡 Medium; single-source Always-Do patterns
- **Low Confidence (must ask human)**: claims marked 🔴 Low; IRRESOLVABLE items
- **Edge Cases (pause)**: version released <30 days ago; active CVE; EOL technology
- **Emergency Stop**: all sources community-only; version EOL and replacement exists
