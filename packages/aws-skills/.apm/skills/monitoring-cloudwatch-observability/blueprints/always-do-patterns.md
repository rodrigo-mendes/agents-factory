# Always Do Patterns — monitoring-cloudwatch-observability

Full mandatory patterns (8) with verification commands. Summary in [../SKILL.md](../SKILL.md).
Source: research_cloud_AWS_CloudWatch_Observability_2026.md (research date 2026-08-30; official AWS docs accessed 2026-08-30).

---

## Pattern 1 — Set log retention at creation

**Pillar**: Cost Optimization, Operational Excellence

The default is "Never Expire" (unbounded cost). Set `RetentionInDays` in IaC (CloudFormation property or CDK) at log group creation; never create log groups console-only.

| Log type | Retention |
|---|---|
| Debug / trace | 14 days |
| Application | 90 days |
| Access | 365 days |
| Audit / compliance | 2555 days (7 years) |

Events past a new boundary are deleted within 72 hours of the policy change. Detect violations with an AWS Config rule.

```bash
aws logs put-retention-policy --log-group-name <name> --retention-in-days 90
aws logs describe-log-groups --query 'logGroups[?retentionInDays==null].[logGroupName,storedBytes]'
# Expected: []  (any row is a violation)
```

Source: [Working with log groups and streams](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/Working-with-log-groups-and-streams.html) (2026-08-30)

---

## Pattern 2 — Encrypt log groups with a customer managed key

**Pillar**: Security (Data Protection)

- Associate a symmetric KMS key at log group creation (asymmetric keys are not supported).
- Key policy grants `logs.<region>.amazonaws.com`: Encrypt, Decrypt, ReEncrypt*, GenerateDataKey*, Describe*, with condition `kms:EncryptionContext:aws:logs:arn` scoped to the log group ARN.

```bash
aws logs associate-kms-key --log-group-name <name> --kms-key-id <arn>
aws logs describe-log-groups --query 'logGroups[*].[logGroupName,retentionInDays,kmsKeyId]'
# Expected: kmsKeyId present for sensitive/compliance groups
```

Source: [Encrypt log data with KMS](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/encrypt-log-data-kms.html) (2026-08-30)

---

## Pattern 3 — Metric alarms wired to SNS on all three transitions

**Pillar**: OPS04-BP01, OPS04-BP02, Reliability

- Alarm every critical metric (HTTP 5xx rate, P99 latency, queue depth).
- Configure SNS actions for ALARM, OK and INSUFFICIENT_DATA.
- Use console "Alarm recommendations" for AWS-recommended thresholds; "Download alarm code" yields CloudFormation/Terraform.
- Alarms invoke actions only on state change (Auto Scaling actions repeat each minute while in ALARM).

```bash
aws cloudwatch describe-alarms \
  --query 'MetricAlarms[*].[AlarmName,AlarmActions,OKActions,InsufficientDataActions]'
# Expected: no empty AlarmActions on critical metrics
```

Source: [Alarm best practices](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Best-Practice-Alarms.html) (2026-08-30)

---

## Pattern 4 — Composite alarms per application tier

**Pillar**: OPS04-BP05, Reliability

- One composite alarm per tier (web, app, database) using Boolean rules over child alarm states.
- Example rule: `(ALARM("ALB-5xx-Rate-High") OR ALARM("ALB-TargetResponseTime-High")) AND OK("ALB-HealthyHostCount-Low")`.
- SNS action on the composite only; suppress child-alarm SNS actions.
- Avoid circular references (A references B and B references A: both stop evaluating).
- Composite alarms cannot run EC2/Auto Scaling actions and are not supported cross-account.

```bash
aws cloudwatch describe-alarms --alarm-types CompositeAlarm \
  --query 'CompositeAlarms[*].[AlarmName,AlarmRule,AlarmActions]'
# Expected: at least one per tier
```

Source: [Create a composite alarm](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Create_Composite_Alarm.html) (2026-08-30)

---

## Pattern 5 — Anomaly detection on variable metrics

**Pillar**: OPS04-BP02, Reliability

- Enable on ALB `RequestCount`, `TargetResponseTime`, Lambda `Invocations`, application error rate.
- Start the band at 2-3 standard deviations.
- Exclude deployment windows via `PutAnomalyDetector` `ExcludedTimeRanges`.
- Model trains on up to two weeks of history (state `PENDING_TRAINING` until then).
- 2026: PromQL-based anomaly detection for OTel metrics is also supported.

```bash
aws cloudwatch describe-anomaly-detectors
aws cloudwatch describe-alarms --alarm-types MetricAlarm \
  --query 'MetricAlarms[?ThresholdMetricId!=null]'
```

Source: [Anomaly detection](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Anomaly_Detection.html) (2026-08-30)

---

## Pattern 6 — Instrument all tiers with ADOT

**Pillar**: OPS04-BP05 (risk if absent: HIGH)

- Use AWS Distro for OpenTelemetry on every tier; the X-Ray SDK/Daemon is in maintenance mode (exact announcement date: unverified).
- Lambda: enable Active Tracing. ECS/EKS: ADOT Collector as sidecar.
- Default X-Ray sampling: 1 request/second reservoir + 5% of additional requests; review per environment.
- X-Ray Annotations (max 50 per trace) for searchable fields such as `customerId`, `tenantId`; Metadata for unindexed context.

```bash
aws lambda list-functions --query 'Functions[*].[FunctionName,TracingConfig.Mode]'
# Expected: Active (PassThrough = tracing disabled)
aws xray get-sampling-rules
```
Also check CloudWatch console > ServiceLens > Service Map: every tier appears as a node.

Sources: [OPS04-BP05](https://docs.aws.amazon.com/wellarchitected/latest/framework/ops_observability_dist_trace.html); [Application tracing (Prescriptive Guidance)](https://docs.aws.amazon.com/prescriptive-guidance/latest/implementing-logging-monitoring-cloudwatch/application-tracing-xray.html) (2026-08-30)

---

## Pattern 7 — Golden-signals dashboard per tier

**Pillar**: OPS04-BP01

- One dashboard per tier: P50/P95/P99 latency, requests per second, error rate, saturation.
- Layer CloudWatch RUM (browser latency) over backend latency; Application Signals can populate SLO-aligned dashboards.
- Define as code with `AWS::CloudWatch::Dashboard`.
- Cost: $3/month per dashboard; first 3 free. Verify: console > Dashboards shows all four signal types per tier.

Source: [CloudWatch dashboards](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Dashboards.html) (2026-08-30)

---

## Pattern 8 — Cross-account observability via OAM

**Pillar**: Operational Excellence, Security

1. Monitoring account: create an OAM sink and choose accepted types (Logs, Metrics, Traces, Application Signals, Application Insights, Internet Monitor).
2. Each source account: create an OAM link to the sink ARN.
3. Onboard an Organizations OU with CloudFormation StackSets.
4. IAM, monitoring account: `oam:CreateSink`, `oam:PutSinkPolicy`, `oam:Get*`, `oam:List*`. Source account: `oam:CreateLink`, `oam:UpdateLink`, `cloudwatch:Link`, `logs:Link`, `xray:Link`, `application-signals:Link`.
5. Optional log-group filter by name prefix (max 5 conditional operands, 2000-character filter string).

Up to 100,000 source accounts per monitoring account; each source may share with up to 5 monitoring accounts. No extra cost for logs/metrics; first trace copy free. Data stays in source accounts (not replicated).

```bash
aws oam list-sinks
aws oam list-attached-links --sink-identifier <sink-arn>
aws oam list-links   # run in a source account
```

Source: [Cross-account observability setup](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Unified-Cross-Account-Setup.html) (2026-08-30)
