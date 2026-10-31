# Dev Services (dev and test only)

Back to [SKILL.md](../SKILL.md). Quarkiverse 3.23.x. Fetched 2026-10-28. Test patterns, the mock event server and the removed `quarkus-test-amazon-lambda` belong to [testing-quarkus-amazon-lambda-v3-40](../../testing-quarkus-amazon-lambda-v3-40/SKILL.md); this blueprint fixes only the rule about `endpoint-override`.

## Contents

- [A11. No endpoint-override with Dev Services](#a11-no-endpoint-override-with-dev-services)
- [Provider and images](#provider-and-images)
- [Page contradictions](#page-contradictions)
- [Test sketch](#test-sketch)

## A11. No endpoint-override with Dev Services

Dev Services start "a containerized AWS stack in dev mode and when running tests" unless, among other exceptions, "the `endpoint-override` is configured". Property text: "Dev Services starts a container unless `aws.endpoint-override` is set". S3 and DynamoDB `devservices.enabled`: "If this is true and endpoint-override is not configured then a local AWS stack will be started". Evidence: dev-services, DynamoDB and S3 pages (triangulated) ([dev-services](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/dev-services.html), [DynamoDB](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-dynamodb.html), [S3](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-s3.html)).

```properties
# Quarkiverse 3.23.x: leave endpoint-override unset; Dev Services provide the local endpoint in dev and test
# quarkus.dynamodb.endpoint-override=http://localhost:4566   <- setting this disables Dev Services for DynamoDB
quarkus.s3.devservices.buckets=my-local-bucket
```

`my-local-bucket` is an example value, not a default.

## Provider and images

- `quarkus.aws.devservices.provider` default `localstack` (medium confidence, M10); also `ministack`, `moto`, `floci`.
- Images listed per provider (medium confidence, M10): `localstack/localstack:4.13`, `ministackorg/ministack:latest`, `motoserver/moto:latest`, `floci/floci:latest`. The `:latest` images are not reproducible.
- "Dev Services for Amazon Services does not verify if the chosen stack actually implements a mock for a given service."
- Without Docker: "In test mode, it will cause the test to fail… Either disable Dev Services or configure the `endpoint-override`."
- 4.0.0.Beta1 makes Floci the default; that is the Quarkus 4 line and does not apply to 3.23.x (family rule 1).
- Provider decision: [C8](./ask-first-data-decisions.md#c8-dev-services-provider).

## Page contradictions

Both are on the 3.23.x pages and neither is resolved there; cite both, assert neither (unverified).

1. Sharing on https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/dev-services.html: the text says "Sharing is disabled by default in dev mode, and is always disabled in test mode", while the reference table lists `quarkus.aws.devservices.<provider>.shared` with default `true`.
2. `quarkus.s3.devservices.enabled` on https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-s3.html: the description says "(default to true)" while the default column is blank.

Register: U10.

## Test sketch

Illustrative, depth lives in the testing skill: `@QuarkusTest` clients point at the Dev Services stack automatically ("The extension client is configured automatically").

```java
@QuarkusTest
class DocumentStoreTest {
    @Inject DocumentStore store;   // clients use the Dev Services stack
    @Test void roundTrip() { /* create table and bucket, save, read */ }
}
```
