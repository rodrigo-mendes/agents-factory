---
description: Install full serverless observability block (JSON Logs, Custom SDK Metrics, Distributed Tracing) in OCI Java Functions
argument-hint: Target function path, metric namespace, tracing strategy
context: fork
agent: oci-functions-java
background: false
disable-model-invocation: true
---

Execute this task now for the OCI serverless project. Read the referenced skill below for the canonical patterns, gather the "Required information", then carry the task through to completion. If the target below is empty, ask for the required information before proceeding.

**Request / target (from the user):** $ARGUMENTS

# Add Function Observability

**Skill**: `observing-oci-java-functions`

## What this does

Instruments an existing OCI Java Function with the complete enterprise Observability Block (the Three Pillars) in a single workflow:
1. **Logs**: Structured JSON with Logback, Logstash encoder, MDC context propagation, and OCI Logging configuration.
2. **Metrics**: Programmatic custom metrics (PostMetricData) using the OCI Monitoring SDK client and Resource Principal authentication.
3. **Tracing**: Distributed tracing via OpenTelemetry or OCI APM Java Agent in `func.yaml` and multi-stage Dockerfile.

## Required information

1. **Target Function**: Path to the existing Java function project folder where the observability block will be installed.
2. **Metric Namespace**: The custom monitoring namespace (e.g., `app_analytics`) to emit business and throughput metrics under.
3. **Tracing Strategy**: Do you want OpenTelemetry (portable, recommended) or native APM tracing?
4. **MDC Custom Fields**: Any business identifiers to propagate to both structured logs and APM spans (e.g., `customerId`, `orderId`)?
5. **Config & Secrets Strategy**: Are regional APM private data keys and metric endpoints retrieved from OCI Vault or from environment config?

## What will be generated

- Complete observability package dependencies in your Maven `pom.xml` (`slf4j`, `logback-classic`, `logstash-logback-encoder`, `oci-java-sdk-monitoring`, etc.)
- A modular `logback.xml` in `src/main/resources/` outputting structured JSON to stdout
- An `ObservabilityHelper` class or custom JDT class initializing cached SDK clients via `ResourcePrincipalAuthenticationDetailsProvider`
- Code transformations in your function's Entry Point/Handler class to handle the cold-start vs hot-invocation metadata logging and timing
- Custom metric-emission blocks with robust timeout budgets, ensuring metrics are sent before the function execution times out
- Multi-stage Dockerfile configurations tracking downstream tracing runtimes and APM keys
- Fully validated `func.yaml` setting up default environment variables for logs, metrics, and tracing
