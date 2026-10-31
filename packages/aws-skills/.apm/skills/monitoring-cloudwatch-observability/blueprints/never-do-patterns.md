# Never Do Patterns — monitoring-cloudwatch-observability

Full anti-patterns (7) with detection commands. Summary in [../SKILL.md](../SKILL.md).
Source: research_cloud_AWS_CloudWatch_Observability_2026.md (research date 2026-08-30; official AWS docs accessed 2026-08-30).

---

## Anti-Pattern 1 — Log groups left at Never-Expire retention [CRITICAL]

**Why**: Logs are kept indefinitely by default; ingestion ($0.50/GB) and storage keep accruing.

- 🚫 WRONG: log group with `retentionInDays = null`.
- ✅ CORRECT: `RetentionInDays` set in CloudFormation at creation; AWS Config custom rule detects null retention.

**Detection**: `aws logs describe-log-groups --query 'logGroups[?retentionInDays==null].[logGroupName,storedBytes]'`
**Impact**: unbounded storage cost, governance audit failure.

Source: [Log groups and streams](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/Working-with-log-groups-and-streams.html) (2026-08-30)

---

## Anti-Pattern 2 — Dashboard-only monitoring without alarms [HIGH]

**Why**: OPS04-BP02. Dashboards need a human watching; MTTD is unbounded.

- 🚫 WRONG: dashboards as sole monitoring; no alarms, no SNS actions.
- ✅ CORRECT: metric + composite alarms with SNS on ALARM and OK transitions, dashboards for context.

**Detection**: `aws cloudwatch describe-alarms` returns empty while `aws cloudwatch list-dashboards` returns dashboards.
**Impact**: outages found only when a user reports them.

Source: [Alarm best practices](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Best-Practice-Alarms.html) (2026-08-30)

---

## Anti-Pattern 3 — Alarm fatigue: no composite alarms [HIGH]

**Why**: one root cause triggers dozens of correlated alarms; operators start ignoring notifications.

- 🚫 WRONG: every metric alarm has its own SNS action; no composite alarms.
- ✅ CORRECT: child metric alarms with SNS suppressed; tier-level composite alarm with a single SNS action.

**Detection**: `aws cloudwatch describe-alarms --alarm-types CompositeAlarm` is empty.
**Impact**: delayed response to real incidents, on-call burden.

Source: [Composite alarms](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Create_Composite_Alarm.html) (2026-08-30)

---

## Anti-Pattern 4 — Plaintext secrets or PII in logs [CRITICAL]

**Why**: any principal with `logs:GetLogEvents` can read them; violates PCI DSS, GDPR, SOC 2.

- 🚫 WRONG: logging `Authorization: Bearer <token>`, `password: <value>`, SSN or card numbers.
- ✅ CORRECT: sanitize before emission; Secrets Manager for secrets (never log retrieved values); CloudWatch Logs data protection policies (PII masking at ingestion); restrict `logs:Unmask` to a break-glass role.

**Detection**: `aws logs describe-data-protection-policy --log-group-name <name>` shows no policy.
**Impact**: credential exposure, compliance violation, secrets in immutable logs.

Source: [Mask sensitive log data](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/mask-sensitive-log-data.html) (2026-08-30)

---

## Anti-Pattern 5 — Single-metric CPU-only alarms [HIGH]

**Why**: OPS04-BP01. Low CPU can coexist with exhausted file descriptors, pool slots or memory. Golden signals need latency, errors, traffic, saturation.

- 🚫 WRONG: one alarm on `CPUUtilization` as the only health signal.
- ✅ CORRECT: composite alarm over `HTTPCode_Target_5XX_Count`, `TargetResponseTime` (P99), ECS `CPUUtilization` and `MemoryUtilization`, plus anomaly detection on `RequestCount`.

**Detection**: `aws cloudwatch describe-alarms --query 'MetricAlarms[?MetricName==`CPUUtilization`].[AlarmName]'`; CPU alarms far outnumber latency/error alarms.
**Impact**: missed user-impacting outages, false escalations during batch jobs.

Source: [OPS04-BP05 / observability](https://docs.aws.amazon.com/wellarchitected/latest/framework/ops_observability_dist_trace.html) (2026-08-30)

---

## Anti-Pattern 6 — No distributed tracing on a multi-service app [HIGH]

**Why**: OPS04-BP05 lists partial instrumentation as a common anti-pattern with HIGH risk; latency spikes cannot be attributed to a service without trace context.

- 🚫 WRONG: logs and metrics only; Lambda `TracingConfig.Mode = PassThrough`.
- ✅ CORRECT: ADOT on all tiers, X-Ray backend, ServiceLens service map, Application Signals for SLO-correlated drill-down.

**Detection**: ServiceLens map empty or single node; `aws lambda list-functions --query 'Functions[*].[FunctionName,TracingConfig.Mode]'` shows Mode other than Active.
**Impact**: MTTD in hours for distributed failures.

Sources: [OPS04-BP05](https://docs.aws.amazon.com/wellarchitected/latest/framework/ops_observability_dist_trace.html); [Application tracing](https://docs.aws.amazon.com/prescriptive-guidance/latest/implementing-logging-monitoring-cloudwatch/application-tracing-xray.html) (2026-08-30)

---

## Anti-Pattern 7 — PutMetricData with high-cardinality dimensions [HIGH]

**Why**: each unique dimension combination is a separately billed custom metric.

- 🚫 WRONG: `PutMetricData` with dimensions `{UserId: "user-12345", RequestId: "req-67890"}`.
- ✅ CORRECT: aggregate dimensions only (Environment, Service, Region); per-user analysis via Logs Insights at query time. EMF is the preferred emission path for serverless, but it also creates one metric per dimension combination, so keep its dimensions low-cardinality too.

**Detection**: `aws cloudwatch list-metrics --namespace <app-namespace>`; counts above 1,000 suggest a cardinality issue (research heuristic). Watch Cost Explorer "Custom Metrics" usage type for steady growth.
**Impact**: bill grows with user base; possible metric quota exhaustion.

Source: [EMF](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format.html) (2026-08-30)
