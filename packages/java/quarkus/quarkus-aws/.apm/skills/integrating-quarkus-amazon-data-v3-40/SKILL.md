---
name: integrating-quarkus-amazon-data-v3-40
description: "Integrates DynamoDB, the DynamoDB enhanced client and S3 (incl. presigned URLs) in Quarkus 3.40 LTS Lambdas via Quarkiverse amazon-services 3.23.0. Use when adding AWS data clients, HTTP client, credentials or tenant isolation. Not for messaging, Terraform, IAM policies or Quarkus 4."
---

# Integrating Quarkus Amazon data clients (DynamoDB, S3) 3.40

> Version lock: every claim applies to **Quarkiverse `quarkus-amazon-services` 3.23.0 on Quarkus 3.40 LTS** only. Research date **2026-10-28**.
> Claims tagged (unverified) or (medium confidence) were not fully confirmed against an official page; each maps to a line of the [register](./blueprints/unverified-and-risks.md#tag-to-register-mapping).
> Scope: `quarkus-amazon-dynamodb`, `quarkus-amazon-dynamodb-enhanced`, `quarkus-amazon-s3` (and the optional transfer manager) used from Lambda handlers: client configuration, HTTP client choice, credentials, region, presigned URLs, Dev Services, tenant isolation. Neighbours in this package: [developing-quarkus-amazon-lambda-v3-40](../developing-quarkus-amazon-lambda-v3-40/SKILL.md) (handlers, `function.zip`, SnapStart) and [testing-quarkus-amazon-lambda-v3-40](../testing-quarkus-amazon-lambda-v3-40/SKILL.md) (tests). By name only: `integrating-quarkus-amazon-messaging-v3-40` (SQS/SNS clients), `designing-dynamodb-nosql` (data modelling), `architecting-aws-s3-storage` (storage design), `provisioning-aws-dynamodb-v6` and `provisioning-aws-s3-v6` (Terraform), `securing-aws-iam-serverless` (IAM). Quarkus 4 and Quarkiverse 4.0.0.Beta* are out of scope.

## Version Context

| Item | Value | Source (fetched 2026-10-28) |
|---|---|---|
| Extension line | `io.quarkiverse.amazonservices` 3.23.0, GitHub release title "3.23.0 (LTS)", the only 3.23.x on Maven Central at the read date; no end-of-support date appeared on the pages read | https://github.com/quarkiverse/quarkus-amazon-services/releases ; https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-services-bom/maven-metadata.xml |
| Release date | 2026-10-01 (year inferred from Maven `lastUpdated`) (medium confidence) | https://github.com/quarkiverse/quarkus-amazon-services/releases |
| Quarkus baseline | 3.23.0 is built on Quarkus 3.40.0 (parent POM `quarkus.version` 3.40.0; release note "bump quarkus.version from 3.39.2 to 3.40.0"). Running it on patch 3.40.1.1 is not stated on a page (medium confidence) | https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-services-parent/3.23.0/quarkus-amazon-services-parent-3.23.0.pom |
| AWS SDK for Java 2.x | 2.55.6 (`awssdk.version`), AWS CRT 0.48.4, Java 17 compiler source/target | same parent POM |
| BOM | `io.quarkiverse.amazonservices:quarkus-amazon-services-bom:3.23.0` (coordinates from Maven Central only; the docs pages do not show them) | https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-services-bom/3.23.0/quarkus-amazon-services-bom-3.23.0.pom |
| Quarkus 3.40 | LTS, released 2026-09-30, community-maintained until 2027-09-30; patch 3.40.1.1 (2026-10-19) | https://quarkus.io/releases |
| Docs set | versioned pages `3.23.x`; read through a summarising fetch tool (coverage limits L1 to L5 in the register) | https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/ |
| Next line | 4.0.0.Beta1 to Beta3 is the Quarkus 4 line: reject | https://github.com/quarkiverse/quarkus-amazon-services/releases |

**Version-lifetime risk** (details in [register](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- 3.23.0 was released 2026-10-01 and read 2026-10-28; its docs may still change. Pin 3.23.0.
- `/dev/` docs and 4.0.0.Beta* notes (Floci default, renamed modules) do not apply here.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Always-do patterns with code (BOM, HTTP client artifact, credentials, injection)](./blueprints/always-do-patterns.md)
- [Data access patterns (streams, pagination, presigning, item size, enhanced client)](./blueprints/data-access-patterns.md)
- [Tenant isolation primitives](./blueprints/tenant-isolation.md)
- [Dev Services](./blueprints/dev-services.md)
- [Ask-first decisions: HTTP client, JVM vs native, region](./blueprints/ask-first-decisions.md)
- [Ask-first decisions: tenant model, presigner, enhanced client, large objects, Dev Services provider](./blueprints/ask-first-data-decisions.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [Limits and production readiness](./blueprints/limits-and-production-readiness.md)
- [Verification Loop](./blueprints/verification-loop.md)
- [Migration notes](./blueprints/migration-notes.md)
- [Unverified and risks register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Import the 3.23.0 BOM and declare the extensions without versions.** The BOM manages the extensions and imports the AWS SDK BOM ([BOM POM](https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-services-bom/3.23.0/quarkus-amazon-services-bom-3.23.0.pom)). See [A1](./blueprints/always-do-patterns.md#a1-bom-and-extensions).
- **Add exactly the HTTP client artifact that matches `*-client.type`.** The extensions declare every transport as optional ([S3 page](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-s3.html)). See [A2](./blueprints/always-do-patterns.md#a2-http-client-artifact).
- **Keep `quarkus.<svc>.aws.credentials.type=default` in Lambda.** The default chain resolves the execution-role keys and survives SnapStart ([AWS SDK Lambda guide](https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/lambda-optimize-starttime.html)). See [A3](./blueprints/always-do-patterns.md#a3-default-credentials-chain).
- **Inject the SDK clients through CDI and reuse them.** No client construction per invocation ([SDK best practices](https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/best-practices.html)). See [A4](./blueprints/always-do-patterns.md#a4-inject-and-reuse-clients).
- **Close every `ResponseInputStream` from `S3Client.getObject`.** An unclosed stream keeps the HTTP connection busy ([SDK best practices](https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/best-practices.html)). See [A5](./blueprints/data-access-patterns.md#a5-close-response-streams).
- **Paginate every Query and Scan until `LastEvaluatedKey` is absent.** One call returns at most 1 MB ([DynamoDB pagination](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Query.Pagination.html)). See [A6](./blueprints/data-access-patterns.md#a6-paginate-query-and-scan).
- **Presign with a short `signatureDuration` and treat the URL as a bearer token.** Role-signed URLs die with the role session ([S3 presigned URLs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html)). See [A7](./blueprints/data-access-patterns.md#a7-short-presigned-urls).
- **Restrict item access with `dynamodb:LeadingKeys` + `ForAllValues:StringEquals`.** The condition keys are documented on the DynamoDB conditions page ([DynamoDB conditions](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/specifying-conditions.html)). See [A8](./blueprints/tenant-isolation.md#a8-leadingkeys-for-dynamodb); the `Scan` exclusion is the second Never Do row.
- **Scope S3 access to a per-principal prefix with an IAM policy variable in the resource ARN** ([IAM policy variables](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_variables.html)). See [A9](./blueprints/tenant-isolation.md#a9-s3-prefix-policy-variable).
- **Keep each DynamoDB item under 400 KB, names included.** ([Constraints](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Constraints.html)). See [A10](./blueprints/data-access-patterns.md#a10-item-size-limit).
- **Leave `endpoint-override` unset when you rely on Dev Services.** ([dev-services page](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/dev-services.html)). See [A11](./blueprints/dev-services.md#a11-no-endpoint-override-with-dev-services).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| HTTP client type | `url` (Quarkiverse default), `apache`, `apache5`, async `netty`, or `aws-crt` (AWS recommends CRT for Lambda; Quarkiverse warns the CRT native library "is not done by default", [common features](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/common-features.html); [AWS SDK](https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/lambda-optimize-starttime.html)). Embedding CRT in a native `function.zip` is (unverified). See [C1](./blueprints/ask-first-decisions.md#c1-http-client-type) | "JVM + SnapStart or native? Sync or async clients? If native, accept the CRT packaging work or stay on `url`?" |
| JVM + SnapStart vs native for this unit | Credentials must stay on `default` with SnapStart; native has the CRT packaging limit. See [C2](./blueprints/ask-first-decisions.md#c2-jvm-snapstart-or-native-consequences) | "Which ADR did the project choose?" |
| Region | Leave `quarkus.<svc>.aws.region` unset (whether 3.23.0 delegates to the SDK chain, and so picks `AWS_REGION`, is not stated on a page and was not resolved: (medium confidence)) or set it per environment. See [C3](./blueprints/ask-first-decisions.md#c3-region) | "Single region? Is a deploy-time smoke test acceptable?" |
| Tenant isolation tier | IAM-enforced pool, app-filtered pool, or silo; applying `LeadingKeys` or an S3 prefix policy variable to a tenant id is (medium confidence). See [C4](./blueprints/ask-first-data-decisions.md#c4-tenant-isolation-model) | "Which isolation tier does each data set need? Where is the verified tenant claim?" |
| Obtaining an `S3Presigner` | Inject (support is (medium confidence)), build once, or per call. See [C5](./blueprints/ask-first-data-decisions.md#c5-s3presigner) | "May a test confirm `@Inject S3Presigner`; otherwise build once?" |
| Enhanced client schema | Bean, builder or `@NamedDynamoDbTable`. See [C6](./blueprints/ask-first-data-decisions.md#c6-enhanced-client-schema) | "Is the entity a JavaBean? Does the table name vary per environment?" |
| Large objects | Bytes or file, stream, Transfer Manager, presigned direct transfer. See [C7](./blueprints/ask-first-data-decisions.md#c7-large-objects) | "Object size range? Must bytes pass through the function?" |
| Dev Services provider | `localstack` (default; medium confidence, M10), `ministack`, `moto`, `floci`; the 3.23.x page contradicts itself on sharing and on `quarkus.s3.devservices.enabled`: cite both, assert neither (unverified; [dev-services page](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/dev-services.html)). See [C8](./blueprints/ask-first-data-decisions.md#c8-dev-services-provider) | "Does CI have Docker?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Put static access keys in `application.properties` of a Lambda ([S3 page](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-s3.html)) | `quarkus.s3.aws.credentials.type=default`, the execution role ([Lambda env vars](https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html)) |
| Rely on access-key environment variables for credentials on a function that uses or may use SnapStart; with SnapStart the runtime uses container credentials (`AWS_CONTAINER_CREDENTIALS_FULL_URI`) instead of access-key env vars "to prevent credentials from expiring before the function is restored" ([AWS SnapStart activation](https://docs.aws.amazon.com/lambda/latest/dg/snapstart-activate.html)) | `quarkus.dynamodb.aws.credentials.type=default` ([AWS SDK Lambda guide](https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/lambda-optimize-starttime.html)) |
| Read a `ResponseInputStream` without closing it ([SDK best practices](https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/best-practices.html)) | try-with-resources around `s3.getObject(...)` |
| Treat one `query` call as the full result ([pagination](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Query.Pagination.html)) | `queryPaginator(...)` or the enhanced `PageIterable` ([SDK pagination](https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/pagination.html)) |
| Take the tenant id from the request path alone, or `Scan` in a tenant-scoped policy; `Scan` "returns all items regardless of the leading keys" ([DynamoDB conditions](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/specifying-conditions.html)) | Take the tenant from the verified token and `Query` on that partition key |
| Expect a role-signed presigned URL to live for its full `signatureDuration` ([S3 presigned URLs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html)) | A short `signatureDuration` such as 10 minutes; the client requests a fresh URL |
| Set a global `endpoint-override` to localhost ([dev-services page](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/dev-services.html)) | Leave it unset; Dev Services supply the endpoint in dev and test |
| Follow 4.0.0.Beta* or `/dev/` docs for a 3.23.x project ([releases](https://github.com/quarkiverse/quarkus-amazon-services/releases)) | Use `3.23.0` and the `3.23.x` docs |

Full ❌/✅ code: [never-do patterns](./blueprints/never-do-patterns.md). Unconfirmed items: [register](./blueprints/unverified-and-risks.md).

## Quick Reference

Defaults are stated per key (page: 3.23.x S3, DynamoDB, common-features and dev-services pages).

| Key or item | Default or value | Source |
|---|---|---|
| `quarkus.s3.sync-client.type`, `quarkus.dynamodb.sync-client.type` | `url`; values `url`, `apache`, `apache5`, `aws-crt` | https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-s3.html ; https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-dynamodb.html |
| `quarkus.s3.async-client.type`, `quarkus.dynamodb.async-client.type` | `netty`; values `netty`, `aws-crt` | https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-s3.html ; https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-dynamodb.html |
| `quarkus.s3.aws.credentials.type`, `quarkus.dynamodb.aws.credentials.type` | `default` | https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-s3.html ; https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-dynamodb.html |
| `quarkus.s3.aws.region`, `quarkus.dynamodb.aws.region` | no default | https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-s3.html ; https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-dynamodb.html |
| `quarkus.dynamodbenhanced.create-table-schemas` | `true` (medium confidence, M10); `client-extensions` has no default listed | https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-dynamodb.html |
| `quarkus.s3.path-style-access` | `false` (medium confidence, M10) | https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-s3.html |
| `quarkus.s3.sync-client.connection-timeout` / `socket-timeout` | `2S` / `30S` (medium confidence, M10) | https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-s3.html |
| `quarkus.s3.async-client.max-concurrency` | `50` (medium confidence, M10) | https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-s3.html |
| `quarkus.s3.telemetry.enabled` | `false` (medium confidence, M10) | https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-s3.html |
| `quarkus.aws.devservices.provider` | `localstack` and image `localstack/localstack:4.13` (medium confidence, M10) | https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/dev-services.html |
| Item, Query, batch limits | 400 KB item; 1 MB per Query/Scan; BatchGetItem 100 items / 16 MB; BatchWriteItem 25 / 16 MB | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Constraints.html |
| Presigned URL maximum | SDK: up to 7 days, capped by the signing credentials (temporary credentials: the URL expires with them) | https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html |
| Lambda build artifact | `function.zip` from the Quarkus build; IaC through `provisioning-aws-*-v6` | https://quarkus.io/version/3.40/guides/aws-lambda |

## External Resources

All fetched 2026-10-28.

- Quarkiverse DynamoDB: https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-dynamodb.html
- Quarkiverse S3: https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-s3.html
- Quarkiverse common features: https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/common-features.html
- Quarkiverse Dev Services: https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/dev-services.html
- AWS SDK for Java Lambda start time: https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/lambda-optimize-starttime.html
- S3 presigned URLs: https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html
- Full bibliography: [unverified and risks](./blueprints/unverified-and-risks.md#source-bibliography)
