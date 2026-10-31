# Research Scope — Format Templates

Format templates for the Three-Tier Operational Guardrails (§3).
Referenced from [SKILL.md](../SKILL.md#3-three-tier-operational-guardrails).

## Always Do

```
Pattern: [Name]
Why: [Official reason + security/compliance impact]
Code: [Minimal HCL example]
Terraform Version: [{{TERRAFORM_VERSION}}+]
Provider Version: [{{PROVIDER_VERSION}}]
Source: [Registry link + Provider docs link]
```

## Ask First

```
Decision: [What to choose]
Options: [A, B, C]
Tradeoffs:
  | Option | Optimizes | Sacrifices | Scaling | State | Drift |
  |--------|-----------|------------|---------|-------|-------|

When: [Decision factors: scale, team size, CI/CD, multi-region]
Agent: "Ask user: [specific decision question]"
Source: [Registry link]
```

## Never Do

```
Anti-Pattern: [What NOT to do]
Why: [Security/state-consistency/compliance reason]
❌ Wrong:
  # DON'T — [reason]
  [bad HCL]
✅ Correct:
  # DO — [reason]
  [correct HCL with explanations]

Impact: [state corruption | security breach | unmanaged drift | data loss]
Severity: [CRITICAL | HIGH | MEDIUM]
Source: [Registry security advisory link]
```
