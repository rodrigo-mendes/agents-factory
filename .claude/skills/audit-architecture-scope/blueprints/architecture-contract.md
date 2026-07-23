# Architecture Contract — Evaluation Baseline & Responsibility Matrix

## Architecture Contract (Evaluation Baseline)

The correct layered architecture follows the **Agent Router Pattern** with strict responsibility boundaries:

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 0 — copilot-instructions.md                          │
│  Always-on global context. Project conventions, provider     │
│  constraints. NO routing logic, NO code examples.            │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 1 — Agent (.agent.md)                                │
│  Pure router. Intent classification, keyword→prompt mapping, │
│  workflow orchestration (P0-P5), tool restrictions.           │
│  NO implementation, NO code examples, NO technical details.  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 2 — Instructions (.instructions.md)                  │
│  Auto-injected guardrails via applyTo. Cross-cutting rules,  │
│  skill routing tables, standards, decision matrices.         │
│  NO full code examples (delegate to skills). NO routing.     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 3 — Prompts (.prompt.md)                             │
│  Specialized workflows for specific domains. Loads required  │
│  skills explicitly. Structured steps, trigger keywords.      │
│  NO implementation code (loads skills instead).              │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 4 — Skills (SKILL.md + blueprints/)                  │
│  Implementation knowledge. Code examples, scripts,           │
│  verification commands live HERE AND ONLY HERE.              │
│  Three-tier (✅⚠️🚫), version context, verification loop.   │
└─────────────────────────────────────────────────────────────┘
```

### Responsibility Matrix (Single Source of Truth)

| Responsibility | Layer 0 | Layer 1 (Agent) | Layer 2 (Instructions) | Layer 3 (Prompts) | Layer 4 (Skills) |
|---|---|---|---|---|---|
| Project-wide conventions | ✅ | ❌ | ❌ | ❌ | ❌ |
| Intent classification / routing | ❌ | ✅ | ❌ | ❌ | ❌ |
| Workflow orchestration (P0-P5) | ❌ | ✅ | ❌ | ❌ | ❌ |
| Tool restrictions | ❌ | ✅ | ❌ | ❌ | ❌ |
| Auto-injected guardrails (applyTo) | ❌ | ❌ | ✅ | ❌ | ❌ |
| Skill routing tables (when to load) | ❌ | ❌ | ✅ | ❌ | ❌ |
| Cross-cutting standards | ❌ | ❌ | ✅ | ❌ | ❌ |
| Domain-specific workflows | ❌ | ❌ | ❌ | ✅ | ❌ |
| Explicit skill loading | ❌ | ❌ | ❌ | ✅ | ❌ |
| Structured generation steps | ❌ | ❌ | ❌ | ✅ | ❌ |
| Code examples & scripts | ❌ | ❌ | ❌ | ❌ | ✅ |
| Three-tier safety (✅⚠️🚫) | ❌ | ❌ | ❌ | ❌ | ✅ |
| Version context & constraints | ❌ | ❌ | ❌ | ❌ | ✅ |
| Verification commands (bash) | ❌ | ❌ | ❌ | ❌ | ✅ |
| Anti-patterns with alternatives | ❌ | ❌ | ❌ | ❌ | ✅ |

**Any ✅ found in the wrong layer is a responsibility leakage violation.**

---
