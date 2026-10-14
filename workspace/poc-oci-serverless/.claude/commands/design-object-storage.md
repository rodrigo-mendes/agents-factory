---
description: Design OCI Object Storage architecture including bucket strategy, lifecycle policies, encryption, and event-driven pipelines
argument-hint: Data types, access patterns, retention requirements
context: fork
agent: oci-serverless-architect
background: false
disable-model-invocation: true
---

Execute this task now for the OCI serverless project. Read the referenced skill below for the canonical patterns, gather the "Required information", then carry the task through to completion. If the target below is empty, ask for the required information before proceeding.

**Request / target (from the user):** $ARGUMENTS

# Design Object Storage

**Skill**: `designing-oci-object-storage`

## What this does

Designs the Object Storage architecture for OCI workloads — bucket hierarchy, lifecycle policies, encryption strategy, access control, and event-driven integration patterns.

## Required information

1. **Data types**: What data will be stored? (logs, documents, media, backups, state files)
2. **Access patterns**: Frequent access, infrequent, or archive? Read-heavy or write-heavy?
3. **Retention requirements**: How long must data be retained? Regulatory constraints?
4. **Encryption needs**: Oracle-managed keys sufficient or customer-managed (Vault)?
5. **Event integration**: Need to trigger Functions on object create/update/delete?
6. **Access control**: Which services/functions need read/write access?
7. **Multi-region**: Cross-region replication needed for DR?
8. **Cost optimization**: Budget constraints for storage tier selection?

## What will be delivered

- Bucket hierarchy and naming strategy
- Storage tier recommendations (Standard vs Archive vs Infrequent Access)
- Lifecycle policy design (transition, expiration rules)
- Encryption strategy and key management
- Event-driven pipeline architecture (Object Storage → Events → Functions)
- IAM access control model
- Implementation guidance with `@oci-terraform` for provisioning
