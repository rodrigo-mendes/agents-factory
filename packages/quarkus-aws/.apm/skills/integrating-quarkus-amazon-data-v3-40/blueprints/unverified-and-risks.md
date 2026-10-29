# Unverified Register, Risks and Bibliography

Research date 2026-10-28. Back to [SKILL.md](../SKILL.md). The research reports a quality score of 84%, a deep run using all 3 iterations, 7 triangulated claims and a Complex domain tier. Family facts verified by the orchestrator on 2026-10-28 keep the tags of the family facts file.

## Contents

- [Version-lifetime risk](#version-lifetime-risk)
- [Unverified items](#unverified-items)
- [Irresolvable items](#irresolvable-items)
- [Medium-confidence items](#medium-confidence-items)
- [Coverage limits](#coverage-limits)
- [Resolved items](#resolved-items)
- [Tag to register mapping](#tag-to-register-mapping)
- [Source Bibliography](#source-bibliography)

## Version-lifetime risk

- Quarkiverse 3.23.0 was released 2026-10-01 and the docs were read 2026-10-28 (the release is stated by the releases page; the year of the date is inferred, (medium confidence), M9). The 3.23.x pages are new and may change.
- Quarkus 3.40 is LTS, released 2026-09-30, community-maintained until 2027-09-30; latest patch 3.40.1.1 (2026-10-19). Quarkus 4.0.0 is "Upcoming" with no date (High; https://quarkus.io/releases). Quarkiverse 4.0.0.Beta1 to Beta3 is the Quarkus 4 line and is rejected for this skill.
- No search for a CVE against 3.23.0 or the AWS SDK 2.55.6 was made; do not read the absence of a finding as "no CVE".

## Unverified items

10 unverified items (do not assert them). U1 to U9 come from the research register; U10 comes from the family facts and research contradictions 1 and 2.

| ID | Item | Impact and workaround |
|---|---|---|
| U1 | What fails at build or run time when the HTTP client artifact for the configured `*-client.type` is missing | Low; always add the artifact (A2) |
| U2 | CDI scope of the produced `DynamoDbClient` and `S3Client` beans | Low; follow-up: source at tag 3.23.0 (consumers of the processor) |
| U3 | How to embed the AWS CRT native library in a Quarkus native Lambda `function.zip` (Quarkiverse only says "not done by default") | Blocks C1 option B for native; stay on `url` or ask |
| U4 | `LeadingKeys` with `StringLike` or prefix match (tenant prefix inside a composite partition key) | Affects the key design of C4 option A; use the whole partition key value |
| U5 | "Store large values in S3 and keep a pointer item" as an AWS-documented DynamoDB pattern | Low; A10 stands on its own |
| U6 | Whether `@NamedDynamoDbTable` accepts a config-expression table name | Use `enhanced.table(name, schema)` when the name varies |
| U7 | Quarkiverse 3.23.x config keys for `apiCallTimeout` and `apiCallAttemptTimeout`; `SdkWarmUp` integration | Ask; do not invent keys |
| U8 | Per-request tenant-scoped credentials with injected singleton clients (no Quarkiverse page) | Ask the user; do not invent a recipe |
| U9 | Whether `S3Presigner.builder()` without a region uses the default region chain (stated for service clients only); a Quarkus property expression of `${AWS_REGION}` for the region (Quarkus config page not read) | Set the region explicitly or smoke-test |
| U10 | Dev Services page contradictions: sharing ("Sharing is disabled by default in dev mode" versus table default `shared=true`) and `quarkus.s3.devservices.enabled` ("(default to true)" versus blank default column) | Cite both statements, assert neither |

## Irresolvable items

1 irresolvable item (research iterations exhausted; the skill text tags it (unverified)). It is kept as its own class because the research proved it cannot be settled from documentation. The former second item (I2, region delegation) was merged with M8 into the single tag (medium confidence).

| ID | Item | Reason and workaround |
|---|---|---|
| I1 | Lifetime of Lambda execution-role sessions, the real upper bound of a role-signed presigned URL | The re:Post page returned HTTP 403 and no docs page states it (iteration 2). F6 says "keep it short" without a number; use 10-minute URLs (AWS example); follow-up is a human check in a deployed function or AWS Support |

## Medium-confidence items

10 medium-confidence items (M8 absorbs the former I2).

| ID | Item | Why medium |
|---|---|---|
| M1 | Running 3.23.0 on Quarkus 3.40.1.1 (built on 3.40.0; patch-level difference) | No page states the pairing. The "built on 3.40.0" fact itself is High (parent POM) |
| M2 | `apache5` value pairs with the `apache5-client` artifact | Inferred from the POM and the value name |
| M3 | `env-variable` credentials type equals the SDK `EnvironmentVariableCredentialsProvider` | Inferred from the value name |
| M4 | `@Inject S3Presigner` support | Source at tag shows presigner wiring; the final registration consumer was not read |
| M5 | Tenant id as `LeadingKeys` value from `${aws:PrincipalTag/...}` on a tenant-scoped session | Composition of two High pages; no single page shows it |
| M6 | Tenant prefix in S3 with the same policy-variable technique | Composition |
| M7 | SaaS whitepaper statements | Both pages are marked "for historical reference only"; one shows its policy only as an image |
| M8 | Whether Quarkiverse 3.23.0 region resolution delegates to the SDK chain, so that `AWS_REGION` is picked up in Lambda (single tag; merged with the former I2) | The docs list omits `AWS_REGION` while the SDK chain includes it; not resolved (iteration 3, budget exhausted); source at tag 3.23.0 (common runtime region provider) not read. Use an explicit region per environment or a deploy-time smoke test |
| M9 | Release date 2026-10-01 | Read from the releases page rendering ("released 01 Oct"); year inferred from Maven `lastUpdated` 2026 |
| M10 | Quarkiverse config defaults extracted from summarised pages (L1) and not recorded verbatim: `quarkus.s3.sync-client.connection-timeout` `2S`, `socket-timeout` `30S`, `quarkus.s3.async-client.max-concurrency` `50`, `quarkus.s3.telemetry.enabled` `false`, `quarkus.s3.path-style-access` `false`, `quarkus.dynamodbenhanced.create-table-schemas` `true`; the Dev Services default provider `localstack` and the provider images (`localstack/localstack:4.13`, `ministackorg/ministack:latest`, `motoserver/moto:latest`, `floci/floci:latest`) (family rule 13) | The pages were read through a tool that summarises and caps quotes at 125 characters (L1); no verbatim row is recorded |

## Coverage limits

5 coverage limits (parts of pages not read, or read through summarisation).

| ID | Limit |
|---|---|
| L1 | Quarkiverse doc pages were read through a fetch tool that summarises and caps quotes at 125 characters; config defaults were extracted from those summaries (DynamoDB page, 104,004 characters, in two passes) |
| L2 | `AbstractAmazonServiceProcessor` was read as an excerpt; the consumer of `AmazonClientExtensionBuildItem` was not read |
| L3 | The S3 runtime directory listing may be incomplete ("View all files") |
| L4 | `ddb-en-client-getting-started` rendered only its dependency section |
| L5 | The OpenTelemetry for Amazon Services page (3.23.x) was not read |

## Resolved items

- The Quarkus baseline of 3.23.0 (formerly medium in the family facts) is resolved to High: parent POM `quarkus.version` 3.40.0 plus the release note "bump quarkus.version from 3.39.2 to 3.40.0". Only the 3.40.1.1 runtime pairing stays medium (M1).
- The 400 KB item size was missing from the service quotas page and is resolved on the Constraints page.
- Research contradiction 5 (AWS SDK "Minimize dependency injection" versus the Quarkiverse CDI model): the AWS page names DI frameworks generally and whether it applies to Quarkus build-time DI is not stated; it is not used as a rule in this skill.

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (medium confidence) Quarkiverse 3.23.0 on Quarkus 3.40.1.1 | SKILL.md Version Context; migration-notes matrix | M1 |
| (medium confidence) `apache5` to `apache5-client` pairing | always-do-patterns A2; ask-first-decisions C1 | M2 |
| (medium confidence) `@Inject S3Presigner` support | SKILL.md Ask First; ask-first-data-decisions C5 | M4 |
| (medium confidence) tenant id from `${aws:PrincipalTag/...}` as LeadingKeys value | SKILL.md Ask First C4 (Always Do keeps only the High parts); tenant-isolation header and A8; ask-first-data-decisions C4 | M5 |
| (medium confidence) tenant prefix in S3 with a policy variable | tenant-isolation A9; ask-first-data-decisions C4 and C5 | M6 |
| (medium confidence) SaaS whitepaper statements | tenant-isolation limits; ask-first-data-decisions C4 (never-do F5 only points to them) | M7 |
| (medium confidence) summarised config defaults (timeouts, max-concurrency, telemetry, path-style-access, create-table-schemas) and the Dev Services default provider and provider images | SKILL.md Quick Reference; limits-and-production-readiness; dev-services provider and images | M10 |
| (medium confidence) release-date years inferred | SKILL.md Version Context; migration-notes line history; version-lifetime risk | M9 |
| (unverified) missing HTTP client artifact failure mode | always-do-patterns A2 | U1 |
| (unverified) CDI scope of produced clients | always-do-patterns A4 | U2 |
| (unverified) CRT native library in a native `function.zip` | SKILL.md Ask First; ask-first-decisions C1 | U3 |
| (unverified) `LeadingKeys` with `StringLike` | tenant-isolation limits | U4 |
| (unverified) pointer-to-S3 pattern | data-access-patterns A10 | U5 |
| (unverified) `@NamedDynamoDbTable` config-expression name | ask-first-data-decisions C6 | U6 |
| (unverified) timeout config keys, `SdkWarmUp` integration | always-do-patterns A4; ask-first-decisions C2; limits-and-production-readiness | U7 |
| (unverified) per-request tenant-scoped clients | always-do-patterns A4; tenant-isolation; ask-first-data-decisions C4 | U8 |
| (unverified) presigner region chain, `${AWS_REGION}` expression | ask-first-decisions C3; ask-first-data-decisions C5 | U9 |
| (unverified) Dev Services page contradictions | SKILL.md Ask First; dev-services | U10 |
| (unverified) role-session lifetime | data-access-patterns A7; never-do-patterns F6 | I1 (U-equivalent, irresolvable) |
| (medium confidence) region delegation to the SDK chain / `AWS_REGION` (single tag; formerly M8 + I2) | SKILL.md Ask First; ask-first-decisions C3 | M8 |
| (medium confidence) `env-variable` value equals `EnvironmentVariableCredentialsProvider` (the Never Do itself rests on the High AWS SnapStart sentences) | ask-first-decisions C2; never-do-patterns F2 (code example only) | M3 |
| (unverified) and (medium confidence) tags inside scenario expectations | evaluation-scenarios | U3, U8, U10, I1, M1, M3, M4, M5, M8 |

## Source Bibliography

All read 2026-10-28.

**Quarkiverse 3.23.x docs (versioned)**

| # | URL | Used for |
|---|---|---|
| S1 | https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/index.html | navigation only (no BOM or versions on the page) |
| S2 | https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-dynamodb.html | injection, enhanced client, config keys (L1) |
| S3 | https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-s3.html | client types, credentials, region, Transfer Manager, CRT (L1) |
| S4 | https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/dev-services.html | Dev Services providers, images, contradictions |
| S5 | https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/common-features.html | CRT native-library warning |

**Maven Central and Quarkiverse GitHub**

| # | URL | Used for |
|---|---|---|
| S6 | https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-services-bom/maven-metadata.xml | versions (3.x latest 3.23.0; 4.0.0.Beta3 latest overall) |
| S7 | https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-dynamodb/maven-metadata.xml | artifact versions |
| S8 | https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-services-bom/3.23.0/quarkus-amazon-services-bom-3.23.0.pom | managed artifacts |
| S9 | https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-services-parent/3.23.0/quarkus-amazon-services-parent-3.23.0.pom | Quarkus, SDK, CRT, Java baselines |
| S10 | https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-s3/3.23.0/quarkus-amazon-s3-3.23.0.pom | optional HTTP clients |
| S11 | https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-dynamodb/3.23.0/quarkus-amazon-dynamodb-3.23.0.pom | optional HTTP clients |
| S12 | https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-dynamodb-enhanced/3.23.0/quarkus-amazon-dynamodb-enhanced-3.23.0.pom | enhanced extension |
| S13 | https://github.com/quarkiverse/quarkus-amazon-services/releases | release notes, line history |
| S14 | https://raw.githubusercontent.com/quarkiverse/quarkus-amazon-services/3.23.0/s3/runtime/src/main/java/io/quarkiverse/amazon/s3/runtime/S3Recorder.java | presigner builder (the runtime directory listing may be incomplete, L3) |
| S15 | https://raw.githubusercontent.com/quarkiverse/quarkus-amazon-services/3.23.0/s3/deployment/src/main/java/io/quarkiverse/amazon/s3/deployment/S3Processor.java | presigner wiring |
| S16 | https://raw.githubusercontent.com/quarkiverse/quarkus-amazon-services/3.23.0/common/deployment/src/main/java/io/quarkiverse/amazon/common/deployment/AbstractAmazonServiceProcessor.java | presigner injection points (excerpt, L2) |

**AWS SDK for Java 2.x developer guide**

Base `https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/` plus: `lambda-optimize-starttime.html` (CRT recommendation, SnapStart credentials, client initialisation); `http-configuration.html` (HTTP client tradeoffs); `credentials-chain.html`; `region-selection.html`; `best-practices.html` (client reuse, streams, timeouts); `pagination.html`; `examples-s3-presign.html`; `ddb-en-client-getting-started.html` (dependency section only, L4); `ddb-en-client-gs-tableschema.html` (bean rules); `ddb-en-client-use-multirecord.html` (PageIterable).

**AWS service guides**

Base `https://docs.aws.amazon.com/` plus: `amazondynamodb/latest/developerguide/Constraints.html` (limits); `.../ServiceQuotas.html`; `.../Query.Pagination.html`; `.../specifying-conditions.html` (LeadingKeys); `AmazonS3/latest/userguide/using-presigned-url.html`; `AmazonS3/latest/userguide/example-bucket-policies.html` (folder section read from saved output); `IAM/latest/UserGuide/reference_policies_variables.html`; `lambda/latest/dg/configuration-envvars.html`; `prescriptive-guidance/latest/presigned-url-best-practices/overview.html`; `prescriptive-guidance/latest/agentic-ai-multitenant/enforcing-tenant-isolation.html`.

**Secondary (official but historical, medium at most, M7)**: https://docs.aws.amazon.com/whitepapers/latest/saas-tenant-isolation-strategies/pooled-storage-isolation-strategies.html (policy shown only as an image) ; https://docs.aws.amazon.com/whitepapers/latest/saas-architecture-fundamentals/tenant-isolation.html.

**Family facts (orchestrator-verified)**: https://quarkus.io/releases ; https://quarkus.io/version/3.40/guides/aws-lambda ; the parent POM (S9).

**Rejected**: https://repost.aws/knowledge-center/presigned-url-s3-bucket-expiration (HTTP 403, not read; basis of I1). Third-party search hits (CloudThat, hidekazu-konishi, advancedweb, oneuptime, Substack, pcg.io) were community sources and are rejected under the source hierarchy.
