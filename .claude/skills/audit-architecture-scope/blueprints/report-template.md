# Agent Architecture Compliance Report — Template

# Agent Architecture Compliance Report
## Agent: {agent-name} | Audit Date: {date}

---

## 1. Executive Summary

[2-3 paragraphs: what the agent does, overall compliance assessment,
most critical finding, and recommended immediate action]

### Compliance Verdict: {✅ PASS | ⚠️ CONDITIONAL | ❌ FAIL}

### Score Summary

| Layer | Score | Status | Critical Issues |
|---|---|---|---|
| Layer 0 — Global Instructions | [X/10] | [✅/⚠️/❌] | [count] |
| Layer 1 — Agent Router | [X/10] | [✅/⚠️/❌] | [count] |
| Layer 2 — Instructions | [X/10] | [✅/⚠️/❌] | [count] |
| Layer 3 — Prompts | [X/10] | [✅/⚠️/❌] | [count] |
| Layer 4 — Skills | [X/10] | [✅/⚠️/❌] | [count] |
| **Overall (weighted)** | **[X.X/10]** | **[Verdict]** | **[total]** |

---

## 2. File Inventory & Dependency Graph

### Files Analyzed

| # | Layer | File | Lines | Status |
|---|---|---|---|---|
| 1 | L0 | .github/copilot-instructions.md | [N] | Analyzed |
| 2 | L1 | .github/agents/{agent}.agent.md | [N] | Analyzed |
| ... | ... | ... | ... | ... |

### Dependency Graph

\```
{agent-name}
├── copilot-instructions.md (L0 — always active)
├── agents/{agent-name}.agent.md (L1 — router)
│   ├── instructions/{instr-1}.instructions.md (L2 — auto-injected)
│   │   └── skills/{skill-1}/SKILL.md (L4 — on-demand)
│   ├── instructions/{instr-2}.instructions.md (L2)
│   │   └── skills/{skill-2}/SKILL.md (L4)
│   └── prompts/{prompt-1}.prompt.md (L3 — workflow)
│       └── skills/{skill-3}/SKILL.md (L4)
└── Orphans: [list or "none"]
\```

---

## 3. Per-Layer Analysis

### 3.1 Layer 0 — Global Instructions

| # | Criterion | Result | Evidence |
|---|---|---|---|
| L0.1 | Project-scoped only | [✅/⚠️/❌] | [specific evidence from file] |
| ... | ... | ... | ... |

**Layer Score: [X/10]**

### 3.2 Layer 1 — Agent Router

| # | Criterion | Result | Evidence |
|---|---|---|---|
| L1.1 | Router purity | [✅/⚠️/❌] | [specific evidence from file] |
| ... | ... | ... | ... |

**Layer Score: [X/10]**

### 3.3 Layer 2 — Instructions

[Repeat per instruction file]

#### {instruction-filename}.instructions.md

| # | Criterion | Result | Evidence |
|---|---|---|---|
| L2.1 | applyTo specificity | [✅/⚠️/❌] | [specific evidence] |
| ... | ... | ... | ... |

**Layer Aggregate Score: [X/10]**

### 3.4 Layer 3 — Prompts

[Repeat per prompt file — sample up to 5]

**Layer Aggregate Score: [X/10]**

### 3.5 Layer 4 — Skills

[Repeat per skill — sample up to 5]

**Layer Aggregate Score: [X/10]**

---

## 4. Cross-Layer Validation

| # | Check | Result | Details |
|---|---|---|---|
| X.1 | Keyword alignment | [✅/⚠️/❌] | [specific mismatches] |
| X.2 | Responsibility leakage | [✅/⚠️/❌] | [where code was found in wrong layer] |
| X.3 | Skill reachability | [✅/⚠️/❌] | [unreachable skills listed] |
| X.4 | Link chain integrity | [✅/⚠️/❌] | [broken links listed] |
| X.5 | Naming consistency | [✅/⚠️/❌] | [inconsistencies listed] |
| X.6 | Coverage gaps | [✅/⚠️/❌] | [instructions without skill refs] |
| X.7 | Orphan detection | [✅/⚠️/❌] | [orphan files listed] |
| X.8 | Duplication detection | [✅/⚠️/❌] | [duplicated content locations] |

---

## 5. Violations Summary

| # | Severity | Criterion | File | Description |
|---|---|---|---|---|
| V1 | 🔴 Critical | [L1.2] | [file] | [description] |
| V2 | 🟡 Medium | [L2.4] | [file] | [description] |
| V3 | 🟢 Low | [L4.6] | [file] | [description] |
| ... | ... | ... | ... | ... |

**Total: [N] violations ([X] critical, [Y] medium, [Z] low)**

---

## 6. Remediation Plan

### Priority 1 — Critical (Fix Immediately)

#### R1: [Title] (fixes V1)

- **File**: `[exact path]`
- **Section**: [section name or line range]
- **What's Wrong**: [specific violation description]
- **Action**: [Remove / Add / Move / Replace]
- **Proposed Change**:

\```markdown
[Exact content to add, remove, or replace]
\```

- **Impact**: [What improves after this fix]

---

### Priority 2 — Medium (Fix This Sprint)

#### R2: [Title] (fixes V2)

[Same format as above]

---

### Priority 3 — Low (Backlog)

#### R3: [Title] (fixes V3)

[Same format as above]

---

## 7. Architecture Adaptation Recommendations

[Beyond fixing violations, these are structural improvements to better align with the layered architecture]

### 7.1 Content Migration Recommendations

| Source (Current Location) | Destination (Correct Layer) | Content to Move |
|---|---|---|
| [file in wrong layer] | [correct layer file] | [what to move] |

### 7.2 Missing Components

| What's Missing | Layer | Recommended Action |
|---|---|---|
| [e.g., verification loop] | L4 | [create/add specific content] |

### 7.3 Agent Workflow Improvements

[Specific recommendations for improving the P0-P5 workflow based on findings]

---

## 8. Compliance Trend (if previous reports exist)

[If a previous AGENT_ARCHITECTURE_COMPLIANCE_REPORT.md exists, compare scores]

| Metric | Previous | Current | Delta |
|---|---|---|---|
| Overall Score | [X.X] | [X.X] | [+/-X.X] |
| Critical Violations | [N] | [N] | [+/-N] |
| ... | ... | ... | ... |

---

## 9. Conclusion

[2-3 paragraphs: overall assessment, what the agent does well,
what the remediation plan will achieve, and expected score after fixes]

---

*Generated by `/audit-architecture-scope` | Audit date: {date}*
*Architecture baseline: Agent Router Pattern v2.0*
*Scoring weights: L0=5%, L1=20%, L2=25%, L3=20%, L4=30%*
```

---
