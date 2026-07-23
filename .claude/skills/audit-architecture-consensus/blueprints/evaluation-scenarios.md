# Evaluation Scenarios — audit-architecture-consensus

Used to verify the skill correctly applies all three models (A/B/C), correlates findings without
artificial inflation, and surfaces consensus-level violations ahead of single-model findings.

---

## Scenario 1: Canonical audit — multi-model consensus with shared finding (standard path)

```json
{
  "skills": ["audit-architecture-consensus"],
  "query": "Run a full multi-model architecture audit on the oci-terraform agent.",
  "expected_behavior": [
    "Runs Model A (Scope Hierarchy) first: discovers L0→L4 file graph, applies L0-L4 and X.1-X.8 criteria, produces per-layer scores",
    "Runs Model B (Invocation Flow): maps all entry points, traces all chains, builds reachability matrix, applies B.1-B.20 criteria",
    "Runs Model C (Technical Mechanisms): maps injection landscape, simulates per-file-type scenarios, applies C.1-C.24 criteria",
    "Normalizes all findings to the common format: unique-id, Models[], Criterion, File, Issue, Severity",
    "Groups findings by underlying issue — a prompt missing its name field is the same root cause whether flagged by L3.10 (A), B.3 (B), or C.24 (C)",
    "Classifies consensus level: 3/3=MUST FIX, 2/3=SHOULD FIX, 1/3=CONSIDER",
    "Generates AGENT_ARCHITECTURE_MULTI_MODEL_REPORT.md with all 8 sections including consensus findings first",
    "Confirms to the user with the exact summary block from Step 7"
  ],
  "success_criteria": {
    "must_pass": [
      "All three models are run and produce independent findings before correlation begins",
      "Each consensus finding cites what each model independently found (not just that '3 models agree')",
      "3/3 findings appear in Section 2 (MUST FIX) before any 2/3 or 1/3 findings",
      "Single-model findings each have an assessment of whether they are real / perspective-specific / false positive",
      "Report is named AGENT_ARCHITECTURE_MULTI_MODEL_REPORT.md and contains all 8 sections"
    ],
    "must_not": [
      "Skip a model because the first one already found 'enough issues'",
      "Average model scores as the overall score — consensus finding count matters more than averages",
      "Artificially inflate consensus by grouping unrelated findings from different models"
    ]
  }
}
```

---

## Scenario 2: Edge case — single-model finding that is a genuine blind-spot catch

```json
{
  "skills": ["audit-architecture-consensus"],
  "query": "Audit the architecture-auditor agent. Model B flagged a dead-end chain that models A and C did not mention.",
  "expected_behavior": [
    "Correctly classifies the finding as 1/3 consensus (Model B only) → 🟢 CONSIDER",
    "Does NOT dismiss it automatically — evaluates whether it is a genuine issue that A and C missed due to their blind spots",
    "Explains why Model A (scope perspective) would not flag a dead-end chain — A focuses on responsibility layer placement, not runtime paths",
    "Explains why Model C (engine mechanics) would not flag it — C focuses on injection correctness, not routing reachability",
    "Assesses 'Likely Real?' as Yes if the chain trace evidence is sound, even though only one model flagged it",
    "Includes it in Section 4 (Single-Model Findings) with the Likely Real? assessment"
  ],
  "success_criteria": {
    "must_pass": [
      "Finding appears in Section 4 with 'Likely Real?' assessment — not silently dropped",
      "Explanation of why the other two models have blind spots for this class of issue is included",
      "If assessed as real, the Unified Remediation Roadmap includes it with 1/3 priority"
    ],
    "must_not": [
      "Dismiss a 1/3 finding without explaining why the other models would not catch it",
      "Elevate a 1/3 finding to 🔴 MUST FIX without consensus evidence"
    ]
  }
}
```

---

## Scenario 3: Misuse — user requests the orchestrator skip one model to save time

```json
{
  "skills": ["audit-architecture-consensus"],
  "query": "Run the consensus audit on oci-terraform but skip Model C — we already know the engine mechanics are fine.",
  "expected_behavior": [
    "Declines to skip a model — explains that consensus prioritization requires all three independent perspectives",
    "Notes that running only two models cannot produce 3/3 consensus findings and degrades the reliability of 2/3 findings",
    "Suggests the correct alternative: if only engine mechanics are known to be fine, run /audit-architecture-scope and /audit-architecture-flow individually, not /audit-architecture-consensus",
    "If the user insists on a partial run, transparently labels the report as 'Two-Model Partial Audit (A+B)' and caps the maximum consensus level at 2/2 rather than misrepresenting it as full consensus"
  ],
  "success_criteria": {
    "must_pass": [
      "The tool either runs all three models or clearly labels the output as partial",
      "The limitation of a partial run is communicated before proceeding",
      "Correct alternative commands (/audit-architecture-scope, /audit-architecture-flow) are offered"
    ],
    "must_not": [
      "Run two models and label the output as a full consensus audit",
      "Silently skip a model and produce a report implying all three were applied"
    ]
  }
}
```

---

## Scenario 4: Cross-model correlation — same root cause, different symptom labels

```json
{
  "skills": ["audit-architecture-consensus"],
  "query": "Audit the skill-author agent. Models A and B each found issues but used different terminology.",
  "expected_behavior": [
    "Model A flagged 'L3.10 — prompt frontmatter incomplete: missing name field'",
    "Model B flagged 'B.3 — no argument-hint: field, user cannot know what to provide'",
    "Skill correctly identifies these as related: both stem from incomplete prompt frontmatter",
    "Groups them as a 2/3 finding (A+B) — not two separate 1/3 findings",
    "Root cause analysis explains: the prompt frontmatter is missing both name (causes L3.10) and argument-hint (causes B.3) — a single edit fixes both findings",
    "Remediation specifies one file, one action, one proposed content block that resolves both criterion violations",
    "Model C is checked: C.24 (No YAML errors) may also be relevant — if so, escalates to 3/3"
  ],
  "success_criteria": {
    "must_pass": [
      "Related findings from different models are grouped as a single finding with the combined consensus level",
      "Root cause analysis is present for every 2/3 and 3/3 finding",
      "Remediation count in the Roadmap reflects grouped issues, not double-counted duplicates",
      "Model C is explicitly checked for the same file before settling on a 2/3 consensus level"
    ],
    "must_not": [
      "List the same underlying issue as two separate findings at different consensus levels",
      "Force unrelated findings into the same group to inflate consensus artificially"
    ]
  }
}
```
