# Evaluation Scenarios — audit-architecture-scope

Used to verify the skill correctly identifies responsibility leakage, validates layer boundaries
(L0→L4), and refuses out-of-scope requests such as code generation.

---

## Scenario 1: Canonical audit — agent with responsibility leakage (standard path)

```json
{
  "skills": ["audit-architecture-scope"],
  "query": "Audit the oci-terraform agent architecture for responsibility compliance.",
  "expected_behavior": [
    "Reads .claude/agents/oci-terraform.md completely before scoring any layer (Step 1)",
    "Builds the full Dependency Graph listing files per layer (L0–L4) and any orphans",
    "Reads every instruction file (Layer 2) and every prompt file (Layer 3) referenced in the agent",
    "Reads every skill SKILL.md (Layer 4) referenced in the routing table",
    "Evaluates each criterion L0.1–L0.5, L1.1–L1.10, L2.1–L2.10, L3.1–L3.10, L4.1–L4.10 with ✅/⚠️/❌",
    "Runs cross-layer checks X.1–X.8 and records any orphaned or duplicated files",
    "Produces per-layer scores and a weighted overall score using the 5%/20%/25%/20%/30% weights",
    "Generates AGENT_ARCHITECTURE_COMPLIANCE_REPORT.md as a single complete file (Step 6)",
    "Confirms to the user with the exact summary block from Step 7"
  ],
  "success_criteria": {
    "must_pass": [
      "Every criterion ID (e.g. L1.2, X.3) is cited when a finding is recorded",
      "Every violation cites the exact file path and section where the issue was found",
      "Every remediation entry includes: Violation ID, File, Section, What's Wrong, How to Fix, Proposed Content, Impact",
      "Weighted overall score calculated correctly: L0(5%)+L1(20%)+L2(25%)+L3(20%)+L4(30%)",
      "Report file is named AGENT_ARCHITECTURE_COMPLIANCE_REPORT.md and persisted"
    ],
    "must_not": [
      "Score a layer without reading its files",
      "Report a violation without citing the specific file and section",
      "Propose moving all code to skills — brief 1-2 line illustrative snippets in instructions are allowed (L2.4)",
      "Generate application code (Terraform, Java, etc.) — only architecture analysis is in scope"
    ]
  }
}
```

---

## Scenario 2: Edge case — agent with no Layer 3 prompts (minimal architecture)

```json
{
  "skills": ["audit-architecture-scope"],
  "query": "Audit the framework-researcher agent. It has no dedicated prompt files — users interact directly via @agent.",
  "expected_behavior": [
    "Correctly maps Layer 3 as empty after scanning for prompts with agent: framework-researcher in frontmatter",
    "Does NOT score Layer 3 as 0 just because it is empty — evaluates whether the gap is intentional (direct @agent pattern)",
    "Checks Layer 1 (agent) for a complete keyword routing table that compensates for missing Layer 3 (L1.5, L1.10)",
    "Flags if the agent lacks a fallback path for unmatched keywords (L1.10) as a ⚠️ or ❌ depending on severity",
    "Records orphan detection result for Layer 3 honestly: 'no prompt files found — direct-entry-only pattern'",
    "Still applies all other layers normally (L0, L1, L2, L4) and produces a complete weighted score",
    "Notes in the Executive Summary that the direct-entry pattern shifts routing responsibility to L1"
  ],
  "success_criteria": {
    "must_pass": [
      "Layer 3 score reflects the intentional absence — not automatically a 0 if the agent handles direct entry correctly",
      "Agent keyword routing table (L1.5) is the primary criterion evaluated in absence of prompts",
      "Orphan detection (X.7) correctly reports 'none' for Layer 3 since no prompt files are expected",
      "Report still produced with all sections populated, even if Layer 3 section is brief"
    ],
    "must_not": [
      "Automatically fail Layer 3 score to 0 without confirming whether the agent supports direct @agent invocation",
      "Skip the cross-layer checks just because one layer is minimal",
      "Omit the Dependency Graph because 'there's not much to graph'"
    ]
  }
}
```

---

## Scenario 3: Misuse — user requests code generation instead of audit

```json
{
  "skills": ["audit-architecture-scope"],
  "query": "Look at the oci-terraform agent and generate the missing skill files it should have.",
  "expected_behavior": [
    "Declines to generate skill files — explicitly states this is out of scope for an architecture auditor",
    "Explains that generating application artifacts is not within Model A's responsibility",
    "Offers the correct alternative: run the audit first to identify missing or non-compliant skills, then use /skill-creator to generate them",
    "If the user insists, reads the agent file and produces an audit finding listing skills that are missing or unreachable (X.7), but does NOT write skill file content"
  ],
  "success_criteria": {
    "must_pass": [
      "No skill file content is generated — only architectural findings are produced",
      "The correct workflow (audit first, then /skill-creator) is clearly communicated",
      "If an audit is run, every finding still cites the specific file and criterion"
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

## Scenario 4: Cross-layer integrity — keyword misalignment between agent and prompts

```json
{
  "skills": ["audit-architecture-scope"],
  "query": "Audit the quality-validator agent. I suspect the prompts and agent routing table are out of sync.",
  "expected_behavior": [
    "Reads the agent routing table from quality-validator.md and extracts all keyword-to-skill mappings",
    "Reads every prompt with agent: quality-validator and extracts their trigger keywords",
    "Runs cross-check X.1 to detect misaligned keywords: keywords in agent routing not present in any prompt trigger, and vice versa",
    "Records each misalignment as a violation citing the criterion X.1, the agent file, and the specific prompt file that is out of sync",
    "Scores Layer 1 (agent) accordingly — missing prompt coverage degrades L1.8 and L1.10",
    "Includes in the remediation plan the exact keywords to add or remove from each file"
  ],
  "success_criteria": {
    "must_pass": [
      "X.1 check is run and produces a concrete table of aligned vs misaligned keywords",
      "Each misalignment is traced back to both the agent file and the affected prompt file",
      "Remediation specifies exact keyword additions/removals with file paths"
    ],
    "must_not": [
      "Report X.1 as passing without actually comparing the keyword lists",
      "Skip the cross-layer checks and only report per-layer findings"
    ]
  }
}
```
