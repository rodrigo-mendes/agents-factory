# Evaluation Scenarios — audit-architecture-flow

Used to verify the skill correctly traces invocation chains from entry point to terminal skill,
builds an accurate reachability matrix, and declines tasks outside runtime flow analysis.

---

## Scenario 1: Canonical audit — complete chain tracing (standard path)

```json
{
  "skills": ["audit-architecture-flow"],
  "query": "Audit the invocation flow for the oci-terraform agent.",
  "expected_behavior": [
    "Maps all entry points: lists every prompt with agent: oci-terraform in its frontmatter (PATH 1) and the direct @oci-terraform entry (PATH 2)",
    "Traces each prompt chain step by step: prompt → agent file exists? → skill declared → agent routing table includes skill? → instruction routing includes skill?",
    "Traces each @agent keyword chain: keyword in agent routing table → skill file exists? → instruction routing includes skill?",
    "Builds the full Reachability Matrix showing which entry points can reach which skills",
    "Identifies UNREACHABLE SKILLS, ORPHAN PROMPTS, and DEAD-END CHAINS explicitly",
    "Evaluates criteria B.1–B.20 per component, marking each ✅/⚠️/❌ with evidence",
    "Scores each component with the 25%/30%/20%/25% weights and produces an overall score",
    "Generates INVOCATION_FLOW_AUDIT_REPORT.md as a single complete file",
    "Reports Flow Health as HEALTHY / DEGRADED / BROKEN with rationale"
  ],
  "success_criteria": {
    "must_pass": [
      "Every entry point is listed in the Entry Point Registry before chain tracing begins",
      "Every chain trace records the break point (step N) if the chain is broken",
      "Reachability Matrix covers all prompts, direct @agent keywords, and instruction applyTo paths",
      "UNREACHABLE SKILLS are listed by name with explanation of why no chain reaches them",
      "Every finding cites the specific file and criterion ID (e.g. B.7, B.16)"
    ],
    "must_not": [
      "Report a skill as reachable solely because its file exists on disk — must verify a chain",
      "Skip the direct @agent path (PATH 2) — it is a valid entry point even when prompts exist",
      "Generate application code or create skill files as part of remediation"
    ]
  }
}
```

---

## Scenario 2: Edge case — skill reachable only via instruction routing table (no direct prompt)

```json
{
  "skills": ["audit-architecture-flow"],
  "query": "Audit the flow for the framework-researcher agent. One of its skills is referenced in an instruction's When-to-Load section but not in any prompt.",
  "expected_behavior": [
    "Identifies the skill as reachable via the instruction routing table even without a dedicated prompt",
    "Does NOT mark the skill as an orphan — instruction routing tables are valid reachability paths (B.16)",
    "Notes in the Reachability Matrix that the only path to this skill is through the instruction passive injection + routing table",
    "Flags as ⚠️ (not ❌) if the skill is reachable via instruction but has no structured prompt entry point (B.2)",
    "Correctly evaluates B.13 — the instruction must work even without the agent active (plain Copilot fallback)"
  ],
  "success_criteria": {
    "must_pass": [
      "Skill correctly appears as REACHABLE in the matrix with the path labeled as instruction-routing",
      "B.16 criterion evaluates the instruction routing table as a valid reachability path",
      "The note about missing structured prompt entry point (PATH 1) appears in the findings if applicable"
    ],
    "must_not": [
      "Mark a skill as orphaned when it is referenced in an instruction's When-to-Load Skills section",
      "Require a dedicated prompt for every skill — instruction routing is a first-class path"
    ]
  }
}
```

---

## Scenario 3: Misuse — user requests creating missing prompt files

```json
{
  "skills": ["audit-architecture-flow"],
  "query": "The flow audit found dead-end chains. Go ahead and create the missing prompt files to fix them.",
  "expected_behavior": [
    "Declines to create prompt files — explicitly states this is outside the invocation flow auditor's scope",
    "Explains that Model B traces and reports flow issues but does not implement fixes",
    "Offers the correct alternative: use the remediation plan from INVOCATION_FLOW_AUDIT_REPORT.md as input to /skill-creator or manual authoring",
    "If asked to at least describe what the prompt should contain, may provide a high-level description of required frontmatter fields (agent:, argument-hint:, skills:) without writing a full prompt"
  ],
  "success_criteria": {
    "must_pass": [
      "No prompt file content is generated or written to disk",
      "The correct next-step workflow is communicated to the user",
      "Explanation clearly distinguishes between 'report the gap' (in scope) and 'fill the gap' (out of scope)"
    ],
    "must_not": [
      "Write or output full prompt file content",
      "Silently create missing files as part of 'completing the audit'"
    ]
  }
}
```

---

## Scenario 4: Cycle detection — prompt that loops back to itself via agent

```json
{
  "skills": ["audit-architecture-flow"],
  "query": "Audit the architecture-auditor agent. I think one of the prompts routes back through the agent to itself.",
  "expected_behavior": [
    "Traces each chain completely, looking for prompt→agent→prompt→agent→... loops",
    "Detects if any agent keyword mapping routes to a prompt that is also the entry point for that keyword",
    "Records the cycle as a 🔴 Critical violation against criterion B.10",
    "Identifies the specific chain where the loop occurs: which prompt, which agent keyword, which prompt it loops back to",
    "Includes in the DEAD-END CHAINS section of the Reachability Matrix with label 'CYCLE'",
    "Proposes remediation: break the cycle by replacing the prompt redirect with a direct skill reference or adding a terminal skill"
  ],
  "success_criteria": {
    "must_pass": [
      "B.10 (No circular reference) is evaluated for every chain — not just checked superficially",
      "Cycle is recorded as 🔴 Critical with the exact circular path documented",
      "Remediation specifies exactly where to break the cycle and what to replace the redirect with"
    ],
    "must_not": [
      "Report a chain as 'COMPLETE' if it loops — a cycle is always a dead-end in practice",
      "Miss the cycle because only the first step of each chain was checked"
    ]
  }
}
```
