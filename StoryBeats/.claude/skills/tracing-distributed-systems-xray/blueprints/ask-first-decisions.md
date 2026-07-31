# Ask First Decisions — AWS X-Ray Distributed Tracing (2026)

Source: [SKILL.md](../SKILL.md) | Research: 2026-07-31

Present these options and **wait for the user's decision** before proceeding with implementation.

---

## Decision 1: Instrumentation Stack

**Ask**: "Must this tracing data also feed a non-AWS backend (Grafana/Datadog/Jaeger/OpenSearch)?"

| Option | AWS Services | Optimizes | Sacrifices | Best When |
|--------|-------------|-----------|------------|-----------|
| **Raw OTel SDK + `awsxray` exporter** | OTel Collector | Vendor-neutrality, portable exporter swap | Self-support collector config and upgrades | Multi-backend / multi-cloud tracing |
| **ADOT** | AWS Distro for OpenTelemetry | AWS-tested/secured, X-Ray Remote Sampler in more languages | Slightly behind upstream OTel releases | AWS-centric workloads; want AWS support SLA |
| **CloudWatch Application Signals** | Application Signals (ADOT/CW agent pre-packaged) | Fastest onboarding; SLOs + service topology out of the box | Most opinionated; highest AWS coupling | Teams wanting APM + SLO with least setup |

**Cost profile**:
- Raw OTel/ADOT: bill on X-Ray traces recorded + retrieved
- Application Signals: adds CloudWatch Logs ingestion and indexing cost (significantly higher at 100% span capture)

**Lock-in assessment**:
- Raw OTel → lowest (repoint the exporter to switch backends)
- ADOT → medium (AWS-tested OTel; still portable)
- Application Signals → highest (AWS-specific APM UX and `aws/spans` span-log model)

**Architect instruction**: If the answer to the multi-backend question is yes, use raw OTel/ADOT with a collector fan-out configuration — do not use Application Signals as the sole path.

**Application Signals ADOT config (sidecar, minimal)**:
```yaml
# Used when CloudWatch Application Signals is chosen
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: "0.0.0.0:4317"

exporters:
  awsxray:
    region: "us-east-1"
  awscloudwatchmetrics:
    region: "us-east-1"
    namespace: "ApplicationSignals"

service:
  pipelines:
    traces:
      receivers: [otlp]
      exporters: [awsxray]
    metrics:
      receivers: [otlp]
      exporters: [awscloudwatchmetrics]
```

**Raw OTel fan-out (multi-backend)**:
```yaml
exporters:
  awsxray:
    region: "us-east-1"
  otlp/datadog:
    endpoint: "https://trace.agent.datadoghq.com"
    headers:
      DD-API-KEY: "${DD_API_KEY}"
  # Add more exporters as needed

service:
  pipelines:
    traces:
      receivers: [otlp]
      exporters: [awsxray, otlp/datadog]
```

**Source**: [X-Ray SDK migration — OTel support options](https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-migration.html#opentelemetry-support) (2026-07-31)

---

## Decision 2: Sampling Strategy

**Ask**: "Is the pain missing error traces, or is it cost?"

| Option | AWS Services | Optimizes | Sacrifices | Best When |
|--------|-------------|-----------|------------|-----------|
| **Head sampling (X-Ray rules / Remote Sampler)** | X-Ray sampling rules | Simplicity; cost predictability | Cannot decide based on trace outcome (error/latency) | Uniform traffic; cost-first priority |
| **Tail sampling (OTel Collector `tailsamplingprocessor`)** | OTel Collector | Retains all error/slow traces regardless of rate | Collector memory + state + buffering complexity | Rare-error or latency-outlier debugging |
| **Transaction Search (100% ingest + bounded % index)** | CloudWatch Transaction Search (`aws/spans`) | No dropped spans; enables business-attribute correlation | Highest ingestion cost; AWS-specific | Compliance capture, business-attribute correlation |

**Cost profile**:
- Head sampling: cheapest (only sampled traces billed at $5.00/1M recorded)
- Tail sampling: moderate (buffering compute overhead in the collector)
- Transaction Search: highest (100% span ingestion adds CloudWatch Logs ingestion + indexing)

**Lock-in**:
- Tail sampling: OTel-portable (runs in the OTel Collector)
- Transaction Search: AWS-specific (`aws/spans` log group model)

**Tail sampling processor config (retain all 5xx and slow traces)**:
```yaml
processors:
  tail_sampling:
    decision_wait: 10s          # wait for all spans before deciding
    num_traces: 100000          # in-memory trace buffer
    expected_new_traces_per_sec: 10
    policies:
      - name: keep-errors
        type: status_code
        status_code:
          status_codes: [ERROR]
      - name: keep-slow-traces
        type: latency
        latency:
          threshold_ms: 5000    # keep traces > 5s
      - name: probabilistic-rest
        type: probabilistic
        probabilistic:
          sampling_percentage: 5  # 5% of the rest

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [tail_sampling]
      exporters: [awsxray]
```

**Note**: Tail sampling requires a **central gateway collector** — all spans of a trace must arrive at the same collector instance. See Decision 3.

**Source**: [X-Ray SDK migration — sampling](https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-migration.html#sampling) (2026-07-31)

---

## Decision 3: Collector Topology

**Ask**: "Is tail sampling required? What is the deployment model (ECS, EC2, EKS, serverless)?"

| Option | AWS Services | Optimizes | Sacrifices | Best When |
|--------|-------------|-----------|------------|-----------|
| **Sidecar collector** | ECS / EKS task sidecar | Isolation; per-service collector config | Resource duplication per task | Strong per-service tenancy; ECS/EKS |
| **Per-host agent** | CloudWatch agent on EC2 | Fewer agents to manage; unified metrics+logs+traces | Shared blast radius per host | EC2 and on-prem fleets |
| **Central gateway collector** | OTel Collector cluster behind NLB | Tail sampling; org-wide sampling policy | Network hop; gateway scaling complexity | Tail sampling required; org-wide policy |

**Sidecar (ECS task definition excerpt)**:
```json
{
  "name": "otel-collector",
  "image": "public.ecr.aws/aws-observability/aws-otel-collector:latest",
  "essential": false,
  "environment": [
    { "name": "AOT_CONFIG_CONTENT", "value": "<base64-encoded-config>" }
  ],
  "portMappings": [
    { "containerPort": 4317, "protocol": "tcp" },
    { "containerPort": 4318, "protocol": "tcp" }
  ]
}
```

**Application container links to the sidecar**:
```json
{
  "environment": [
    {
      "name": "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT",
      "value": "http://localhost:4318/v1/traces"
    }
  ],
  "links": ["otel-collector"]
}
```

**Central gateway (behind NLB — for tail sampling)**:
```yaml
# gateway-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: "0.0.0.0:4317"    # exposed via NLB
      http:
        endpoint: "0.0.0.0:4318"

processors:
  tail_sampling:
    decision_wait: 10s
    policies:
      - name: keep-errors
        type: status_code
        status_code: { status_codes: [ERROR] }
      - name: sample-rest
        type: probabilistic
        probabilistic: { sampling_percentage: 10 }

exporters:
  awsxray:
    region: "us-east-1"

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [tail_sampling]
      exporters: [awsxray]
```

**Decision rule**: If tail sampling is required → central gateway is mandatory. Otherwise: EC2/on-prem → per-host CloudWatch agent; ECS/EKS → sidecar per task.

**Source**: [X-Ray Daemon migration — topology](https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-migration.html#xray-Daemon-migration) (2026-07-31)
