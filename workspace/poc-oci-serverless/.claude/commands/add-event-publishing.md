---
description: Add event/message publishing capability to an existing OCI Function targeting Streaming, Notifications, Queue, Monitoring, or Logging
argument-hint: Target service (Streaming/Notifications/Queue/Monitoring/Logging) and existing function class
context: fork
agent: oci-functions-java
background: false
disable-model-invocation: true
---

Execute this task now for the OCI serverless project. Read the referenced skill below for the canonical patterns, gather the "Required information", then carry the task through to completion. If the target below is empty, ask for the required information before proceeding.

**Request / target (from the user):** $ARGUMENTS

# Add Event Publishing

**Skill**: `publishing-events-from-oci-functions`

## What this does

Adds the ability to publish events or messages from an existing OCI Function to OCI platform services using OCI Java SDK v3.x+.

## Required information

1. **Target service**: Where should events be published?
   - OCI Streaming (Kafka-compatible)
   - OCI Notifications (fan-out to subscribers)
   - OCI Queue (point-to-point messaging)
   - OCI Monitoring (custom metrics)
   - OCI Logging (structured log ingestion)
2. **Existing function class**: Which class to add publishing to?
3. **Message format**: What data will be published? (JSON structure or Java class)
4. **Volume**: Expected message rate? (affects batching strategy)

## What will be generated

- SDK client initialization with Resource Principal auth and client caching
- Message publishing method with proper serialization
- Batching support (for Streaming and Monitoring)
- Error handling with retry logic for transient failures
- Updated pom.xml with the relevant OCI SDK module dependency
