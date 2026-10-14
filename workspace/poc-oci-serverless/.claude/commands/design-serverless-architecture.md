---
description: Design or review OCI serverless architecture patterns following OCI Best Practices 2024. Use when designing a new serverless solution or reviewing an existing architecture (advisory).
argument-hint: "Scope: new design / review existing / evaluate specific concern"
context: fork
agent: oci-serverless-architect
background: false
disable-model-invocation: true
---

Execute this task now for the OCI serverless project. Read the referenced skill below for the canonical patterns, gather the "Required information", then carry the task through to completion. If the target below is empty, ask for the required information before proceeding.

**Request / target (from the user):** $ARGUMENTS

# Design Serverless Architecture

**Skill**: `architecting-oci-serverless`

## What this does

Designs or reviews serverless API backends using OCI Functions and API Gateway, producing architecture decisions, component diagrams, and implementation roadmaps.

## Required information

1. **Scope**:
   - New architecture design from scratch
   - Review and improve an existing architecture
   - Evaluate a specific concern (performance, security, cost, reliability)
2. **Components involved**: Which OCI services are in scope? (Functions, API Gateway, Streaming, Object Storage, Vault, etc.)
3. **Non-functional requirements**: Latency SLA, throughput, availability target, compliance constraints
4. **Business context**: What does this system do? (brief description of the domain)

## What will be delivered

- Architecture overview diagram (text-based)
- Component responsibility mapping
- Data flow description
- Security boundaries and blast radius analysis
- Scaling considerations and cold start mitigation
- Implementation roadmap with agent delegation (`@oci-terraform`, `@oci-functions-java`)
