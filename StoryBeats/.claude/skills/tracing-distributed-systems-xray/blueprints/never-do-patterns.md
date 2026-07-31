# Never Do Patterns — AWS X-Ray Distributed Tracing (2026)

Source: [SKILL.md](../SKILL.md) | Research: 2026-07-31

Each entry shows the ❌ wrong pattern, the ✅ correct alternative, and the impact of the mistake.

---

## 1. Build new instrumentation on the X-Ray SDK / X-Ray Daemon

**Risk level**: HIGH
**Pillar**: Operational Excellence
**Why prohibited**: The X-Ray SDK and X-Ray Daemon enter maintenance mode 2026-02-25 (security fixes only; no new features). End-of-support is 2027-02-25. Building on them now creates forced re-platform debt.

**Detection**: Grep build manifests for `aws-xray-sdk*`; inventory ECS/EC2 tasks running `aws-xray-daemon`.

```python
# ❌ WRONG — new microservice still using the X-Ray SDK
import aws_xray_sdk.core as xray
from aws_xray_sdk.ext.flask.middleware import XRayMiddleware

xray.configure(service='order-service', daemon_address='localhost:2000')
app = Flask(__name__)
XRayMiddleware(app, xray)
```

```yaml
# ❌ WRONG — ECS task definition with X-Ray Daemon sidecar
{
  "name": "xray-daemon",
  "image": "amazon/aws-xray-daemon",
  "portMappings": [{ "containerPort": 2000, "protocol": "udp" }]
}
```

```python
# ✅ CORRECT — new microservice using OpenTelemetry (ADOT)
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

provider = TracerProvider()
provider.add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(
        endpoint="http://localhost:4318/v1/traces"
    ))
)
trace.set_tracer_provider(provider)
```

```yaml
# ✅ CORRECT — ECS task definition with OTel Collector sidecar
{
  "name": "otel-collector",
  "image": "public.ecr.aws/aws-observability/aws-otel-collector:latest",
  "portMappings": [
    { "containerPort": 4317, "protocol": "tcp" },
    { "containerPort": 4318, "protocol": "tcp" }
  ]
}
```

**Impact**: Deprecation debt, missed OTel features, forced re-platform at EOS deadline (2027-02-25).

**Source**: [X-Ray SDK and Daemon Support timeline](https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-daemon-timeline.html) (2026-07-31)

---

## 2. Trace 100% of high-volume requests without a sampling plan

**Risk level**: MEDIUM (cost) / HIGH at scale
**Pillar**: Cost Optimization
**Why prohibited**: Recorded traces are billed at $5.00/1M. A service receiving 50k requests/second with `AlwaysOn` sampler records ~4.3 billion traces/day — approximately $21,500/day. Health-check and polling traffic adds noise to the service map.

**Detection**: Monitor `TracesRecorded` CloudWatch metric; alert on anomalous growth vs. request volume.

```python
# ❌ WRONG — AlwaysOn sampler on a high-volume service
from opentelemetry.sdk.trace.sampling import ALWAYS_ON

provider = TracerProvider(sampler=ALWAYS_ON)
```

```bash
# ❌ WRONG — no sampling rules, relying on default for all paths including /health
# (default is 1/sec + 5% — still records health checks at 5% rate)
```

```python
# ✅ CORRECT — let X-Ray Remote Sampler apply per-rule decisions
import os
os.environ["OTEL_TRACES_SAMPLER"] = "xray"
os.environ["OTEL_TRACES_SAMPLER_ARG"] = "endpoint=http://localhost:2000"
# Collector must have the awsproxy extension running on port 2000
```

```bash
# ✅ CORRECT — suppress health-check paths via sampling rule
aws xray create-sampling-rule --cli-input-json '{
  "SamplingRule": {
    "RuleName": "suppress-healthcheck",
    "Priority": 1,
    "FixedRate": 0.0,
    "ReservoirSize": 0,
    "ServiceName": "*",
    "HTTPMethod": "GET",
    "URLPath": "/health",
    "ResourceARN": "*",
    "Version": 1
  }
}'
```

**Impact**: Cost overrun; noisy service map that hides real latency/error signals.

**Source**: [X-Ray concepts — sampling](https://docs.aws.amazon.com/xray/latest/devguide/xray-concepts.html#xray-concepts-sampling) + [AWS X-Ray pricing](https://aws.amazon.com/xray/pricing/) (2026-07-31)

---

## 3. Trust inbound `X-Amzn-Trace-Id` from untrusted clients

**Risk level**: HIGH
**Pillar**: Security
**Why prohibited**: A client-controlled tracing header can forge trace IDs (causing trace ID collisions or poisoning existing traces) and manipulate the `Sampled=1` flag (forcing 100% sampling on expensive paths). `X-Forwarded-For` client IPs in the header can also be forged.

**Detection**: Inspect API Gateway / ALB configuration; confirm that the entry service regenerates the tracing header rather than forwarding the client-supplied value.

```python
# ❌ WRONG — forwarding inbound X-Amzn-Trace-Id to downstream services
# (happens automatically if you do not strip it at the edge)
@app.route('/api/orders', methods=['POST'])
def create_order():
    # X-Amzn-Trace-Id from the client is already in request.headers
    # and will be forwarded by the OTel propagator as-is
    return process_order(request)
```

```python
# ✅ CORRECT — strip and regenerate at the trust boundary
# API Gateway active tracing strips client-provided X-Amzn-Trace-Id and
# injects its own. For services behind a custom edge, strip it explicitly:

from opentelemetry.propagators.aws.aws_xray_propagator import AwsXRayPropagator

@app.before_request
def strip_inbound_trace_header():
    # Remove any client-supplied tracing header before propagation
    if 'X-Amzn-Trace-Id' in request.headers:
        # Mutable headers object — strip before OTel propagation reads it
        del request.environ['HTTP_X_AMZN_TRACE_ID']
        # OTel will create a new root trace for this request
```

```yaml
# ✅ CORRECT — API Gateway active tracing (AWS strips client headers)
# aws_apigateway_stage.tf
resource "aws_api_gateway_stage" "main" {
  xray_tracing_enabled = true   # AWS Gateway mints the root trace; client header ignored
}
```

**Impact**: Trace poisoning, sampling manipulation (cost spike), misleading forensic data.

**Source**: [X-Ray concepts — tracing header](https://docs.aws.amazon.com/xray/latest/devguide/xray-concepts.html#xray-concepts-tracingheader) (2026-07-31)

---

## 4. Store searchable high-cardinality keys in metadata

**Risk level**: MEDIUM
**Pillar**: Operational Excellence
**Why prohibited**: X-Ray metadata is NOT indexed; filter expressions like `metadata.order_id = "123"` are not supported. You cannot pivot from a CloudWatch alarm to the affected trace by business key unless it is stored as an annotation.

**Detection**: Review instrumentation code for `putMetadata` / `set_attribute` on business keys; test filter expressions in the X-Ray console before production cutover.

```python
# ❌ WRONG — searchable business key stored as metadata (not indexed)
subsegment.put_metadata("order_id", order.id)
subsegment.put_metadata("customer_id", order.customer_id)
# Later: aws xray get-trace-summaries --filter-expression 'metadata.order_id = "ORD-001"'
# → Returns nothing (metadata is not indexed)
```

```python
# ❌ WRONG — OTel span attribute not declared as annotation
span.set_attribute("order_id", order.id)
# Without aws.xray.annotations, order_id becomes metadata in X-Ray
```

```python
# ✅ CORRECT — annotation for searchable keys (max 50 per trace)
subsegment.put_annotation("order_id", order.id)        # indexed
subsegment.put_annotation("customer_id", order.customer_id)  # indexed
subsegment.put_metadata("request_payload", order.items) # bulk context — metadata OK
```

```python
# ✅ CORRECT — OTel span with aws.xray.annotations declaration
span.set_attribute("order_id", order.id)
span.set_attribute("customer_id", order.customer_id)
span.set_attribute("request_payload", json.dumps(order.items))   # metadata
span.set_attribute(
    "aws.xray.annotations",
    "order_id,customer_id"  # declares which attrs to index as annotations
)
```

**Verification** (run after instrumentation):
```bash
aws xray get-trace-summaries \
  --filter-expression 'annotation.order_id = "ORD-001"' \
  --start-time $(date -d '5 min ago' +%s) \
  --end-time $(date +%s)
# Expected: matching trace returned
```

**Impact**: Slow MTTR — cannot correlate a business event (payment failure, order error) with its trace.

**Source**: [X-Ray concepts — annotations and metadata](https://docs.aws.amazon.com/xray/latest/devguide/xray-concepts.html#xray-concepts-annotations) (2026-07-31)

---

## 5. Leave trace encryption on the default AWS-owned key for regulated workloads

**Risk level**: MEDIUM (context-dependent; HIGH under PCI/HIPAA)
**Pillar**: Security / Compliance
**Why prohibited**: Regulated workloads (PCI DSS, HIPAA) require customer control over encryption key rotation and auditable change tracking. The default AWS-owned key provides no key-rotation ownership and no AWS Config change history.

**Detection**: `aws xray get-encryption-config` returns `"Type": "NONE"` (no encryption) or `"Type": "KMS"` with an AWS-managed key (not a customer-managed key ARN in your account).

```bash
# ❌ WRONG — default AWS-owned encryption, no AWS Config tracking
aws xray get-encryption-config
# Returns: { "EncryptionConfig": { "Type": "NONE", "Status": "ACTIVE" } }
# Trace data for a PCI-scoped workload — no CMK, no Config rule
```

```bash
# ✅ CORRECT — Step 1: Create or identify CMK
KMS_KEY_ARN=$(aws kms create-key \
  --description "X-Ray trace encryption" \
  --query 'KeyMetadata.Arn' --output text)

aws kms create-alias \
  --alias-name alias/xray-traces \
  --target-key-id "$KMS_KEY_ARN"

# Step 2: Grant X-Ray access to the CMK
aws kms put-key-policy \
  --key-id "$KMS_KEY_ARN" \
  --policy-name default \
  --policy '{
    "Version":"2012-10-17",
    "Statement":[{
      "Effect":"Allow",
      "Principal":{"Service":"xray.amazonaws.com"},
      "Action":["kms:GenerateDataKey","kms:Decrypt"],
      "Resource":"*"
    },{
      "Effect":"Allow",
      "Principal":{"AWS":"arn:aws:iam::123456789012:root"},
      "Action":"kms:*",
      "Resource":"*"
    }]
  }'

# Step 3: Apply to X-Ray
aws xray put-encryption-config \
  --type KMS \
  --key-id "$KMS_KEY_ARN"

# Step 4: Verify
aws xray get-encryption-config
# Expected: "Type": "KMS", "KeyId": "<your-key-arn>", "Status": "ACTIVE"
```

```hcl
# ✅ CORRECT — Terraform (IaC enforcement)
resource "aws_xray_encryption_config" "this" {
  type   = "KMS"
  key_id = aws_kms_key.xray_traces.arn
}

resource "aws_kms_key" "xray_traces" {
  description             = "X-Ray trace data encryption"
  enable_key_rotation     = true
  deletion_window_in_days = 30
}
```

**Impact**: Compliance violation (PCI/HIPAA audit finding); unmanaged key exposure; no config-change audit trail.

**Source**: [X-Ray encryption config + AWS Config](https://docs.aws.amazon.com/xray/latest/devguide/xray-api-config.html) (2026-07-31)
