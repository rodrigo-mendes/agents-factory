# Quick Start — 3 Steps

Minimal end-to-end pipeline: research technology → create skill → validate quality.
Estimated time: 15-20 minutes. No prerequisites beyond Claude Code open in the project.

---

## What will happen

```
Step 1: /researching-technical-frameworks
         → agent asks for: technology, version, official URL, partners
         → produces: StoryBeat/research_FastAPI_v0.115.md

Step 2: /skill-creator StoryBeat/research_FastAPI_v0.115.md
         → agent loads patterns + applies three-tier
         → produces: .claude/skills/fastapi-async-api/SKILL.md + blueprints/

Step 3: /skill-best-practices-validator .claude/skills/fastapi-async-api/
         → agent verifies quality against the official checklist
         → produces: report in chat with score + improvement items
```

> **Version Absolutism**: replace `FastAPI 0.115` with any technology and specific version.
> The folder name and the research file adjust automatically.

---

## Step 1 — Research the Technology

```
/researching-technical-frameworks
```

The agent will ask (interactively):

| Field | Example |
|-------|---------|
| Technology | `FastAPI` |
| Version | `0.115` |
| Official URL | `https://fastapi.tiangolo.com/` |
| Integration partners | `Pydantic v2, SQLAlchemy 2.0, pytest` |

**Produced output**:

```
StoryBeat/research_FastAPI_v0.115.md
```

Sections the file contains:
- `## Version_Context` — changelog and breaking changes
- `## Mandatory_Patterns (✅)` — mandatory patterns with validated code
- `## Conditional_Patterns (⚠️)` — decisions with trade-offs
- `## Forbidden_Patterns (🚫)` — anti-patterns with alternatives
- `## Source_Bibliography` — all sources with URL + date

> **What to do if the agent stops**: if the agent says "version not found" or "I cannot
> confirm version X", provide the exact official URL of the documentation for that version.

---

## Step 2 — Create the Skill

```
/skill-creator StoryBeat/research_FastAPI_v0.115.md
```

The agent loads the research file and automatically applies:
- Skill name: `fastapi-async-api` (derived from name + context)
- Three-tier structure: Mandatory_Patterns → ✅, Conditional → ⚠️, Forbidden → 🚫
- Correct YAML frontmatter (name ≤ 64 chars, description with "Use when...")
- Blueprints with evaluation scenarios

**Produced output**:

```
.claude/skills/fastapi-async-api/
├── SKILL.md                              ← Versioned knowledge base
└── blueprints/
    └── evaluation-scenarios.md           ← 3+ use and evaluation scenarios
```

Quick check:
```bash
wc -l .claude/skills/fastapi-async-api/SKILL.md   # should be ≤ 500
```

---

## Step 3 — Validate the Skill

```
/skill-best-practices-validator .claude/skills/fastapi-async-api/
```

The agent verifies automatically:

| Check | Criterion |
|-------|----------|
| Frontmatter `name` | ≤ 64 chars, kebab-case |
| Frontmatter `description` | Includes "Use when…" |
| ✅ Always Do section | Present with executable code |
| ⚠️ Ask First section | Present with trade-off table |
| 🚫 Never Do section | Present with alternative + impact |
| Size | SKILL.md < 500 lines |
| Blueprints | `evaluation-scenarios.md` exists with ≥ 3 scenarios |
| Version absolutism | Single version declared |

**Output**: report in chat with score per dimension and concrete improvement suggestions.

---

## Expected Results

After the 3 steps, you have:

- A knowledge base validated against official sources, versioned and ready for use by agents
- A skill with three-tier guardrails that any agent can load at P0
- A quality report confirming the skill follows the framework's standards

---

## Next Steps

| Want to... | Go to |
|---------|---------|
| Use this skill in an agent | [Creating Agents](criando-agentes.md) |
| Research another technology or domain | [Researching Technologies](pesquisando-tecnologias.md) |
| See all researcher types | [Catalog — Research](../capacidades/prompts-pesquisa.md) |
| Validate the entire project | [Validating Artifacts](validando-artefatos.md) → Step 3 |
| See the complete pipeline with audit | [Project Creation Flow](../fluxos/fluxo-criacao-projeto.md) |
| Complete reference with all commands | [Agent Usage Manual](../manual/README.md) |
