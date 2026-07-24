# Evaluation Scenarios — audit-cc-architecture-flow

Used to verify the skill correctly traces the Claude Code invocation chain
(`/command → subagent → rules → skills`), maps the three entry paths, builds the Reachability Matrix,
and does not mis-flag description-reachable knowledge skills as orphans.

---

## Scenario 1: Canonical chain tracing (standard path)

```json
{
  "skills": ["audit-cc-architecture-flow"],
  "query": "Audit the invocation flow for the framework-researcher subagent.",
  "expected_behavior": [
    "Lists all SKILL.md with context: fork + agent: framework-researcher (PATH 1 commands)",
    "Reads .claude/agents/framework-researcher.md and its description 'Use when' (PATH 2 auto-delegation)",
    "Lists auto-invocable knowledge skills without disable-model-invocation (PATH 3)",
    "Builds the Entry Point Registry for all three paths",
    "Traces every chain step by step, verifying each reference actually appears inside the referencing file",
    "Labels each chain COMPLETE or BROKEN at step N",
    "Builds the Reachability Matrix (rows = commands / @subagent / knowledge skills / rule paths; cols = skills)",
    "Evaluates FCC.1–FCC.20 and scores with the 25%/30%/20%/25% weights",
    "Generates CC_INVOCATION_FLOW_AUDIT_REPORT.md as a single complete file"
  ],
  "success_criteria": {
    "must_pass": [
      "Every criterion ID (e.g. FCC.7, FCC.16) is cited when a finding is recorded",
      "Each chain has an explicit COMPLETE / BROKEN-at-step-N label",
      "The Reachability Matrix includes the REACHABLE BY ≥1 PATH row",
      "Report file is named CC_INVOCATION_FLOW_AUDIT_REPORT.md"
    ],
    "must_not": [
      "Mark a chain reachable based on file existence without verifying the reference inside the file",
      "Trace only /command entry points and skip PATH 2 and PATH 3",
      "Skip the reachability matrix"
    ]
  }
}
```

---

## Scenario 2: Knowledge-skill reachability (a skill with no command)

```json
{
  "skills": ["audit-cc-architecture-flow"],
  "query": "Audit the invocation flow. One knowledge skill (authoring-agent-skills) has no /command forking to it — is it an orphan?",
  "expected_behavior": [
    "Confirms authoring-agent-skills has NO disable-model-invocation → it is auto-invocable (PATH 3)",
    "Checks its description 'Use when' trigger is specific enough to be reached by description match",
    "Records it as REACHABLE via PATH 3, NOT as an orphan",
    "Reserves 'orphan' for files reachable by none of the three paths (e.g. a command whose agent: points to a missing subagent)",
    "Still traces all other chains normally"
  ],
  "success_criteria": {
    "must_pass": [
      "A knowledge skill reachable via description match is NOT flagged as an orphan",
      "The distinction between PATH-3-reachable and truly-unreachable is stated explicitly",
      "FCC.16 reachability accounts for the description-match path"
    ],
    "must_not": [
      "Flag a valid auto-invocable knowledge skill as an orphan just because no command forks to it",
      "Assume every skill must have a dedicated command"
    ]
  }
}
```

---

## Scenario 3: Misuse — user requests fixing a broken chain

```json
{
  "skills": ["audit-cc-architecture-flow"],
  "query": "The flow audit found a command whose agent: points to a subagent that doesn't exist. Create the missing subagent for me.",
  "expected_behavior": [
    "Declines to create the subagent — states that implementing fixes is outside the flow auditor's scope",
    "Explains that Model B traces and reports chain integrity but does not author artifacts",
    "Provides the remediation from the report: the exact command file, the missing agent: value, and whether to fix the reference or create the subagent (via /skill-creator or the skill-author subagent)",
    "Confirms the report already contains the Proposed Change for this fix"
  ],
  "success_criteria": {
    "must_pass": [
      "No subagent file is created or written",
      "The broken chain is described precisely: command file + dangling agent: value + break step",
      "The correct remediation route (fix reference or author subagent) is stated"
    ],
    "must_not": [
      "Author a subagent or any artifact",
      "Generate corrected file content beyond what is in the report's Proposed Change block"
    ]
  }
}
```

---

## Scenario 4: Cycle detection

```json
{
  "skills": ["audit-cc-architecture-flow"],
  "query": "Audit the invocation flow for a project where a command forks to a subagent that re-invokes the same command for the same intent.",
  "expected_behavior": [
    "Traces the chain and detects that the subagent redirects back to the command that re-forks into it (FCC.10)",
    "Labels the chain as a CYCLE (a form of dead-end that produces no terminal skill)",
    "Records the exact loop: command → subagent → same command, with file paths",
    "Recommends breaking the cycle by pointing the subagent at a terminal skill instead of the command",
    "Does not report the cycle as 'reachable' in the Reachability Matrix"
  ],
  "success_criteria": {
    "must_pass": [
      "FCC.10 cycle detection runs on every chain and names the exact loop",
      "The cycle is listed under DEAD-END CHAINS in the matrix output",
      "Remediation specifies how to break the loop with file paths"
    ],
    "must_not": [
      "Report a cycle as a complete, reachable chain",
      "Skip cycle detection and only check file existence"
    ]
  }
}
```
