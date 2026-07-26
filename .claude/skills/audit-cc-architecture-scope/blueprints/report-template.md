# Claude Code Architecture Compliance Report — Template

# Claude Code Architecture Compliance Report
## Target: {target-name} | Audit Date: {date}

---

## 1. Executive Summary

[2-3 paragraphs: what the target does, overall compliance assessment,
most critical finding, and recommended immediate action]

### Compliance Verdict: {✅ PASS | ⚠️ CONDITIONAL | ❌ FAIL}

### Score Summary

| Layer | Score | Status | Critical Issues |
|---|---|---|---|
| G0 — CLAUDE.md (Global) | [X/10] | [✅/⚠️/❌] | [count] |
| G1 — Subagent | [X/10] | [✅/⚠️/❌] | [count] |
| G2 — Rules (paths:) | [X/10] | [✅/⚠️/❌] | [count] |
| G3 — Commands | [X/10] | [✅/⚠️/❌] | [count] |
| G4 — Skills | [X/10] | [✅/⚠️/❌] | [count] |
| G-perm — settings.json | [X/10] | [✅/⚠️/❌] | [count] |
| **Overall (weighted)** | **[X.X/10]** | **[Verdict]** | **[total]** |

---

## 2. File Inventory & Dependency Graph

### Files Analyzed

| # | Layer | File | Lines | Class | Status |
|---|---|---|---|---|---|
| 1 | G0 | CLAUDE.md | [N] | — | Analyzed |
| 2 | G1 | .claude/agents/{target}.md | [N] | subagent | Analyzed |
| 3 | G2 | .claude/rules/{rule}.md | [N] | paths: {glob} | Analyzed |
| 4 | G3 | .claude/skills/{cmd}/SKILL.md | [N] | command (disable-model-invocation) | Analyzed |
| 5 | G4 | .claude/skills/{skill}/SKILL.md | [N] | knowledge (auto-invocable) | Analyzed |
| ... | ... | ... | ... | ... | ... |

### Dependency Graph

```
{target-name}
├── CLAUDE.md (G0 — always-on)
├── .claude/agents/{target}.md (G1 — subagent)
│   ├── .claude/rules/{rule-1}.md (G2 — paths: {glob})
│   │   └── .claude/skills/{skill-1}/SKILL.md (G4 — knowledge)
│   ├── .claude/skills/{cmd-1}/SKILL.md (G3 — command, forks here)
│   │   └── .claude/skills/{skill-2}/SKILL.md (G4 — knowledge)
│   └── .claude/settings.json (G-perm — governance)
└── Orphans: [list or "none"]
```

---

## 3. Per-Layer Analysis

### 3.1 G0 — CLAUDE.md

| # | Criterion | Result | Evidence |
|---|---|---|---|
| G0.1 | Project-scoped only | [✅/⚠️/❌] | [specific evidence from file] |
| ... | ... | ... | ... |

**Layer Score: [X/10]**

### 3.2 G1 — Subagent

| # | Criterion | Result | Evidence |
|---|---|---|---|
| G1.1 | Router/specialist purity | [✅/⚠️/❌] | [specific evidence from file] |
| ... | ... | ... | ... |

**Layer Score: [X/10]**

### 3.3 G2 — Rules

[Repeat per rule file]

#### {rule-filename}.md (paths: {glob})

| # | Criterion | Result | Evidence |
|---|---|---|---|
| G2.1 | paths: specificity | [✅/⚠️/❌] | [specific evidence] |
| ... | ... | ... | ... |

**Layer Aggregate Score: [X/10]**

### 3.4 G3 — Commands

[Repeat per command SKILL.md — those with disable-model-invocation: true]

**Layer Aggregate Score: [X/10]**

### 3.5 G4 — Skills

[Repeat per knowledge SKILL.md — those without disable-model-invocation]

**Layer Aggregate Score: [X/10]**

### 3.6 G-perm — settings.json

[Permission coherence: allowed-tools skills need aren't denied; no dead permissions]

**Layer Score: [X/10]**

---

## 4. Cross-Layer Validation

| # | Check | Result | Details |
|---|---|---|---|
| XCC.1 | Keyword alignment | [✅/⚠️/❌] | [CLAUDE.md ↔ command ↔ subagent description mismatches] |
| XCC.2 | Responsibility leakage | [✅/⚠️/❌] | [where code was found in wrong layer] |
| XCC.3 | Skill reachability | [✅/⚠️/❌] | [unreachable skills listed] |
| XCC.4 | Link chain integrity | [✅/⚠️/❌] | [broken links listed] |
| XCC.5 | Naming consistency | [✅/⚠️/❌] | [name != folder/filename, non-kebab-case] |
| XCC.6 | Rule coverage gaps | [✅/⚠️/❌] | [rules firing with no skill/guidance] |
| XCC.7 | Orphan detection | [✅/⚠️/❌] | [orphan files; note G4 reachable via description] |
| XCC.8 | Duplication detection | [✅/⚠️/❌] | [duplicated content locations] |
| XCC.9 | Field-swap check | [✅/⚠️/❌] | [tools: on skill / allowed-tools: on subagent] |
| XCC.10 | G3/G4 classification | [✅/⚠️/❌] | [mis-classified SKILL.md by frontmatter] |

---

## 5. Violations Summary

| # | Severity | Criterion | File | Description |
|---|---|---|---|---|
| V1 | 🔴 Critical | [G1.2] | [file] | [description] |
| V2 | 🟡 Medium | [G2.4] | [file] | [description] |
| V3 | 🟢 Low | [G4.6] | [file] | [description] |
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

```markdown
[Exact content to add, remove, or replace]
```

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

### 7.1 Content Migration Recommendations

| Source (Current Location) | Destination (Correct Layer) | Content to Move |
|---|---|---|
| [file in wrong layer] | [correct layer file] | [what to move] |

### 7.2 Missing Components

| What's Missing | Layer | Recommended Action |
|---|---|---|
| [e.g., verification loop] | G4 | [create/add specific content] |

### 7.3 Subagent Workflow Improvements

[Specific recommendations for improving the P0-P5 / fan-out workflow based on findings]

---

## 8. Conclusion

[2-3 paragraphs: overall assessment, what the target does well,
what the remediation plan will achieve, and expected score after fixes]

---

*Generated by `/audit-cc-architecture-scope` | Audit date: {date}*
*Architecture baseline: Skill (`/command`) → Subagent → Rules → Skills*
*Scoring weights: G0=5%, G1=20%, G2=20%, G3=20%, G4=30%, G-perm=5%*
