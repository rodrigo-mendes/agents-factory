---
name: researching-technical-frameworks
description: "Researches technologies, frameworks, and SDKs to produce hallucination-proof research_[TECH]_v[VERSION].md documents. Use when starting technical research for a new skill, researching a version migration, or researching an SDK integration (e.g., Stripe Java SDK, Terraform AWS provider)."
argument-hint: "<tech> <version> (e.g. FastAPI 0.115)"
context: fork
agent: framework-researcher
disable-model-invocation: true
---

## Function
Produces hallucination-proof `research_[TECH]_v[VERSION].md` documents by enforcing version absolutism, source hierarchy, and three-tier guardrails for downstream skill authoring.

Transform vague technology requirements into **research_[TECH]_v[VERSION].md** documents that:
- Prevent hallucination through official documentation validation
- Enforce version-specific patterns
- Provide executable verification commands
- Supply sufficient detail for downstream skill authoring

## Input Variables

- `SYSTEM_OR_TECH_NAME`: specific name — e.g., "FastAPI", "Redis", "Next.js" (never generic like "database")
- `TARGET_VERSION`: semantic version — e.g., "0.100", "7.2", "14.0" (never "latest" or unspecified)
- `OFFICIAL_URL_IF_KNOWN`: optional — primary docs URL if known
- `INTEGRATION_PARTNERS_LIST`: comma-separated — e.g., "PostgreSQL, JWT, pytest"

## Quick Navigation

- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — Mandatory implementation patterns
- **[Ask First](./blueprints/ask-first-decisions.md)** — Architectural decisions requiring context
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — Anti-patterns with alternatives
- **[Integration Patterns](./blueprints/integration-patterns.md)** — SDK/library integration template
- **[Output Format Template](./blueprints/output-format-template.md)** — Full output document structure with all sections
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — Test cases: canonical path, edge cases, misuse, anti-pattern traps
- **[Research Execution Workflow](#research-execution-workflow)** — Phase-by-phase research process
- **[Verification Loop](#verification-loop)** — Validation commands and expected outputs
- **[External Resources](#external-resources)** — Official documentation links

---

## Version Context

**Applies to**: 
- All technology research across all versions
- Works with: FastAPI, Terraform, Kafka, PostgreSQL, Next.js, Redis, etc.

**Research Framework**: Version-Absolutism
- Only patterns for the specified target version are accepted
- Treat older/newer versions as separate research tasks
- Flag every source date; flag if >6 months old; reject if >12 months old (unless it documents the current stable version)

⚠️ **Agent Warning**: 
Do NOT conflate versions. Terraform 1.6 ≠ 1.7. PostgreSQL 14 ≠ 15.
Each version requires dedicated research output.

---

## ✅ Always Do

For complete patterns with examples, see [Always Do Patterns](./blueprints/always-do-patterns.md).

**Summary of mandatory patterns**:
- **Input Variable Validation** — Validate technology name, version, and research scope before starting
- **Source Hierarchy Enforcement** — Official docs > release notes > API references > community. Never invert
- **Version Tagging on Every Claim** — Every code sample and behavior must specify exact version

---

## ⚠️ Ask First

### Decision: Breadth vs. Depth of Research

**Decision Point**: How comprehensively should research cover the technology?

| Option | Scope | Time | Output Size | Best When |
|--------|-------|------|-------------|-----------|
| **Minimal** | Core patterns only | 1-2 hours | 5-10 page doc | Single, focused skill needed (e.g., "async routes") |
| **Standard** | Full API + integrations | 4-6 hours | 15-25 pages | Complete skill required (e.g., "FastAPI complete") |
| **Comprehensive** | + Edge cases, 3.x migration | 8-12 hours | 30-50 pages | Framework change/version jump (e.g., FastAPI v0.99→v0.100) |

**Agent Behavior**:
"Before researching, ask:
'What is the primary goal? 
A) Single, focused skill on one pattern (Minimal)
B) Complete skill covering all patterns (Standard)
C) Comprehensive guide for framework migration (Comprehensive)'"

**Decision Factors**:
- Skill deadline
- Complexity of technology
- Number of integration partners
- Whether this is migration research

**Source**: [Ask First Decisions — Decision 1](./blueprints/ask-first-decisions.md)

### Decision: Cloud Provider for Terraform Research

**Decision Point**: Which cloud provider should Terraform research target?

| Option | Ecosystem | Complexity | Provider | Maturity |
|--------|-----------|-----------|----------|----------|
| **AWS** | Largest (200+ resources) | High | hashicorp/aws | Most mature |
| **Google Cloud** | Medium (100+ resources) | Medium | hashicorp/google | Stable |
| **Azure** | Medium (120+ resources) | Medium | hashicorp/azurerm | Stable |
| **Multi-Cloud** | All above + cross-cloud patterns | Very high | All 3 providers | Complex state management |

**Agent Behavior**:
"For Terraform research, ask:
'Which cloud provider? AWS (most complete documentation), Google Cloud, Azure, or multi-cloud patterns?'"

**Decision Factors**:
- Organization's cloud strategy
- Documentation availability
- Team expertise
- Multi-region/multi-account requirements

**Source**: [Terraform Registry Providers](https://registry.terraform.io/browse/providers)

---

## 🚫 Never Do

For complete anti-patterns with examples, see [Never Do Patterns](./blueprints/never-do-patterns.md).

**Summary of prohibited patterns**:
- **Generic Tech Names** — "React" without version is ambiguous. Always use "React 18.2.x"
- **Mixing Versions** — Never combine patterns from different major versions in one research document
- **Undated Sources** — Sources without dates cannot be validated for currency. Always include access date

---

## Research Execution Workflow

### Phase 1: Input Validation (5 mins)
```bash
# ✅ Agent validates all inputs present and specific
SYSTEM_OR_TECH_NAME=?        # Must be specific (e.g., "FastAPI")
TARGET_VERSION=?             # Must be semantic version (e.g., "0.100+")
OFFICIAL_URL_IF_KNOWN=?      # Optional but preferred
INTEGRATION_PARTNERS_LIST=?  # Comma-separated or empty
```

### Phase 2: Authority Mapping (10-15 mins)
```bash
# Identify primary documentation sources

## Generic Template (all technologies)
Primary:       [OFFICIAL_DOCS_URL]
Registry:      [PACKAGE_REGISTRY]   # pypi.org, registry.terraform.io, mvnrepository.com, etc.
GitHub:        [REPO_URL]
Release Notes: [RELEASE_NOTES_URL]

## Example: FastAPI v0.100
Primary: https://fastapi.tiangolo.com/
Registry: https://pypi.org/project/fastapi/
GitHub: https://github.com/tiangolo/fastapi/
Release Notes: https://fastapi.tiangolo.com/release-notes/
Changelog: https://github.com/tiangolo/fastapi/releases/tag/0.100.0

## Example: Terraform AWS Provider v5.x
Primary: https://registry.terraform.io/providers/hashicorp/aws/latest
Official Repo: https://github.com/hashicorp/terraform-provider-aws
Blog: https://www.hashicorp.com/blog/
```

### Phase 3: Research Scope (2-4 hours)

**1. Authority & Versioning** — Locate primary official documentation; reject patterns not validated for `{{TARGET_VERSION}}`; identify release date and support/EOL timeline.

**2. Domain Complexity Assessment** — Assess before extracting patterns:

| Tier | Description | Always Do | Ask First | Never Do | Indicators |
|------|-------------|-----------|-----------|----------|------------|
| **Foundational** | Single-concern, wrapper | 3-4 | 2-3 | 2-3 | Single integration, limited config surface |
| **Standard** | Multi-concern, moderate config | 5-6 | 3-4 | 4-5 | Multiple integrations, security considerations |
| **Complex** | Security-critical, multi-layer | 7-9 | 4-6 | 5-7 | Auth, encryption, multi-service, compliance |

Quality rule: let domain complexity drive the count. Never pad or cap artificially.

**3. Three-Tier Operational Guardrails**

✅ **Always Do** (mandatory patterns — security configs, lifecycle, type safety):
```
Pattern: [Name]
Why: [Official reason]
Code: [Minimal example]
Source: [Dated link]
```

⚠️ **Ask First** (architectural crossroads — multiple valid approaches exist):
```
Decision: [What to choose]
Options: [A, B, C]
Tradeoffs: [Each optimizes/sacrifices what]
When: [Decision factors]
Source: [Dated link]
```

🚫 **Never Do** (forbidden patterns — deprecated methods, CVEs, data loss patterns):
```
Anti-Pattern: [What NOT to do]
Why: [Security/stability reason]
❌ Wrong: [Bad code or concrete artifact example]
✅ Correct: [Right code or concrete artifact example]
Impact: [What breaks]
Source: [Dated link]
```
> Every Never Do **must** include a side-by-side ❌/✅ example. For non-code domains use concrete artifact examples (wrong-source vs correct-source) — not prose only.

**4. Migration Considerations** — Breaking changes from previous version, upgrade path with exact commands, compatibility matrix, deprecation warnings.

**5. Ecosystem Interoperability** — For each `{{INTEGRATION_PARTNERS_LIST}}` item:
```
Integration: [System ↔ Partner]
Approach: [Library/pattern]
Install: [Commands]
Example: [Working code]
Versions: [Compatibility]
Issues: [Gotchas]
Source: [Dated link]
```

**6. Executable Verification** — All command blocks marked `# Representative — adapt to your environment`:
```bash
# Representative — adapt to your environment
# Project Init:  [command with flags]
# Validation:    [lint/type-check command]
# Testing:       [run tests + coverage]
# Health Check:  [start service + health endpoint + logs]
# Expected: [success output or criteria]
```

**7. Isolation & Mocking**:
```
Framework: [Name + version]
Mocking: [Library/pattern]
Example: [Test mocking external dependency]
Guarantee: [Test independence method]
Source: [Dated link]
```

**8. Production Considerations** — Scalability boundaries, gotchas at scale, monitoring metrics, security hardening checklist.

### Phase 4: Source Documentation (30-45 mins)
```markdown
## Source Bibliography

### Primary Sources
- [Official Docs](URL) - Published: DATE
- [Release Notes](URL) - Published: DATE
- [GitHub Repo](URL) - Main branch: DATE

### Validation Sources
- [Stack Overflow - [fastapi] + v0.100](URL)
- [GitHub Issues - fastapi/fastapi](URL)

### All Deep-Links (Organized by Section)
[Complete list with dates]
```

### Phase 5: Quality Validation (15 mins)
```bash
# ✅ Before finalizing research document:

[ ] All code examples tested/verified?
[ ] Every claim links to official source?
[ ] Sources dated (flagged if >6 months; rejected if >12 months, unless documenting current stable)?
[ ] Version mentioned 5+ times throughout?
[ ] Anti-patterns include correct alternatives?
[ ] CLI commands include expected output?
[ ] No generic/vague language?
[ ] Follows researching-technical-frameworks/SKILL.md structure?
```

---

## Output Format

Full document structure, section order, field definitions, Completion Checklist, and Research Gaps format are in **[Output Format Template](./blueprints/output-format-template.md)**.

Save as `research_{{SYSTEM_OR_TECH_NAME}}_v{{TARGET_VERSION}}.md`.

---

## Output Priorities

1. Security vulnerabilities & anti-patterns
2. Mandatory patterns
3. Version-specific pitfalls
4. Performance optimization
5. Advanced patterns

---

## Integration Patterns

When researching SDKs or libraries that integrate with external services, capture these generic concerns regardless of technology:

- **Auth clients** — how credentials are injected (env var, secret manager, SDK config)
- **Retries** — built-in retry policy vs. manual; which errors are retryable
- **Webhook handling** — signature verification, idempotency key, event ordering
- **Idempotency** — whether the API enforces it and how to implement it from the client side

For the full technology-agnostic template, version-pinning rules (semver/date/channel), and a language-neutral skeleton, see [Integration Patterns Blueprint](./blueprints/integration-patterns.md).

---

## Verification Loop

### Self-Validation Commands

```bash
# 1. Verify markdown structure
grep -E "^### ✅|^### ⚠️|^### 🚫" research_[TECH]_v[VERSION].md
# Exit code: 0 (match found) | 1 (no match)
# Expected: All three tiers present

# 2. Check version mentions
grep -i "version" research_[TECH]_v[VERSION].md | wc -l
# Exit code: 0 (match found) | 1 (no match)
# Expected: 5+ mentions throughout document

# 3. Validate source links (sample)
grep -E "http" research_[TECH]_v[VERSION].md | head -5
# Exit code: 0 (match found) | 1 (no match)
# Expected: All URLs return 200 (test 3 random URLs)

# 4. Check code block formatting
grep -c '```' research_[TECH]_v[VERSION].md
# Exit code: 0 (match found) | 1 (no match)
# Expected: Even number (every code block closed)

# 5. Verify anti-pattern alternatives
grep -c "# ✅\|# DO" research_[TECH]_v[VERSION].md
# Exit code: 0 (match found) | 1 (no match)
# Expected: Same count as "# 🚫\|# DON'T"

# 6. Confirm mandatory output sections are present
grep -E "^## (Mandatory_Patterns|Conditional_Patterns|Forbidden_Patterns|Version_Context|Source_Bibliography)" \
  research_*.md
# Expected: all section headers appear in the research output file

# 7. Confirm every Never-Do entry has a correct alternative
grep -c "✅ Correct" research_*.md
# Expected: count equals or exceeds the number of anti-pattern entries
```

### Manual Validation Checklist

- [ ] **Input Variables**: All 4 required inputs provided and specific?
- [ ] **Version Lock**: Target version mentioned in 5+ places?
- [ ] **Three Tiers**: ✅ + ⚠️ + 🚫 all present with content?
- [ ] **Code Examples**: 3+ working, commented, version-tagged?
- [ ] **Source Dates**: Every URL includes publication date?
- [ ] **No Hallucinations**: Every claim traces to official source?
- [ ] **Tested CLI**: All commands marked as tested/verified?
- [ ] **Migration Guide**: Breaking changes documented?
- [ ] **Anti-patterns**: All have correct alternatives?
- [ ] **Ready for Skill Author**: Document >15 pages with actionable detail?

---

## Common Mistakes vs. Correct Usage

| Aspect | ❌ Incorrect | ✅ Correct |
|--------|-------------|-----------|
| **Input** | "I need a database skill" | "I need PostgreSQL v15 with async using SQLAlchemy v2.0" |
| **Versioning** | "FastAPI docs say..." (no date) | "FastAPI v0.100 (Oct 2023) uses lifespan context..." |
| **Sources** | "I found on Stack Overflow..." | "Stack Overflow [fastapi] tag filtered for v0.100+ answers (Jan 2024)" |
| **Anti-patterns** | "Don't use sync" | Side-by-side: `# 🚫 time.sleep()` vs `# ✅ await asyncio.sleep()` |

---

## Quick Reference

| Aspect | Pattern |
|--------|---------|
| **Output naming** | `research_<Tech>_<Context>_v<X.Y>.md` |
| **Source priority** | Official docs > GitHub releases > API reference > Stack Overflow (filtered) |
| **Version absolutism** | Target version mentioned 5+ times: title, context, code comments, anti-patterns, final warning |
| **Research depth** | Scope-dependent: Minimal 5-10 / Standard 15-25 / Comprehensive 30-50 — confirm via Ask First Decision 1 |
| **Code examples** | 3+ working, commented, version-tagged |
| **Every claim** | Must trace to official source with publication date |

## External Resources

### Related Commands
- [Technical Framework Researcher — Terraform](../technical-framework-researcher-terraform/SKILL.md) — IaC variant for Terraform/provider research

### Skill Authoring
- [Skill Author Specialist](../skill-creator/SKILL.md) - Transforms research into skills
- [SKILL Template](../../templates/skills/TEMPLATE.SKILL.md) - Structure reference


### Official Documentation References
- [Python Official Docs](https://docs.python.org) - Python stdlib
- [Terraform Registry](https://registry.terraform.io) - Terraform providers
- [FastAPI Docs](https://fastapi.tiangolo.com) - FastAPI framework
- [PostgreSQL Docs](https://www.postgresql.org/docs) - PostgreSQL
- [AWS Documentation](https://docs.aws.amazon.com) - AWS services

---

## Agent Operation Notes

### High Confidence (Execute without asking)
- Input validation (reject generic inputs)
- Source date checking (flag if >6 months; reject if >12 months, unless documenting current stable version)
- Version tagging on every claim
- Extraction of mandatory/conditional/forbidden patterns
- Structure validation (3 tiers, metadata, bibliography)

### Medium Confidence (Validate with user)
- Research breadth (minimal vs standard vs comprehensive)
- Cloud provider selection (for Terraform)
- Integration partner depth
- Whether to include migration guide

### Low Confidence (Must ask user)
- Emerging/beta technologies (limited official docs)
- Rare edge cases (custom integrations)
- End-of-life technology versions (finding reliable sources)

### Edge Cases (When to pause)
- User requests research for version with <30 days of release (incomplete docs)
- Technology has active CVE/security incident

### Emergency Stop
- Halt if sources are all community/opinion (no official docs exist)
- Halt if version is EOL and replacement version exists

---

## Next Steps After This Skill

1. **Complete Research**: This skill outputs `research_[TECH]_v[VERSION].md`
2. **Author Skill**: Pass output to [Skill Author Specialist](../skill-creator/SKILL.md)
