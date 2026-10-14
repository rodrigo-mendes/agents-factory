---
description: Design OCI Connector Hub data pipeline architecture for log routing, metrics derivation, and event processing
argument-hint: Data sources, processing needs, target destinations
context: fork
agent: oci-observability
background: false
disable-model-invocation: true
---

Execute this task now for the OCI serverless project. Read the referenced skill below for the canonical patterns, gather the "Required information", then carry the task through to completion. If the target below is empty, ask for the required information before proceeding.

**Request / target (from the user):** $ARGUMENTS

# Design Connector Hub

**Skill**: `designing-oci-connector-hub`

## What this does

Designs data pipeline architecture using OCI Service Connector Hub — routing logs to storage, deriving custom metrics, integrating with external SIEMs, and building event processing pipelines.

## Required information

1. **Data sources**: What data needs routing? (Logs, Streaming messages, Queue messages)
2. **Processing needs**: Pass-through, filtering, or function-based transformation?
3. **Target destinations**: Where should data flow? (Object Storage, Logging Analytics, Functions, Monitoring, Notifications)
4. **Throughput**: Expected data volume (messages/sec, GB/day)?
5. **Latency tolerance**: Near-real-time or batch acceptable?
6. **Fan-out**: Single source to multiple targets needed?
7. **Error handling**: DLQ or retry requirements?

## What will be delivered

- Data pipeline topology diagram (source → task → target)
- Service Connector configuration strategy
- IAM policy requirements for connector service principal
- Batching and throughput optimization recommendations
- Error handling and monitoring strategy
- Multi-connector composition for complex pipelines
- Provisioning handoff to `@oci-observability` (`/add-apm-dashboards`, `/add-apm-infrastructure`, `/add-logging`, `/add-connector-hub`)
