### ⚠️ Ask First

**Decision Point**: Event source type selection

Which OCI service triggers this function?

**Available Options**:

| Option | Optimizes For | Sacrifices | Choose When |
|--------|--------------|-----------|-------------|
| `APIGatewayFunction<Req, Res>` | Type-safe HTTP, query params, headers, status codes | Flexibility | Function is API Gateway backend (sync request/response) |
| `ConnectorHubFunction<T>` | Batch efficiency, typed event data | Response control (void handler) | SCH target (Monitoring/Logging/Streaming/Queue) |
| `NotificationFunction<T>` | Single message typing, header access | Batch processing | OCI Notification topic subscription |
| Raw `handleRequest` | Full control, no extra deps | Manual JSON parsing | Direct invocation, multiple trigger types |

**Agent Behavior**:
"Before implementing, ask the user:
'What OCI service triggers this function? (API Gateway / Service Connector Hub / Notifications / Direct invocation)'"

**Decision Factors**:
- API Gateway → synchronous HTTP request/response pattern
- Service Connector Hub → asynchronous batch event processing
- Notifications → asynchronous single message processing
- Direct → no OCI service envelope, raw FDK handler

**Source**: [fn-events README](https://github.com/fnproject/fdk-java/blob/master/fn-events/README.md)

---

**Decision Point**: ConnectorHubFunction data type

What is the Service Connector Hub source service?

**Available Options**:

| Option | Optimizes For | Sacrifices | Choose When |
|--------|--------------|-----------|-------------|
| `ConnectorHubFunction<MetricData>` | Pre-defined metric schema | Custom fields | Processing OCI Monitoring metrics |
| `ConnectorHubFunction<LoggingData>` | Pre-defined log schema | Custom fields | Processing OCI audit/service logs |
| `ConnectorHubFunction<StreamingData<T>>` | Auto base64 decode, typed value | Simplicity | Processing OCI Streaming messages |
| `ConnectorHubFunction<T>` (custom) | Full control of schema | Platform metadata | OCI Queue messages with custom JSON |

**Agent Behavior**:
"Before implementing, ask the user:
'What is the Service Connector Hub source? (Monitoring / Logging / Streaming / Queue)'"

**Decision Factors**:
- Monitoring → `MetricData` provides typed access to OCI metric fields and datapoints
- Logging → `LoggingData` provides typed access to audit/service log entries
- Streaming → `StreamingData<T>` auto-decodes base64 value to generic type T
- Queue → custom type T receives direct JSON message body

**Source**: [Connector Hub Monitoring Example](https://github.com/fnproject/fdk-java/blob/master/examples/connectorhub-monitoring/README.md)

---

**Decision Point**: Error handling strategy for batch functions

How should the function handle partial batch failures?

**Available Options**:

| Option | Optimizes For | Sacrifices | Choose When |
|--------|--------------|-----------|-------------|
| Fail-fast (throw on first error) | Data consistency, simple logic | Batch throughput, causes duplicate processing | All-or-nothing semantics required |
| Fail-safe (log errors, continue) | Throughput, partial success | Failed items lost | Non-critical events, best-effort processing |
| Dead-letter (collect failures, report) | Visibility, no data loss | Complexity | Critical data, audit requirements |

**Agent Behavior**:
"Before implementing batch error handling, ask the user:
'Are partial batch failures acceptable? Does the batch need all-or-nothing semantics?'"

**Decision Factors**:
- Data criticality (can individual events be lost?)
- Retry behavior (SCH retries entire batch on 502)
- Processing idempotency (can items be safely reprocessed?)

**Source**: [SCH Overview](https://docs.oracle.com/en-us/iaas/Content/connector-hub/overview.htm#deactivate)

---

**Decision Point**: API Gateway function error response strategy

How should the API Gateway function respond to errors?

**Available Options**:

| Option | Optimizes For | Sacrifices | Choose When |
|--------|--------------|-----------|-------------|
| Return `APIGatewayResponseEvent` with 4xx/5xx | Client-friendly errors, custom error body | Slightly more code | API endpoints with error contracts |
| Throw `RuntimeException` | Simplicity | No structured error response (raw 502) | Unexpected/unrecoverable failures only |

**Agent Behavior**:
"For API Gateway functions, always prefer returning typed error responses for expected failures (validation, not found, unauthorized). Use RuntimeException only for unexpected crashes."

**Source**: [API Gateway Example](https://github.com/fnproject/fdk-java/blob/master/examples/apigateway-event/README.md)

---

