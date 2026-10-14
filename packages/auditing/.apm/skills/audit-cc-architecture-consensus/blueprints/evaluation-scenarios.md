# Evaluation Scenarios — audit-cc-architecture-consensus

Used to verify the orchestrator runs all three Claude Code lenses independently, correlates findings by
root cause, prioritizes by consensus (3/3 → 🔴, 2/3 → 🟡, 1/3 → 🟢), and never fabricates consensus.

---

## Scenario 1: Canonical multi-model audit (standard path)

```json
{
  "skills": ["audit-cc-architecture-consensus"],
  "query": "Run a full consensus architecture audit of the framework-researcher subagent.",
  "expected_behavior": [
    "Reads the full dependency graph (G0→G4 + settings.json) before applying any model",
    "Runs Model A (Scope), Model B (Flow), Model C (Engine) to completion INDEPENDENTLY, each with its own criterion IDs (G/XCC, FCC, ECC)",
    "Fans out the three lenses in parallel via the architecture-auditor subagent's Agent tool",
    "Normalizes findings and correlates by the SAME underlying root cause, not by model label",
    "Prioritizes: 3/3 → 🔴 MUST FIX, 2/3 → 🟡 SHOULD FIX, 1/3 → 🟢 CONSIDER, with MUST FIX first",
    "Generates CC_ARCHITECTURE_MULTI_MODEL_REPORT.md with all 8 sections",
    "Confirms with the summary block from Step 7"
  ],
  "success_criteria": {
    "must_pass": [
      "All three models are run to completion before correlation begins",
      "Each consensus finding shows what each model independently observed with its criterion ID",
      "MUST FIX (3/3) section appears before SHOULD FIX (2/3) before CONSIDER (1/3)",
      "Report file is named CC_ARCHITECTURE_MULTI_MODEL_REPORT.md"
    ],
    "must_not": [
      "Average the three scores into an overall score",
      "Begin correlation before all three models are complete",
      "Double-count one underlying issue at multiple consensus levels"
    ]
  }
}
```

---

## Scenario 2: Single-model blind-spot catch

```json
{
  "skills": ["audit-cc-architecture-consensus"],
  "query": "Run a consensus audit. I expect a command missing disable-model-invocation to show up.",
  "expected_behavior": [
    "Model A flags it as G3.2 (missing disable-model-invocation → mis-classified command)",
    "Model B flags it as FCC.1/FCC.5 (not a clean fork entry point)",
    "Model C flags it as ECC.5 (pollutes the auto-listing budget)",
    "Correlates all three as ONE 3/3 consensus finding with a single root cause and one fix block",
    "Also assesses any 1/3 finding: states whether it's a real blind spot, perspective-specific, or a false positive"
  ],
  "success_criteria": {
    "must_pass": [
      "The three symptoms are merged into one 3/3 finding, not counted as three findings",
      "Per-model evidence is shown (G3.2 + FCC.5 + ECC.5)",
      "Every 1/3 finding gets a Likely-Real assessment"
    ],
    "must_not": [
      "List the same root cause three times at different consensus levels",
      "Dismiss a 1/3 finding without explaining why the other two models missed it"
    ]
  }
}
```

---

## Scenario 3: Misuse — user asks to skip a model

```json
{
  "skills": ["audit-cc-architecture-consensus"],
  "query": "Run the consensus audit but skip Engine — I know the mechanics are fine.",
  "expected_behavior": [
    "Explains that running only two models prevents genuine 3/3 consensus",
    "Asks whether to run all three and note expected-clean areas, OR to run the individual /audit-cc-architecture-engine standalone instead",
    "Does NOT silently produce a 'consensus' report from only two models",
    "If the user confirms two-model, labels the report clearly as a two-model correlation, not a 3/3 consensus"
  ],
  "success_criteria": {
    "must_pass": [
      "The limitation of skipping a model is stated before proceeding",
      "The report, if produced with two models, is explicitly labeled as such",
      "The option to run the skipped model standalone is offered"
    ],
    "must_not": [
      "Present a two-model result as a full 3/3 consensus audit",
      "Fabricate a Model C section that wasn't run"
    ]
  }
}
```

---

## Scenario 4: Cross-model finding correlation (related but not identical)

```json
{
  "skills": ["audit-cc-architecture-consensus"],
  "query": "Run a consensus audit on quality-validator and correlate related findings carefully.",
  "expected_behavior": [
    "Model A flags a rule with an inline routing table (G2.3 ⚠️)",
    "Model C flags redundant content across rules (ECC.14 ⚠️)",
    "Correlates them as a 2/3 SHOULD FIX finding ONLY if they share the same root cause / file; otherwise keeps them separate",
    "Explains the dissenting model's reasoning (why Model B would not flag it from the flow perspective)",
    "Does not stretch unrelated findings into false consensus"
  ],
  "success_criteria": {
    "must_pass": [
      "Findings are grouped only when they share the same root cause and affected file/section",
      "The 2/3 finding names the agreeing models and the dissenting model's reasoning",
      "Unrelated findings remain separate at their own consensus level"
    ],
    "must_not": [
      "Inflate consensus by merging unrelated findings",
      "Merge findings from different files as if they were the same issue"
    ]
  }
}
```
