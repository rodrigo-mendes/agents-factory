# Limits and Production Readiness

Back to [SKILL.md](../SKILL.md). Quarkiverse 3.23.0, AWS SDK 2.55.x. Fetched 2026-10-28.

## Contents

- [Performance](#performance)
- [DynamoDB limits](#dynamodb-limits)
- [Monitoring](#monitoring)
- [Security checklist](#security-checklist)

## Performance

- Reuse injected clients ([A4](./always-do-patterns.md#a4-inject-and-reuse-clients)); choose the HTTP client per [C1](./ask-first-decisions.md#c1-http-client-type) and [C2](./ask-first-decisions.md#c2-jvm-snapstart-or-native-consequences).
- AWS names `SdkWarmUp` for SnapStart warm-up ([Lambda start time](https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/lambda-optimize-starttime.html)); whether Quarkiverse integrates it is not stated (unverified).
- AWS: "The SDK provides default values… but not for API call timeouts" for `apiCallTimeout` and `apiCallAttemptTimeout` ([best practices](https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/best-practices.html)). The Quarkiverse 3.23.x key for these is not recorded (unverified).
- Quarkiverse S3 HTTP defaults: `quarkus.s3.sync-client.connection-timeout` `2S`, `quarkus.s3.sync-client.socket-timeout` `30S`, `quarkus.s3.async-client.max-concurrency` `50` (medium confidence, M10: defaults read from a summarised page) ([S3 page](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-s3.html)).

## DynamoDB limits

From [Constraints](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Constraints.html):

| Limit | Value |
|---|---|
| Item size | 400 KB (names and values) |
| Partition key / sort key length | 1 to 2048 bytes / 1 to 1024 bytes |
| Query and Scan | 1 MB per call |
| BatchGetItem | 100 items / 16 MB |
| BatchWriteItem | 25 put or delete requests / 16 MB |
| Transactions | 100 unique items / 4 MB |
| Expression | 4 KB string; 300 operators |
| Item collection with an LSI | 10 GB |

From [service quotas](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/ServiceQuotas.html): initial 2,500 tables per Region; on-demand per-table default 40,000 RRU and WRU.

## Monitoring

- SDK metrics can be collected ([best practices](https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/best-practices.html)); `quarkus.s3.telemetry.enabled` default `false` (medium confidence, M10) ([S3 page](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-s3.html)).
- The OpenTelemetry for Amazon Services page of 3.23.x exists in the navigation but was not read (coverage limit L5).
- Logging: family rule 7 (JSON with `requestId` and `tenantId`, no PII, bounded tenant dimensions).

## Security checklist

- [ ] `credentials.type=default` everywhere ([A3](./always-do-patterns.md#a3-default-credentials-chain), F1, F2).
- [ ] IAM least privilege for the execution role; tenant isolation per [C4](./ask-first-data-decisions.md#c4-tenant-isolation-model); `Scan` excluded from LeadingKeys policies ([A8](./tenant-isolation.md#a8-leadingkeys-for-dynamodb)).
- [ ] Presigned URLs short-lived; consider the bucket policy condition `s3:signatureAge` (the AWS example denies signatures older than 600000 ms) and network-path conditions `aws:SourceIp` and `aws:SourceVpce` ([S3 presigned URLs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html)). IaC for these belongs to `provisioning-aws-s3-v6`.
- [ ] Policy variables carry `"Version":"2012-10-17"`; a missing tag makes the Allow statement not take effect ([IAM policy variables](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_variables.html)).
- [ ] `quarkus.s3.path-style-access` default `false` (medium confidence, M10); "DNS style… is preferred" ([S3 page](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-s3.html)).
