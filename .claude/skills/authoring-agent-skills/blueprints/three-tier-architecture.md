## File Structure & Nomenclature

## Contents
1. [File Structure & Nomenclature](#file-structure--nomenclature)
2. [Three-Tier Architecture (Framework Core)](#three-tier-architecture-framework-core)
   - [Tier 1: Always Do (Mandatory Patterns)](#-tier-1-always-do-mandatory-patterns)
   - [Tier 2: Ask First (Architectural Crossroads)](#%EF%B8%8F-tier-2-ask-first-architectural-crossroads)
   - [Tier 3: Never Do (Anti-Patterns)](#-tier-3-never-do-anti-patterns)

### ✅ Always Do
**Exact Location**:
```
.claude/skills/<skill-name>/SKILL.md
```

**Naming Rules** (from [official Claude docs](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#naming-conventions)):
- `name`: max 64 characters, lowercase letters/numbers/hyphens only, no XML tags, no reserved words (`anthropic`, `claude`)
- Folder name = `name` field in YAML = `lowercase-kebab-case`
- Filename EXACTLY: `SKILL.md` (case-sensitive)
- **Prefer gerund form** (verb + -ing): `processing-pdfs`, `provisioning-oci-functions`
- Valid examples:
  - ✅ `.claude/skills/processing-pdfs/` → `name: processing-pdfs`
  - ✅ `.claude/skills/provisioning-oci-functions/` → `name: provisioning-oci-functions`
  - ✅ `.claude/skills/analyzing-spreadsheets/` → `name: analyzing-spreadsheets`

**YAML Description Pattern** (from [official Claude docs](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#writing-effective-descriptions)):
```yaml
---
name: skill-name
description: "[Action verb] [what] with [TECH] [VERSION]. Use when [trigger context]."
---
```
- `description`: max 1536 characters, non-empty, no XML tags
- Write in **third person** — not "I can help" or "You can use"
- Include BOTH what the skill does AND when to use it

**Examples of correct descriptions**:
- ✅ "Builds async REST APIs with FastAPI v0.100+. Use when creating high-performance Python APIs."
- ✅ "Provisions OCI Functions resources with Terraform OCI Provider v6.x+. Use when provisioning Functions infrastructure."
- ✅ "Analyzes Excel spreadsheets and generates charts. Use when analyzing .xlsx files or tabular data."

**INCORRECT examples**:
- ❌ "Helps with FastAPI" (vague, no trigger)
- ❌ "I can help you process Excel files" (first person)
- ❌ "Useful for building APIs" (no specific technology/version)

### ⚠️ Ask First

- **Inline code examples vs. `blueprints/`**: When a pattern's code exceeds ~30 lines or has multiple variations, ask whether to keep it inline or delegate to a blueprint file. Inline keeps context local; blueprints reduce SKILL.md length and enable progressive disclosure.
- **Auto-invocable vs. deliberate-action command**: When authoring a command skill, ask whether it should be auto-invocable (knowledge skill — omit `disable-model-invocation`) or deliberate-action (researcher/generator/validator — add `context: fork`, `agent:`, `disable-model-invocation: true`). Wrong choice either hides the skill from auto-selection or exposes it at unintended cost.

### 🚫 Never Do
- ❌ Mixed case in folder names: `FastAPI-Async`
- ❌ Different names between folder and YAML
- ❌ Generic descriptions without trigger phrase
- ❌ Absolute paths in links
- ❌ Reserved words in name: `anthropic-helper`, `claude-tools`

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