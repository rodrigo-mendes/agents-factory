# Always Do Patterns — observing-aws-cloudwatch

> Full detail for the 5 mandatory patterns summarized in SKILL.md.
> Source: research_cloud_AWS_Observability-CloudWatch_2026.md (accessed 2026-07-31)

---

## 1. Set Explicit Log-Group Retention

**Pillar alignment**: Operational Excellence + Cost Optimization

**Why**: CloudWatch Logs retains data forever by default. `retentionInDays == null` means unbounded
`TimedStorage-ByteHrs` billing and potential compliance exposure for undeleted PII/audit data.

**Decision table**:

| Data Class | Recommended Retention | Log Class |
|---|---|---|
| Operational / application logs | 30–90 days | Standard |
| Security / access logs | 90–365 days | Standard or Infrequent Access |
| Compliance / audit logs | 1–7 years | Infrequent Access or Archive Instant Access |

**IaC (AWS CDK — TypeScript)**:
```typescript
import * as logs from 'aws-cdk-lib/aws-logs';

// ✅ Always set retention on every log group
const appLogGroup = new logs.LogGroup(this, 'AppLogs', {
  logGroupName: '/myapp/prod/app',
  retention: logs.RetentionDays.THREE_MONTHS,  // 90 days Standard
});

const auditLogGroup = new logs.LogGroup(this, 'AuditLogs', {
  logGroupName: '/myapp/prod/audit',
  retention: logs.RetentionDays.THREE_YEARS,   // 1095 days
  // Move to Infrequent Access log class for cost savings
});
```

**CLI — set retention on an existing log group**:
```bash
aws logs put-retention-policy \
  --log-group-name /myapp/prod/app \
  --retention-in-days 90
```

**Verification**:
```bash
# Must return [] in production accounts
aws logs describe-log-groups \
  --query 'logGroups[?retentionInDays==`null`].logGroupName'
```

**Enforcement**: Add an AWS Config managed rule or an Organizations SCP to deny log-group creation
without `retentionInDays`. Example AWS Config rule: `cloudwatch-log-group-retention-period-check`.

---

## 2. Alarm on Sustained Breaches: M-out-of-N + Explicit TreatMissingData

**Pillar alignment**: Operational Excellence + Reliability

**Why**: CloudWatch alarms act only on sustained state changes across the evaluation window. A single
breaching data point does not trigger `ALARM` state. Misconfigured `TreatMissingData` or a `period`
shorter than the metric resolution produces chronic `INSUFFICIENT_DATA` and silent outages.

**Key rules**:
- `period >= metric native resolution` (e.g. ≥300s for EC2 5-min basic monitoring)
- `DatapointsToAlarm` = M in M-out-of-N to avoid single-spike pages (e.g. 3 out of 3)
- `TreatMissingData`:
  - `breaching` — use when no data means the resource is down (heartbeat alarm)
  - `notBreaching` — use when no data means the resource is idle/detached (expected silence)
  - `ignore` — use inside a composite alarm member where you want state to persist
  - `missing` (default) — only acceptable when explicitly decided; document intent

**AWS CLI — create a correctly configured alarm**:
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name "prod-checkout-error-rate" \
  --namespace "AWS/ApplicationELB" \
  --metric-name "HTTPCode_Target_5XX_Count" \
  --dimensions Name=LoadBalancer,Value=app/prod-alb/abc123 \
  --statistic Sum \
  --period 300 \
  --evaluation-periods 3 \
  --datapoints-to-alarm 3 \
  --threshold 10 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --treat-missing-data notBreaching \
  --alarm-actions arn:aws:sns:us-east-1:123456789012:prod-alerts
```

**Composite alarm (roll up noisy individual alarms)**:
```bash
aws cloudwatch put-composite-alarm \
  --alarm-name "prod-checkout-composite" \
  --alarm-rule "ALARM(\"prod-checkout-error-rate\") AND ALARM(\"prod-checkout-latency-p99\")" \
  --alarm-actions arn:aws:sns:us-east-1:123456789012:on-call-pager
```

**Verification**:
```bash
aws cloudwatch describe-alarms \
  --query 'MetricAlarms[].[AlarmName,TreatMissingData,EvaluationPeriods,DatapointsToAlarm,Period]'
```

---

## 3. Centralize Observability into a Dedicated Monitoring Account

**Pillar alignment**: Operational Excellence + Security

**Why**: Per-workload monitoring silos prevent cross-account root-cause analysis. CloudWatch
cross-account observability (OAM) provides a central account to view metrics, logs, and traces
from all source accounts without copying data.

**Setup — monitoring account (create sink)**:
```bash
# Create OAM sink in the monitoring/central observability account
aws oam create-sink --name central-observability-sink

# Link to an AWS Organization (auto-links all current and future accounts)
# Run in the Organizations management account or a delegated admin
aws oam create-link \
  --sink-identifier arn:aws:oam:us-east-1:MONITORING_ACCT_ID:sink/SINK_ID \
  --resource-types AWS::CloudWatch::Metric AWS::Logs::LogGroup AWS::XRay::Trace \
  --label-template "$Account"
```

**Verify from monitoring account**:
```bash
aws oam list-sinks    # Should list configured sink
aws oam list-links    # Should list all linked source accounts
```

**Known constraints** (do not attempt these cross-account):
- Composite alarms across accounts are unsupported
- Math expression functions `ANOMALY_DETECTION_BAND`, `INSIGHT_RULE`, `SERVICE_QUOTA` unsupported cross-account
- Cross-account alarms that trigger EC2/Auto Scaling actions are unsupported

---

## 4. Publish Custom Metrics via EMF in Serverless/Containers

**Pillar alignment**: Performance Efficiency + Cost Optimization

**Why**: Synchronous `PutMetricData` in a Lambda or ECS request path adds API call latency (tens
of milliseconds) and per-call cost. Embedded Metric Format (EMF) writes metrics as structured log
events; CloudWatch extracts them asynchronously. One log write delivers both logs and metrics.

**EMF envelope — minimum valid structure**:
```json
{
  "_aws": {
    "Timestamp": 1690000000000,
    "CloudWatchMetrics": [
      {
        "Namespace": "MyApp/Prod",
        "Dimensions": [["Service", "Environment"]],
        "Metrics": [
          { "Name": "TransactionLatency", "Unit": "Milliseconds" },
          { "Name": "TransactionCount",   "Unit": "Count" }
        ]
      }
    ]
  },
  "Service": "checkout",
  "Environment": "prod",
  "TransactionLatency": 42.5,
  "TransactionCount": 1
}
```

**Lambda — Node.js using `aws-embedded-metrics` library**:
```javascript
const { createMetricsLogger, Unit } = require('aws-embedded-metrics');

exports.handler = async (event) => {
  const metrics = createMetricsLogger();
  metrics.setNamespace('MyApp/Prod');
  metrics.putDimensions({ Service: 'checkout', Environment: process.env.ENV });

  const start = Date.now();
  // ... business logic ...
  const latencyMs = Date.now() - start;

  metrics.putMetric('TransactionLatency', latencyMs, Unit.Milliseconds);
  metrics.putMetric('TransactionCount', 1, Unit.Count);
  await metrics.flush();  // Writes structured log + extracts metrics
};
```

**Cardinality rule**: Keep `Dimensions` to bounded, low-cardinality values (Service, Environment,
Region). Never use `RequestId`, `UserId`, or transaction identifiers as dimensions.

---

## 5. Standardize Instrumentation on OpenTelemetry (OTLP)

**Pillar alignment**: Operational Excellence (portability + future-proofing)

**Why**: CloudWatch now exposes native OTLP endpoints — no proprietary agent or format conversion
needed. The same OTel SDK instrumentation can target CloudWatch or any third-party backend (Jaeger,
Grafana, Datadog). OTel metrics support up to 150 labels (vs 30 dimensions for traditional metrics)
and histogram/exponential-histogram types queried via PromQL in CloudWatch Query Studio.

**OTel Collector config — send to CloudWatch OTLP endpoint**:
```yaml
# otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

exporters:
  awscloudwatchlogs:
    region: us-east-1
    log_group_name: /otel/myapp
    log_stream_name: collector
  awsemf:
    region: us-east-1
    namespace: MyApp/OTel
    log_group_name: /otel/metrics

service:
  pipelines:
    metrics:
      receivers: [otlp]
      exporters: [awsemf]
    logs:
      receivers: [otlp]
      exporters: [awscloudwatchlogs]
```

**Team decision to document**:

Choose one query model and enforce it:
- **Metrics Insights** → use for traditional CloudWatch metrics (namespaces, dimensions, `GetMetricStatistics`)
- **PromQL / Query Studio** → use for OTLP metrics (labels, histograms)

Do not mix query models in the same alarm or dashboard; they use different APIs and billing paths.

**Verification**:
```bash
# OTel metrics appear in Query Studio (PromQL) within ~2 min
# Traditional metrics appear via GetMetricStatistics / Metrics Insights
aws cloudwatch list-metrics --namespace "MyApp/OTel"
```
