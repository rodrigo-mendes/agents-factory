---
description: Generic entry point for OCI Terraform provisioning. Collects what to provision, environment context, and compartment info, then routes to the oci-terraform agent.
argument-hint: Describe what OCI infrastructure you need to provision
context: fork
agent: oci-terraform
background: false
disable-model-invocation: true
---

Execute this task now for the OCI serverless project. Read the referenced skill below for the canonical patterns, gather the "Required information", then carry the task through to completion. If the target below is empty, ask for the required information before proceeding.

**Request / target (from the user):** $ARGUMENTS

# Provision Infrastructure

## Context Collection

Before starting, I need to understand your provisioning request.

**Answer these questions:**

1. **What do you need to provision?**
   - OCI Functions (Application + Function)
   - API Gateway (Gateway + Deployment + Routes)
   - IAM (Dynamic Groups + Policies)
   - Networking (VCN + Subnets + NSGs + Gateways)
   - Vault (Vault + Keys + Secrets)
   - Streaming (Stream Pool + Streams)
   - Event Rules (Event-driven automation)
   - Full serverless stack (Functions + API Gateway + IAM integrated)

2. **Environment**: Which environment is this for? (dev / staging / prod)

3. **Compartment**: Which OCI compartment will host these resources?

4. **Existing infrastructure**: Is there existing Terraform code in this workspace, or is this a new project?

## Workflow

Once I have your answers, I will follow the P0–P5 workflow:
- **P0**: Load the right provisioning skill(s)
- **P1**: Analyze existing .tf files
- **P2**: Consult skill patterns (✅/🚫 rules)
- **P3**: Propose a plan for your approval
- **P4**: Generate Terraform code
- **P5**: Validate with `terraform fmt` and `terraform validate`
