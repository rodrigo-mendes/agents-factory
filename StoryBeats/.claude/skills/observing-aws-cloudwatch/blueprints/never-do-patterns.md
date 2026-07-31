# Never Do Patterns — observing-aws-cloudwatch

> Full anti-patterns with ❌ wrong configuration, ✅ correct alternative, CLI detection, and impact.
> Source: research_cloud_AWS_Observability-CloudWatch_2026.md (accessed 2026-07-31)

---

## 1. Log Group with Default (Never-Expire) Retention

**Risk level**: HIGH
**Pillars**: Cost Optimization + Compliance

**Why prohibited**: CloudWatch Logs never expires data unless you explicitly set `retentionInDays`.
Every log group created via CDK, Terraform, CloudFormation, or the console without a retention
policy accumulates `TimedStorage-ByteHrs` indefinitely. This is both an unbounded cost driver and
a compliance liability (undeleted PII or audit data beyond the required retention window).

```bash
# ❌ WRONG: log group created with no retention (console shows "Never expire")
aws logs create-log-group --log-group-name /myapp/prod

# ✅ CORRECT: always set retentionInDays
aws logs create-log-group --log-group-name /myapp/prod
aws logs put-retention-policy --log-group-name /myapp/prod --retention-in-days 90
```

**Detection**:
```bash
# Lists every log group with infinite retention — must be empty in production
aws logs describe-log-groups \
  --query 'logGroups[?retentionInDays==`null`].logGroupName'
```

**Enforcement**: AWS Config managed rule `cloudwatch-log-group-retention-period-check`.

**Impact if ignored**: Unbounded storage cost + compliance violation.

---

## 2. Latency Alarm with `Statistic: Average`

**Risk level**: MEDIUM
**Pillars**: Reliability + Performance Efficiency

**Why prohibited**: Average latency hides tail behavior. A p99 of 3 seconds (SLO breach) can coexist
with an average of 200ms (looks healthy). Alarming on Average gives false confidence.

```bash
# ❌ WRONG: ALB latency alarm on Average — hides p99 spikes
aws cloudwatch put-metric-alarm \
  --alarm-name "prod-alb-latency-wrong" \
  --namespace "AWS/ApplicationELB" \
  --metric-name "TargetResponseTime" \
  --dimensions Name=LoadBalancer,Value=app/prod-alb/abc123 \
  --statistic Average \
  --period 300 \
  --evaluation-periods 3 \
  --datapoints-to-alarm 3 \
  --threshold 0.2 \
  --comparison-operator GreaterThanOrEqualToThreshold

# ✅ CORRECT: use p99 (or p95) extended statistic aligned to your SLO
aws cloudwatch put-metric-alarm \
  --alarm-name "prod-alb-latency-p99" \
  --namespace "AWS/ApplicationELB" \
  --metric-name "TargetResponseTime" \
  --dimensions Name=LoadBalancer,Value=app/prod-alb/abc123 \
  --extended-statistic p99 \
  --period 300 \
  --evaluation-periods 3 \
  --datapoints-to-alarm 3 \
  --threshold 1.0 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --treat-missing-data notBreaching
```

**Detection**:
```bash
# Flag latency alarms using Average statistic
aws cloudwatch describe-alarms \
  --query 'MetricAlarms[?contains(MetricName,`Latency`) && Statistic==`Average`].[AlarmName,Statistic]'
# Expected: []
```

**Note**: Percentile statistics are supported for custom metrics with raw points and for select
AWS services (API Gateway, ALB, EC2, ELB, Kinesis, Lambda, RDS). They are not available on metrics
published as statistic sets or when any value is negative.

**Impact if ignored**: Silent user-facing SLO violations; on-call never paged until it's too late.

---

## 3. Critical Alarm Without Explicit `TreatMissingData`

**Risk level**: HIGH
**Pillar**: Reliability

**Why prohibited**: The default missing-data handling (`missing`) puts an alarm into
`INSUFFICIENT_DATA` state when no data arrives. If this happens to a production health alarm,
the state is neither `OK` nor `ALARM` — operators may interpret it as "healthy" when the resource
is actually broken. Conversely, setting `breaching` on a legitimately idle resource generates
continuous false pages.

```bash
# ❌ WRONG: critical alarm with no TreatMissingData (defaults to `missing`)
aws cloudwatch put-metric-alarm \
  --alarm-name "prod-db-connections" \
  --namespace "AWS/RDS" \
  --metric-name "DatabaseConnections" \
  --dimensions Name=DBInstanceIdentifier,Value=prod-db \
  --statistic Average \
  --period 300 \
  --evaluation-periods 3 \
  --datapoints-to-alarm 3 \
  --threshold 100 \
  --comparison-operator GreaterThanOrEqualToThreshold
  # MISSING: --treat-missing-data

# ✅ CORRECT for a heartbeat alarm (no data = something is wrong)
aws cloudwatch put-metric-alarm \
  --alarm-name "prod-db-connections" \
  --namespace "AWS/RDS" \
  --metric-name "DatabaseConnections" \
  --dimensions Name=DBInstanceIdentifier,Value=prod-db \
  --statistic Average \
  --period 300 \
  --evaluation-periods 3 \
  --datapoints-to-alarm 3 \
  --threshold 100 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --treat-missing-data breaching   # No data from DB = treat as breach

# ✅ CORRECT for a legitimately idle resource (no data = expected silence)
# Example: a detached EBS volume that stops emitting metrics
aws cloudwatch put-metric-alarm \
  --alarm-name "optional-batch-volume-usage" \
  --treat-missing-data notBreaching
```

**Detection**:
```bash
# List alarms still on default missing-data handling — review each for intent
aws cloudwatch describe-alarms \
  --query 'MetricAlarms[?TreatMissingData==`missing`].[AlarmName,TreatMissingData]'
```

**Impact if ignored**: Service outage undetected (silent) OR sustained alert fatigue on idle resources.

---

## 4. Every Metric Alarm Wired Directly to On-Call SNS (No Composite Rollup)

**Risk level**: MEDIUM
**Pillar**: Operational Excellence

**Why prohibited**: Paging on dozens of individual metric alarms produces alert fatigue. When a
real incident fires multiple correlated conditions simultaneously, operators are buried in noise
and may suppress or ignore pages — exactly when attention is most needed.

```bash
# ❌ WRONG: 20 individual metric alarms each with --alarm-actions pointing to the on-call SNS topic
# (illustrative — do not replicate this pattern)
# aws cloudwatch put-metric-alarm --alarm-name "cpu-high" --alarm-actions arn:aws:sns:::on-call
# aws cloudwatch put-metric-alarm --alarm-name "errors-high" --alarm-actions arn:aws:sns:::on-call
# aws cloudwatch put-metric-alarm --alarm-name "latency-high" --alarm-actions arn:aws:sns:::on-call
# ... (×17 more)

# ✅ CORRECT: keep individual alarms for debugging context; page only on the composite
# Individual alarms → no on-call action, optionally a low-priority notification channel
aws cloudwatch put-metric-alarm \
  --alarm-name "prod-errors-high" \
  --alarm-actions arn:aws:sns:us-east-1:123456789012:low-priority-slack

aws cloudwatch put-metric-alarm \
  --alarm-name "prod-latency-p99-high" \
  --alarm-actions arn:aws:sns:us-east-1:123456789012:low-priority-slack

# Composite alarm → pages on-call only when a meaningful combination holds
aws cloudwatch put-composite-alarm \
  --alarm-name "prod-checkout-incident" \
  --alarm-rule "ALARM(\"prod-errors-high\") AND ALARM(\"prod-latency-p99-high\")" \
  --alarm-actions arn:aws:sns:us-east-1:123456789012:on-call-pager
```

**Detection**:
```bash
# Count metric alarms with on-call SNS actions vs composite alarms in the account
# A high ratio of direct-paging metric alarms signals missing rollups
aws cloudwatch describe-alarms --alarm-types MetricAlarm \
  --query 'MetricAlarms[?AlarmActions!=`[]`].[AlarmName,AlarmActions]' | grep "on-call"
```

**Impact if ignored**: Alert fatigue → real incidents missed; on-call burnout.

---

## 5. High-Cardinality Value as a Metric Dimension

**Risk level**: MEDIUM
**Pillar**: Cost Optimization

**Why prohibited**: Each unique combination of dimension values is stored as a separate, independently
billed CloudWatch metric. Using `RequestId`, `UserId`, or `OrderId` as a dimension creates a new
metric for every request — metric count and `MetricMonitorUsage` cost explode in proportion to
request volume. The same problem applies to OTLP labels, though the label budget is larger (150).

```bash
# ❌ WRONG: RequestId as a dimension via PutMetricData
# This creates a unique metric for every single API request
aws cloudwatch put-metric-data \
  --namespace "MyApp/Prod" \
  --metric-data '[{
    "MetricName": "TransactionLatency",
    "Dimensions": [
      {"Name": "Service",   "Value": "checkout"},
      {"Name": "RequestId", "Value": "a1b2c3d4-e5f6-..."}
    ],
    "Value": 42.5,
    "Unit": "Milliseconds"
  }]'
```

```json
// ✅ CORRECT via EMF: RequestId goes in a log field, NOT in Dimensions
{
  "_aws": {
    "Timestamp": 1690000000000,
    "CloudWatchMetrics": [{
      "Namespace": "MyApp/Prod",
      "Dimensions": [["Service", "Environment"]],
      "Metrics": [{ "Name": "TransactionLatency", "Unit": "Milliseconds" }]
    }]
  },
  "Service":     "checkout",
  "Environment": "prod",
  "RequestId":   "a1b2c3d4-e5f6-...",
  "TransactionLatency": 42.5
}
```

**Detection**:
```bash
# Watch for a rapidly growing metric count in a namespace
aws cloudwatch list-metrics --namespace "MyApp/Prod" | jq '.Metrics | length'
# A number growing by thousands per hour indicates unbounded cardinality

# Monitor Cost Explorer for MetricMonitorUsage spikes
aws ce get-cost-and-usage \
  --time-period Start=$(date -d '-7 days' '+%Y-%m-%d'),End=$(date '+%Y-%m-%d') \
  --granularity DAILY \
  --metrics "UnblendedCost" \
  --filter '{"Dimensions": {"Key": "USAGE_TYPE", "Values": ["MetricMonitorUsage"]}}'
```

**Impact if ignored**: Uncapped cost growth proportional to request volume.
