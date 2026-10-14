---
description: Build, push, deploy, and validate an OCI Function — full deployment lifecycle with pre-flight checks. Use when deploying a new version of an existing function to OCI.
argument-hint: Function name or path to service directory
context: fork
agent: oci-deployer
background: false
disable-model-invocation: true
---

Execute this task now for the OCI serverless project. Read the referenced skill below for the canonical patterns, gather the "Required information", then carry the task through to completion. If the target below is empty, ask for the required information before proceeding.

**Request / target (from the user):** $ARGUMENTS

# Deploy Function

**Skill**: `deploying-oci-functions`

## What this does

Executes the full deployment lifecycle for an OCI Function: pre-flight validation, Docker build, push to OCIR, Terraform deploy, and smoke testing.

## Required information

1. **Function**: Which function to deploy? (name or path in `services/`)
2. **Registry**: OCIR region and repository (usually from `.env`)
3. **Image tag**: Version tag for the image (or use `latest`)
4. **Deploy method**: Terraform apply or fn CLI?
5. **Smoke test**: Run invoke test after deploy?

## Workflow executed (P0-P6)

1. **P0**: Validate prerequisites (Docker, OCI CLI, .env)
2. **P1**: Identify target function
3. **P2**: Pre-flight checks (Dockerfile CMD, SDK deps, no secrets)
4. **P3**: Build & push Docker image to OCIR
5. **P4**: Deploy (update function image digest via Terraform)
6. **P5**: Smoke test (invoke function, validate response)
7. **P6**: Report deployment summary
