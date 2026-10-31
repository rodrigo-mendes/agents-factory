# Ask-First Decisions: tenant model, presigner, schema, large objects, Dev Services

Back to [SKILL.md](../SKILL.md). Quarkiverse 3.23.0. Fetched 2026-10-28. Every decision here is put to the user; none has a default. HTTP client, ADR and region: [ask-first decisions](./ask-first-decisions.md).

## Contents

- [C4. Tenant isolation model](#c4-tenant-isolation-model)
- [C5. S3Presigner](#c5-s3presigner)
- [C6. Enhanced client schema](#c6-enhanced-client-schema)
- [C7. Large objects](#c7-large-objects)
- [C8. Dev Services provider](#c8-dev-services-provider)

## C4. Tenant isolation model

Each primitive is High; applying it to tenants is (medium confidence). Primitives and limits: [tenant isolation](./tenant-isolation.md). Family rule 6: any option takes the tenant from the verified token, never from the path alone.

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| A. Pooled table, partition key = tenant id, IAM `dynamodb:LeadingKeys` on a tenant-scoped session | Isolation enforced by IAM even if code forgets a filter; S3 equivalent through the prefix policy | Needs tenant-scoped credentials (an STS session with a tenant tag) instead of the plain execution role; `Scan` excluded; per-request client construction is (unverified) | Regulated tenants, shared tables |
| B. Pooled table with application-side filtering only | Simplest; plain execution role | One missing key condition leaks data (whitepaper: authentication is not isolation, medium confidence) | Low-risk internal data |
| C. Silo (table or bucket per tenant) | Coarse per-resource IAM | More resources; initial quota of 2,500 tables per Region | Few large tenants |

Ask: "Which isolation tier does each data set need, and where is the verified tenant claim read?" Hand IAM and STS provisioning to `provisioning-aws-*-v6` and data modelling to `designing-dynamodb-nosql`. Sources: [DynamoDB conditions](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/specifying-conditions.html), [service quotas](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/ServiceQuotas.html), [IAM policy variables](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_variables.html).

## C5. S3Presigner

The 3.23.x S3 page has no occurrence of "presign" or "Presigner". Source at tag 3.23.0: `S3Processor` overrides `presignerClientName()` (returns `S3Presigner`) and `presignerBuilderClass()`; `S3Recorder.createPresignerBuilder()` applies the S3 service configuration (path-style, accelerate, checksum, chunked encoding, ARN region) and dualstack; `AbstractAmazonServiceProcessor` creates presigner builders only for presigner injection points. The final bean registration happens in a consumer that was not read (coverage limit L2), so injection support is (medium confidence). AWS examples create the presigner with `S3Presigner.create()` inside try-with-resources ([S3 page](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-s3.html), [S3Recorder](https://raw.githubusercontent.com/quarkiverse/quarkus-amazon-services/3.23.0/s3/runtime/src/main/java/io/quarkiverse/amazon/s3/runtime/S3Recorder.java), [S3Processor](https://raw.githubusercontent.com/quarkiverse/quarkus-amazon-services/3.23.0/s3/deployment/src/main/java/io/quarkiverse/amazon/s3/deployment/S3Processor.java), [AbstractAmazonServiceProcessor](https://raw.githubusercontent.com/quarkiverse/quarkus-amazon-services/3.23.0/common/deployment/src/main/java/io/quarkiverse/amazon/common/deployment/AbstractAmazonServiceProcessor.java), [SDK presign](https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/examples-s3-presign.html)).

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| A. `@Inject S3Presigner presigner;` | Same configuration as `S3Client` (path-style, dualstack) | Undocumented (medium confidence); verify in a test | Projects that already test the injection |
| B. Build one with `S3Presigner.builder()` at startup, close on shutdown | Documented SDK API, reused | Must mirror region, credentials and path-style yourself; region chain for the builder is (unverified) | Safe choice when A is not confirmed |
| C. `S3Presigner.create()` in try-with-resources per call | Matches the AWS example | Re-creates the presigner per request | Rare presigning |

```java
@ApplicationScoped
public class UploadUrls {
    private final S3Presigner presigner = S3Presigner.builder().build();   // option B

    public String uploadUrl(String bucket, String tenantId, String docId) {
        String key = tenantId + "/" + docId;   // tenant prefix, application is (medium confidence)
        return presigner.presignPutObject(PutObjectPresignRequest.builder()
                .signatureDuration(Duration.ofMinutes(10))
                .putObjectRequest(PutObjectRequest.builder().bucket(bucket).key(key).build())
                .build())
            .url().toExternalForm();
    }

    @PreDestroy void close() { presigner.close(); }
}
```

Option B loses path-style and dualstack parity with the injected `S3Client` (the recorder applies them only to its own presigner builder). Ask: "May a test confirm `@Inject S3Presigner`? Otherwise build once (B)."

## C6. Enhanced client schema

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| A. `@DynamoDbBean` + `TableSchema.fromClass(...)` (Quarkiverse example) or `fromBean(...)` (AWS example) | Least code; schema built at startup by the extension | JavaBean shape | Most tables |
| B. `TableSchema.builder(...)` in code | No introspection | Verbose, manual | Hot paths or non-JavaBean classes |
| C. Inject `@NamedDynamoDbTable("name") DynamoDbTable<T>` | No manual `enhanced.table(...)` | Table name fixed at build; whether it accepts a config-expression name is (unverified) | One table per entity |

Ask: "Can the entity follow the JavaBean shape? Does the table name vary per environment (then use `enhanced.table(name, schema)`)?" Sources: [DynamoDB page](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-dynamodb.html), [table schema](https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/ddb-en-client-gs-tableschema.html).

## C7. Large objects

Lambda memory and `/tmp` sizing belong to `developing-quarkus-amazon-lambda-v3-40`.

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| A. `getObjectAsBytes` or `RequestBody.fromFile` (Quarkiverse example) | Simplest | Whole object in memory or on disk | Small objects |
| B. `getObject` to `ResponseInputStream` ([A5](./data-access-patterns.md#a5-close-response-streams)) | Constant memory | Must read fully and close promptly | Streaming transforms |
| C. `quarkus-amazon-s3-transfer-manager` (`@Inject S3TransferManager`) | Multipart, progress | Extra extension; `PresignedFileDownload` "does not support pause and resume" | Large files inside the function |
| D. Presigned URL, client transfers directly ([A7](./data-access-patterns.md#a7-short-presigned-urls)) | Bytes bypass Lambda | Bearer-token handling, header signing rules | Browser or mobile uploads and downloads |

Ask: "Object size range, and must the bytes pass through the function?" Sources: [S3 page](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-s3.html), [best practices](https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/best-practices.html), [SDK presign](https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/examples-s3-presign.html).

## C8. Dev Services provider

Options and images: [dev services](./dev-services.md#provider-and-images). Tradeoff: LocalStack (default, pinned image `localstack/localstack:4.13`) versus `:latest`-tagged alternatives (non-reproducible). Ask: "Does CI have Docker? The provider decision is finalised in the testing skill."
