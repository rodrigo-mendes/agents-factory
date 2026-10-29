# Cardinality, Cost and Built-in Metrics

Back to [SKILL.md](../SKILL.md). Fetched 2026-10-28. Pricing is unversioned and region-specific (medium confidence); verify with `managing-aws-costs` (name only) before budgeting.

## Contents

- [Cardinality arithmetic](#cardinality-arithmetic)
- [Cost](#cost)
- [Built-in Lambda metrics not to re-emit](#built-in-lambda-metrics-not-to-re-emit)
- [EMF delivery and alarms](#emf-delivery-and-alarms)

## Cardinality arithmetic

Each unique namespace + metric name + dimension combination is a metric ([metric concepts](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/cloudwatch_concepts.html)). "Every DimensionSet used creates a new metric in CloudWatch" ([EMF spec](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html)). The agreed ceiling for an ADR is metrics x dimension sets x allowed dimension values.

Example: 2 metrics x 1 DimensionSet `[Service, TenantTier]` x (1 service x 3 tiers) = 6 metrics. Adding `TenantId` with 500 tenants gives 2 x 1 x (1 x 500) = 1,000 metrics for the same code path.

## Cost

| Item | Value | Tag |
|---|---|---|
| Custom metric | $0.30 per metric per month for the first 10,000, prorated by the hour, US East (N. Virginia) | (medium confidence) |
| Free tier | 10 custom metrics | (medium confidence) |
| Log ingestion | billed separately; the price per GB is not quoted: the pricing page examples conflict ($0.25 vs $0.50 for the same scenario, as in the logging skill) | (unverified) |
| PutMetricData price | the tool returned "$0.01/M requests"; the unit is ambiguous | (unverified) |
| Logs Insights scan price | not found in the parts of the page read | (unverified) |
| Deletion | metrics cannot be deleted; they expire after 15 months without data | High ([concepts](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/cloudwatch_concepts.html)) |

Source for prices: https://aws.amazon.com/cloudwatch/pricing/ (read as tool summaries in two passes, L4).

## Built-in Lambda metrics not to re-emit

Namespace `AWS/Lambda`; dimensions `FunctionName`, `Resource`, `ExecutedVersion`, `EventSourceMappingUUID` ([viewing metrics](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-metrics-view.html)). Built-ins ([metric types](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-metrics-types.html)):

- Invocation: `Invocations`, `Errors`, `DeadLetterErrors`, `DestinationDeliveryFailures`, `Throttles`.
- Performance: `Duration` (supports percentiles; "does not include cold start time"), `PostRuntimeExtensionsDuration`.
- Concurrency: `ConcurrentExecutions`, `UnreservedConcurrentExecutions`, `ClaimedAccountConcurrency`, provisioned-concurrency metrics.
- Event sources: `IteratorAge`, `OffsetLag`, opt-in event-source-mapping metrics.
- Async: `AsyncEventsReceived`, `AsyncEventAge`, `AsyncEventsDropped`, `RecursiveInvocationsDropped`.

`InitDuration` is not in this list (medium confidence, absence of evidence). Lambda sends these "in 1-minute intervals" with no extra execution-role permission and no additional charge ([Lambda metrics](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-metrics.html)). Alarms and dashboards on them: `monitoring-cloudwatch-observability` and `provisioning-aws-cloudwatch-v6` (names only).

## EMF delivery and alarms

EMF delivery is "at least one time"; duplicate metric values may occur ([EMF spec](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html)). EMF metrics depend on log processing, so alarm periods must allow for log delivery ([EMF alarms](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Alarms.html)). PutMetricData: 1,000 metrics and 1 MB per request, 150 values per metric, 30 dimensions; 500 requests per second per Region, adjustable ([PutMetricData](https://docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/API_PutMetricData.html), [quotas](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/cloudwatch_limits.html), only the metrics table read, L5).
