## ✅ Always Do

### Pattern: Input Variable Validation

**Validate all INPUT VARIABLES before research begins**

```python
# ✅ HIGH CONFIDENCE: Always validate inputs first

INPUT_REQUIREMENTS = {
    "SYSTEM_OR_TECH_NAME": {
        "required": True,
        "valid_examples": ["FastAPI", "PostgreSQL", "Terraform", "Redis"],
        "invalid": ["framework", "database", "cool system"],
    },
    "TARGET_VERSION": {
        "required": True,
        "format": "semantic versioning or release date",
        "invalid": ["latest", "newest", "current"],
    },
    "OFFICIAL_URL_IF_KNOWN": {
        "required": False,
        "valid_examples": [
            "https://docs.python.org",
            "https://registry.terraform.io",
        ],
        "invalid_if": ["404", "non-official domain"],
    },
    "INTEGRATION_PARTNERS_LIST": {
        "required": False,
        "format": "comma-separated list",
        "invalid": ["all integrations", "everything"],
    },
}

def validate_inputs(inputs):
    """
    Validates that user provided specific, versionable inputs.
    Rejects generic terms that would produce hallucinations.
    """
    if not inputs.get("SYSTEM_OR_TECH_NAME"):
        raise ValueError("❌ SYSTEM_OR_TECH_NAME is required (e.g., 'FastAPI', not 'framework')")
    
    if not inputs.get("TARGET_VERSION"):
        raise ValueError("❌ TARGET_VERSION is required (e.g., '0.100+', not 'latest')")
    
    # Reject generic patterns
    generic_terms = ["tool", "framework", "framework", "system", "lib"]
    for term in generic_terms:
        if term in inputs["SYSTEM_OR_TECH_NAME"].lower():
            raise ValueError(
                f"❌ '{inputs['SYSTEM_OR_TECH_NAME']}' is too generic. "
                f"Be specific (e.g., 'FastAPI', 'PostgreSQL')"
            )
    
    return True
```

**Why mandatory**: 
Generic inputs ("framework", "latest") lead to hallucinations and outdated research.
Version specificity prevents conflating incompatible patterns.

**Failure if omitted**: 
Research becomes useless for skill authoring (incompatible patterns, outdated docs).

**Source**: Technical Framework Researcher Prompt — Input Variables section

### Pattern: Source Hierarchy Enforcement

**Enforce strict source priority during research**

```markdown
## Source Priority (Non-Negotiable)

1. **Official Documentation** (Primary Authority)
   - Registry:terraform.io for Terraform providers
   - docs.python.org for Python
   - Official GitHub repos
   - Release notes (official channels only)

2. **Official Blog / Announcements**
   - AWS Blog, HashiCorp Blog, etc.
   - Links directly from official homepage

3. **Validated Community**
   - Stack Overflow (v[VERSION] tagged)
   - GitHub issues for [SYSTEM] labeled [TARGET_VERSION]
   - ArXiv technical papers (peer-reviewed)

4. 🚫 **REJECTED**
   - Medium articles (no fact-checking)
   - Reddit (opinion-based)
   - Outdated (>12 months old)
   - Tutorials without version tags
   - ChatGPT/LLM generated content

## Conflict Resolution
Official Docs > Blog > GitHub Issues > Community
```

**Why mandatory**: 
Prevents AI hallucinations by restricting sources to verifiable, authoritative channels.

**Failure if omitted**: 
Research mixes official with opinion content → skills contain false patterns.

**Source**: [AI Safety Research - Hallucination Prevention](https://research.anthropic.com/long-context)

### Pattern: Version Tagging on Every Claim

**Tag EVERY code example and pattern with version context**

```markdown
# ✅ CORRECT: Version-tagged code

## Pattern: Async Context Manager
**Version**: FastAPI v0.100+ (Changed in October 2023)
**Breaking**: In FastAPI v0.99, use `startup`/`shutdown` events (deprecated)

```python
# ✅ FastAPI v0.100+ ONLY
# DO NOT use in v0.99 or earlier

from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up")
    yield
    # Shutdown
    print("Shutting down")

app = FastAPI(lifespan=lifespan)  # ✅ v0.100+
```

**Breaking Changes from v0.99 → v0.100**:
- `startup` event → removed
- `shutdown` event → removed
- `lifespan` context manager → required

**Compatibility**:
- ✅ Works in: v0.100, v0.101, v0.102+
- ❌ Fails in: v0.99, v0.98, v0.97
- 🔄 Migration: https://fastapi.tiangolo.com/migration-guide
```

**Why mandatory**: 
Enables skill authors to reject patterns from wrong versions.

**Failure if omitted**: 
Skills written from research contain version-incompatible patterns → runtime failures.

**Source**: [FastAPI Migration Guide](https://fastapi.tiangolo.com/migration-guide)

---

