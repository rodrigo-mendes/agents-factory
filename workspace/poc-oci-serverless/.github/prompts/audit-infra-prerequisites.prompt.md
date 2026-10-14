---
description: 'Audit infrastructure prerequisites for a specific pattern, verifying module existence and capabilities'
agent: oci-serverless-architect
argument-hint: 'Pattern document path and list of expected modules/capabilities'
---

# Audit Infrastructure Prerequisites

**Skill**: `architecting-oci-serverless`

## What this does

Audits the `infra/` directory against a pattern specification document to verify all required Terraform modules exist and have the necessary capabilities. Reports gaps with actionable remediation steps.

## Required information

1. **Pattern document path**: Path to the pattern spec (e.g., `docs/patterns/03-api-facade/03-api-facade.md`)
2. **Infrastructure directory**: Path to Terraform root (default: `infra/`)

## Mandatory verification steps

The agent MUST perform these checks (in order):

### Step 1 — Module Existence
```
list_dir infra/modules/
```
Compare directory listing against the pattern's "Módulos Terraform necessários" table. Mark each as ✅ EXISTS or ❌ MISSING.

### Step 2 — Module Capabilities
For each EXISTING module, read its `variables.tf` to verify it supports the required features:
- Does `functions` module support multi-function? (check for `var.functions`)
- Does `api-gateway` module support multi-backend? (check for `var.route_backends`)
- Does `iam` module include required policy statements?

### Step 3 — IAM Policy Coverage
Read `modules/iam/main.tf` and verify all required policy statements from the pattern spec are present.

### Step 4 — Gap Report
Produce a structured report:

| Module | Status | Gap | Remediation |
|--------|--------|-----|-------------|
| network | ✅ | — | — |
| vault | ❌ | Not provisioned | Use `/add-vault` prompt |

### Step 5 — Recommendations
- Priority classification: CRITICAL (blocks pattern) / RECOMMENDED / OPTIONAL
- Agent delegation: which agent + prompt to use for each remediation
- Dependency order: which gaps must be fixed first

## Critical rule

> **NEVER declare a module as MISSING without first running `list_dir` on `infra/modules/`.**
> The architect agent must ALWAYS verify physical directory existence before making claims about module availability.
