# Migration Notes

Back to [SKILL.md](../SKILL.md). Fetched 2026-10-28. No official metrics migration guide for Quarkus 3.40 exists (medium confidence, absence of evidence).

## Status changes relevant to this skill

- No Quarkus 3.40-specific metrics break was found. The Quarkus-maintained Micrometer extensions are `micrometer`, `micrometer-registry-prometheus` and `micrometer-opentelemetry`; CloudWatch has never appeared in the Quarkiverse registry set on Central (High, family fact; [listing](https://repo1.maven.org/maven2/io/quarkiverse/micrometer/registry/)).
- Lambda JSON log format and log-level filtering are opt-in; changing the format affects only new logs ([log format](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-logformat.html)). AWS warns Node.js EMF users to upgrade libraries when switching to JSON; no equivalent Java statement exists (medium confidence).
- Lambda Managed Instances "only support JSON log format" and support concurrent invocations; this skill does not cover Quarkus on Managed Instances.
- `aws-embedded-metrics-java`: last version 4.2.0 (2024-08-02); freshness risk.
- Powertools for AWS Lambda (Java) 2.x supports Java 17 to 25; the Lambda guide's Powertools SAM sample still uses `java11` (medium confidence, M14: treat the Lambda sample as outdated). A v1 to v2 metrics migration guide was not read. The existing `implementing-lambda-powertools-java` skill is locked to 2.10.0 (family fact, name only).

## From per-invocation PutMetricData to EMF

1. Keep namespace, metric names, units and dimension names identical, or the new series are separate metrics ([metric concepts](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/cloudwatch_concepts.html)).
2. Replace the SDK call with an EMF line written before the handler returns.
3. Remove `cloudwatch:PutMetricData` from the execution role only if nothing else uses it; Terraform changes go to `provisioning-aws-*-v6` (family rule 4).
4. Deploy, invoke, confirm with `aws cloudwatch list-metrics` (up to 15 minutes; statistics up to 2 minutes).

## Compatibility matrix

| Dependency | Version | Notes |
|---|---|---|
| `io.quarkus:quarkus-amazon-lambda` | 3.40.1.1 | family fact |
| `io.quarkus:quarkus-micrometer` | 3.40.1.1 (BOM) | only for option (d) |
| `io.micrometer:micrometer-registry-cloudwatch2` | 1.17.1 | managed by `micrometer-bom` 1.17.1, imported by the Quarkus BOM (medium confidence); docs page is 1.17.2 (M3) |
| `software.amazon.cloudwatchlogs:aws-embedded-metrics` | 4.2.0 | Quarkus and native unverified |
| `software.amazon.lambda:powertools-metrics` | 2.11.0 | Quarkus: (unverified) |
| Lambda runtime (JVM) | `java17.al2023`, `java21`, `java25` | family fact |
| Lambda runtime (native) | `provided.al2023` | family fact; pairing caveat in the [developing skill](../../developing-quarkus-amazon-lambda-v3-40/SKILL.md) |
