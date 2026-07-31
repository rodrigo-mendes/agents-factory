# Always Do Patterns — AWS X-Ray Distributed Tracing (2026)

Source: [SKILL.md](../SKILL.md) | Research: 2026-07-31

---

## 1. Instrument new workloads with OpenTelemetry / ADOT (not the X-Ray SDK)

**Why**: The X-Ray SDK enters maintenance mode 2026-02-25 (security fixes only); all new features land in OpenTelemetry. Every new service should emit OTLP to a local collector; the `awsxray` exporter converts OTel spans to X-Ray segments and subsegments.

**OTel Collector config (minimal — sends traces to X-Ray)**:
```yaml
# otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: "0.0.0.0:4317"
      http:
        endpoint: "0.0.0.0:4318"

processors:
  batch:

exporters:
  awsxray:
    region: "us-east-1"
    # Uses the task/instance role — no explicit credentials needed on AWS

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [awsxray]
```

**Application environment variables (language-agnostic)**:
```bash
OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://localhost:4318/v1/traces
OTEL_PROPAGATORS=tracecontext,xray   # W3C default + X-Ray for AWS-native hops
OTEL_SERVICE_NAME=my-service
OTEL_RESOURCE_ATTRIBUTES=aws.log.group.names=/aws/ecs/my-service
```

**Required IAM permissions** (task role / instance profile):
```json
{
  "Effect": "Allow",
  "Action": [
    "xray:PutTraceSegments",
    "xray:PutTelemetryRecords",
    "xray:GetSamplingRules",
    "xray:GetSamplingTargets"
  ],
  "Resource": "*"
}
```

**Source**: [Migrating from X-Ray to OpenTelemetry](https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-migration.html) (2026-07-31)

---

## 2. Replace the X-Ray Daemon with the CloudWatch agent or OTel Collector

**Why**: The X-Ray Daemon is maintenance-mode; the CloudWatch agent (v1.300025.0+) consolidates metrics + logs + traces into one agent and receives OTLP on ports 4317/4318. The OTel Collector provides the same trace path with the `awsxray` exporter and optionally the `awsproxy` extension (for X-Ray remote sampling on UDP 2000).

**CloudWatch agent config snippet (trace section)**:
```json
{
  "traces": {
    "traces_collected": {
      "otlp": {
        "grpc_endpoint": "0.0.0.0:4317",
        "http_endpoint": "0.0.0.0:4318"
      },
      "xray": {
        "bind_address": "127.0.0.1:2000",
        "tcp_proxy": {
          "bind_address": "127.0.0.1:2000"
        }
      }
    }
  }
}
```

**OTel Collector config with awsproxy (X-Ray remote sampling)**:
```yaml
extensions:
  health_check:
    endpoint: "0.0.0.0:13133"
  awsproxy:
    endpoint: "0.0.0.0:2000"   # replaces X-Ray Daemon on the same port

receivers:
  otlp:
    protocols:
      grpc:
        endpoint: "0.0.0.0:4317"
      http:
        endpoint: "0.0.0.0:4318"

exporters:
  awsxray:
    region: "us-east-1"

service:
  extensions: [health_check, awsproxy]
  pipelines:
    traces:
      receivers: [otlp]
      exporters: [awsxray]
```

**Migration steps**:
1. Stop the existing X-Ray Daemon (free port 2000)
2. Deploy the CloudWatch agent or OTel Collector with the config above
3. Update `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT` on the application
4. Verify: `curl http://localhost:13133/` → `{"status":"Server available",...}`

**Source**: [X-Ray Daemon migration](https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-migration.html#xray-Daemon-migration) (2026-07-31)

---

## 3. Apply explicit sampling rules; reserve 100% for critical low-volume paths

**Why**: The default reservoir (1 req/sec + 5% additional) is intentionally conservative. Health-check and polling paths must sample low. State-changing/transactional endpoints may warrant 100%.

**AWS CLI — create a sampling rule (100% for checkout paths)**:
```bash
aws xray create-sampling-rule --cli-input-json '{
  "SamplingRule": {
    "RuleName": "checkout-100pct",
    "Priority": 1,
    "FixedRate": 1.0,
    "ReservoirSize": 10,
    "ServiceName": "checkout-service",
    "ServiceType": "*",
    "Host": "*",
    "HTTPMethod": "POST",
    "URLPath": "/checkout*",
    "ResourceARN": "*",
    "Version": 1
  }
}'
```

**AWS CLI — suppress health-check tracing**:
```bash
aws xray create-sampling-rule --cli-input-json '{
  "SamplingRule": {
    "RuleName": "suppress-healthcheck",
    "Priority": 2,
    "FixedRate": 0.0,
    "ReservoirSize": 0,
    "ServiceName": "*",
    "ServiceType": "*",
    "Host": "*",
    "HTTPMethod": "GET",
    "URLPath": "/health",
    "ResourceARN": "*",
    "Version": 1
  }
}'
```

**OTel SDK — enable X-Ray Remote Sampler (Java example)**:
```java
// Requires aws-opentelemetry-agent or ADOT Java SDK
// Set via environment variable — no code change needed:
// OTEL_TRACES_SAMPLER=xray
// OTEL_TRACES_SAMPLER_ARG=endpoint=http://localhost:2000
```

**Source**: [X-Ray sampling rules console](https://docs.aws.amazon.com/xray/latest/devguide/xray-console-sampling.html) (2026-07-31)

---

## 4. Put searchable business keys in annotations; bulk context in metadata

**Why**: Annotations are indexed and searchable via filter expressions; metadata is not. OTel spans use the `aws.xray.annotations` resource/span attribute to declare which span attributes X-Ray should index as annotations.

**OTel SDK — Python example**:
```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("process-order") as span:
    # Annotations — indexed, searchable (max 50 per trace)
    span.set_attribute("order_id", order.id)          # becomes annotation
    span.set_attribute("customer_id", order.customer)  # becomes annotation

    # Declare which attributes to index as X-Ray annotations:
    span.set_attribute(
        "aws.xray.annotations",
        "order_id,customer_id"  # comma-separated list
    )

    # Metadata — not indexed, not searchable, no cap
    span.set_attribute("request.body", json.dumps(order.items))
```

**X-Ray SDK equivalent (for existing code — do not use for new code)**:
```python
# ❌ Legacy pattern — maintenance mode; shown only for migration context
subsegment.put_annotation("order_id", order.id)      # indexed
subsegment.put_metadata("request_body", order.items) # not indexed
```

**Filter expression to verify**:
```bash
aws xray get-trace-summaries \
  --filter-expression 'annotation.order_id = "ORD-001"' \
  --start-time $(date -d '10 min ago' +%s) \
  --end-time $(date +%s)
```

**Source**: [X-Ray concepts — annotations and metadata](https://docs.aws.amazon.com/xray/latest/devguide/xray-concepts.html#xray-concepts-annotations) (2026-07-31)

---

## 5. Enable Transaction Search when 100% span visibility is required

**Why**: Head sampling can drop the single trace you need for a rare-error investigation or a compliance audit. Transaction Search ingests 100% of spans as structured logs into `aws/spans` and indexes a configurable percentage as X-Ray trace summaries, decoupling "capture everything" from "index everything."

**Enable via AWS CLI**:
```bash
# Enable Transaction Search on a CloudWatch log group
aws cloudwatch put-log-delivery-destination \
  --name xray-transaction-search \
  --delivery-destination-configuration \
    logGroupName=/aws/spans \
  --region us-east-1
```

**Enable via CDK (TypeScript)**:
```typescript
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';
import * as logs from 'aws-cdk-lib/aws-logs';

const spansLogGroup = new logs.LogGroup(this, 'SpansLogGroup', {
  logGroupName: '/aws/spans',
  retention: logs.RetentionDays.ONE_MONTH,
});

// Enable Transaction Search — done from the CloudWatch console
// or via the CloudWatch API (TransactionSearch enablement API).
// See: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Transaction-Search-ingesting-spans.html
```

**Key limits**:
- Max 10,000 spans per trace
- Spans stored in OTel semantic-convention format with W3C trace IDs
- PII masking: configure CloudWatch Logs data masking on the `aws/spans` log group
- Cost: 100% span ingestion adds CloudWatch Logs ingestion + indexing cost (verify on [CloudWatch pricing](https://aws.amazon.com/cloudwatch/pricing/))

**Source**: [CloudWatch Transaction Search](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Transaction-Search.html) (2026-07-31)

---

## 6. Encrypt trace data; use a customer-managed KMS key for regulated workloads

**Why**: Trace data can contain sensitive request context (user IDs, request paths, partial payloads). X-Ray supports customer-managed KMS encryption; AWS Config can track any change to the encryption configuration.

**Configure CMK encryption via AWS CLI**:
```bash
# Step 1 — create or identify your CMK
KMS_KEY_ARN="arn:aws:kms:us-east-1:123456789012:key/your-key-id"

# Step 2 — apply to X-Ray
aws xray put-encryption-config \
  --type KMS \
  --key-id "$KMS_KEY_ARN" \
  --region us-east-1

# Verify
aws xray get-encryption-config --region us-east-1
# Expected: "Type": "KMS", "KeyId": "<your-key-arn>", "Status": "ACTIVE"
```

**Required KMS grant on the key policy**:
```json
{
  "Effect": "Allow",
  "Principal": { "Service": "xray.amazonaws.com" },
  "Action": ["kms:GenerateDataKey", "kms:Decrypt"],
  "Resource": "*"
}
```

**AWS Config rule to detect non-CMK encryption** (managed rule):
```bash
aws configservice put-config-rule --config-rule '{
  "ConfigRuleName": "xray-kms-encryption-enabled",
  "Source": {
    "Owner": "CUSTOM_LAMBDA",
    "SourceDetails": [{ "EventSource": "aws.config", "MessageType": "ConfigurationItemChangeNotification" }]
  },
  "Scope": { "ComplianceResourceTypes": ["AWS::XRay::EncryptionConfig"] }
}'
```

**Transaction Search + PII masking**:
```bash
# Create a data masking policy on the aws/spans log group
aws logs put-data-protection-policy \
  --log-group-identifier /aws/spans \
  --policy-document file://pii-masking-policy.json
```

**Source**: [X-Ray encryption config + AWS Config](https://docs.aws.amazon.com/xray/latest/devguide/xray-api-config.html) (2026-07-31)
