---
name: evaluating-skill-scenarios
description: "Executes a skill's evaluation scenarios from blueprints/evaluation-scenarios.md, invokes the skill under test via LLM-as-judge, and reports pass/fail per criterion. Use when verifying that a skill responds correctly to its canonical, edge, and misuse test cases."
argument-hint: "Skill name to evaluate (e.g. cloud-architecture-researcher)"
context: fork
agent: skill-evaluator
disable-model-invocation: true
---
# Prompt: Evaluating Skill Scenarios

## Objective

Execute all scenarios in `blueprints/evaluation-scenarios.md` for the skill named in `$ARGUMENTS`.
For each scenario, invoke the skill under test (by injecting its SKILL.md body as context) and
apply LLM-as-judge to assess whether the actual response satisfies `success_criteria.must_pass`
and avoids `success_criteria.must_not`.

## Quick Navigation

- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 3 meta scenarios for this evaluator
- **[Blueprints & Guardrails](#blueprints--guardrails)** — Always Do / Ask First / Never Do
- **[Judging Rubric](#judging-rubric)** — how to score must_pass and must_not
- **[Report Format](#report-format)** — exact structure of the output file
- **[Verification Loop](#verification-loop)** — checks before saving

---

## Agent Instructions

Act as a Skill Behavioral Evaluator. Simulate invoking the skill under test with each scenario's
`query` and judge whether the response meets the defined criteria. The rubric below governs how to
execute, judge, and report — the `skill-evaluator` agent applies it.

---

## Blueprints & Guardrails

### ✅ Always Do

- **Read the full SKILL.md before executing any scenario** — the skill prompt is the context
  injected into the spawned Agent; an incomplete read produces invalid test results.
- **Execute scenarios sequentially** — capture each result before moving to the next; parallel
  execution risks context confusion between scenarios.
- **Cite actual response fragments as evidence** — every PASS and FAIL verdict must quote a
  specific fragment from the captured response; no paraphrasing or impressionistic verdicts.
- **Verify with Glob that evaluation-scenarios.md exists** before starting; abort with a clear
  error message if missing.
- **Save the report only after all scenarios complete** — no partial reports mid-run.

### ⚠️ Ask First

- **Researcher skills with canonical/edge scenarios** — execution may trigger real web searches
  (WebSearch/WebFetch), increasing cost and latency. Confirm before running if the skill is a
  researcher type and the user has not indicated they want full-fidelity execution.
- **Directory path as $ARGUMENTS** — if the argument points to a directory (not a single skill
  name), confirm before iterating all skills in that directory.
- **--fix flag** — if `$ARGUMENTS` contains `--fix`, confirm with the user before modifying
  any skill file.

### 🚫 Never Do

- **Never fabricate response content** — if a spawned Agent call fails or returns empty, mark the
  scenario as `⚠️ EXECUTION ERROR`; do not invent a plausible response to judge.
  ✅ Report the error and continue with the remaining scenarios.
- **Never judge using expected_behavior prose alone** — `expected_behavior` is context for
  understanding the scenario, not the verdict checklist.
  ✅ Ground every PASS/FAIL in a specific `must_pass` or `must_not` item.
- **Never rewrite the skill under test** — evaluate and report; leave skill files unchanged.
  ✅ Document recommended fixes in the report's "Findings & Recommended Fixes" section.

---

## Judging Rubric

### must_pass criteria

For each item in `success_criteria.must_pass`:

| Verdict | Condition | Evidence required |
|---|---|---|
| ✅ PASS | Response satisfies the criterion | Quote the fragment that demonstrates it |
| 🚫 FAIL | Response does not satisfy the criterion | State what is missing or wrong |

### must_not criteria

For each item in `success_criteria.must_not`:

| Verdict | Condition | Evidence required |
|---|---|---|
| ✅ OK | Criterion not violated | Brief confirmation (one line) |
| 🚫 VIOLATED | Response violates the criterion | Quote the offending fragment |

### Scenario overall verdict

| Verdict | Condition |
|---|---|
| ✅ PASS | All must_pass = PASS AND all must_not = OK |
| ⚠️ PARTIAL | ≥1 must_pass FAIL but ≥50% pass, AND all must_not = OK |
| 🚫 FAIL | >50% must_pass FAIL OR any must_not VIOLATED |

---

## Report Format

Save to: `.claude/skills/{skill-name}/{skill-name}-evaluation-report.md`

```markdown
# Evaluation Report — {skill-name}
**Date**: {YYYY-MM-DD}
**Scenarios executed**: {N}
**Overall**: {N} PASS / {N} PARTIAL / {N} FAIL

---

## Summary Matrix

| Scenario | Type | must_pass | must_not | Verdict |
|---|---|---|---|---|
| Scenario 1: {title} | canonical | {X}/{total} ✅ | all OK | ✅ PASS |
| Scenario 2: {title} | edge | {X}/{total} ✅ | all OK | ⚠️ PARTIAL |
| Scenario 3: {title} | misuse | {X}/{total} ✅ | all OK | ✅ PASS |

---

## Scenario Detail

### Scenario {N}: {title}
**Type**: canonical | edge | misuse
**Query**: {query}

#### must_pass
- ✅ "{criterion}" — "{evidence quote from response}"
- 🚫 "{criterion}" — FAILED: "{what is missing or wrong}"

#### must_not
- ✅ "{criterion}" — OK
- 🚫 "{criterion}" — VIOLATED: "{evidence quote}"

**Verdict**: ✅ PASS | ⚠️ PARTIAL | 🚫 FAIL

---

[repeat for each scenario]

---

## Findings & Recommended Fixes

### Critical (🚫 FAIL scenarios)
[Skill changes needed to satisfy each failed criterion — cite criterion + scenario]

### Improvements (⚠️ PARTIAL scenarios)
[Skill improvements per partially-satisfied criterion]
```

---

## Verification Loop

Before saving, confirm the content checklist:

- [ ] Each scenario has a verdict (✅ PASS / ⚠️ PARTIAL / 🚫 FAIL)
- [ ] Every must_pass item has cited evidence or a specific failure statement
- [ ] Every must_not item has a verdict (OK or VIOLATED)
- [ ] Summary matrix row count equals the total scenario count

After saving, confirm with Glob:

```
Glob(".claude/skills/{skill-name}/{skill-name}-evaluation-report.md")
```

Expected: 1 file found. If 0, save failed — retry before reporting completion.

---

## External Resources

- [Claude Agent Skills — Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) — C1: ≥3 evaluation scenarios required per skill
- [skill-creator SKILL.md](./../skill-creator/SKILL.md) — evaluation-scenarios.md structure convention
- [skill-frontmatter rules](./../../rules/skill-frontmatter.md) — frontmatter conventions

---

**Typical invocation**:
```
/evaluating-skill-scenarios cloud-architecture-researcher
```

**Output**: `.claude/skills/cloud-architecture-researcher/cloud-architecture-researcher-evaluation-report.md`
