# Cloud Architecture Research — Output Template

# Output Format

Save as `research_cloud_{{CLOUD_PROVIDER}}_{{ARCHITECTURE_DOMAIN}}_{{TARGET_EDITION}}.md`

## Metadata
```yaml
Full_Name: "{{CLOUD_PROVIDER}} {{ARCHITECTURE_DOMAIN}}"
Cloud_Provider: "{{CLOUD_PROVIDER}}"
Architecture_Domain: "{{ARCHITECTURE_DOMAIN}}"
Target_Edition: "{{TARGET_EDITION}}"
Architecture_Context: "{{ARCHITECTURE_CONTEXT}}"
Official_Source_URL: "{{OFFICIAL_SOURCE_IF_KNOWN}}"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "[Date]"
Currency_Threshold: "[Date 12 months from research — after which this research should be reviewed]"
```

## Executive Summary
[2–3 paragraphs covering:
1. What `{{ARCHITECTURE_DOMAIN}}` means within `{{CLOUD_PROVIDER}}` and its role in cloud architecture practice
2. What changed in `{{TARGET_EDITION}}` vs previous editions — new services, retired services, revised guidance
3. The three most critical architecture guardrails for the given `{{ARCHITECTURE_CONTEXT}}`]

## Cloud Architecture Glossary

10–20 terms that the architect must understand precisely — defined from official `{{CLOUD_PROVIDER}}` documentation, not informal usage:

```
Term: [Term from {{CLOUD_PROVIDER}} documentation]
Definition: [Exact meaning per {{TARGET_EDITION}}]
Provider Docs Section: [Where defined]
Architect Usage: [How to apply this term when making architecture decisions]
Common Confusion: [What it is frequently (incorrectly) confused with — especially cross-provider confusion]
```

## Architecture Guardrails

### ✅ Mandatory Patterns
**[Pattern Name]**
- Pillar Alignment: [Which framework pillar this satisfies]
- Why: [Official framework rationale — cite exactly]
- {{CLOUD_PROVIDER}} Services: [Specific services involved]
- Architecture Decision:
  [Pattern description with key configuration elements]
- Verification:
  [How to validate — console check, CLI command, audit tool]
- Source: [URL]

### ⚠️ Architectural Decisions
**[Decision Point]**
- Options:

  | Option | {{CLOUD_PROVIDER}} Service | Optimizes | Sacrifices | Best When |
  |--------|---------------------------|-----------|------------|-----------|

- Cost Profile: [Relative comparison]
- Lock-in Assessment: [Portability implications]
- Architect Instruction: "Ask [specific question] when [condition is met]"
- Source: [URL]

### 🚫 Anti-Patterns
**[Anti-Pattern Name]**
- Risk Level: [CRITICAL | HIGH | MEDIUM]
- Why: [Framework pillar violation — cite exactly]
- Instead: [Correct pattern with {{CLOUD_PROVIDER}} services]
- Detection: [Audit tool, CLI command, or policy check]
- Impact: [Data breach | Outage | Cost overrun | Compliance violation]
- Source: [URL]

## Cloud-Native Design Patterns

**[Pattern Name]**
- Category: [Resilience | Scalability | Data | Communication | Migration]
- Problem: [Architectural challenge]
- Solution on {{CLOUD_PROVIDER}}: [Service composition]
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|

- Source: [URL]

## Security Architecture

**[Security Domain]**
- {{CLOUD_PROVIDER}} Services: [Service composition]
- Architecture: [How services compose for the security pattern]
- Compliance Alignment: [Framework reference — not legal advice]
- Source: [URL]

## Operational Patterns

**[Operational Domain]**
- RTO/RPO (if applicable): [Values]
- {{CLOUD_PROVIDER}} Services: [Service composition]
- Cost Profile: [Low | Medium | High + cost driver]
- Automation: [What to automate vs manual decision points]
- Source: [URL]

## Reference Architectures

**[Architecture Name]**
- Context: [Workload type]
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|

- Key Decisions: [What to customize]
- Scaling Path: [Growth evolution]
- Source: [URL]

## Service Equivalence Map
[Cross-provider mapping table — only include if CLOUD_PROVIDER is "Multi-Cloud" or if comparison aids decision-making]

## Provider Differentiators
[Unique capabilities relevant to {{ARCHITECTURE_CONTEXT}}]

## Scenario Coverage

**Standard Case**: [Most common architecture for `{{ARCHITECTURE_CONTEXT}}`]
- Approach: [Pattern composition]
- Key Decisions: [What the architect must decide]

**Edge Case**: [Boundary scenario — scale limit, regulatory constraint, hybrid requirement]
- Approach: [How to handle with {{CLOUD_PROVIDER}} services]

**Anti-Pattern Case**: [What the architect must refuse or flag]
- Clarification: [What to ask before proceeding]
