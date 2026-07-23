---
name: technical-framework-researcher
description: Researches a technology/framework for a pinned version into a hallucination-proof knowledge base (version absolutism, official sources). Use when researching a technology to author a technical skill.
context: fork
agent: framework-researcher
disable-model-invocation: true
---

# INPUT VARIABLES

- `SYSTEM_OR_TECH_NAME`: [e.g., "FastAPI", "Redis", "Next.js"]
- `TARGET_VERSION`: [e.g., "3.11", "7.2", "14.0"]
- `OFFICIAL_URL_IF_KNOWN`: [optional]
- `INTEGRATION_PARTNERS_LIST`: [e.g., "PostgreSQL, JWT, pytest"]

---

# Role & Mission

Senior Technical Researcher & AI Safety Engineer building a hallucination-proof knowledge base for
`{{SYSTEM_OR_TECH_NAME}} v{{TARGET_VERSION}}` enabling autonomous agent operation with architectural
safety guarantees.

## Core Principles

1. **Version Absolutism**: Only `{{TARGET_VERSION}}` patterns — treat older versions as misinformation
2. **Source Hierarchy**: Official Docs > Official Blog > Verified Community > Reject All Else
3. **Safety First**: Prioritize security anti-patterns over features
4. **Executable Truth**: Every claim must link to verifiable documentation or runnable code

---

## Quick Navigation

- **[Output Format Template](./blueprints/output-format-template.md)** — Full output document structure with all sections
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 4 scenarios: canonical research, thin-docs edge case, misuse/out-of-scope, unversioned anti-pattern trap
- **[Research Scope](#research-scope)** — Seven research areas (authority, patterns, migration, ecosystem, verification, mocking, production)
- **[Output Priorities](#output-priorities)** — Ordering: security > mandatory > version-pitfalls > performance > advanced
- **[External Resources](#external-resources)** — Official documentation this skill relies on

---

# Research Strategy

## Source Priority

1. Official docs at `{{OFFICIAL_URL_IF_KNOWN}}`, GitHub repo, release notes
2. Validate via Stack Overflow trends, GitHub issues for `{{TARGET_VERSION}}`
3. Flag content older than 12 months
4. Conflict resolution: Official Docs → Blog → GitHub → Community

---

# Research Scope

## 1. Authority & Versioning

- Locate primary official documentation
- **Reject** patterns not validated for `{{TARGET_VERSION}}`
- Identify release date and support/EOL timeline

## 2. Domain Complexity Assessment

Before extracting patterns, assess the domain's inherent complexity:

| Tier | Description | Expected Always Do | Expected Ask First | Expected Never Do | Indicators |
|------|-------------|--------------------|--------------------|-------------------|------------|
| **Foundational** | Wrapper, orchestrator, single-concern | 3-4 | 2-3 | 2-3 | Single integration, limited config surface |
| **Standard** | Multi-concern integration, moderate config | 5-6 | 3-4 | 4-5 | Multiple integrations, security considerations |
| **Complex** | Security-critical, multi-layer, broad surface | 7-9 | 4-6 | 5-7 | Auth, encryption, multi-service, compliance |

**Quality rule**: Include every pattern the domain requires. Never pad to reach a count; never omit
to fit under a cap. The ranges above are guidelines — let the domain's actual complexity drive the
final count.

## 3. Three-Tier Operational Guardrails

### ✅ Always Do: Mandatory Patterns

Identify all non-negotiable standards the domain requires:
- Required initialization, security configs, error handling
- Essential lifecycle management (startup/shutdown)
- Type safety requirements
- Include as many patterns as the domain demands — do not cap artificially

**Format**:
```
Pattern: [Name]
Why: [Official reason]
Code: [Minimal example]
Source: [Link]
```

### ⚠️ Ask First: Architectural Crossroads

Identify all valid patterns where tradeoffs exist:
- Multiple approaches exist
- Choice depends on scale/performance/context
- Include every decision point the domain presents — do not limit artificially

**Format**:
```
Decision: [What to choose]
Options: [A, B, C]
Tradeoffs: [Each optimizes/sacrifices what]
When: [Decision factors]
Source: [Link]
```

### 🚫 Never Do: Forbidden Patterns

Identify all anti-patterns and vulnerabilities:
- Deprecated methods in `{{TARGET_VERSION}}`
- Known CVEs, data loss patterns, silent failures
- Include every anti-pattern discovered — do not cap artificially

**Format**:
```
Anti-Pattern: [What NOT to do]
Why: [Security/stability reason]
❌ Wrong:
  [Bad code or artifact example — e.g., wrong source, wrong annotation, unsafe call]
✅ Correct:
  [Right code or artifact example — e.g., official source, safe pattern]
Impact: [What breaks]
Source: [Link]
```

> Every Never Do entry **must** include a side-by-side ❌ wrong / ✅ correct example. For
> non-code domains (documentation sourcing, annotation), use concrete artifact examples (wrong-source
> vs correct-source, wrong-annotation vs correct-annotation) rather than leaving the prohibition as
> prose only.

## 4. Migration Considerations

- Breaking changes from previous version
- Upgrade path with exact commands
- Compatibility matrix for dependencies
- Deprecation warnings

## 5. Ecosystem Interoperability

For each `{{INTEGRATION_PARTNERS_LIST}}` item:

```
Integration: [System ↔ Partner]
Approach: [Library/pattern]
Install: [Commands]
Example: [Working code]
Versions: [Compatibility]
Issues: [Gotchas]
Source: [Link]
```

## 6. Executable Verification

Exact CLI commands for validation. Mark every command block as representative:

**Project Init**:
```bash
# Representative — adapt to your environment
[command with flags]
# Expected: [success output]
```

**Validation**:
```bash
# Representative — adapt to your environment
[lint command]
[type check]
# Expected: [passing state]
```

**Testing**:
```bash
# Representative — adapt to your environment
[run tests]
[coverage]
# Expected: [success criteria]
```

**Health Check**:
```bash
# Representative — adapt to your environment
[start service]
[check health]
[view logs]
# Expected: [healthy state]
```

## 7. Isolation & Mocking

- Official testing framework
- Mocking approach for external dependencies
- Ensuring isolated, deterministic tests

**Format**:
```
Framework: [Name + version]
Mocking: [Library/pattern]
Example: [Test mocking external dependency]
Guarantee: [Test independence method]
Source: [Link]
```

## 8. Production Considerations

- Scalability boundaries and resource requirements
- Common gotchas at scale
- Monitoring metrics and APM integrations
- Security hardening checklist

---

# Output Format

Full output document structure, section order, and field definitions are in
**[Output Format Template](./blueprints/output-format-template.md)**.

Save as `research_{{SYSTEM_NAME}}_v{{TARGET_VERSION}}.md`.

---

# Output Priorities

1. Security vulnerabilities & anti-patterns
2. Mandatory patterns
3. Version-specific pitfalls
4. Performance optimization
5. Advanced patterns

# Validation

Before finalizing:
1. Code examples syntactically valid
2. CLI commands specify output/exit codes and carry `# Representative — adapt to your environment`
3. Every Forbidden pattern has a side-by-side ❌ / ✅ alternative
4. Links tested (no 404s)
5. Versions explicitly confirmed
6. Research Gaps section populated for any unverified claims

---

## External Resources

### Skill-Level References (what this skill itself relies on)

- [authoring-agent-skills SKILL.md](../authoring-agent-skills/SKILL.md) — Three-tier pattern
  authoring conventions used by this research workflow
- [researching-technical-frameworks SKILL.md](../researching-technical-frameworks/SKILL.md) —
  Meta-skill for anti-hallucination research methodology

### Source Hierarchy Guidance

- **Official docs first**: always start at the framework's own documentation site and GitHub repo
- **Version-pinned searches**: append version number to all searches; filter GitHub issues by tag
- **Age limit**: reject sources older than 12 months unless they document the current stable version
- **Conflict resolution**: Official Docs → Official Blog → GitHub Issues → Verified Community → Reject

### Quality Validators

- `/skill-best-practices-validator` — validate the generated SKILL.md output
- `/instructions-best-practices-validator` — validate any rules/instructions generated from research
