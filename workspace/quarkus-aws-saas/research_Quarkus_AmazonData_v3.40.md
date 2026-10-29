# Research — Quarkiverse quarkus-amazon-services 3.23.x (DynamoDB + S3) on Quarkus 3.40 LTS

> Unit U4 of the quarkus-aws-saas family -> future skill `integrating-quarkus-amazon-data-v3-40` (package `quarkus-aws`).
> Source need: "DynamoDB and S3 from Quarkus Lambdas".
> Target version: Quarkiverse `quarkus-amazon-services` **3.23.0** (the only 3.23.x on Maven Central at the read date), built on Quarkus **3.40.0**, used by applications on Quarkus **3.40.1.1** LTS.
> All pages were read on **2026-10-28**. Tags follow `_family_rules_v3.40.md`: `(medium confidence)`, `(unverified)`; coverage limits are listed as L-items in Research Gaps.
> Scope approval: relayed from `workspace/quarkus-aws-saas/PIPELINE_STATE.md#approvals` (G1 "Approve, start pilot U1", G2 "Fix pilot, then fan-out (Recommended)", both 2026-10-28). This document did not run its own plan gate (see Agent Operation Notes).

---

## Metadata

```yaml
Full_Name: Quarkiverse Quarkus Amazon Services — DynamoDB, DynamoDB Enhanced and S3 extensions
Target_Version: 3.23.0 (3.23.x line; only release on Maven Central at 2026-10-28)
Release_Date: 2026-10-01 (GitHub release "3.23.0 (LTS)", "released 01 Oct")
Support_Status: LTS per the GitHub release title; no end-of-support date found (unverified)
Quarkus_Baseline: quarkus.version 3.40.0 in quarkus-amazon-services-parent-3.23.0.pom; target apps on Quarkus 3.40.1.1
AWS_SDK_Baseline: awssdk.version 2.55.6; awscrt.version 0.48.4 (parent POM 3.23.0)
Java_Baseline: maven.compiler.source/target 17 (parent POM 3.23.0)
Primary_Docs: https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/
Official_Repo: https://github.com/quarkiverse/quarkus-amazon-services (tag 3.23.0)
Research_Date: 2026-10-28
Domain_Complexity: Complex   # multi-service, credentials, presigned bearer URLs, multi-tenant isolation
Research_Depth: deep
Max_Iterations: 3
Gap_Loop_Ran: true
Iterations_Used: 3 of 3
Triangulated_Count: 7
Unverified_Count: 9
Irresolvable_Count: 2
Medium_Count: 9
Research_Quality_Score: 84%   # (total claims ~126 - unverified 9 - irresolvable 2 - partial-evidence 9) / 126 (approximate; see note in Agent Operation Notes)
```

---

## Executive Summary

Quarkiverse `quarkus-amazon-services` exposes AWS SDK for Java 2.x service clients "through configuration properties and CDI injection" (https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/index.html, read 2026-10-28). For this unit the relevant extensions are `quarkus-amazon-dynamodb`, `quarkus-amazon-dynamodb-enhanced` and `quarkus-amazon-s3` (plus the optional `quarkus-amazon-s3-transfer-manager`), all managed at `${project.version}` = 3.23.0 by `io.quarkiverse.amazonservices:quarkus-amazon-services-bom:3.23.0`, which also imports `software.amazon.awssdk:bom` at 2.55.6 (BOM and parent POM on Maven Central, read 2026-10-28). The parent POM of 3.23.0 pins `quarkus.version` 3.40.0, which **upgrades family fact 17 from medium to High** for "3.23.0 is built on Quarkus 3.40.0"; running it on Quarkus 3.40.1.1 is a patch-level difference that no page states compatibility for `(medium confidence)`. The next line, 4.0.0.Beta1–Beta3, is the Quarkus 4 line ("feat: bump to quarkus 4") and is out of scope (family rule 1).

What matters in 3.23.x for Lambda: (1) the extensions declare every HTTP transport (`url-connection-client`, `apache-client`, `apache5-client`, `netty-nio-client`, `aws-crt-client`) as **optional**, so the application must add the one matching `quarkus.<svc>.sync-client.type` (default `url`) / `async-client.type` (default `netty`); (2) `quarkus.<svc>.aws.credentials.type` defaults to `default`, the SDK default chain, which in Lambda resolves the execution-role keys that Lambda puts in `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY`/`AWS_SESSION_TOKEN`; (3) Dev Services start a LocalStack-based stack in dev/test unless `endpoint-override` is configured, so `endpoint-override` and Dev Services are mutually exclusive; (4) the enhanced client no longer needs `@RegisterForReflection` on `@DynamoDbBean` classes and builds table schemas at startup (`quarkus.dynamodbenhanced.create-table-schemas`, default `true`). The AWS SDK guide recommends AWS CRT HTTP clients for Lambda, while the Quarkiverse docs warn that since AWS CRT 0.31.0 the native library "must be embedded in the docker image. This is not done by default" — the HTTP client choice is therefore an Ask-First decision tied to the JVM+SnapStart vs native ADR (family rule 3).

Three critical patterns: **close every `ResponseInputStream`** from `S3Client.getObject` (connection-pool exhaustion otherwise, AWS SDK best practices); **paginate every Query/Scan** (1 MB per call, `LastEvaluatedKey`; use SDK paginators or enhanced `PageIterable`); **presigned URLs are bearer tokens whose real lifetime is capped by the signing credentials** (Lambda signs with temporary role credentials, so the URL expires with the role session even if a longer `signatureDuration` is set). Multi-tenant isolation is documented by AWS only as primitives: `dynamodb:LeadingKeys` with `ForAllValues:StringEquals` on the partition key, `Scan` excluded because it "returns all items regardless of the leading keys", and per-prefix S3 access with policy variables such as `${aws:PrincipalTag/team}`. Domain complexity is **Complex** (credentials, bearer URLs, tenant isolation, native/HTTP-client interplay).

---

## Architectural Guardrails

> Confidence legend: 🟢 High (versioned official page, Maven Central POM, source at tag, or current AWS documentation page read by the researcher) | 🟡 Medium (inference, historical whitepaper, partial evidence) | 🔴 Low (community; not used).
> Confidence follows family rule 5 (evidence rule): a single versioned official source is High; the ✓✓ badge records triangulation separately (see Agent Operation Notes).

### ✅ Mandatory Patterns

**A1 — Import the 3.23.0 BOM and declare the extensions without versions**
> Confidence: 🟢 High | [✓✓ Triangulated | maven-metadata.xml (lastUpdated 2026-10-17) + BOM POM 3.23.0 + GitHub release 3.23.0 (2026-10-01)]
- Why: the BOM manages `quarkus-amazon-common`, `quarkus-amazon-dynamodb`, `quarkus-amazon-dynamodb-enhanced`, `quarkus-amazon-s3`, `quarkus-amazon-s3-transfer-manager` (and `-deployment`) at `${project.version}` and imports `software.amazon.awssdk:bom` at `${awssdk.version}` (2.55.6 in the parent POM), so SDK HTTP-client artifacts are version-aligned too.
- Code:
  ```xml
  <!-- Quarkiverse amazon-services 3.23.0 on Quarkus 3.40 LTS -->
  <dependencyManagement>
    <dependencies>
      <dependency>
        <groupId>io.quarkiverse.amazonservices</groupId>
        <artifactId>quarkus-amazon-services-bom</artifactId>
        <version>3.23.0</version>
        <type>pom</type>
        <scope>import</scope>
      </dependency>
    </dependencies>
  </dependencyManagement>
  <dependencies>
    <dependency>
      <groupId>io.quarkiverse.amazonservices</groupId>
      <artifactId>quarkus-amazon-dynamodb</artifactId>
    </dependency>
    <dependency>
      <groupId>io.quarkiverse.amazonservices</groupId>
      <artifactId>quarkus-amazon-dynamodb-enhanced</artifactId>
    </dependency>
    <dependency>
      <groupId>io.quarkiverse.amazonservices</groupId>
      <artifactId>quarkus-amazon-s3</artifactId>
    </dependency>
  </dependencies>
  ```
- Source: https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-services-bom/maven-metadata.xml (2026-10-28); https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-services-bom/3.23.0/quarkus-amazon-services-bom-3.23.0.pom (2026-10-28); https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-services-parent/3.23.0/quarkus-amazon-services-parent-3.23.0.pom (2026-10-28)
- Note: the BOM is not stated on the docs pages (index and common-features pages do not show BOM coordinates); the coordinates come from Maven Central only.

**A2 — Add exactly the HTTP client artifact that matches the configured client type**
> Confidence: 🟢 High | [✓✓ Triangulated | amazon-s3 3.23.x page + amazon-dynamodb 3.23.x page + extension POMs 3.23.0]
- Why: in `quarkus-amazon-s3-3.23.0.pom` and `quarkus-amazon-dynamodb-3.23.0.pom` the SDK service artifact excludes `netty-nio-client`, `url-connection-client`, `apache-client`, `apache5-client`, and each transport is re-declared `optional`; the docs tell you to "add a URL connection client dependency" for the default sync client and "the Netty HTTP client dependency" for the default async client.
- Defaults (per key, family rule 10):
  - `quarkus.s3.sync-client.type` — default `url`; values `url`, `apache`, `apache5`, `aws-crt`.
  - `quarkus.s3.async-client.type` — default `netty`; values `netty`, `aws-crt`.
  - `quarkus.dynamodb.sync-client.type` — default `url`; values `url`, `apache`, `apache5`, `aws-crt`.
  - `quarkus.dynamodb.async-client.type` — default `netty`; values `netty`, `aws-crt`.
- Artifact per type (groupId `software.amazon.awssdk`, version from the imported SDK BOM): `url` -> `url-connection-client`; `apache` -> `apache-client`; `aws-crt` -> `aws-crt-client`; `netty` -> `netty-nio-client`. The `apache5` -> `apache5-client` pairing is inferred from the POM's optional `apache5-client` and the value name `(medium confidence)`.
- Code:
  ```xml
  <!-- default sync client type 'url' (3.23.x) -->
  <dependency>
    <groupId>software.amazon.awssdk</groupId>
    <artifactId>url-connection-client</artifactId>
  </dependency>
  ```
- Source: https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-s3.html (2026-10-28); https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-dynamodb.html (2026-10-28); https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-s3/3.23.0/quarkus-amazon-s3-3.23.0.pom (2026-10-28); https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-dynamodb/3.23.0/quarkus-amazon-dynamodb-3.23.0.pom (2026-10-28)
- What fails when the artifact is missing is not stated on these pages `(unverified)`.

**A3 — Keep `quarkus.<svc>.aws.credentials.type=default` in Lambda (execution role via the default chain)**
> Confidence: 🟢 High | [✓✓ Triangulated | amazon-s3 3.23.x config reference + Lambda env-vars page + SDK default chain page]
- Why: `quarkus.s3.aws.credentials.type` / `quarkus.dynamodb.aws.credentials.type` default to `default` ("the provider will attempt to identify the credentials automatically"); the SDK default chain checks environment variables `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`; Lambda sets those to "The access keys obtained from the function's execution role". The SDK Lambda guide adds: "If you intend to use Lambda SnapStart for Java at some point, you should rely on the default credentials provider chain", because on SnapStart activation the access-key environment variables "are not available to the Java SDK".
- Code:
  ```properties
  # Quarkiverse 3.23.x — explicit for readability; 'default' is already the default value
  quarkus.dynamodb.aws.credentials.type=default
  quarkus.s3.aws.credentials.type=default
  ```
- Source: https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-s3.html (2026-10-28); https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-dynamodb.html (2026-10-28); https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html (2026-10-28); https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/credentials-chain.html (2026-10-28); https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/lambda-optimize-starttime.html (2026-10-28)
- Note: the Quarkiverse page's own description of the `default` chain lists system properties, environment variables, profile file, ECS container and EC2 instance profile; the SDK page lists web identity as well. Both include the environment-variable step used by Lambda.

**A4 — Inject the SDK clients via CDI and reuse them; never build a client per invocation**
> Confidence: 🟢 High | [✓✓ Triangulated | Quarkiverse amazon-dynamodb/amazon-s3 3.23.x + SDK best practices + SDK Lambda start-time page]
- Why: the extension produces `DynamoDbClient`, `DynamoDbAsyncClient`, `DynamoDbEnhancedClient`, `DynamoDbEnhancedAsyncClient`, `S3Client`, `S3AsyncClient` (and `@S3Crt S3AsyncClient`, `S3TransferManager`) as injectable beans. AWS: "Each service client maintains its own HTTP connection pool… We recommend sharing a single instance of the client… All service clients are thread safe", and "We recommend initializing an SDK client outside of the Lambda handler method".
- Code:
  ```java
  // Quarkiverse 3.23.x injection points (types as documented)
  @Inject DynamoDbClient dynamo;                 // sync
  @Inject DynamoDbAsyncClient dynamoAsync;       // async
  @Inject DynamoDbEnhancedClient enhanced;       // enhanced sync
  @Inject S3Client s3;                           // sync
  @Inject S3AsyncClient s3Async;                 // async
  @Inject @S3Crt S3AsyncClient s3Crt;            // io.quarkiverse.amazon.s3.runtime.S3Crt (needs aws-crt-client)
  ```
- Source: https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-dynamodb.html (2026-10-28); https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-s3.html (2026-10-28); https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/best-practices.html (2026-10-28); https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/lambda-optimize-starttime.html (2026-10-28)
- The bean scope Quarkiverse uses for these producers is not stated on the pages `(unverified)`.

**A5 — Close every `ResponseInputStream` from `S3Client.getObject` as soon as possible**
> Confidence: 🟢 High | single official source (SDK best practices); Quarkiverse S3 page shows only `getObjectAsBytes` / `AsyncResponseTransformer.toPublisher()`
- Why: "the input stream is a direct stream of data from the HTTP connection and the underlying HTTP connection can't be reused until all data from the stream has been read and the stream is closed. If these rules are not followed, the client can run out of resources by allocating too many open, but unused, HTTP connections."
- Code:
  ```java
  // AWS SDK 2.55.x via Quarkiverse 3.23.0 S3Client
  try (ResponseInputStream<GetObjectResponse> in =
           s3.getObject(GetObjectRequest.builder().bucket(bucket).key(key).build())) {
      process(in);   // read fully, then the stream is closed by try-with-resources
  }
  ```
- Source: https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/best-practices.html (2026-10-28)

**A6 — Paginate every DynamoDB Query/Scan (1 MB per call); stop only when `LastEvaluatedKey` is absent**
> Confidence: 🟢 High | [✓✓ Triangulated | DynamoDB Constraints page + DynamoDB Query.Pagination page + SDK pagination page + SDK enhanced multirecord page]
- Why: "The result set from a `Query` is limited to 1 MB per call" (same for `Scan`); "The only way to know when you have reached the end of the result set is when `LastEvaluatedKey` is empty", and with a `FilterExpression` "a page can return zero matching items and still include a `LastEvaluatedKey`". SDK 2.x autopagination methods (`queryPaginator`, `scanPaginator`, `listObjectsV2Paginator`) and the enhanced client's `PageIterable`/`PagePublisher` handle this.
- Code:
  ```java
  // low-level client (SDK 2.55.x): all pages, lazily
  dynamo.queryPaginator(QueryRequest.builder()
          .tableName(table)
          .keyConditionExpression("pk = :pk")
          .expressionAttributeValues(Map.of(":pk", AttributeValue.builder().s(pk).build()))
          .limit(25)                   // items evaluated per page, not a total cap
          .build())
      .items()
      .forEach(this::handle);

  // enhanced client: PageIterable
  table.query(QueryEnhancedRequest.builder()
          .queryConditional(QueryConditional.keyEqualTo(k -> k.partitionValue(pk)))
          .build())
      .items()
      .forEach(this::handle);
  ```
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Constraints.html (2026-10-28); https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Query.Pagination.html (2026-10-28); https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/pagination.html (2026-10-28); https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/ddb-en-client-use-multirecord.html (2026-10-28)

**A7 — Presign with a short `signatureDuration`; treat the URL as a bearer token**
> Confidence: 🟢 High | [✓✓ Triangulated | S3 user guide presigned URLs + SDK presign page + Prescriptive Guidance presigned-URL overview]
- Why: "presigned URLs are bearer tokens that grant access to those who possess them"; with SDKs "the expiration time can be set as high as 7 days", but for temporary credentials "the URL expires when the credential expires… even if the URL was created with a later expiration time", and for IAM role credentials "The presigned URL expires when the role session expires". Lambda signs with the execution role's temporary keys (A3). S3 checks expiry "at the time of the HTTP request". Header-mapped fields (`metadata`, `serverSideEncryption`, `acl`, `storageClass`) must be sent by the caller as `x-amz-*` headers, or put into the URL with `putRawQueryParameter`; `signedHeaders()` shows what the caller must send.
- Code:
  ```java
  // AWS SDK 2.55.x — upload URL for one tenant-scoped key, 10 minutes (as in the AWS example)
  PresignedPutObjectRequest p = presigner.presignPutObject(PutObjectPresignRequest.builder()
          .signatureDuration(Duration.ofMinutes(10))
          .putObjectRequest(PutObjectRequest.builder().bucket(bucket).key(key).build())
          .build());
  String url = p.url().toExternalForm();
  Set<String> mustSend = p.signedHeaders().keySet();   // e.g. [host]
  ```
- Source: https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html (2026-10-28); https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/examples-s3-presign.html (2026-10-28); https://docs.aws.amazon.com/prescriptive-guidance/latest/presigned-url-best-practices/overview.html (2026-10-28)
- How `presigner` is obtained in Quarkus is an Ask-First item (C5).

**A8 — Restrict item access with `dynamodb:LeadingKeys` + `ForAllValues:StringEquals`, and never grant `Scan` in that policy**
> Confidence: 🟢 High | [✓✓ Triangulated | DynamoDB fine-grained access page (Examples 1, 2, 6) + IAM policy-variables page]
- Why: `dynamodb:LeadingKeys` "Represents the first key attribute of a table—in other words, the partition key… you must use the `ForAllValues` modifier when using `LeadingKeys` in a condition." Example 2: "The list of actions does not include permissions for `Scan` because `Scan` returns all items regardless of the leading keys." Policy variables need `"Version":"2012-10-17"`. A variable with no value makes `StringEquals`/`StringLike` not match, "and the policy statement does not take effect".
- Code (IaC itself belongs to `provisioning-aws-dynamodb-v6`; family rule 4):
  ```json
  {
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": ["dynamodb:GetItem","dynamodb:BatchGetItem","dynamodb:Query",
                 "dynamodb:PutItem","dynamodb:UpdateItem","dynamodb:DeleteItem","dynamodb:BatchWriteItem"],
      "Resource": ["arn:aws:dynamodb:us-west-2:123456789012:table/GameScores"],
      "Condition": { "ForAllValues:StringEquals": { "dynamodb:LeadingKeys": ["${www.amazon.com:user_id}"] } }
    }]
  }
  ```
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/specifying-conditions.html (2026-10-28); https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_variables.html (2026-10-28)
- Using a tenant identifier (instead of a user id) as the leading-key value, and sourcing it from `${aws:PrincipalTag/<tenant-tag>}` on a tenant-scoped session, is an application of these two pages that no single AWS page shows `(medium confidence)` — see C4.

**A9 — Scope S3 access to a per-principal prefix with a policy variable in `Resource` and `s3:prefix`**
> Confidence: 🟢 High | [✓✓ Triangulated | IAM policy-variables page + S3 example bucket policies ("Grant users access to specific folders")]
- Why: the IAM page shows `"Resource": ["arn:aws:s3:::amzn-s3-demo-bucket/${aws:PrincipalTag/team}/*"]` and `"Condition": {"StringLike": {"s3:prefix": ["${aws:PrincipalTag/team}/*"]}}` on `s3:ListBucket`; the S3 page shows the same per-folder shape for `home/JohnDoe/`.
- Code:
  ```json
  {
    "Version": "2012-10-17",
    "Statement": [
      { "Effect": "Allow", "Action": ["s3:ListBucket"],
        "Resource": ["arn:aws:s3:::amzn-s3-demo-bucket"],
        "Condition": {"StringLike": {"s3:prefix": ["${aws:PrincipalTag/team}/*"]}} },
      { "Effect": "Allow", "Action": ["s3:GetObject","s3:PutObject"],
        "Resource": ["arn:aws:s3:::amzn-s3-demo-bucket/${aws:PrincipalTag/team}/*"] }
    ]
  }
  ```
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_variables.html (2026-10-28); https://docs.aws.amazon.com/AmazonS3/latest/userguide/example-bucket-policies.html (2026-10-28)
- Tenant-prefix use is the same application step as A8 `(medium confidence)`.

**A10 — Keep each DynamoDB item under 400 KB (names + values)**
> Confidence: 🟢 High | single official source
- Why: "The maximum item size in DynamoDB is 400 KB, which includes both attribute name binary length (UTF-8 length) and attribute value lengths… The attribute name counts towards the size limit." 1 KB = 1024 bytes in DynamoDB.
- Code:
  ```java
  // Design rule, not an API: large payloads go to S3 and the item keeps the key (pattern itself: see gap U5)
  item.setPayloadKey("tenants/" + tenantId + "/docs/" + docId);
  ```
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Constraints.html (2026-10-28)
- The "store large values in S3 and keep a pointer" pattern is not stated on the Constraints page `(unverified)` (U5).

**A11 — Do not configure `endpoint-override` when you want Dev Services**
> Confidence: 🟢 High | [✓✓ Triangulated | dev-services 3.23.x + amazon-dynamodb 3.23.x + amazon-s3 3.23.x]
- Why: Dev Services start "a containerized AWS stack in dev mode and when running tests" unless, among other exceptions, "the `endpoint-override` is configured"; property text: "Dev Services starts a container unless `aws.endpoint-override` is set". S3/DynamoDB `devservices.enabled`: "If this is true and endpoint-override is not configured then a local AWS stack will be started". (Family/U6 fact; testing depth belongs to U6.)
- Code:
  ```properties
  # Quarkiverse 3.23.x — leave endpoint-override unset; Dev Services provide the local endpoint in dev/test
  # quarkus.dynamodb.endpoint-override=http://localhost:4566   <- setting this disables Dev Services for DynamoDB
  quarkus.s3.devservices.buckets=my-local-bucket
  ```
- Source: https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/dev-services.html (2026-10-28); https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-dynamodb.html (2026-10-28); https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-s3.html (2026-10-28)

### ⚠️ Conditional Patterns

**C1 — HTTP client: `url` (Quarkiverse default) vs `aws-crt` (AWS SDK Lambda recommendation) vs `apache`/`apache5` vs `netty`**
> Confidence: 🟢 High for each quoted statement; which is fastest for a Quarkus Lambda is not measured by any page `(unverified)`
- Options: A) `url` + `url-connection-client`; B) `aws-crt` + `aws-crt-client`; C) `apache5`/`apache`; D) async `netty` + `netty-nio-client`.
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A `url` | Quarkiverse default; SDK: "minimize the number of jars and third-party libraries" | SDK: no HTTP PATCH, no configurable idle connection timeout | Sync DynamoDB/S3 calls, minimal dependencies |
  | B `aws-crt` | SDK: "For working with AWS Lambda, we recommend the AwsCrtHttpClient… AwsCrtAsyncHttpClient"; CRT footnote "we recommend that you use the AWS CRT-based HTTP clients if possible" | Quarkiverse: "Since AWS CRT version 0.31.0, native library must be embedded in the docker image. This is not done by default." SDK: `javax.net.ssl.keyStore`/`trustStore` system properties not supported | JVM (+SnapStart) Lambdas; native only with the CRT native library handled `(unverified how, for the Lambda zip)` |
  | C `apache5`/`apache` | SDK: low latency over high throughput; Apache5 is the SDK default sync client since 2.46.0 | SDK: "Slower startup time compared to other HTTP clients"; `ApacheHttpClient` (4.x) is deprecated by the SDK | Long-lived JVM services, not cold-start-sensitive Lambdas |
  | D `netty` | Default async client in both SDK and Quarkiverse | SDK: "Slower startup time compared to other HTTP clients" | Async clients without CRT |

- Agent: "Ask the user: JVM+SnapStart or native (family rule 3)? Sync or async clients? If native, accept the CRT native-library packaging work or stay on `url`?"
- Source: https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/common-features.html (2026-10-28); https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/http-configuration.html (2026-10-28); https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/lambda-optimize-starttime.html (2026-10-28); https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-s3.html (2026-10-28)
- The Quarkiverse 3.23.x docs say nothing about cold start for any client type (common-features, S3 and DynamoDB pages read; no "cold"/"startup" statement except Dev Services bucket creation).

**C2 — JVM + SnapStart vs native (family rule 3) — consequences for this unit only**
> Confidence: 🟢 High for the credential quote; the rest is the family ADR
- Options: A) JVM + SnapStart; B) native (`provided.al2023`, family fact 13).
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A JVM+SnapStart | SDK guidance for CRT client applies directly; SDK `SdkWarmUp` can warm clients before the snapshot | Must keep the default credentials chain (env-var provider loses keys on SnapStart activation) | Teams on managed Java runtimes |
  | B native | No JVM startup | CRT native library "must be embedded… not done by default"; `@RegisterForReflection` needs only for non-enhanced classes per the Quarkiverse note | Lowest cold start without SnapStart |

- Agent: "Ask which ADR the project chose before picking the HTTP client (C1) or credential provider."
- Source: https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/lambda-optimize-starttime.html (2026-10-28); https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/common-features.html (2026-10-28)

**C3 — Region: rely on the provider chain vs set `quarkus.<svc>.aws.region`**
> Confidence: 🟡 Medium
- Options: A) leave `quarkus.s3.aws.region` / `quarkus.dynamodb.aws.region` unset; B) set them explicitly per environment.
- Facts: both keys have no default; the S3 page says "If not set, region is retrieved via the default providers chain in the following order: `aws.region` system property, `region` property from the profile file, Instance profile file" (it does **not** list `AWS_REGION`). The SDK chain checks `AWS_REGION` ("The Lambda container sets this environment variable"). Whether Quarkiverse 3.23.0 delegates to the SDK chain (and so picks `AWS_REGION` in Lambda) is not stated `(medium confidence)`; setting it to a Quarkus property expression of `AWS_REGION` is a Quarkus-config technique not covered by these pages `(unverified)`.
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A chain | Region-independent code | Depends on undocumented delegation `(medium confidence)` | Verified once in a deployed function |
  | B explicit | Deterministic; SDK: explicit region "shortcuts the SDK's default Region lookup" | Per-environment config | Multi-region or strict environments |

- Agent: "Ask whether the function is single-region and whether a deploy-time smoke test confirms region resolution."
- Source: https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-s3.html (2026-10-28); https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/region-selection.html (2026-10-28); https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/lambda-optimize-starttime.html (2026-10-28)

**C4 — Multi-tenant data isolation model (only AWS-documented primitives)**
> Confidence: 🟡 Medium for the tenant application; 🟢 High for each primitive
- Options: A) pooled table, partition key = tenant id, IAM `dynamodb:LeadingKeys` on a tenant-scoped session; B) pooled table with application-side filtering only; C) silo (table/bucket per tenant).
- Facts: AWS whitepapers (both marked "for historical reference only") say "the tenant identifier would be in the leading key, constraining access to data for a given tenant" and "the fact that a tenant user is authenticated does not mean that your system has achieved isolation" `(medium confidence: historical whitepapers)`. Prescriptive Guidance (agentic multi-tenant) describes acquiring "tenant-scoped credentials from the AWS Identity and Access Management (IAM) service". `LeadingKeys` with `StringEquals` matches the **whole** partition key value; restricting a partition key that merely *starts with* the tenant id (e.g. `TENANT#t1#...`) would need `StringLike` with a wildcard, which no AWS page shows for `LeadingKeys` `(unverified)`.
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A IAM-enforced pool | Isolation enforced by IAM even if code forgets a filter; S3 equivalent via A9 | Needs tenant-scoped credentials (STS session with a tenant tag) instead of the plain execution role; `Scan` excluded | Regulated tenants, shared tables |
  | B app-filter pool | Simplest; plain execution role | One missing key condition leaks data (whitepaper: authentication is not isolation) | Low-risk internal data |
  | C silo | Coarse, per-resource IAM | More resources, quotas (2,500 tables per Region initial quota) | Few large tenants |

- Agent: "Ask the user which isolation tier each data set needs; any option must take the tenant from the verified token, never from the path alone (family rule 6). Hand IAM/STS provisioning to `provisioning-aws-*-v6` and data modelling to `designing-dynamodb-nosql`."
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/specifying-conditions.html (2026-10-28); https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_variables.html (2026-10-28); https://docs.aws.amazon.com/whitepapers/latest/saas-tenant-isolation-strategies/pooled-storage-isolation-strategies.html (2026-10-28, historical); https://docs.aws.amazon.com/whitepapers/latest/saas-architecture-fundamentals/tenant-isolation.html (2026-10-28, historical); https://docs.aws.amazon.com/prescriptive-guidance/latest/agentic-ai-multitenant/enforcing-tenant-isolation.html (2026-10-28); https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/ServiceQuotas.html (2026-10-28)
- How a Quarkus Lambda builds per-request tenant-scoped clients from the injected singletons is not documented by Quarkiverse 3.23.x `(unverified)`.

**C5 — Obtaining an `S3Presigner`: inject it vs build it yourself**
> Confidence: 🟡 Medium for injection
- Options: A) `@Inject S3Presigner presigner;`; B) build one `S3Presigner` at startup with `S3Presigner.builder()` and close it on shutdown; C) `S3Presigner.create()` in try-with-resources per call (AWS example style).
- Facts: the 3.23.x S3 page has **no** occurrence of "presign"/"Presigner". Source at tag 3.23.0: `S3Processor` overrides `presignerClientName()` (returns `S3Presigner`) and `presignerBuilderClass()`; `S3Recorder.createPresignerBuilder()` applies the S3 service configuration (path-style, accelerate, checksum, chunked encoding, ARN region) and dualstack; `AbstractAmazonServiceProcessor` creates presigner builders only for presigner injection points. The final bean registration happens in a consumer not read here, so injection support is `(medium confidence)`. AWS examples create the presigner with `S3Presigner.create()` inside try-with-resources.
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A inject | Same config as `S3Client` (path-style, dualstack) | Undocumented `(medium confidence)`; verify in a test | Projects that already test the injection |
  | B build once | Documented SDK API; reused | Must mirror region/credentials/path-style yourself | Default safe choice |
  | C per call | Matches AWS example | Re-creates the presigner per request | Rare presigning |

- Agent: "Ask whether a test confirming `@Inject S3Presigner` is acceptable; otherwise use B."
- Source: https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-s3.html (2026-10-28); https://raw.githubusercontent.com/quarkiverse/quarkus-amazon-services/3.23.0/s3/runtime/src/main/java/io/quarkiverse/amazon/s3/runtime/S3Recorder.java (2026-10-28); https://raw.githubusercontent.com/quarkiverse/quarkus-amazon-services/3.23.0/s3/deployment/src/main/java/io/quarkiverse/amazon/s3/deployment/S3Processor.java (2026-10-28); https://raw.githubusercontent.com/quarkiverse/quarkus-amazon-services/3.23.0/common/deployment/src/main/java/io/quarkiverse/amazon/common/deployment/AbstractAmazonServiceProcessor.java (2026-10-28); https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/examples-s3-presign.html (2026-10-28)

**C6 — Enhanced client: annotated bean vs builder schema; `@NamedDynamoDbTable` injection**
> Confidence: 🟢 High
- Options: A) `@DynamoDbBean` class + `TableSchema.fromClass(...)` (Quarkiverse example) / `TableSchema.fromBean(...)` (AWS example); B) `TableSchema.builder(...)` in code; C) inject `@NamedDynamoDbTable("name") DynamoDbTable<T>`.
- Facts: Quarkiverse 3.23.x: "TableSchemas generated from bean classes are registered and cached at startup", "You don't need to explicitely instantiate them at class-load time", "Note that you don't need to add `@RegisterForReflection` anymore"; config `quarkus.dynamodbenhanced.create-table-schemas` (default `true`) and `quarkus.dynamodbenhanced.client-extensions` (no default listed). AWS: bean must have a public no-arg constructor and getters/setters, at least `@DynamoDbPartitionKey`; "You can skip the cost of bean introspection if you define the table schema in code."
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A bean | Least code; schema built at startup by the extension | JavaBean shape | Most tables |
  | B builder | No introspection | Verbose, manual | Hot paths or non-JavaBean classes |
  | C named table | No manual `enhanced.table(...)` | Table name fixed at build | One table per entity |

- Agent: "Ask whether the entity can follow the JavaBean shape; whether the table name varies per environment (then use `enhanced.table(name, schema)`)."
- Source: https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-dynamodb.html (2026-10-28); https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/ddb-en-client-gs-tableschema.html (2026-10-28)
- Whether `@NamedDynamoDbTable` accepts a config-expression name is not stated `(unverified)`.

**C7 — Large objects: bytes vs stream vs file vs Transfer Manager vs presigned direct transfer**
> Confidence: 🟢 High for each API; Lambda memory/`/tmp` sizing is out of scope (U1)
- Options: A) `getObjectAsBytes` / `RequestBody.fromFile` (Quarkiverse example); B) `getObject` -> `ResponseInputStream` (A5); C) `quarkus-amazon-s3-transfer-manager` (`@Inject S3TransferManager`); D) presigned URL so the client transfers directly to S3 (A7).
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A bytes/file | Simplest | Whole object in memory or on disk | Small objects |
  | B stream | Constant memory | Must read fully and close promptly | Streaming transforms |
  | C Transfer Manager | Multipart, progress | Extra extension; `PresignedFileDownload` "does not support pause and resume" | Large files inside the function |
  | D presigned | Bytes bypass Lambda | Bearer-token handling, header signing rules | Browser/mobile uploads and downloads |

- Agent: "Ask object size range and whether bytes must pass through the function."
- Source: https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-s3.html (2026-10-28); https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/best-practices.html (2026-10-28); https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/examples-s3-presign.html (2026-10-28)

**C8 — Dev Services provider (dev/test only; depth in U6)**
> Confidence: 🟢 High
- Options: `quarkus.aws.devservices.provider` default `localstack`; also `ministack`, `moto`, `floci`. Default images: `localstack/localstack:4.13`, `ministackorg/ministack:latest`, `motoserver/moto:latest`, `floci/floci:latest`. "Dev Services for Amazon Services does not verify if the chosen stack actually implements a mock for a given service." Without Docker: "In test mode, it will cause the test to fail… Either disable Dev Services or configure the `endpoint-override`."
- Tradeoffs: LocalStack (default, pinned image) vs `:latest`-tagged alternatives (non-reproducible).
- Agent: "Ask whether CI has Docker; defer the provider decision to U6."
- Source: https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/dev-services.html (2026-10-28)
- 4.0.0.Beta1 makes Floci the default — Quarkus 4 line, not applicable to 3.23.x (family rule 1).

### 🚫 Forbidden Patterns

**F1 — Static access keys in `application.properties` (or `func`-style env config) of a Lambda**
> Severity: Critical
> Confidence: 🟢 High
- Why: Lambda already provides temporary execution-role keys to the default chain (A3); `static` is a non-default type that uses "the access key and secret access key specified in the `static-provider` section of the config"; Quarkiverse uses `static` only in its *local* quickstart example. A presigned URL signed with IAM-user keys can stay valid "up to 7 days", unlike role-signed URLs.
- Impact: long-lived keys in configuration/VCS; bypasses the execution role and its rotation.
- ❌ Wrong:
  ```properties
  quarkus.s3.aws.credentials.type=static
  quarkus.s3.aws.credentials.static-provider.access-key-id=AKIA...
  quarkus.s3.aws.credentials.static-provider.secret-access-key=...
  ```
- ✅ Correct:
  ```properties
  # Quarkiverse 3.23.x: default chain -> Lambda execution role (AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY/AWS_SESSION_TOKEN)
  quarkus.s3.aws.credentials.type=default
  ```
- Source: https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-s3.html (2026-10-28); https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html (2026-10-28); https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html (2026-10-28)

**F2 — `EnvironmentVariableCredentialsProvider` hard-wired on a function that uses (or may use) SnapStart**
> Severity: High
> Confidence: 🟢 High
- Why: "when SnapStart is activated, the Java runtime sets container credentials environment variables. On activation, the environment variables used by the `EnvironmentVariableCredentialsProvider`—access key environment variables—are not available to the Java SDK."
- Impact: credential failures after SnapStart restore.
- ❌ Wrong:
  ```properties
  quarkus.dynamodb.aws.credentials.type=env-variable
  ```
- ✅ Correct:
  ```properties
  quarkus.dynamodb.aws.credentials.type=default
  ```
- Source: https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/lambda-optimize-starttime.html (2026-10-28); https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-s3.html (2026-10-28) (value list includes `env-variable`)
- The mapping `env-variable` -> SDK `EnvironmentVariableCredentialsProvider` is inferred from the value name `(medium confidence)`; the ✅ alternative (`default`) is High (family rule 9).

**F3 — Reading a `ResponseInputStream` without closing it**
> Severity: High
> Confidence: 🟢 High
- Why/Impact: the HTTP connection "can't be reused until all data from the stream has been read and the stream is closed"; otherwise "the client can run out of resources".
- ❌ Wrong:
  ```java
  InputStream in = s3.getObject(req);   // never closed
  return parse(in);
  ```
- ✅ Correct:
  ```java
  try (ResponseInputStream<GetObjectResponse> in = s3.getObject(req)) {
      return parse(in);
  }
  ```
- Source: https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/best-practices.html (2026-10-28)

**F4 — One Query call treated as the full result, or stopping on an empty page**
> Severity: High
> Confidence: 🟢 High
- Why/Impact: 1 MB per call; with a filter "a page can return zero matching items and still include a `LastEvaluatedKey`" -> silent data loss.
- ❌ Wrong:
  ```java
  List<Map<String, AttributeValue>> all = dynamo.query(req).items();   // first 1 MB page only
  ```
- ✅ Correct:
  ```java
  dynamo.queryPaginator(req).items().forEach(this::handle);   // SDK autopagination
  ```
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Query.Pagination.html (2026-10-28); https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/pagination.html (2026-10-28)

**F5 — Tenant id taken from the request path alone, or `Scan` in a tenant-scoped policy**
> Severity: Critical
> Confidence: 🟢 High (AWS quotes); the "token, not path" rule is family rule 6
- Why: "the fact that a tenant user is authenticated does not mean that your system has achieved isolation" (historical whitepaper) and `Scan` "returns all items regardless of the leading keys" (DynamoDB FGAC page).
- Impact: cross-tenant reads.
- ❌ Wrong:
  ```java
  String tenant = request.getPathParameters().get("tenantId");   // caller-controlled
  table.scan().items().stream().filter(i -> tenant.equals(i.getTenantId()));
  ```
- ✅ Correct:
  ```java
  String tenant = verifiedTenantFromToken();   // claim from the authenticated principal (see U2/U3 security skills)
  table.query(QueryEnhancedRequest.builder()
          .queryConditional(QueryConditional.keyEqualTo(k -> k.partitionValue(tenant)))
          .build()).items().forEach(this::handle);
  ```
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/specifying-conditions.html (2026-10-28); https://docs.aws.amazon.com/whitepapers/latest/saas-architecture-fundamentals/tenant-isolation.html (2026-10-28, historical — the isolation quote is (medium confidence)); family rule 6 (`workspace/quarkus-aws-saas/_family_rules_v3.40.md`)
- `verifiedTenantFromToken()` is a placeholder; how the token is read belongs to the Lambda security unit.

**F6 — Expecting a role-signed presigned URL to live for its full `signatureDuration`**
> Severity: Moderate
> Confidence: 🟢 High
- Why: with IAM role credentials "The presigned URL expires when the role session expires, even if you specify a longer expiration time."
- Impact: `ExpiredToken`/403 for clients holding "valid" URLs.
- ❌ Wrong:
  ```java
  .signatureDuration(Duration.ofDays(7))   // signed by the Lambda execution role
  ```
- ✅ Correct:
  ```java
  .signatureDuration(Duration.ofMinutes(10))   // short-lived; client requests a fresh URL when needed
  ```
- Source: https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html (2026-10-28); https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/examples-s3-presign.html (2026-10-28)

**F7 — Global `endpoint-override` pointing at localhost**
> Severity: High
> Confidence: 🟢 High
- Why: it disables Dev Services (A11) and sends deployed traffic to the override URI ("The endpoint URI with which the SDK should communicate").
- Impact: deployed function calls `localhost:4566` and fails; local stack no longer auto-started.
- ❌ Wrong:
  ```properties
  quarkus.s3.endpoint-override=http://localhost:4566
  ```
- ✅ Correct:
  ```properties
  # leave quarkus.s3.endpoint-override unset; Dev Services supply the endpoint in dev/test
  quarkus.s3.devservices.buckets=my-local-bucket
  ```
- Source: https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-s3.html (2026-10-28); https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/dev-services.html (2026-10-28)

**F8 — Following 4.0.0.Beta* or `/dev/` docs for a 3.23.x project**
> Severity: Moderate
> Confidence: 🟢 High
- Why: 4.0.0.Beta1 "feat: bump to quarkus 4", Floci default Dev Services stack, no per-service container isolation, `quarkus-amazon-ce` renamed — none of this applies to 3.23.0 on Quarkus 3.40 (family rules 1, 2).
- ❌ Wrong:
  ```xml
  <version>4.0.0.Beta3</version>
  ```
- ✅ Correct:
  ```xml
  <version>3.23.0</version>
  ```
- Source: https://github.com/quarkiverse/quarkus-amazon-services/releases (2026-10-28); https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-services-bom/maven-metadata.xml (2026-10-28)

---

## Migration Guide

> Confidence: 🟢 High | Sources: https://github.com/quarkiverse/quarkus-amazon-services/releases (2026-10-28) + parent POM 3.23.0 (2026-10-28)

**Breaking Changes (3.22.x -> 3.23.0)**: none listed in the 3.23.0 release notes. Dependency bumps: "bump quarkus.version from 3.39.2 to 3.40.0"; "bump software.amazon.awssdk:bom from 2.54.13 to 2.55.6".

**Line history (for context only)**: 3.22.0 (2026-09-07) Quarkus 3.38.1, SDK 2.51.4; 3.22.1 (2026-09-10) Quarkus 3.39.2, SDK 2.54.13; 3.23.0 (2026-10-01, "LTS") Quarkus 3.40.0, SDK 2.55.6.

**SDK-level changes visible through the BOM (AWS SDK docs, not Quarkiverse)**: `Apache5HttpClient` "replaced `ApacheHttpClient` as the default synchronous client in version 2.46.0" and `ApacheHttpClient` is deprecated (https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/http-configuration.html, 2026-10-28). Quarkiverse keeps its own default `sync-client.type=url`; it does not follow the SDK default.

**Not applicable (Quarkus 4 line)**: 4.0.0.Beta1 breaking changes (Floci default, no container isolation, OpenTelemetry on by default, `quarkus-amazon-ce` -> `quarkus-amazon-costexplorer`) — reject for 3.23.x.

**Upgrade Steps (from 3.22.x)**:
1. Move the application to Quarkus 3.40.x (family fact 8).
2. Set `quarkus-amazon-services-bom` to `3.23.0`.
3. Re-check HTTP-client artifacts against the `*-client.type` keys (A2).
4. Run the verification commands below.

**Compatibility Matrix**:

| Dependency | Min | Max | Notes |
|------------|-----|-----|-------|
| Quarkus | 3.40.0 (build baseline) | 3.40.x | 3.40.1.1 runtime pairing `(medium confidence)`; Quarkus 4 -> use 4.0.0.Beta* (out of scope) |
| AWS SDK for Java 2.x | 2.55.6 | via BOM | imported by `quarkus-amazon-services-bom` |
| AWS CRT | 0.48.4 | via BOM | `software.amazon.awssdk.crt:aws-crt` managed by the BOM |
| Java | 17 (compiler source/target) | — | Lambda Java runtimes: family fact 15 |

---

## Implementation Blueprint

> Confidence: 🟢 High for each API used (cited inline); the assembled class is an illustrative composition, not an official example.

**Lifecycle**:
```properties
# application.properties — Quarkiverse 3.23.x on Quarkus 3.40 LTS
quarkus.dynamodb.sync-client.type=url        # default; requires url-connection-client
quarkus.s3.sync-client.type=url              # default; requires url-connection-client
quarkus.dynamodb.aws.credentials.type=default
quarkus.s3.aws.credentials.type=default
quarkus.dynamodbenhanced.create-table-schemas=true   # default
# region: see C3 (no default; chain behaviour medium confidence)
# endpoint-override: leave unset (Dev Services in dev/test, real endpoints in Lambda)
```

```java
// Init: clients are CDI beans produced by the extensions (A4); no client construction in the handler.
// Usage: DynamoDB enhanced + S3 stream + presign. Cleanup: try-with-resources for streams (A5).
@ApplicationScoped
public class DocumentStore {

    @Inject DynamoDbEnhancedClient enhanced;   // quarkus-amazon-dynamodb-enhanced 3.23.0
    @Inject S3Client s3;                       // quarkus-amazon-s3 3.23.0

    // TableSchema: cached at startup by the extension; AWS: designed to be static and immutable
    static final TableSchema<Doc> SCHEMA = TableSchema.fromClass(Doc.class);

    public void save(Doc d) {
        enhanced.table("docs", SCHEMA).putItem(d);   // item must stay < 400 KB (A10)
    }

    public void forEachDoc(String tenantId, Consumer<Doc> sink) {
        enhanced.table("docs", SCHEMA)
                .query(QueryEnhancedRequest.builder()
                        .queryConditional(QueryConditional.keyEqualTo(k -> k.partitionValue(tenantId)))
                        .build())
                .items()                 // PageIterable -> all pages (A6)
                .forEach(sink);
    }

    public long countBytes(String bucket, String key) throws IOException {
        try (ResponseInputStream<GetObjectResponse> in =
                 s3.getObject(GetObjectRequest.builder().bucket(bucket).key(key).build())) {
            return in.transferTo(OutputStream.nullOutputStream());
        }
    }
}

@DynamoDbBean
public class Doc {                      // JavaBean: public no-arg ctor + getters/setters
    private String tenantId;
    private String docId;
    @DynamoDbPartitionKey public String getTenantId() { return tenantId; }
    public void setTenantId(String t) { this.tenantId = t; }
    @DynamoDbSortKey public String getDocId() { return docId; }
    public void setDocId(String d) { this.docId = d; }
}
```
- Sources: https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-dynamodb.html (2026-10-28) (`TableSchema.fromClass`, injection, caching); https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/ddb-en-client-gs-tableschema.html (2026-10-28) (JavaBean rules, "static and immutable"); https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/ddb-en-client-use-multirecord.html (2026-10-28); https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/best-practices.html (2026-10-28).
- `@ApplicationScoped` on the holder class is a standard Quarkus CDI choice not covered by these pages (see the `developing-quarkus-arc-v3-40` skill).

**Integration**: Quarkiverse 3.23.x ↔ S3Presigner (C5 option B — documented SDK API)
```java
@ApplicationScoped
public class UploadUrls {
    private final S3Presigner presigner = S3Presigner.builder().build();   // default region/credentials chains (C3)

    public String uploadUrl(String bucket, String tenantId, String docId) {
        String key = tenantId + "/" + docId;                                // tenant prefix (A9, medium for tenant use)
        return presigner.presignPutObject(PutObjectPresignRequest.builder()
                .signatureDuration(Duration.ofMinutes(10))
                .putObjectRequest(PutObjectRequest.builder().bucket(bucket).key(key).build())
                .build())
            .url().toExternalForm();
    }

    @PreDestroy void close() { presigner.close(); }   // S3Presigner is used in try-with-resources in the AWS examples
}
```
- Sources: https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/examples-s3-presign.html (2026-10-28). That the builder without `.region(...)` uses the default region chain is stated for service clients on the region page, not for the presigner `(unverified)`. Path-style/dualstack parity with the injected `S3Client` is lost in option B (the recorder applies them only to its own presigner builder).

**Dev Services (dev/test only)**:
```properties
# leave endpoint-override unset -> LocalStack (localstack/localstack:4.13) is started for dev and tests
quarkus.s3.devservices.buckets=docs-local
quarkus.aws.devservices.provider=localstack   # default
```
- Source: https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/dev-services.html (2026-10-28); https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-s3.html (2026-10-28)

---

## Quality Control

**Verification Commands**:
```bash
# Representative — adapt to your environment
# 1. BOM line is 3.23.0 and no Quarkus-4 line leaked in
mvn -q help:evaluate -Dexpression=project.dependencyManagement -DforceStdout | grep -c "quarkus-amazon-services-bom" 
grep -n "quarkus-amazon-services-bom" -A1 pom.xml | grep -E "3\.23\.0"     # Expected: one match
grep -nE "4\.0\.0\.Beta" pom.xml                                            # Expected: no output

# 2. The HTTP client artifact matches the configured type (A2)
mvn -q dependency:tree -Dincludes=software.amazon.awssdk:url-connection-client,software.amazon.awssdk:aws-crt-client,software.amazon.awssdk:netty-nio-client,software.amazon.awssdk:apache-client
grep -nE "quarkus\.(s3|dynamodb)\.(sync|async)-client\.type" src/main/resources/application.properties

# 3. No static keys, no global endpoint-override (F1, F7)
grep -nE "credentials\.(type=static|static-provider)" src/main/resources/application.properties   # Expected: no output
grep -nE "^quarkus\.(s3|dynamodb)\.endpoint-override" src/main/resources/application.properties   # Expected: no output

# 4. Streams closed and queries paginated (F3, F4) — heuristic
grep -rn "getObject(" src/main/java | grep -v "try (" 
grep -rnE "\.query\(|\.scan\(" src/main/java

# 5. Build the Lambda artifact (family rule 4: function.zip)
./mvnw clean package        # Expected: target/function.zip (family fact 10)
```

**Mocking / tests**: Dev Services provide the local stack for `@QuarkusTest` (A11, C8). Test patterns, mock-event-server usage and the removal of `quarkus-test-amazon-lambda` (family fact 23) belong to U6; this unit only fixes the rule "do not set `endpoint-override` if you rely on Dev Services".
```java
// Illustrative — depth in U6
@QuarkusTest
class DocumentStoreTest {
    @Inject DocumentStore store;   // clients point at the Dev Services stack automatically ("The extension client is configured automatically")
    @Test void roundTrip() { /* create table/bucket, save, read */ }
}
```
- Source: https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/dev-services.html (2026-10-28)

---

## Production Readiness

- **Performance**: reuse injected clients (A4); choose the HTTP client per C1/C2; SDK `SdkWarmUp` exists for SnapStart warm-up (https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/lambda-optimize-starttime.html, 2026-10-28) — whether Quarkiverse integrates it is not stated `(unverified)`. Set `apiCallTimeout`/`apiCallAttemptTimeout`: "The SDK provides default values… but not for API call timeouts" (https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/best-practices.html, 2026-10-28); the Quarkiverse 3.23.x key for these is not recorded `(unverified)`. Quarkiverse S3 HTTP defaults: `quarkus.s3.sync-client.connection-timeout` `2S`, `quarkus.s3.sync-client.socket-timeout` `30S`, `quarkus.s3.async-client.max-concurrency` `50` (https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-s3.html, 2026-10-28).
- **Scalability / limits** (https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Constraints.html, 2026-10-28): item 400 KB; partition key 1–2048 bytes; sort key 1–1024 bytes; Query/Scan 1 MB per call; BatchGetItem 100 items / 16 MB; BatchWriteItem 25 put/delete / 16 MB; transactions 100 unique items / 4 MB; expression string 4 KB; 300 operators per expression. Initial 2,500 tables per Region; on-demand per-table default 40,000 RRU/WRU (https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/ServiceQuotas.html, 2026-10-28). Item collections with an LSI cannot exceed 10 GB.
- **Monitoring**: SDK metrics can be collected (best-practices page); `quarkus.s3.telemetry.enabled` default `false` (S3 page); OpenTelemetry integration page exists in 3.23.x navigation but was not read `(unverified)`. Logging rules: family rule 7 (no PII, bounded tenant dimensions).
- **Security**:
  - [ ] `credentials.type=default` everywhere (A3, F1, F2).
  - [ ] IAM least privilege for the execution role; tenant isolation per C4; `Scan` excluded from LeadingKeys policies (A8).
  - [ ] Presigned URLs short-lived; consider bucket policy `s3:signatureAge` (example denies signatures older than 600000 ms) and network-path conditions `aws:SourceIp`/`aws:SourceVpce` (https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html, 2026-10-28). IaC for these -> `provisioning-aws-s3-v6`.
  - [ ] Policy variables require `"Version":"2012-10-17"`; a missing tag makes the Allow statement not take effect (IAM page).
  - [ ] `quarkus.s3.path-style-access` default `false`; "DNS style… is preferred" (S3 page).

---

## Reference Implementations

- Quarkiverse DynamoDB guide (sync/async/enhanced, `@NamedDynamoDbTable`): https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-dynamodb.html (2026-10-28)
- Quarkiverse S3 guide (sync/async, CRT `@S3Crt`, Transfer Manager): https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-s3.html (2026-10-28)
- AWS presign examples (GET/PUT, signed headers, query params): https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/examples-s3-presign.html (2026-10-28) — linked complete examples at awsdocs/aws-doc-sdk-examples commits `d73001d…` and `0a2b7b1…` (not opened).
- AWS enhanced-client paging (scan/query PageIterable/PagePublisher): https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/ddb-en-client-use-multirecord.html (2026-10-28)
- Quarkiverse source at tag 3.23.0 (S3 presigner wiring): https://github.com/quarkiverse/quarkus-amazon-services/tree/3.23.0 (2026-10-28)
- Related skills (do not duplicate): `designing-dynamodb-nosql` (data modelling), `provisioning-aws-dynamodb-v6`, `provisioning-aws-s3-v6` (Terraform), U1 Lambda packaging, U6 testing.

---

## Source Bibliography

**Primary — Quarkiverse 3.23.x docs (versioned)**
- https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/index.html — read 2026-10-28 (navigation + 2 sentences; no BOM/versions on page)
- https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-dynamodb.html — read 2026-10-28 (104,004 chars; 0–100,000 then 100,000–104,004 and a 90,000+ key listing; via tool summaries, see L1)
- https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-s3.html — read 2026-10-28 (≈70k chars, not truncated per tool; summaries, see L1)
- https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/dev-services.html — read 2026-10-28
- https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/common-features.html — read 2026-10-28

**Primary — Maven Central (POMs/metadata)**
- https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-services-bom/maven-metadata.xml — read 2026-10-28 (lastUpdated 20261017211443; latest 4.0.0.Beta3; 3.x latest 3.23.0)
- https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-dynamodb/maven-metadata.xml — read 2026-10-28
- https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-services-bom/3.23.0/quarkus-amazon-services-bom-3.23.0.pom — read 2026-10-28
- https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-services-parent/3.23.0/quarkus-amazon-services-parent-3.23.0.pom — read 2026-10-28
- https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-s3/3.23.0/quarkus-amazon-s3-3.23.0.pom — read 2026-10-28
- https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-dynamodb/3.23.0/quarkus-amazon-dynamodb-3.23.0.pom — read 2026-10-28
- https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-dynamodb-enhanced/3.23.0/quarkus-amazon-dynamodb-enhanced-3.23.0.pom — read 2026-10-28

**Primary — Quarkiverse GitHub (release notes, source at tag 3.23.0)**
- https://github.com/quarkiverse/quarkus-amazon-services/releases — read 2026-10-28
- https://github.com/quarkiverse/quarkus-amazon-services/tree/3.23.0/s3/runtime/src/main/java/io/quarkiverse/amazon/s3/runtime — read 2026-10-28 (listing possibly incomplete)
- https://raw.githubusercontent.com/quarkiverse/quarkus-amazon-services/3.23.0/s3/runtime/src/main/java/io/quarkiverse/amazon/s3/runtime/S3Recorder.java — read 2026-10-28
- https://raw.githubusercontent.com/quarkiverse/quarkus-amazon-services/3.23.0/s3/deployment/src/main/java/io/quarkiverse/amazon/s3/deployment/S3Processor.java — read 2026-10-28
- https://raw.githubusercontent.com/quarkiverse/quarkus-amazon-services/3.23.0/common/deployment/src/main/java/io/quarkiverse/amazon/common/deployment/AbstractAmazonServiceProcessor.java — read 2026-10-28 (excerpt; bean-registration consumer not read)

**Primary — AWS SDK for Java 2.x developer guide**
- https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/lambda-optimize-starttime.html — read 2026-10-28
- https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/http-configuration.html — read 2026-10-28
- https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/credentials-chain.html — read 2026-10-28
- https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/region-selection.html — read 2026-10-28
- https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/best-practices.html — read 2026-10-28
- https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/pagination.html — read 2026-10-28
- https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/examples-s3-presign.html — read 2026-10-28
- https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/ddb-en-client-getting-started.html — read 2026-10-28 (dependency section only rendered)
- https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/ddb-en-client-gs-tableschema.html — read 2026-10-28
- https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/ddb-en-client-use-multirecord.html — read 2026-10-28

**Primary — AWS service guides**
- https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Constraints.html — read 2026-10-28
- https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/ServiceQuotas.html — read 2026-10-28
- https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Query.Pagination.html — read 2026-10-28
- https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/specifying-conditions.html — read 2026-10-28
- https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html — read 2026-10-28
- https://docs.aws.amazon.com/AmazonS3/latest/userguide/example-bucket-policies.html — read 2026-10-28 (folder section read from saved output)
- https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_variables.html — read 2026-10-28
- https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html — read 2026-10-28
- https://docs.aws.amazon.com/prescriptive-guidance/latest/presigned-url-best-practices/overview.html — read 2026-10-28
- https://docs.aws.amazon.com/prescriptive-guidance/latest/agentic-ai-multitenant/enforcing-tenant-isolation.html — read 2026-10-28

**Secondary — official but historical (medium at most)**
- https://docs.aws.amazon.com/whitepapers/latest/saas-tenant-isolation-strategies/pooled-storage-isolation-strategies.html — read 2026-10-28 ("for historical reference only"; policy shown only as an image)
- https://docs.aws.amazon.com/whitepapers/latest/saas-architecture-fundamentals/tenant-isolation.html — read 2026-10-28 ("for historical reference only")

**Rejected / not usable**
- https://repost.aws/knowledge-center/presigned-url-s3-bucket-expiration — HTTP 403, not read.
- Third-party search hits (CloudThat, hidekazu-konishi, advancedweb, oneuptime, Substack, pcg.io) — community, rejected per source hierarchy.

**Family inputs applied (not edited)**: `workspace/quarkus-aws-saas/_family_facts_v3.40.md`, `workspace/quarkus-aws-saas/_family_rules_v3.40.md`, `workspace/_family_facts_v3.40.md`, `workspace/_family_rules_v3.40.md`.

---

## Research Gaps

> Register ids per inherited family rule 12: U (unverified), I (irresolvable), M (medium), L (coverage limits).

**Unverified**
```
U1 Gap: What fails at build/run time when the HTTP client artifact for the configured *-client.type is missing.
   Impact: low (A2 already requires adding it). Workaround: always add it. Follow-up: Quarkiverse source at tag 3.23.0 (common runtime).
U2 Gap: CDI scope of the produced DynamoDbClient/S3Client beans.
   Impact: low. Follow-up: source at tag 3.23.0 (AbstractAmazonServiceProcessor consumers).
U3 Gap: How to embed the AWS CRT native library in a Quarkus native Lambda function.zip (Quarkiverse only says "not done by default").
   Impact: blocks C1 option B for native. Follow-up: Quarkiverse issues/source; AWS CRT docs.
U4 Gap: LeadingKeys with StringLike/prefix match (tenant prefix inside a composite partition key).
   Impact: affects C4 option A key design. Follow-up: DynamoDB API permissions reference.
U5 Gap: "Store large values in S3 and keep a pointer item" as an AWS-documented DynamoDB pattern.
   Impact: low (A10 is High on its own). Follow-up: DynamoDB best-practices "large items" page.
U6 Gap: Whether @NamedDynamoDbTable accepts a config-expression table name.
U7 Gap: Quarkiverse 3.23.x config keys for apiCallTimeout/apiCallAttemptTimeout; SdkWarmUp integration.
U8 Gap: Per-request tenant-scoped credentials with injected singleton clients (no Quarkiverse page).
U9 Gap: Whether S3Presigner.builder() without region uses the default region chain (stated for service clients only); Quarkus property expression ${AWS_REGION} for region (Quarkus config page not read here).
```

**Irresolvable (after 3 iterations)**
```
I1 Gap: Lifetime of Lambda execution-role sessions, i.e. the real upper bound of a role-signed presigned URL.
   Impact: F6 says "keep it short" without a number. Workaround: 10-minute URLs (AWS example). Follow-up: human check in a deployed function / AWS Support.
   §7-ref: Iteration 2 — IRRESOLVABLE
I2 Gap: Whether Quarkiverse 3.23.0 region resolution delegates to the SDK chain (AWS_REGION) — the doc list omits AWS_REGION.
   Impact: C3. Workaround: explicit region per environment, or deploy-time smoke test. Follow-up: source at tag 3.23.0 (common runtime region provider).
   §7-ref: Iteration 3 — IRRESOLVABLE (not attempted beyond the docs; budget exhausted)
```

**Medium confidence**
```
M1 3.23.0 runtime compatibility with Quarkus 3.40.1.1 (built on 3.40.0; patch-level, no page states it).
M2 apache5 -> apache5-client artifact pairing (from POM + value name).
M3 env-variable credentials type == SDK EnvironmentVariableCredentialsProvider (from value name).
M4 @Inject S3Presigner support (source at tag; final registration consumer not read).
M5 Tenant id as LeadingKeys value from ${aws:PrincipalTag/...} on a tenant-scoped session (composition of two High pages).
M6 Tenant prefix in S3 via the same policy-variable technique (composition).
M7 SaaS whitepaper statements (historical reference only).
M8 Quarkiverse region resolution picking AWS_REGION in Lambda (C3; see I2).
M9 Release date 2026-10-01 read from the GitHub releases page rendering ("released 01 Oct", year inferred from Maven lastUpdated 2026).
```

**Coverage limits**
```
L1 Quarkiverse doc pages were read through a fetch tool that summarizes and caps quotes at 125 characters; config defaults were extracted from those summaries (DynamoDB page 104,004 chars covered in two passes).
L2 AbstractAmazonServiceProcessor was read as an excerpt; the consumer of AmazonClientExtensionBuildItem was not read.
L3 The S3 runtime directory listing may be incomplete ("View all files").
L4 ddb-en-client-getting-started rendered only its dependency section.
L5 The OpenTelemetry for Amazon Services page (3.23.x) was not read.
```

---

## Research Iteration Changelog

| Iteration | Section | Item | Action | Source |
|-----------|---------|------|--------|--------|
| 1 | Metadata / Migration | Quarkus baseline of 3.23.0 (family fact 17 was medium) | Resolved — parent POM `quarkus.version` 3.40.0 (High) | https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-services-parent/3.23.0/quarkus-amazon-services-parent-3.23.0.pom (2026-10-28) |
| 1 | C5 | S3Presigner absent from the 3.23.x S3 page | Updated — source at tag shows presigner builder wiring; kept (medium confidence) | https://raw.githubusercontent.com/quarkiverse/quarkus-amazon-services/3.23.0/s3/runtime/src/main/java/io/quarkiverse/amazon/s3/runtime/S3Recorder.java (2026-10-28) |
| 1 | C6 | Exact enhanced-client config keys | Resolved — `quarkus.dynamodbenhanced.create-table-schemas` (true), `quarkus.dynamodbenhanced.client-extensions` | https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-dynamodb.html (2026-10-28, offset 90000) |
| 1 | A10 / Production | 400 KB item size not on ServiceQuotas page | Resolved — Constraints page | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Constraints.html (2026-10-28) |
| 2 | A8 / A9 / C4 | Tenant isolation primitives with AWS sources | Added — IAM policy variables (`${aws:PrincipalTag/...}`), S3 folder policy, Prescriptive Guidance; whitepapers kept medium | https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_variables.html (2026-10-28) |
| 2 | F6 | Lambda execution-role session lifetime | ⚠️ IRRESOLVABLE — re:Post page 403; no docs page states it | — |
| 3 | C3 | Quarkiverse region chain vs SDK chain (AWS_REGION) | ⚠️ IRRESOLVABLE — docs list omits AWS_REGION; SDK chain includes it; source not read within budget | https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/region-selection.html (2026-10-28) |

---

## Completion Checklist

- [x] Domain complexity tier assessed and documented (Complex)
- [x] All scope areas cited (BOM, artifacts, injection, HTTP clients, credentials, region, endpoint-override/Dev Services, enhanced client/native, presigned URLs, streams, Dev Services, tenant isolation, 400 KB/1 MB limits, pagination)
- [x] Pattern counts driven by domain needs (11 Always / 8 Conditional / 8 Forbidden)
- [x] Every anti-pattern has alternative (❌/✅ side by side; ✅ options are High, family rule 9)
- [x] All CLI commands validated/marked as representative
- [x] Integration examples complete (enhanced + S3 stream + presigner)
- [x] Sources dated and linked (2026-10-28)
- [x] Security documented
- [x] 1+ copy-paste working example (illustrative composition; APIs individually sourced)
- [x] Confidence badge applied to every pattern entry
- [x] All Always-Do patterns triangulated or labelled single-source (family rule 5 keeps single versioned sources High)
- [x] Research Iteration Changelog present and complete
- [x] Research_Quality_Score calculated and added to Metadata
- [x] Every Research Gap cross-referenced in §7 (I1, I2)

---

## Agent Operation Notes

- **High Confidence (execute without asking)**: A1–A11 and F1–F8 as written; Quarkiverse 3.23.x defaults: `sync-client.type=url`, `async-client.type=netty`, `aws.credentials.type=default`, `path-style-access=false`, `devservices.buckets=default`, `quarkus.aws.devservices.provider=localstack`, `quarkus.dynamodbenhanced.create-table-schemas=true`; AWS limits (400 KB, 1 MB, 100/16 MB, 25/16 MB, 100/4 MB); presign maximum 7 days with SDK, capped by temporary credentials.
- **Medium Confidence (validate with user)**: M1–M9; C3, C4, C5.
- **Low Confidence (must ask human)**: I1, I2; U1–U9.
- **Contradictions / tensions found (report both URLs)**:
  1. Dev Services sharing: text "Sharing is disabled by default in dev mode, and is always disabled in test mode" vs reference table `quarkus.aws.devservices.<provider>.shared` default `true` — both on https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/dev-services.html.
  2. `quarkus.s3.devservices.enabled`: description "(default to true)" vs blank default column — https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-s3.html.
  3. HTTP client for Lambda: AWS recommends CRT (https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/lambda-optimize-starttime.html) while Quarkiverse defaults to `url` and warns the CRT native library is not embedded by default (https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/common-features.html). Not a factual contradiction; handled as C1.
  4. Region chain: Quarkiverse list omits `AWS_REGION` (https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-s3.html) vs SDK chain includes it (https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/region-selection.html). Handled as C3/I2.
  5. AWS SDK "Minimize dependency injection" (lambda-optimize-starttime) vs the Quarkiverse CDI model — the AWS page names DI frameworks generally; whether it applies to Quarkus build-time DI is not stated `(unverified)`; not used as a rule.
  6. Family fact 17 (3.23.0 ↔ Quarkus 3.40.0, medium) is **confirmed**, not contradicted: parent POM 3.23.0 `quarkus.version` 3.40.0 + release note "bump quarkus.version from 3.39.2 to 3.40.0" (https://github.com/quarkiverse/quarkus-amazon-services/releases). Suggest the orchestrator upgrade fact 17 to High.
- **Process notes**: P2.parallel and the P3 plan gate were not run — the caller's hard constraints forbade spawning agents and plan mode, citing the user's recorded approvals (verified present in PIPELINE_STATE.md lines 25, 29, 74). P4 was written directly (no research-synthesizer) for the same reason. The template's "single source -> Medium" triangulation rule is overridden by inherited family rule 5 (single versioned official source stays High); single-source Always-Do items (A5, A10) are labelled as such.
- **Quality score note**: claim count is an estimate from the document (≈126 discrete sourced statements); score = (126 − 9 U − 2 I − 9 M) / 126 ≈ 84%.
- **Edge Cases (pause)**: 3.23.0 released 2026-10-01 (27 days before research; inside the "<30 days" pause window of the skill — flagged, not blocking since the docs site for 3.23.x exists); no active CVE found (not searched specifically `(unverified)`).
- **Emergency Stop**: not triggered (official sources available; 3.23.x is the current 3.x line).
- **Version lock reminder**: everything here is Quarkiverse 3.23.0 / AWS SDK 2.55.6 / Quarkus 3.40 LTS. Content from 4.0.0.Beta*, `/dev/` docs or Quarkus 4 is misinformation for this skill.
