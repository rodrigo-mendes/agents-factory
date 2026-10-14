---
description: Execute a pattern specification document end-to-end, following its defined prompt sequence
argument-hint: Path to the pattern spec document (e.g., docs/patterns/03-api-facade/03-api-facade.md)
context: fork
agent: oci-serverless-stack
background: false
disable-model-invocation: true
---

Execute this task now for the OCI serverless project. Read the referenced skill below for the canonical patterns, gather the "Required information", then carry the task through to completion. If the target below is empty, ask for the required information before proceeding.

**Request / target (from the user):** $ARGUMENTS

# Execute Pattern

**Skills**: All skills referenced in the pattern document's "Sequência de Prompts" section.

## What this does

Reads a pattern specification document (from `docs/patterns/`) and executes its complete implementation workflow — from infrastructure audit through Java development, testing, and observability configuration.

## Required information

1. **Pattern document path**: Path to the pattern spec (e.g., `docs/patterns/03-api-facade/03-api-facade.md`)
2. **Environment**: Target environment (dev, staging, prod)
3. **OCIR namespace**: Docker registry namespace for function images
4. **Skip steps**: Any steps to skip if already completed (optional)

## Execution workflow

The agent will:

1. **Read the pattern spec** — Extract architecture, requirements, and prompt sequence
2. **Prompt 0 — Audit** — Verify all infrastructure prerequisites exist
3. **Prompt 1 — Terraform** — Provision/update infrastructure (function + routes)
4. **Prompt 2 — Java SDK** — Create service clients (Vault, Object Storage, etc.)
5. **Prompt 3 — Java Handler** — Create DTOs and handler with routing logic
6. **Prompt 4 — Tests** — Create unit tests per spec criteria
7. **Prompt 5 — Observability** — Configure logs and alarms

Each step follows the agent delegation defined in the pattern's "Sequência de Prompts" section.

## Validation criteria

From the pattern's "Critérios de Verificação" section:
- All specified tests must pass (`mvn clean package`)
- `terraform validate` must succeed
- `terraform plan` must show only additive changes (no destroy)

## Error handling

If a step fails:
1. Log the error and solution to `docs/patterns/{pattern}/IMPLEMENTATION-LOG.md`
2. Attempt fix based on error type
3. Re-run validation
4. Continue to next step only after current step passes
