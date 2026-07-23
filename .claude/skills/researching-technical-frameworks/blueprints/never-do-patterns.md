## 🚫 Never Do

### Anti-Pattern: Generic Tech Names

```markdown
# 🚫 WRONG: Generic technology names

User says: "I need a skill for databases"
Research output: [Ambiguous, covers 10+ database types]

# ✅ CORRECT: Specific technology with version

User says: "I need a skill for PostgreSQL v15 with async queries using SQLAlchemy v2.0"
Research output: research_PostgreSQL_v15_SQLAlchemy_v2.0.md
```

**Why prohibited**: 
Generic names produce unfocused research that conflates different patterns.

**Actual impact**: 
Skill authors receive 50 pages of mixed content for "databases" → can't extract clear patterns.

**Solution**: 
Ask user to specify exact technology name + version before starting research.

**Source**: Technical Framework Researcher Prompt — Authority & Versioning section

### Anti-Pattern: Mixing Versions in Single Research

```markdown
# 🚫 WRONG: Version mixing in one research document

## Async in FastAPI
- v0.95: Use `startup` and `shutdown` events
- v0.100: Use `lifespan` context manager
- Trade-offs between the two...
[Confuses skill author: which one to use?]

# ✅ CORRECT: Version-specific, separate research

# research_FastAPI_v0.100.md
ONLY includes v0.100 patterns.

# research_FastAPI_v0.95.md
ONLY includes v0.95 patterns.

# research_FastAPI_Migration_v0.95_to_v0.100.md
ONLY migration guide.
```

**Why prohibited**: 
Mixing versions creates ambiguity for skill authors (which pattern to enforce?).

**Actual impact**: 
Skill becomes incorrect for the target version (can work on v0.99 but breaks on v0.100).

**Solution**: 
Create separate research documents per version.
Use `research_[TECH]_Migration_v[OLD]_to_v[NEW].md` for migration guides.

**Source**: Technical Framework Researcher Prompt — Core Principles section

### Anti-Pattern: Undated Sources

```markdown
# 🚫 WRONG: Source without publication date

"According to the FastAPI docs, use startup events for initialization"
[No date - could be from v0.95 (2022) or v0.100 (2023)]

# ✅ CORRECT: Explicit date on every source

"According to FastAPI Official Blog (Oct 15, 2023), 
lifespan context manager replaces startup/shutdown events in v0.100+"

Source: https://fastapi.tiangolo.com/release-notes/ (Published: Oct 15, 2023)
```

**Why prohibited**: 
Undated sources allow outdated patterns to slip into current research.

**Actual impact**: 
Research recommends deprecated patterns because source date is unknown.

**Solution**: 
Include publication date for every external source.
Flag sources older than 6 months (especially for framework research); reject sources older than 12 months unless they document the current stable version.

**Source**: Technical Framework Researcher Prompt — Source Priority section

---

