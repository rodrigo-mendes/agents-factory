# Always-Do Patterns: data access

Back to [SKILL.md](../SKILL.md). Quarkiverse 3.23.0, AWS SDK 2.55.x. Fetched 2026-10-28. Setup and clients: [always-do patterns](./always-do-patterns.md).

## Contents

- [A5. Close response streams](#a5-close-response-streams)
- [A6. Paginate Query and Scan](#a6-paginate-query-and-scan)
- [A7. Short presigned URLs](#a7-short-presigned-urls)
- [A10. Item size limit](#a10-item-size-limit)
- [Enhanced client schemas](#enhanced-client-schemas)
- [Assembled example](#assembled-example)

## A5. Close response streams

Single official source (SDK best practices); the Quarkiverse S3 page shows only `getObjectAsBytes` and `AsyncResponseTransformer.toPublisher()`. AWS: "the input stream is a direct stream of data from the HTTP connection and the underlying HTTP connection can't be reused until all data from the stream has been read and the stream is closed. If these rules are not followed, the client can run out of resources by allocating too many open, but unused, HTTP connections." ([best practices](https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/best-practices.html)).

```java
// AWS SDK 2.55.x via Quarkiverse 3.23.0 S3Client
try (ResponseInputStream<GetObjectResponse> in =
         s3.getObject(GetObjectRequest.builder().bucket(bucket).key(key).build())) {
    process(in);   // read fully; try-with-resources closes the stream
}
```

## A6. Paginate Query and Scan

"The result set from a `Query` is limited to 1 MB per call" (same for `Scan`). "The only way to know when you have reached the end of the result set is when `LastEvaluatedKey` is empty", and with a `FilterExpression` "a page can return zero matching items and still include a `LastEvaluatedKey`". SDK autopagination (`queryPaginator`, `scanPaginator`, `listObjectsV2Paginator`) and the enhanced client's `PageIterable` and `PagePublisher` handle it ([Constraints](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Constraints.html), [Query pagination](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Query.Pagination.html), [SDK pagination](https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/pagination.html), [enhanced multi-record](https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/ddb-en-client-use-multirecord.html)).

```java
// low-level client: all pages, lazily
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

## A7. Short presigned URLs

AWS: "presigned URLs are bearer tokens that grant access to those who possess them". With SDKs "the expiration time can be set as high as 7 days", but for temporary credentials "the URL expires when the credential expires… even if the URL was created with a later expiration time", and for IAM role credentials "The presigned URL expires when the role session expires". Lambda signs with the execution role's temporary keys ([A3](./always-do-patterns.md#a3-default-credentials-chain)). S3 checks expiry "at the time of the HTTP request". The real lifetime of a Lambda execution-role session is not stated on any page read (unverified); use the 10-minute AWS example duration. Header-mapped fields (`metadata`, `serverSideEncryption`, `acl`, `storageClass`) must be sent by the caller as `x-amz-*` headers, or put into the URL with `putRawQueryParameter`; `signedHeaders()` shows what the caller must send ([S3 presigned URLs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html), [SDK presign](https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/examples-s3-presign.html), [Prescriptive Guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/presigned-url-best-practices/overview.html)).

```java
// AWS SDK 2.55.x: upload URL for one tenant-scoped key, 10 minutes (as in the AWS example)
PresignedPutObjectRequest p = presigner.presignPutObject(PutObjectPresignRequest.builder()
        .signatureDuration(Duration.ofMinutes(10))
        .putObjectRequest(PutObjectRequest.builder().bucket(bucket).key(key).build())
        .build());
String url = p.url().toExternalForm();
Set<String> mustSend = p.signedHeaders().keySet();   // for example [host]
```

How `presigner` is obtained in Quarkus is Ask First: [C5](./ask-first-data-decisions.md#c5-s3presigner). The S3 bucket policy condition `s3:signatureAge` and network-path conditions are listed in [limits and production readiness](./limits-and-production-readiness.md#security-checklist).

## A10. Item size limit

"The maximum item size in DynamoDB is 400 KB, which includes both attribute name binary length (UTF-8 length) and attribute value lengths… The attribute name counts towards the size limit." 1 KB is 1024 bytes in DynamoDB ([Constraints](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Constraints.html)). Single official source.

```java
// Design rule, not an API: large payloads go to S3 and the item keeps the key
item.setPayloadKey("tenants/" + tenantId + "/docs/" + docId);
```

The "store large values in S3 and keep a pointer" pattern is not stated on the Constraints page (unverified).

## Enhanced client schemas

Quarkiverse 3.23.x: "TableSchemas generated from bean classes are registered and cached at startup", "You don't need to explicitely instantiate them at class-load time", "Note that you don't need to add `@RegisterForReflection` anymore". Config: `quarkus.dynamodbenhanced.create-table-schemas` (default `true`, medium confidence, M10) and `quarkus.dynamodbenhanced.client-extensions` (no default listed). AWS: the bean needs a public no-arg constructor, getters and setters, and at least `@DynamoDbPartitionKey`; "You can skip the cost of bean introspection if you define the table schema in code." ([DynamoDB page](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-dynamodb.html), [table schema](https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/ddb-en-client-gs-tableschema.html)). Choice between bean, builder and named table: [C6](./ask-first-data-decisions.md#c6-enhanced-client-schema).

## Assembled example

An illustrative composition, not an official example; each API is sourced above. `@ApplicationScoped` on the holder is a standard Quarkus CDI choice not covered by these pages.

```java
@ApplicationScoped
public class DocumentStore {
    @Inject DynamoDbEnhancedClient enhanced;   // quarkus-amazon-dynamodb-enhanced 3.23.0
    @Inject S3Client s3;                       // quarkus-amazon-s3 3.23.0

    // cached at startup by the extension; AWS: designed to be static and immutable
    static final TableSchema<Doc> SCHEMA = TableSchema.fromClass(Doc.class);

    public void save(Doc d) { enhanced.table("docs", SCHEMA).putItem(d); }   // item < 400 KB (A10)

    public void forEachDoc(String tenantId, Consumer<Doc> sink) {
        enhanced.table("docs", SCHEMA)
                .query(QueryEnhancedRequest.builder()
                        .queryConditional(QueryConditional.keyEqualTo(k -> k.partitionValue(tenantId)))
                        .build())
                .items()                 // PageIterable: all pages (A6)
                .forEach(sink);
    }

    public long countBytes(String bucket, String key) throws IOException {
        try (ResponseInputStream<GetObjectResponse> in =
                 s3.getObject(GetObjectRequest.builder().bucket(bucket).key(key).build())) {
            return in.transferTo(OutputStream.nullOutputStream());   // A5
        }
    }
}

@DynamoDbBean
public class Doc {   // JavaBean: public no-arg constructor + getters and setters
    private String tenantId;
    private String docId;
    @DynamoDbPartitionKey public String getTenantId() { return tenantId; }
    public void setTenantId(String t) { this.tenantId = t; }
    @DynamoDbSortKey public String getDocId() { return docId; }
    public void setDocId(String d) { this.docId = d; }
}
```
