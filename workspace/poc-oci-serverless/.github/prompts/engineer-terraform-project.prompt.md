---
description: 'Design or review Terraform project structure, module architecture, state management, and CI/CD governance for OCI'
agent: oci-terraform
argument-hint: 'Project scope, team size, environment strategy'
---

# Engineer Terraform Project

**Skill**: `engineering-terraform-oci`

## What this does

Designs or reviews Terraform project architecture for OCI workloads — directory layout, module decomposition, state isolation strategy, CI/CD pipeline design, and testing approach.

## Required information

1. **Project scope**: What OCI resources will be managed? (serverless, compute, database, networking)
2. **Environments**: How many environments? (dev, staging, prod)
3. **Team size**: How many engineers will contribute?
4. **State strategy**: Local state (POC) or remote backend (production)?
5. **CI/CD platform**: Azure DevOps, GitHub Actions, or GitLab CI?
6. **Module reuse**: Internal modules only or publish to registry?
7. **Testing requirements**: Validate-only or full apply integration tests?

## What will be delivered

- Directory layout recommendation (monorepo vs polyrepo)
- Module decomposition strategy
- State isolation boundaries (per-environment, per-service)
- CI/CD pipeline skeleton
- Testing strategy (static + plan-only + apply)
- Naming and tagging conventions
