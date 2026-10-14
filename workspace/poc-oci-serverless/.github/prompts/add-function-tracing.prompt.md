---
description: 'Add APM distributed tracing to OCI Java Functions using OpenTelemetry or native APM tracer'
agent: oci-functions-java
argument-hint: 'Tracing strategy (OpenTelemetry or Native APM), APM domain details'
---

# Add Function Tracing

**Skill**: `observing-oci-java-functions`

## What this does

Instruments an existing OCI Java Function with distributed tracing using either the OpenTelemetry Java Agent or the native OCI APM Java Agent Tracer.

## Required information

1. **Tracing strategy**: OpenTelemetry Agent (standard, portable), OCI APM Agent (Oracle-native), or Manual Java Tracer SDK (low overhead)?
2. **Runtime Environment**: Java version (Java 11, 17, or 21) or custom Docker image?
3. **APM Domain Private Key**: Do you have the APM Private Data Key saved in OCI Vault (or local config)? *(Never use APM Public Core Key for server-side functions!)*
4. **Collector Endpoint**: The OTLP endpoint URL for your OCI APM domain.
5. **Target Function**: Path to the Maven project in the workspace to instrument.
6. **MDC/Context Correlation**: Do you want trace identifiers (traceId, spanId) propagated into your application logs?

## What will be generated

- Dockerfile modifications to fetch and configure the trace agent (OpenTelemetry Java Agent or APM Agent)
- Maven JVM options in `func.yaml` to bootstrap the tracer agent (`JVM_ARGS` with `-javaagent:...`)
- APM domain and trace key configuration environment variables in `func.yaml`
- Programmatic span instrumentation helpers in the handler code if utilizing the native Tracer SDK
- MDC correlation logging configuration in `logback.xml` or custom logging code
- Configuration validations to prevent cold-start crashes due to missing tracing parameters
