# Output Format Template — technical-framework-researcher

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
```

---

## Executive Summary

[2-3 paragraphs: what it does, key changes in this version, critical guardrails, domain complexity tier
and why that tier was assigned]

---

## Architectural Guardrails

### ✅ Mandatory Patterns

**[Pattern Name]**
- Why: [Reason]
- Code:
  ```[language]
  [example]
  ```
- Source: [Link]

### ⚠️ Conditional Patterns

**[Decision Point]**
- Options: [A, B, C]
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|

- Agent: "Ask user [decision based on factors]"
- Source: [Link]

### 🚫 Forbidden Patterns

**[Anti-Pattern]**

```[language]
// DON'T
[bad code]
```

- Why: [Reason]
- Instead:
  ```[language]
  // DO
  [good code]
  ```
- Impact: [What breaks]
- Source: [Link]

---

## Migration Guide

**Breaking Changes**: [List]

**Upgrade Steps**: [Numbered list with commands]

**Compatibility Matrix**:

| Dependency | Min | Max | Notes |
|------------|-----|-----|-------|

---

## Implementation Blueprint

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

---

## Research Gaps

```
Gap: [What's missing]
Impact: [Effect on safety]
Workaround: [Temporary approach]
Follow-up: [Where to check]
```

---

## Agent Operation Notes

- **High Confidence**: [Can execute without asking]
- **Medium**: [Should validate]
- **Low**: [Must ask human]
- **Edge Cases**: [When to pause]
- **Emergency Stop**: [Halt conditions]
