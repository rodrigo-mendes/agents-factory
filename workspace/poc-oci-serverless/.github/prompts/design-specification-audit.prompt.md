---
description: 'Audit infrastructure and service directories against project documentation and copilot capabilities, producing an evolution specification'
agent: oci-serverless-architect
argument-hint: 'Project directories to audit, documentation sources, scope of review'
---

# Design Specification Audit

**Skill**: `architecting-oci-serverless`

## What this does

Audits existing infrastructure and service directories against project documentation, identifying gaps, missing modules, and deviations from best practices — then produces a structured evolution specification that can be executed by implementation agents.

## Required information

1. **Infrastructure directory**: Path to the infrastructure-as-code directory to audit (e.g., `infra/`, `terraform/`)
2. **Service directory**: Path to the application/function code directory to audit (e.g., `service/`, `functions/`)
3. **Documentation source**: Path to the project documentation that defines what SHOULD exist (e.g., architecture docs, ADRs, README)
4. **Copilot context directory**: Path to the `.github` directory containing agents, skills, and instructions that define implementation capabilities
5. **Audit scope**:
   - Full audit (all modules and services)
   - Infrastructure only (Terraform modules vs documented requirements)
   - Services only (function implementations vs documented capabilities)
   - Specific concern (e.g., security/Vault, networking, events)

## What will be delivered

- Gap analysis matrix: documented requirements vs implemented modules
- Missing modules identification with priority classification (critical / recommended / optional)
- Best practices deviation report per existing module
- Evolution specification for the infrastructure directory (what to add, modify, or restructure)
- Evolution specification for the service directory (what functions to add or update)
- Dependency map between infrastructure and service changes
- Implementation roadmap with agent delegation (`@oci-terraform` for infra, `@oci-functions-java` for services, `@oci-serverless-stack` for end-to-end)
