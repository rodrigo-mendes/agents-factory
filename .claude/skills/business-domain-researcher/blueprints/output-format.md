# Output Format — business-domain-researcher

Save research output as `research_{{DOMAIN_OR_FUNCTION_NAME}}_{{ORGANIZATIONAL_CONTEXT}}.md`

---

## Domain Context

```yaml
Domain_Function: [Official name of the function]
Organizational_Context: [Description of org type, size, sector, geography]
Primary_Regulatory_Body: [Name + URL]
Applicable_Legislation: [List of laws/norms/standards with effective dates]
Internal_Policy_Owner: [Role, not name]
Internal_Policy_Version: [Version and effective date if available]
Jurisdiction: [Country/Region]
Research_Date: [Date]
Currency_Threshold: [Date after which this research must be reviewed]
```

---

## Executive Summary

[2–3 paragraphs: what {{DOMAIN_OR_FUNCTION_NAME}} does in {{ORGANIZATIONAL_CONTEXT}}, key regulatory obligations, and critical operational guardrails the agent must respect]

---

## Domain Terminology Glossary

[10–20 key terms used in this domain that the agent must understand precisely — definitions sourced from regulation or authoritative standards, not informal usage]

```
Term: [Domain-specific term]
Definition: [Precise definition as used in {{ORGANIZATIONAL_CONTEXT}}]
Regulatory Basis: [Where this term is defined or used in law/regulation]
Agent Usage: [How the agent should interpret this term in context]
```

---

## Operational Guardrails

### ✅ Mandatory Practices

[Practice Name]
- Why: [Regulatory/policy basis]
- How: [Step-by-step or checklist]
- Applies When: [Trigger]
- Verification: [How to confirm compliance]
- Source: [Link]

### ⚠️ Human Validation Required

[Decision Point]
- Options: [A, B, C]
- Tradeoffs:

  | Path | Benefit | Risk | Stakeholders Affected | Best When |
  |------|---------|------|-----------------------|-----------|

- Escalation Path: [Role → Role → Role, within [timeframe]]
- Agent Instruction: "Ask/notify [role] when [specific condition]"
- Source: [Link]

### 🚫 Prohibited Actions

[Prohibition]
- Why: [Legal/ethical/policy reason]
- Instead: [Correct approach]
- Impact: [Category of harm]
- Severity: [CRITICAL | HIGH | MEDIUM]
- Source: [Link]

---

## Policy Update Guide

**Breaking Changes**: [List of regulatory or policy changes requiring immediate adaptation]
**Transition Steps**: [Numbered list with deadlines]
**Compatibility Matrix**:

| Existing Practice | Status After Update | Action Required | Deadline |
|-------------------|---------------------|-----------------|----------|

---

## Process Blueprint

**Standard Interaction Lifecycle**:
```
[Initiation → Execution → Compliance Check → Closure → Post-Interaction]
[With decision gates and escalation points clearly marked]
```

**Stakeholder Handoff Protocol**: {{DOMAIN_OR_FUNCTION_NAME}} ↔ [Stakeholder]
```
[Complete process sequence with required fields, SLAs, and confirmation steps]
```

---

## Process Quality Control

**Verification Checklist**:
```
Pre-interaction:    [Required context and authorization checks]
During-interaction: [Compliance checkpoints]
Post-interaction:   [Mandatory documentation and follow-up]
Escalation:         [Verification that escalation was correctly executed]
```

**Scenario Coverage**:
```
High-frequency scenario: [Scenario + expected agent behavior]
Edge case scenario:      [Scenario + expected fallback behavior]
Prohibited scenario:     [Scenario + agent refusal behavior]
```

---

## Operational Readiness

- **Volume Capacity**: [Interactions per hour/day within guardrails, escalation limits]
- **SLA Commitments**: [Response time, resolution time, escalation response time]
- **Audit Trail**: [What the agent must log, in what format, in which system]
- **Regulatory Monitoring**: [Metrics the agent must track for compliance reporting]
- **Human Oversight**: [How humans monitor and intervene in agent operation]

---

## Reference Processes

- [Official regulatory guidance documents with URLs]
- [Industry standard process templates]
- [Internal policy documents — reference by title, not content]
- [Professional association guidelines]

---

## Source Bibliography

**Primary**: [Official regulation, legislation, standards body publications with URLs and effective dates]
**Validation**: [Professional association reports, industry surveys, established frameworks with relevance notes]
**All Deep-Links**: [Complete organized list of sources used]

---

## Completion Checklist

- [ ] All scope areas cited with sources
- [ ] 3+ process examples for mandatory practices
- [ ] Every prohibition has a correct alternative
- [ ] All escalation paths specify roles and timeframes
- [ ] Stakeholder interoperability protocols complete
- [ ] Scenarios cover high-frequency, edge, and prohibited cases
- [ ] Sources dated and linked
- [ ] Regulatory obligations documented
- [ ] 1+ complete interaction lifecycle example

---

## Research Gaps

```
Gap: [What domain knowledge is missing or uncertain]
Impact: [Effect on agent safety or compliance]
Workaround: [Temporary conservative approach]
Follow-up: [Where to obtain this information — role, document, body]
```

---

## Agent Delegation Notes

- **High Confidence**: [Actions agent can execute autonomously — e.g., providing documented information, completing standard checklists]
- **Medium Confidence**: [Actions agent should validate before executing — e.g., applying a policy to a non-standard case]
- **Low Confidence**: [Actions agent must hand off to a human — e.g., any commitment with financial or legal consequence]
- **Edge Cases**: [When to pause and request human review]
- **Emergency Stop**: [Conditions under which the agent must immediately halt and alert a human — e.g., potential regulatory breach, customer distress signals, conflict of interest detected]
