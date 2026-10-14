---
description: 'Setup structured logging in OCI Java Functions — framework selection, OCI Logging integration, MDC lifecycle'
agent: oci-functions-java
argument-hint: 'Logging framework preference, log routing needs'
---

# Setup Function Logging

**Skill**: `logging-oci-java-functions`

## What this does

Configures structured logging for OCI Java Functions — Java framework selection (SLF4J/Logback/Log4j2), stdout capture via OCI Log resources, programmatic ingestion via LoggingIngestionClient, and MDC lifecycle management.

## Required information

1. **Logging framework**: SLF4J + Logback (recommended), Log4j2, or java.util.logging?
2. **Log format**: JSON structured or plain text?
3. **Log routing**: stdout capture only, or programmatic OCI Logging ingestion?
4. **MDC fields**: Which context fields to propagate? (requestId, functionName, correlationId)
5. **Log levels**: Default level and per-package overrides?
6. **Separate log groups**: Audit logs separate from application logs?
7. **Downstream routing**: Forward to Logging Analytics or Object Storage?

## What will be generated

- Logging framework dependencies in pom.xml
- Configuration file (logback.xml or log4j2.xml)
- MDC initialization in @FnConfiguration
- Structured log format with JSON fields
- OCI Logging integration patterns
- Log level configuration for hot function model
