---
description: 'Generic entry point for OCI serverless architecture design and review. Collects design scope and existing components, then routes to the oci-serverless-architect agent.'
agent: oci-serverless-architect
argument-hint: 'Describe what you want to design or review'
---

# OCI Serverless Architecture Design

## Context Collection

Before starting, I need to understand your design request.

**Answer these questions:**

1. **What do you need?**
   - Design a new serverless architecture from scratch
   - Review an existing architecture for improvements
   - Evaluate a specific concern (security, performance, cost, reliability)

2. **Scope**:
   - Single function design
   - API surface design (set of routes and functions)
   - Full stack architecture (Functions + API Gateway + IAM + Networking + Vault)
   - Network topology review
   - Security model review

3. **Existing components**: What OCI resources are already in place? (Functions, API Gateway, VCN, Vault, etc.)

4. **Non-functional requirements**: Any specific constraints? (latency SLA, compliance, cost target, high availability)

## Workflow

Once I have your answers, I will follow the P0–P5 workflow:
- **P0**: Load relevant architecture/design skills
- **P1**: Analyze existing codebase (.tf and .java files)
- **P2**: Consult architecture patterns and OCI Best Practices 2024
- **P3**: Present architecture overview and recommendations
- **P4**: Deliver ADRs, diagrams, and implementation roadmap
- **P5**: Validate design against OCI Well-Architected Framework

> **Note**: This agent is advisory only. It will recommend which specialized agent to use for implementation (`@oci-terraform`, `@oci-functions-java`).
