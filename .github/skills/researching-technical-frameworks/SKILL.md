---
name: researching-technical-frameworks
description: Researches technologies and frameworks to create comprehensive, hallucination-proof knowledge bases enabling skill authoring. Use when starting technical research for a new skill.
---

## Core Mission
Transform vague technology requirements into **research_[TECH]_v[VERSION].md** documents that:
- Prevent hallucination through official documentation validation
- Enforce version-specific patterns
- Provide executable verification commands
- Supply sufficient detail for downstream skill authoring

## Quick Navigation

- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — Mandatory implementation patterns
- **[Ask First](#ask-first)** — Architectural decisions requiring context
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — Anti-patterns with alternatives
- **[Research Execution Workflow](#research-execution-workflow)** — Phase-by-phase research process
- **[Verification Loop](#verification-loop)** — Validation commands and expected outputs
- **[External Resources](#external-resources)** — Official documentation links

---

## Version Context

**Applies to**: 
- All technology research across all versions
- Works with: FastAPI, Terraform, Kafka, PostgreSQL, Next.js, Redis, etc.

**Research Framework**: Version-Absolutism
- Only {{TARGET_VERSION}} patterns accepted
- Treat older/newer versions as separate research tasks
- Flag every source date; reject content >12 months old

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
- **Async Context Manager** — Use correct async patterns for the target framework version

---

## ⚠️ Ask First

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

**Source**: [Research Scope Planning](../../prompts/technical-framework-researcher.prompt.md)

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

## FastAPI v0.100
Primary: https://fastapi.tiangolo.com/
Registry: https://pypi.org/project/fastapi/
GitHub: https://github.com/tiangolo/fastapi/
Release Notes: https://fastapi.tiangolo.com/release-notes/
Changelog: https://github.com/tiangolo/fastapi/releases/tag/0.100.0

## Terraform AWS Provider v5.x
Primary: https://registry.terraform.io/providers/hashicorp/aws/latest
Official Repo: https://github.com/hashicorp/terraform-provider-aws
Blog: https://www.hashicorp.com/blog/
```

### Phase 3: Deep Pattern Extraction (2-4 hours)
```
For each section of the Technical Framework Researcher prompt:

1. Authority & Versioning
   → Confirm release date, support status, EOL timeline

2. Three-Tier Guardrails
   → Extract mandatory patterns (count driven by domain complexity — see tiers below)
   → Extract conditional patterns with tradeoff matrices
   → Extract anti-patterns with corrected code
   
   Domain Complexity Tiers (guides expected pattern counts):
   - Foundational (single-concern): ~3-4 always / 2-3 ask-first / 2-3 never
   - Standard (multi-concern): ~5-6 always / 3-4 ask-first / 4-5 never
   - Complex (security-critical): ~7-9 always / 4-6 ask-first / 5-7 never
   Quality rule: Include every pattern the domain requires. Never pad or cap artificially.

3. Migration Considerations
   → Document breaking changes
   → Create step-by-step upgrade path

4. Ecosystem Interoperability
   → For each INTEGRATION_PARTNERS_LIST item:
      * Create installation instructions
      * Working integration example
      * Known gotchas

5. Executable Verification
   → Test every CLI command locally
   → Document expected output
   → Note common errors and fixes

6. Testing / Mocking
   → Official test framework
   → Mocking patterns for external deps
   → Example test with isolation

7. Production Considerations
   → Performance boundaries
   → Scalability limits
   → Monitoring checklist
   → Security hardening
```

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
[ ] Sources dated (none >12 months old)?
[ ] Version mentioned 5+ times throughout?
[ ] Anti-patterns include correct alternatives?
[ ] CLI commands include expected output?
[ ] No generic/vague language?
[ ] Follows researching-technical-frameworks.prompt.md structure?
```

---

## Output Format

### Standard Output Naming
```
research_[SYSTEM_NAME]_v[TARGET_VERSION].md

Examples:
- research_FastAPI_v0.100.md
- research_PostgreSQL_v15.md
- research_Terraform_AWS_v5.45.md
- research_Kafka_v3.5.md
```

### Mandatory Structure (from prompt template)

```markdown
---
Full_Name: [Official Name]
Target_Version: [Version]
Release_Date: [Date]
Support_Status: [Active/LTS/EOL]
Primary_Docs: [URL]
Official_Repo: [URL]
Research_Date: [Today]
Domain_Complexity: [Foundational/Standard/Complex]
---

# Executive Summary
[2-3 paragraphs]

# Architectural Guardrails

## ✅ Mandatory Patterns
[Patterns with code examples — count driven by domain complexity]

## ⚠️ Conditional Patterns
[Decisions with tradeoff matrices — count driven by domain complexity]

## 🚫 Forbidden Patterns
[Anti-patterns with correct alternatives — count driven by domain complexity]

# Migration Guide
[Breaking changes + upgrade steps]

# Implementation Blueprint
[Lifecycle code + integration examples]

# Quality Control
[Verification commands with expected outputs]

# Production Readiness
[Performance, scalability, monitoring, security]

# Source Bibliography
[Organized, dated links]

# Agent Operation Notes
[Confidence levels for skill authoring]
```

---

## Integration with Skill Authoring Pipeline

### Input to This Skill
```
User Request: 
"I need a Terraform skill for AWS RDS with PostgreSQL"

User Provides:
- CLOUD_PROVIDER: AWS
- SERVICE_NAME: RDS PostgreSQL
- TERRAFORM_VERSION: 1.7
- PROVIDER_VERSION: aws v5.x
- INTEGRATION_PARTNERS_LIST: VPC, Security Groups, Secrets Manager
```

### This Skill's Output
```
research_AWS_RDS_PostgreSQL_v5.45.md
├─ Metadata (versions, dates, support)
├─ Executive summary
├─ Mandatory patterns (Terraform block, provider, encryption)
├─ Conditional patterns (local state vs S3)
├─ Forbidden patterns (hardcoded credentials, public RDS)
├─ Integration examples (RDS ↔ VPC, RDS ↔ Secrets Manager)
├─ Verification commands (terraform validate, tfsec, etc.)
└─ Source bibliography (Registry docs, AWS docs, etc.)
```

### Input to Skill Author Specialist
```
research_AWS_RDS_PostgreSQL_v5.45.md
    ↓ (Skill Author transforms)
.github/skills/terraform-aws-rds/SKILL.md
    ↓ (Copilot uses)
@github create Terraform RDS setup following terraform-aws-rds skill
```

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
| **Research depth** | 20-30 pages covering all 3 tiers + integrations + verification |
| **Code examples** | 3+ working, commented, version-tagged |
| **Every claim** | Must trace to official source with publication date |

## External Resources

### Research Prompts
- [Technical Framework Researcher Prompt](../../prompts/technical-framework-researcher.prompt.md) - Generic research
- [Technical Framework Researcher Prompt - Terraform](../../prompts/technical-framework-researcher-terraform.prompt.md) - IaC research

### Skill Authoring
- [Skill Author Specialist](../authoring-agent-skills/SKILL.md) - Transforms research into skills
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
- Source date checking (flag >12 months old)
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
2. **Author Skill**: Pass output to [Skill Author Specialist](../authoring-agent-skills/SKILL.md)
