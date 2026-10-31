# Never-Do Patterns

Back to [SKILL.md](../SKILL.md). Quarkiverse 3.23.0. Fetched 2026-10-28. Severity wording: low, moderate, high. Every ✅ names only High options (family rule 9).

## Contents

- [F1. Static access keys in Lambda configuration](#f1-static-access-keys-in-lambda-configuration-severity-high)
- [F2. env-variable credentials with SnapStart](#f2-env-variable-credentials-with-snapstart-severity-high)
- [F3. Unclosed ResponseInputStream](#f3-unclosed-responseinputstream-severity-high)
- [F4. One Query call as the full result](#f4-one-query-call-as-the-full-result-severity-high)
- [F5. Tenant from the path, or Scan in a tenant policy](#f5-tenant-from-the-path-or-scan-in-a-tenant-policy-severity-high)
- [F6. Expecting a role-signed URL to live its full duration](#f6-expecting-a-role-signed-url-to-live-its-full-duration-severity-moderate)
- [F7. Global endpoint-override to localhost](#f7-global-endpoint-override-to-localhost-severity-high)
- [F8. Following 4.0.0.Beta or dev docs](#f8-following-400beta-or-dev-docs-severity-moderate)

## F1. Static access keys in Lambda configuration (severity: high)

Lambda already provides temporary execution-role keys to the default chain. `static` is a non-default type that uses "the access key and secret access key specified in the `static-provider` section of the config"; Quarkiverse uses it only in its local quickstart example. A presigned URL signed with IAM-user keys can stay valid "up to 7 days", unlike role-signed URLs. Impact: long-lived keys in configuration or VCS; bypasses the execution role and its rotation ([S3 page](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-s3.html), [Lambda env vars](https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html), [S3 presigned URLs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html)).

```properties
# ❌ WRONG
quarkus.s3.aws.credentials.type=static
quarkus.s3.aws.credentials.static-provider.access-key-id=AKIA...
quarkus.s3.aws.credentials.static-provider.secret-access-key=...

# ✅ CORRECT: default chain, Lambda execution role
quarkus.s3.aws.credentials.type=default
```

## F2. env-variable credentials with SnapStart (severity: high)

AWS: with SnapStart the runtime uses container credentials (`AWS_CONTAINER_CREDENTIALS_FULL_URI`) instead of access-key environment variables "to prevent credentials from expiring before the function is restored" ([AWS SnapStart activation](https://docs.aws.amazon.com/lambda/latest/dg/snapstart-activate.html)). The SDK guide adds: "when SnapStart is activated, the Java runtime sets container credentials environment variables. On activation, the environment variables used by the `EnvironmentVariableCredentialsProvider`—access key environment variables—are not available to the Java SDK" ([Lambda start time](https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/lambda-optimize-starttime.html)). Impact: credential failures after SnapStart restore. The Never Do rests on these two High sentences only: do not rely on access-key environment variables for credentials on a function that uses or may use SnapStart. Which Quarkiverse value maps to that provider is not part of the rule; see [Ask First C2](./ask-first-decisions.md#c2-jvm-snapstart-or-native-consequences). The ✅ alternative is High.

```properties
# ❌ WRONG: credentials taken from access-key environment variables under SnapStart
# (the Quarkiverse value `env-variable` is assumed to map to this provider: medium confidence, M3)
quarkus.dynamodb.aws.credentials.type=env-variable

# ✅ CORRECT
quarkus.dynamodb.aws.credentials.type=default
```

## F3. Unclosed ResponseInputStream (severity: high)

The HTTP connection "can't be reused until all data from the stream has been read and the stream is closed"; otherwise "the client can run out of resources" ([best practices](https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/best-practices.html)).

```java
// ❌ WRONG
InputStream in = s3.getObject(req);   // never closed
return parse(in);

// ✅ CORRECT
try (ResponseInputStream<GetObjectResponse> in = s3.getObject(req)) {
    return parse(in);
}
```

## F4. One Query call as the full result (severity: high)

1 MB per call; with a filter "a page can return zero matching items and still include a `LastEvaluatedKey`". Impact: silent data loss ([Query pagination](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Query.Pagination.html), [SDK pagination](https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/pagination.html)).

```java
// ❌ WRONG
List<Map<String, AttributeValue>> all = dynamo.query(req).items();   // first 1 MB page only

// ✅ CORRECT
dynamo.queryPaginator(req).items().forEach(this::handle);
```

## F5. Tenant from the path, or Scan in a tenant policy (severity: high)

`Scan` "returns all items regardless of the leading keys" (DynamoDB conditions page). Impact: cross-tenant reads. The rule "tenant from the token, not the path" is family rule 6. `verifiedTenantFromToken()` is a placeholder; token handling is outside this skill ([DynamoDB conditions](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/specifying-conditions.html)). The historical whitepaper statements on authentication versus isolation (medium confidence) are in [tenant isolation limits](./tenant-isolation.md#limits-of-these-primitives).

```java
// ❌ WRONG
String tenant = request.getPathParameters().get("tenantId");   // caller-controlled
table.scan().items().stream().filter(i -> tenant.equals(i.getTenantId()));

// ✅ CORRECT
String tenant = verifiedTenantFromToken();   // claim from the authenticated principal
table.query(QueryEnhancedRequest.builder()
        .queryConditional(QueryConditional.keyEqualTo(k -> k.partitionValue(tenant)))
        .build()).items().forEach(this::handle);
```

## F6. Expecting a role-signed URL to live its full duration (severity: moderate)

With IAM role credentials "The presigned URL expires when the role session expires, even if you specify a longer expiration time." Impact: `ExpiredToken` or 403 for clients holding "valid" URLs. The session lifetime itself could not be resolved from documentation (unverified) ([S3 presigned URLs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html), [SDK presign](https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/examples-s3-presign.html)).

```java
// ❌ WRONG
.signatureDuration(Duration.ofDays(7))   // signed by the Lambda execution role

// ✅ CORRECT: short-lived; the client requests a fresh URL when needed
.signatureDuration(Duration.ofMinutes(10))
```

## F7. Global endpoint-override to localhost (severity: high)

It disables Dev Services and sends deployed traffic to the override URI ("The endpoint URI with which the SDK should communicate"). Impact: the deployed function calls `localhost:4566` and fails; the local stack is no longer started ([S3 page](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-s3.html), [dev-services](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/dev-services.html)).

```properties
# ❌ WRONG
quarkus.s3.endpoint-override=http://localhost:4566

# ✅ CORRECT: leave endpoint-override unset; Dev Services supply the endpoint in dev and test
quarkus.s3.devservices.buckets=my-local-bucket
```

## F8. Following 4.0.0.Beta or dev docs (severity: moderate)

4.0.0.Beta1 "feat: bump to quarkus 4", Floci as default Dev Services stack, no per-service container isolation and `quarkus-amazon-ce` renamed: none of it applies to 3.23.0 on Quarkus 3.40 (family rules 1 and 2) ([releases](https://github.com/quarkiverse/quarkus-amazon-services/releases), [BOM metadata](https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-services-bom/maven-metadata.xml)).

```xml
<!-- ❌ WRONG -->
<version>4.0.0.Beta3</version>

<!-- ✅ CORRECT -->
<version>3.23.0</version>
```
