# Verification Loop

Back to [SKILL.md](../SKILL.md). Representative commands (Quarkus 3.40.1.1, AWS CLI v2); adapt names. Fetched 2026-10-28.

```bash
# 1. Unit test: the serializer emits valid EMF (see emf-implementation.md, Unit test)
./mvnw -q test
# Expected: tests green; each captured stdout line parses as JSON with _aws.Timestamp and _aws.CloudWatchMetrics

# 2. Check the function's logging configuration (if the logging skill chose JSON, level must be INFO or more detailed)
aws lambda get-function-configuration --function-name orders-fn --query LoggingConfig
# Expected: {"LogFormat": "Text", ...} or {"LogFormat": "JSON", "ApplicationLogLevel": "INFO", ...}

# 3. Invoke once, then look for the metric (statistics up to 2 min, list-metrics up to 15 min)
aws cloudwatch list-metrics --namespace SaaS/Orders --metric-name OrdersPlaced
# Expected: one entry per published dimension combination, e.g. Service=orders, TenantTier=premium

# 4. Confirm the series count stays bounded (cost guard, family rule 7)
aws cloudwatch list-metrics --namespace SaaS/Orders --query 'length(Metrics)'
# Expected: at most metrics x dimension sets x allowed dimension values agreed in the ADR

# 5. No Quarkus logger call carries EMF
grep -rnE "Log\.(info|debug|warn)\(.*_aws" src/main/java
# Expected: no output
```

EMF parsing and validation failures are reported as metrics in the `AWS/Logs` namespace ([EMF spec](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html)); the metric names were not read (unverified). Timing source: [publishing metrics](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/publishingMetrics.html).
