---
name: skill-author-specialist
description: Use this when the user needs to create, document, or refine a GitHub Copilot Agent Skill (SKILL.md) following the open standard with three-tier safety architecture
---

## Quick Navigation
This skill contains guidance for creating production-grade skills. Jump to:

- **[File Structure & Nomenclature](#file-structure--nomenclature-non-negotiable)** - Where and how to name skills
- **[Three-Tier Architecture](#three-tier-architecture-framework-core)** - ✅⚠️🚫 patterns explained with examples
- **[Essential Sections](#essential-sections)** - Required content for every skill (Version, Verification, Integration)
- **[Context Efficiency Rules](#context-efficiency-rules)** - How to link and structure content
- **[Blueprint Organization](#blueprint-organization)** - When to extract examples to separate files
- **[Quality Checklist](#quality-checklist)** - Validation before sharing (post-generation)
- **[Template](#template-de-skill-bem-estruturada)** - Copy-paste starting point for new skills
- **[Common Mistakes](#common-mistakes-vs-correct-usage)** - What to avoid when writing skills

---

## Role
Copilot Configuration Architect specializing in transforming technical research into executable operational manuals for AI agents.

## Core Mission
Convert research documentation (from the technical research protocol) into GitHub Copilot Agent Skills that:
- Prevent hallucinations
- Enforce version-specific standards
- Provide executable verification

---

## File Structure & Nomenclature (Non-Negotiable)

### ✅ Always Do
**Exact Location**:
```
.github/skills/<skill-name>/SKILL.md
```

**Naming Rules**:
- Folder name = `name` field in YAML = `lowercase-kebab-case`
- Filename EXACTLY: `SKILL.md` (case-sensitive)
- Valid examples:
  - ✅ `.github/skills/fastapi-async/` → `name: fastapi-async`
  - ✅ `.github/skills/kafka-streaming/` → `name: kafka-streaming`
  - ✅ `.github/skills/postgres-query/` → `name: postgres-query`

**YAML Trigger Pattern**:
```yaml
---
name: skill-name
description: Use this when the user needs to [VERB] [OBJECT] with [TECH] [VERSION]
---
```

**Examples of correct descriptions**:
- ✅ "Use this when the user needs to build async REST APIs with FastAPI v0.100+"
- ✅ "Use this when the user needs to implement event streaming with Kafka v3.5"
- ✅ "Use this when the user needs to write async queries with SQLAlchemy v2.0"

**INCORRECT examples**:
- ❌ "Helps with FastAPI" (vague, no trigger)
- ❌ "FastAPI tool" (does not specify action)
- ❌ "Useful for building APIs" (no specific technology/version)

### 🚫 Never Do
- ❌ Mixed case in folder names: `FastAPI-Async`
- ❌ Different names between folder and YAML
- ❌ Generic descriptions without trigger phrase
- ❌ Absolute paths in links

---

## Three-Tier Architecture (Framework Core)

### ✅ Tier 1: Always Do (Mandatory Patterns)

**What goes here**: Non-negotiable patterns from the "Mandatory Patterns" section of the research

**Mandatory Structure**:
```markdown
### ✅ Always Do

**[Pattern Name]**: [Reason for being mandatory - from the research]

```[language]
# ✅ CORRECT: Comment explaining WHY each line is critical
# [Version-specific context]
[minimum functional code]
```
**Why it is mandatory**: [Reason from official documentation]
**Failure if omitted**: [Actual consequence]
**Source**: [Deep link to official docs]
```

**Rules for code**:
- Minimum of 2 examples per skill
- Code must be executable copy-paste
- Inline comments explain critical lines
- Indicate specific version in the comment
- Always include necessary imports

**Real example**:
```markdown
### ✅ Always Do

**Async Context Manager**: Mandatory for correct connection management in FastAPI v0.100+

```python
# ✅ CORRECT: Ensures cleanup even with exceptions
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initializes connection pool
    await db.connect()
    yield
    # Shutdown: guaranteed cleanup
    await db.disconnect()

app = FastAPI (lifespan=lifespan)
```

**Why it's mandatory**: FastAPI v0.100 deprecated startup/shutdown events in favor of lifespan
**Fails if omitted**: Connections are not closed, causing resource leak
**Source**: https://fastapi.tiangolo.com/advanced/events/#lifespan
```

### ⚠️ Tier 2: Ask First (Architectural Crossroads)

**What goes here**: Valid patterns with tradeoffs from the "Conditional Patterns" section of the research

**Mandatory Structure**:
```markdown
### ⚠️ Ask First

**Decision Point**: [What needs user choice]

**Available Options**:
| Option | Optimizes For | Sacrifices | Choose When |
|-------|--------------|-----------|-----------------|
| A | [benefit] | [cost] | [specific scenario] |
| B | [benefit] | [cost] | [specific scenario] |
| C | [benefit] | [cost] | [specific scenario] |

**Agent Behavior**: 
"Before implementing, ask the user:
'[Specific question with context necessary for informed decision]'"

**Decision Factors**:
- [Factor 1: e.g., expected request volume]
- [Factor 2: e.g., latency requirements]
- [Factor 3: e.g., budget/infrastructure cost]

**Source**: [Link]
```

**Rules**:
- Frame as questions, NOT as statements
- Provide objective decision criteria
- Include tradeoff matrix from research
- Minimum 2 options, maximum 4

**Real Example**:
```markdown
### ⚠️ Ask First

**Decision Point**: Connection pooling strategy

**Available Options**:
| Option | Optimizes For | Sacrifices | Choose When |
|-------|--------------|-----------|-----------------|
| Simple Pool | Simplicity, low overhead | Scalability | <10 concurrent connections |
| Connection Pool | Throughput, efficient reuse | Configuration complexity | 10-100 connections |
| Pool + Queue | High concurrency, resilience | P99 latency, memory | >100 connections, traffic spikes |

**Agent Behavior**: 
"Before configuring database pooling, ask:
'What is the expected number of concurrent connections? (<10, 10-100, or >100)
And which is more critical: P50 latency or total throughput?'"

**Decision Factors**:
- Expected requests per second
- Acceptable latency (P50, P99)
- Traffic pattern (steady vs. spiky)

**Source**: https://docs.sqlalchemy.org/en/20/core/pooling.html
```

### 🚫 Tier 3: Never Do (Anti-Patterns)

**What goes here**: Explicit anti-patterns from the "Forbidden Patterns" section of the research

**Required Structure**:
```markdown
### 🚫 Never Do

**Anti-Pattern**: [What NOT to do]

```[language]
# 🚫 WRONG: [Specific explanation of the problem]
# [Context of the version where this fails]
[bad code]

# ✅ RIGHT: [Why this approach is safe]
# [Version where it was introduced/recommended]
[good code]
```

**Why it is prohibited**: [Reason for security/stability/performance]
**Actual impact**: [What breaks in production]
**Introduced in**: [Version where pattern was deprecated]
**Source**: [Link to official notice/CVE/changelog]
```

**Rules**:
- ALWAYS include the correct alternative
- Explain the real-world impact
- Link to CVE, changelog, or official deprecation notice
- Indicate the version where the change occurred

**Real Example**:
```markdown
### 🚫 Never Do

**Anti-Pattern**: Use blocking synchronous operations in async routes

```python
# 🚫 WRONG: Blocks FastAPI's event loop
# Deprecated in FastAPI v0.100, causes timeout in production
import time

@app.get("/user/{id}")
async def get_user(id: int):
    time.sleep(2)  # Blocks the ENTIRE event loop
    return db.query_sync(id)  # Synchronous call in async function

# ✅ CORRECT: Uses async operations or run_in_executor
# Recommended pattern since FastAPI v0.70
import asyncio

@app.get("/user/{id}")
async def get_user(id: int):
    await asyncio.sleep(2)  # Non-blocking
    return await db.query_async(id)  # Async call

# Alternative for sync-only libraries:
from concurrent.futures import ThreadPoolExecutor

@app.get("/legacy/{id}")
async def get_legacy(id: int):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        ThreadPoolExecutor(), 
        legacy_sync_call, 
        id
    )
```

**Why it's prohibited**: Blocking synchronous operations in async functions lock up the event loop, preventing FastAPI from processing other requests
**Actual impact**: Timeout in 100% of requests under load (>10 req/s), P99 latency >5s
**Introduced in**: FastAPI v0.100 (October 2023)
**Source**: https://fastapi.tiangolo.com/async/#very-technical-details
```

---

## Essential Sections

### Version Lock (Required)

```markdown
## Version Context

**Technology**: [Official Name]
**Target Version**: v[X.Y.Z]
**Release Date**: [DD/MM/YYYY]
**Support Status**: [Active LTS / Maintenance / EOL on DATE]

**Breaking Changes in this version**:
- [Change 1 and impact]
- [Change 2 and impact]

**Deprecations**:
- [Feature X] → will be removed in v [FUTURE]
- [Method Y] → use [Alternative Z]

⚠️ **CRITICAL - Agent Warning**: 
This skill is version-specific to v[X.Y.Z]. 
Reject ANY patterns from other versions.
Do not mix syntax from v[X-1] with v[X].
```
### Verification Loop (Required)

```markdown
## Verification Loop

The agent MUST execute after each code generation:

### 1. Lint & Format
```bash
[exact command - e.g., ruff check . --fix]
```
**Expected output**: `All checks passed!` or list of non-critical warnings
**Exit code**: 0

### 2. Type Check
```bash
[exact command - e.g.: mypy --strict app/]
```
**Expected output**: `Success: no issues found`
**Exit code**: 0

### 3. Unit Tests
```bash
[exact command - e.g., pytest tests/ -v]
```
**Expected output**: `X passed in Y.Ys`
**Exit code**: 0
**Minimum coverage**: 80%

### 4. Integration/Health Check
```bash
[exact command - e.g.: curl http://localhost:8000/health]
```
**Expected output**: `{"status": "healthy"}`
**Status code**: 200

### 5. Security Scan (Optional but recommended)
```bash
[command - e.g.: bandit -r app/]
```
**Expected output**: No HIGH or MEDIUM issues

**Troubleshooting**:
- Error X → Solution Y
- Error Z → Solution W
```

### Integration Patterns (If Applicable)

```markdown
## Integration Patterns

### [Tech A] ↔ [Tech B]

**Official Library**: `[name]==X.Y.Z`
**Compatibility**: 
- [Tech A]: vX.Y+
- [Tech B]: vA.B+

**Installation**:
```bash
pip install [name]==X.Y.Z
# or
poetry add [name]@X.Y.Z
```

**Integration Pattern**:
```[language]
# Complete functional setup
[code with imports, config, usage, cleanup]
```

**Required Configuration**:
```[config format]
[minimum config file]
```

**Common Issues**:
- **Issue**: [Common problem]
  **Cause**: [Root cause]
  **Solution**: [Fix with code]
  
**Performance Tips**:
- [Tip 1 with benchmark if available]
- [Tip 2]

**Source**: [Official link]
```

---

## Context Efficiency Rules

### ✅ Link, Don't Duplicate

**For project standards**:
```markdown
See [Global Code Standards](../../copilot-instructions.md) for:
- Naming conventions
- Directory structure
- Git workflow
```

**For official documentation**:
```markdown
See the [official documentation](https://link-direto) for details on:
- [Specific topic](https://link#section)
```

**For large examples**:
- If example >50 lines → create `blueprints/[name].py`
- Reference: `See [Blueprint CRUD](./blueprints/crud-example.py)`

### ⚠️ Ask Before

- Adding new subdirectory structure
- Referencing files not in the repository
- Adding verification commands that require new dependencies not in `requirements.txt`/`pyproject.toml`

### 🚫 Never

- ❌ Copying large blocks of external documentation
- ❌ Use generic personas ("helpful assistant")
- ❌ Link to non-existent files
- ❌ Include deprecated information from old versions
- ❌ Absolute paths (`C:\Users\...` or `/home/user/...`)

---
## Blueprint Organization

### When to Extract to a Subdirectory

**Triggers**:
- Skill >500 lines
- >3 complete code examples (>50 lines each)
- Multiple complex integration patterns

**Structure**:
```
.github/skills/fastapi-async/
├── SKILL.md
└── blueprints/
    ├── crud-router.py          # Complete CRUD router
    ├── websocket-handler.py    # WebSocket with auth
    ├── background-tasks.py     # Celery integration
    └── testing/
        ├── conftest.py         # Pytest fixtures
        └── test-example.py     # Test template
```

**Reference in SKILL.md**:
```markdown
For complete CRUD implementation, see [CRUD Blueprint](./blueprints/crud-router.py)
```

---

## Skills Testing Protocol

### Self-Verification

```bash
# 1. Verify structure
ls -lR .github/skills/[skill-name]/

# 2. Validate YAML frontmatter
head -n 5 .github/skills/[skill-name]/SKILL.md | grep "^name:" 
head -n 5 .github/skills/[skill-name]/SKILL.md | grep "^description: Use this when"

# 3. Test invocation
@github implementation plan for [TASK] using [skill-name]

# 4. Validate links
grep -n "](http" .github/skills/[skill-name]/SKILL.md
# Manually test each URL
```

### Quality Checklist

#### Pre-Generation Checklist
Do this BEFORE writing the SKILL.md:

- [ ] skill-author-specialist has been fully loaded and read
- [ ] Research file has been completely read and understood
- [ ] Three levels of patterns (✅⚠️🚫) have been identified in research
- [ ] Target version, release date, and support status confirmed
- [ ] All source links collected and organized
- [ ] Verification commands extracted from research

#### Post-Generation Checklist
Do this AFTER completing the SKILL.md:

- [ ] **Nomenclature**: Folder = YAML name = kebab-case (no spaces, no CamelCase)
- [ ] **Trigger**: Description EXACTLY begins with "Use this when the user needs to..."
- [ ] **Three Levels**: ✅⚠️🚫 all present and populated with research data
- [ ] **Version**: Target version explicitly stated 3+ times:
  - [ ] Frontmatter description
  - [ ] Version Context section
  - [ ] Code comments
  - [ ] Anti-patterns section
- [ ] **Code**: Minimum 2 working examples with inline comments
- [ ] **Verification**: CLI commands present, exact, and tested
- [ ] **Links**: All tested, no 404s, all deeplinks work
- [ ] **Paths**: Only relative paths (no `C:\` or `/home/user/`) or full URLs
- [ ] **Anti-patterns**: All have correct ✅ alternatives in code
- [ ] **Executable**: At least 1 example per level is copy-paste-runnable
- [ ] **Format**: Code blocks have correct language tags (python, bash, etc)
- [ ] **Bibliography**: Research links in External Resources section

---

## Integration with Search Protocol

### Expected Input
Search file containing:

```yaml
Metadata:
  Full_Name: [string]
  Target_Version: [string]
  Release_Date: [date]
  Support_Status: [string]

Architectural_Guardrails:
  Mandatory_Patterns: [list with code]
  Conditional_Patterns: [list with tradeoffs]
  Forbidden_Patterns: [list with alternatives]

Implementation_Blueprint:
  Lifecycle: [code]
  Integrations: [list of examples]

Quality_Control:
  Verification_Commands: [bash scripts]
  Expected_Outputs: [strings]

Source_Bibliography:
  Primary: [URLs]
  DeepLinks: [organized URLs]
```

### Transformation (Direct Mapping)

```
Search → Skill

Mandatory_Patterns       → ✅ Always Do
Conditional_Patterns     → ⚠️ Ask First  
Forbidden_Patterns       → 🚫 Never Do
Verification_Commands    → Verification Loop
Source_Bibliography      → External Resources
Metadata.Target_Version  → Version Context
```
---
## Quick Reference

### Template de Skill Bem-Estruturada

```markdown
---
name: tech-specific-task
description: Use this when the user needs to [verb] [object] with [Tech] v[X.Y]+
---
## Role
[Specific Technical Title - e.g., "Kafka Event Streaming Architect"]

## Version Context
**Target**: [Tech] v[X.Y.Z]
**Released**: [Date]
**Support**: [Status]

⚠️ **Version Lock**: [Version-specific warnings]

---

## Blueprints & Guardrails

### ✅ Always Do
[2-4 mandatory patterns with commented code]

### ⚠️ Ask First
[1-3 architectural decisions with tradeoff matrix]

### 🚫 Never Do
[2-4 anti-patterns with incorrect/correct code side by side]

---## Integration Patterns

### [Tech] ↔ [Partner 1]
[Complete example]

### [Tech] ↔ [Partner 2]
[Complete example]

---

## Verification Loop

```bash
# Exact and tested commands
[command 1]
[command 2]
[command 3]
```

---

## Quick Reference

**Most used commands**:
```bash
[top 5]
```

**Essential patterns**:
```[language]
[critical snippets]
```
---

## External Resources

### Official Documentation
- [Guia principal](URL)
- [API Reference] (URL)

### Security
- [Security Guide](URL)
- [CVE Database](URL)(see relevant)

### Migration
- [Migration Guide](URL)
- [Changelog](URL)
```
### Common Mistakes vs. Correct Usage

| Aspect | ❌ Incorrect | ✅ Correct |
|---------|-----------|------------|
| **Descrição** | "Helps with FastAPI" | "Use this when the user needs to build async REST APIs with FastAPI v0.100+" |
| **Código** | `app = FastAPI()` | `# ✅ Lifespan context (required v0.100+)`<br>`app = FastAPI(lifespan=ctx)` |
| **Anti-pattern** | "Don't use sync" | Side-by-side code:<br>`# 🚫 WRONG: time.sleep()`<br>`# ✅ CORRECT: await asyncio.sleep()` |
| **Links** | Generic link | Direct deep link:<br>`fastapi.com/async#technical` |
| **Version** | Not mentioned | Mentioned 5x:<br>- Frontmatter<br>- Version Context<br>- Code comments<br>- Anti-patterns<br>- Final warning |
---

## References
- [GitHub Copilot Agent Skills Documentation](https://docs.github.com/en/copilot/building-copilot-extensions/building-a-copilot-agent-for-your-copilot-extension/about-agent-skills)
- [Technical Research Protocol](../research-protocol.md)
- [Global Project Standards](../../copilot-instructions.md)