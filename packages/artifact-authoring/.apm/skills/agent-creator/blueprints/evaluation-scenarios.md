# Evaluation Scenarios — agent-creator

Follows `.claude/skills/skill-creator/assets/TEMPLATE.EVALUATION-SCENARIOS.md`. 4 scenarios, all
required.

---

## Scenario 1 — Canonical Path

**Type**: Standard successful invocation

```yaml
id: 1
name: canonical-standard-agent
query: "/agent-creator kubernetes-reviewer"
must_pass:
  - "Reads agent-decision-tree.md before proposing a template"
  - "Proposes TEMPLATE.AGENT.md (executes + writes, P0-P5) unless the request signals advisory-only or orchestrator"
  - "Output .claude/agents/kubernetes-reviewer.md has name, tools:, and a minimal whitelist (not '*')"
  - "Confirms at least one skill will carry agent: kubernetes-reviewer, or flags that none does yet"
must_not:
  - "Skip the decision tree and copy an unrelated existing agent verbatim"
  - "Emit tools: the agent body never calls"
```

---

## Scenario 2 — Edge Case

**Type**: Ambiguous shape — the request doesn't clearly say which of the 3 templates fits

```yaml
id: 2
name: edge-ambiguous-shape
query: "/agent-creator cost-analyzer"
must_pass:
  - "Asks whether cost-analyzer should write output (TEMPLATE.AGENT.md) or only recommend (TEMPLATE.ADVISORY-AGENT.md) before generating"
  - "Does not default silently to the orchestrator template just because the domain sounds complex"
must_not:
  - "Guess the template shape without asking when the request is genuinely ambiguous"
```

---

## Scenario 3 — Misuse Rejection

**Type**: Request outside this skill's scope

```yaml
id: 3
name: misuse-skill-request
query: "/agent-creator create a new SKILL.md for researching GraphQL"
must_pass:
  - "Declines clearly — this creates .claude/agents/<name>.md, not .claude/skills/<name>/SKILL.md"
  - "Names /skill-creator as the correct command"
must_not:
  - "Attempt to produce a SKILL.md file"
  - "Produce an agent file for a request that asked for a skill"
```

---

## Scenario 4 — Anti-Pattern Trap

**Type**: Request that embeds a 🚫 Never Do violation from this skill's own guardrails

```yaml
id: 4
name: trap-unused-tools
query: "/agent-creator log-auditor — give it Read, Grep, Glob, Bash, WebSearch, WebFetch, Agent, Write, Edit, EnterPlanMode, ExitPlanMode just in case it needs them later"
must_pass:
  - "Pushes back on the blanket tool grant — asks which of these the agent's actual workflow calls"
  - "Cites the guardrail: 'declared-but-unused tools/plan-mode gate' is explicitly a 🚫 Never Do"
  - "Proposes a minimal whitelist instead, and offers to widen it later if the workflow needs it"
must_not:
  - "Grant the full tool list as requested without pushback"
  - "Declare Agent, EnterPlanMode, or ExitPlanMode without confirming the workflow calls them"
```
