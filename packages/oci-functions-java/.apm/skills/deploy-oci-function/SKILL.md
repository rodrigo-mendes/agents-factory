---
name: deploy-oci-function
description: "Deploys an OCI Function via the oci-deployer agent (P0-P6 workflow: preflight, build, push to OCIR, Terraform apply, smoke test, auto-fix, rollback). Use when deploying a new image version of an OCI Function to existing infrastructure."
argument-hint: "Function name or description [approve=tfplan sha256=<hash>] (e.g. 'func-rr-rest-proxy', 'deploy new version of event-producer with tag 0.0.5')"
context: fork
agent: oci-deployer
disable-model-invocation: true
---

Routes to the `oci-deployer` agent for OCI Function deployment lifecycle management.

The agent executes a 7-step workflow (P0-P6): validate prerequisites, identify target,
run pre-flight checks, build & push to OCIR, deploy via Terraform, smoke test,
and auto-fix or rollback on failure.

## What This Command Does

Delegates the full deployment lifecycle to `oci-deployer`:

- Validates Docker, OCI CLI session, and `.env` credentials
- Runs mandatory pre-flight checks (Dockerfile CMD, HTTP provider, no secrets in func.yaml)
- Builds Docker image and pushes to OCIR with version tag
- Updates `infra/environments/dev/terraform.tfvars`, plans, and applies the approved saved plan via Terraform (two-step flow below)
- Smoke tests the deployed endpoint (HTTP 200/400 = success, 502/503 = auto-fix cycle)
- Attempts up to 2 auto-fix cycles for known patterns before offering rollback
- Writes a `deploy-report.md` to `docs/handoff/<capability>/`

## Two-step apply flow (approval relay)

The agent runs forked and cannot ask you mid-run, so every apply is two launches:

1. `/deploy-oci-function <function>` — runs P0-P4 up to `terraform plan -input=false -out=tfplan` and `sha256sum tfplan`, then stops. `deploy-report.md` records `outcome: needs-input`, the plan summary (add/change/destroy), the plan file with its sha256 and the exact relaunch line.
2. After your own yes, relaunch with `/deploy-oci-function <function> approve=tfplan sha256=<hash>` — the agent verifies the hash of the existing `tfplan`; on a match it runs `terraform apply -input=false tfplan` without re-planning, then the smoke test. On a mismatch it applies nothing and returns a new plan (`needs-input`).

A rollback (P6) and every P5.5 auto-fix re-apply repeat the same two steps with a new plan and a new `approve=` line. `-auto-approve` is never used.

## Skills the agent loads

| Situation | Skill |
|---|---|
| Always | `deploying-oci-functions` |
| On P5 failure | `debugging-deployed-functions` |
| RMS/webhook function | `integrating-oracle-rms-webhooks` |

## Evaluation Scenarios

See [blueprints/evaluation-scenarios.md](./blueprints/evaluation-scenarios.md)
