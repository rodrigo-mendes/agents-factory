# Migration Notes

Back to [SKILL.md](../SKILL.md). Quarkiverse amazon-services 3.22.x to 3.23.0 on Quarkus 3.40. Fetched 2026-10-28.

## Breaking changes 3.22.x to 3.23.0

None are listed in the 3.23.0 release notes. The items are the Quarkus bump "from 3.39.2 to 3.40.0", the AWS SDK BOM "from 2.54.13 to 2.55.6", a docs link fix and Maven plugin bumps ([release 3.23.0](https://github.com/quarkiverse/quarkus-amazon-services/releases/tag/3.23.0)). Only the Quarkus 3.40 base matters for this family.

## Deprecations seen on 3.23.x pages

- `quarkus.sns.devservices.isolated` and `quarkus.eventbridge.devservices.isolated` are marked deprecated (default `true`) ([SNS page](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-sns.html), [EventBridge page](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-eventbridge.html)).
- The SQS page lists `isolated` (default `true`) without a deprecation note in the tool's summary (medium confidence) ([SQS page](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-sqs.html)).
- Dev Services belongs to the [testing skill](../../testing-quarkus-amazon-lambda-v3-40/SKILL.md). The Dev Services page contradicts itself on sharing (family fact); cite both statements there.

## Do not upgrade into

`4.0.0.Beta1` to `Beta3` is the Quarkus 4 line ("feat: bump to quarkus 4"). It also makes Floci the default Dev Services stack and notes "The Apache (v4) client is deprecated in favor of `apache5`" ([releases](https://github.com/quarkiverse/quarkus-amazon-services/releases)). Family rule 1 rejects it. The `apache5` sync type already exists in 3.23.x ([SQS page](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-sqs.html)).

## Upgrade steps

1. Set the Quarkus platform to 3.40.1.1 (lambda skill); pairing with 3.23.0 is (medium confidence).
2. Import `io.quarkiverse.amazonservices:quarkus-amazon-services-bom:3.23.0` ([BOM POM](https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-services-bom/3.23.0/quarkus-amazon-services-bom-3.23.0.pom)).
3. Remove versions from the `quarkus-amazon-*` dependencies (managed by the BOM).
4. Keep `software.amazon.awssdk:url-connection-client` for the SQS, SNS and EventBridge sync clients.
5. If you loaded SSM or Secrets Manager values by hand at boot, consider the config sources ([Q1](./ask-first-decisions.md#q1-source-of-secrets-and-parameters)). Both are off by default (`quarkus.ssm.config.enabled=false`, `quarkus.secretsmanager.config.enabled=false`).

```bash
# Representative - adapt to your environment
mvn -q dependency:tree -Dincludes=io.quarkiverse.amazonservices
# Expected: every quarkus-amazon-* at 3.23.0 (no 4.0.0.Beta*)
```

## Compatibility matrix

| Dependency | Min | Max | Notes |
|---|---|---|---|
| Quarkus | 3.40.0 | 3.40.x | `quarkus.version` 3.40.0 in the 3.23.0 parent POM; family target 3.40.1.1 (medium confidence) |
| AWS SDK for Java v2 | 2.55.6 | 2.55.6 | `awssdk.version` in the parent POM |
| AWS CRT | 0.48.4 | 0.48.4 | `awscrt.version` in the parent POM |
| Java | 17 | page not recorded | parent POM compiles with source and target 17; Lambda runtime choice is the lambda skill |
| `aws-lambda-java-events` | 3.16.1 managed by `quarkus-bom` 3.40.1.1 (medium confidence, M13) | 3.16.1 (latest on Central, lastUpdated 2025-07-16) | Brought by `quarkus-amazon-lambda-common` 3.40.1.1; native reflection for its classes is (unverified) (U4). Older than 12 months but the current stable, so not rejected |

Sources: [parent POM](https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-services-parent/3.23.0/quarkus-amazon-services-parent-3.23.0.pom), [events metadata](https://repo1.maven.org/maven2/com/amazonaws/aws-lambda-java-events/maven-metadata.xml), [lambda-common POM](https://repo1.maven.org/maven2/io/quarkus/quarkus-amazon-lambda-common/3.40.1.1/quarkus-amazon-lambda-common-3.40.1.1.pom).

## Stale wording in the Quarkus guide

The Quarkus 3.40 Lambda guide says "Quarkus now has extensions for DynamoDB, S3, SNS and SQS (more coming)", while the 3.23.x index lists 45 services. It is stale wording, not a conflict with any family fact ([Quarkus guide](https://quarkus.io/version/3.40/guides/aws-lambda), [3.23.x index](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/index.html)).
