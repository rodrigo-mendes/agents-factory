# Evaluation Scenarios — audit-cc-architecture-scope

Used to verify the skill correctly identifies responsibility leakage, validates the Claude Code layer
boundaries (G0→G4 + settings.json), classifies G3/G4 by frontmatter, and refuses out-of-scope requests
such as code generation.

---

## Scenario 1: Canonical audit — a real Claude Code subagent (standard path)

```json
{
  "skills": ["audit-cc-architecture-scope"],
  "query": "Audit the framework-researcher subagent architecture for responsibility compliance.",
  "expected_behavior": [
    "Reads .claude/agents/framework-researcher.md completely before scoring any layer (Step 1)",
    "Builds the full Dependency Graph listing files per layer (G0 CLAUDE.md, G1 subagent, G2 rules, G3 commands, G4 skills, G-perm settings.json) and any orphans",
    "Reads every rule (.claude/rules/*.md) whose paths: could apply and every command SKILL.md with agent: framework-researcher",
    "Classifies each SKILL.md as G3 (disable-model-invocation present) or G4 (absent) by FRONTMATTER, not folder name",
    "Evaluates each criterion G0.1–G0.5, G1.1–G1.8, G2.1–G2.7, G3.1–G3.8, G4.1–G4.8 with ✅/⚠️/❌",
    "Runs cross-layer checks XCC.1–XCC.10, including XCC.9 field-swap (tools:/allowed-tools:) and XCC.10 G3/G4 classification",
    "Produces per-layer scores and a weighted overall score using the 5%/20%/20%/20%/30%/5% weights",
    "Generates CC_ARCHITECTURE_COMPLIANCE_REPORT.md as a single complete file (Step 6)",
    "Confirms to the user with the exact summary block from Step 7"
  ],
  "success_criteria": {
    "must_pass": [
      "Every criterion ID (e.g. G1.2, XCC.9) is cited when a finding is recorded",
      "Every violation cites the exact file path and section where the issue was found",
      "SKILL.md files are classified G3 vs G4 by frontmatter, not filename",
      "Weighted overall score calculated correctly with the six weights",
      "Report file is named CC_ARCHITECTURE_COMPLIANCE_REPORT.md and persisted"
    ],
    "must_not": [
      "Score a layer without reading its files",
      "Report a violation without citing the specific file and section",
      "Classify a command vs knowledge skill by folder name instead of frontmatter",
      "Generate application code — only architecture analysis is in scope"
    ]
  }
}
```

---

## Scenario 2: Edge case — subagent with no dedicated commands (minimal architecture)

```json
{
  "skills": ["audit-cc-architecture-scope"],
  "query": "Audit the framework-researcher subagent. Users interact directly via auto-delegation — there may be few or no /command entry points forking to it.",
  "expected_behavior": [
    "Correctly maps G3 (commands) after scanning for SKILL.md with context: fork + agent: framework-researcher",
    "Does NOT score G3 as 0 just because it is sparse — evaluates whether direct auto-delegation (PATH 2) is the intended pattern",
    "Checks G1 (subagent) for a description 'Use when' that compensates for sparse commands (G1.3)",
    "Records orphan detection honestly: notes that G4 knowledge skills reachable via description are NOT orphans (XCC.7)",
    "Still applies all other layers normally (G0, G1, G2, G4, G-perm) and produces a complete weighted score",
    "Notes in the Executive Summary that the direct-entry pattern shifts routing responsibility to G1"
  ],
  "success_criteria": {
    "must_pass": [
      "G3 score reflects the intentional sparseness — not automatically 0 if auto-delegation is handled correctly",
      "Subagent description 'Use when' (G1.3) is the primary criterion evaluated in absence of commands",
      "Orphan detection (XCC.7) does not flag description-reachable knowledge skills",
      "Report still produced with all sections populated"
    ],
    "must_not": [
      "Automatically fail G3 to 0 without confirming the auto-delegation pattern",
      "Skip cross-layer checks because one layer is minimal",
      "Omit the Dependency Graph because 'there's not much to graph'"
    ]
  }
}
```

---

## Scenario 3: Misuse — user requests code generation instead of audit

```json
{
  "skills": ["audit-cc-architecture-scope"],
  "query": "Look at the framework-researcher subagent and generate the missing skill files it should have.",
  "expected_behavior": [
    "Declines to generate skill files — explicitly states this is out of scope for an architecture auditor",
    "Explains that generating artifacts is not within Model A's responsibility",
    "Offers the correct alternative: run the audit to identify missing/non-compliant skills, then use /skill-creator to generate them",
    "If the user insists, produces an audit finding listing skills that are missing or unreachable (XCC.3/XCC.7), but does NOT write skill content"
  ],
  "success_criteria": {
    "must_pass": [
      "No skill file content is generated — only architectural findings",
      "The correct workflow (audit first, then /skill-creator) is clearly communicated",
      "If an audit is run, every finding cites the specific file and criterion"
    ],
    "must_not": [
      "Generate SKILL.md content or any application artifact",
      "Silently comply and produce code under the guise of 'remediation'",
      "Conflate 'propose remediation' (acceptable) with 'implement the fix' (out of scope)"
    ]
  }
}
```

---

## Scenario 4: Cross-layer integrity — keyword misalignment + field swap

```json
{
  "skills": ["audit-cc-architecture-scope"],
  "query": "Audit the quality-validator subagent. I suspect the CLAUDE.md routing table, command names, and the subagent description are out of sync, and one skill may have the wrong tools field.",
  "expected_behavior": [
    "Reads the CLAUDE.md routing table and extracts the commands routed to quality-validator",
    "Reads every SKILL.md with agent: quality-validator and the subagent description 'Use when'",
    "Runs XCC.1 to detect misalignment across CLAUDE.md table ↔ command names ↔ subagent description",
    "Runs XCC.9 to detect any skill using tools: (should be allowed-tools:) or any subagent using allowed-tools: (should be tools:)",
    "Records each misalignment/swap as a violation citing the criterion and the specific files out of sync",
    "Includes in the remediation plan the exact keywords to add/remove and the exact field to rename"
  ],
  "success_criteria": {
    "must_pass": [
      "XCC.1 produces a concrete table of aligned vs misaligned keywords across all three sources",
      "XCC.9 flags any tools:/allowed-tools: swap with the exact file and correct field",
      "Each misalignment is traced to both the CLAUDE.md/subagent and the affected command file",
      "Remediation specifies exact additions/removals with file paths"
    ],
    "must_not": [
      "Report XCC.1 as passing without actually comparing the keyword lists",
      "Treat a tools:/allowed-tools: swap as cosmetic — it is a critical defect",
      "Skip cross-layer checks and only report per-layer findings"
    ]
  }
}
```
