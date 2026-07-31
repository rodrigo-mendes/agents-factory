# Agent: skill-evaluator

> **Model:** `sonnet` | **Tools:** Read, Grep, Glob, Agent, Write
> **Role:** Skill Behavioral Evaluator — executes evaluation scenarios for a skill by invoking it as a sub-agent and applying LLM-as-judge to verify responses against must_pass/must_not criteria.

**What it does:** Reads `blueprints/evaluation-scenarios.md` from the target skill, executes each scenario via Agent sub-agent with the full SKILL.md body as context, and judges responses producing a behavioral evaluation report.

**What it does NOT do:** Evaluate static quality of artifacts (frontmatter, line count, naming conventions) — this is the `quality-validator`'s domain. Does not research technologies, generate skills, or rewrite the evaluated skill.

**LLM-as-judge:** Each scenario is executed by a separate Agent sub-agent with the SKILL.md injected as context, simulating the real command invocation. The `skill-evaluator` then judges the response against the criteria defined in the scenario.

---

## Recommended Order of Use

The `skill-evaluator` complements the `quality-validator` — use after validating the static quality of the skill:

```
1. /skill-best-practices-validator .claude/skills/<name>/   ← static quality first
        ↓ if OK
2. /evaluating-skill-scenarios <name>                        ← behavioral validation
```

---

## /evaluating-skill-scenarios

> **Agent:** `skill-evaluator` | **Context:** fork | **Model invocation:** disabled

### When to Use

Use to verify whether a skill responds correctly to its own test cases — the canonical path, edge cases and misuse rejection.

**Trigger words:** "test skill", "evaluate behavior", "run scenarios", "LLM-as-judge", "validate skill responses", "evaluation scenarios".

### Prerequisites

- The skill must have `.claude/skills/{name}/blueprints/evaluation-scenarios.md` with at least 3 scenarios
- If the file is absent, the agent aborts with a clear error message

### Inputs

| Field | Required | Example |
|-------|:-----------:|---------|
| Skill name | ✅ | `cloud-architecture-researcher` |

### Call Example

```
/evaluating-skill-scenarios cloud-architecture-researcher
```

### Execution Method

The agent follows 4 phases (P0–P3):

| Phase | Action |
|------|------|
| **P0** | Confirms it has the full rubric from the invoking skill's SKILL.md in context |
| **P1** | Reads `.claude/skills/{name}/SKILL.md` and `.claude/skills/{name}/blueprints/evaluation-scenarios.md` |
| **P2** | Executes each scenario **sequentially** — injects SKILL.md + query into an Agent sub-agent and captures the response |
| **P3** | Judges each response with LLM-as-judge and writes the report |

### Sequential Execution (not parallel)

Scenarios are executed one by one — each execution is isolated and the result must be captured before starting the next one.

### Tool Selection for the Sub-agent

| Skill type | Injected tools |
|---------------|-----------------|
| Researcher (name contains "researcher") | Read, Grep, Glob, WebSearch, WebFetch |
| Validator / Auditor | Read, Grep, Glob |
| Unknown | Read, Grep, Glob, WebSearch, WebFetch (safe superset) |

### Verdicts per Scenario

| Verdict | Condition |
|-----------|----------|
| ✅ PASS | all must_pass = PASS AND all must_not = OK |
| ⚠️ PARTIAL | ≥1 must_pass FAIL but ≥50% pass, AND all must_not = OK |
| 🚫 FAIL | >50% must_pass FAIL OR any must_not VIOLATED |

### Output Produced

```
.claude/skills/{skill-name}/{skill-name}-evaluation-report.md
```

Report structure:

```markdown
# Evaluation Report — {skill-name}

## Summary
| Scenario | Verdict | must_pass | must_not |
|---------|-----------|:---------:|:--------:|

## Results by Scenario

### Scenario N — {title}
**Query:** ...
**Verdict:** ✅ PASS / ⚠️ PARTIAL / 🚫 FAIL

#### must_pass
- [✅/🚫] criterion: cited evidence

#### must_not
- [✅/🚫] criterion: cited evidence (or "not violated")

## Recommendations
[Improvement suggestions grouped by priority]
```

### Report Verification

```bash
test -f .claude/skills/<name>/<name>-evaluation-report.md && echo "OK" || echo "MISSING"
grep -c "✅ PASS\|⚠️ PARTIAL\|🚫 FAIL" .claude/skills/<name>/<name>-evaluation-report.md
```

---

## Agent Principles

**Evaluate; never fix** — reports findings and suggests corrections in the report; does not modify the evaluated skill unless the user passes `--fix` in `$ARGUMENTS`.

**Never fabricate** — if the execution of a scenario fails, marks it as `⚠️ EXECUTION ERROR`; never invents a plausible response to judge.

**Always cite evidence** — every PASS/FAIL verdict requires a cited fragment from the real response or an explicit statement of absence — no impressionistic verdicts.

**Rubric-driven** — loads the complete rubric from the invoking skill's SKILL.md in P0. Does not substitute with general judgment.

---

*See [manual README](README.md) for general navigation.*
