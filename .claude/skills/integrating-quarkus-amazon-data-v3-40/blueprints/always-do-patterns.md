# Always-Do Patterns: setup and clients

Back to [SKILL.md](../SKILL.md). Quarkiverse 3.23.0 on Quarkus 3.40. Fetched 2026-10-28. Streams, pagination, presigning and item size: [data access patterns](./data-access-patterns.md).

## Contents

- [A1. BOM and extensions](#a1-bom-and-extensions)
- [A2. HTTP client artifact](#a2-http-client-artifact)
- [A3. Default credentials chain](#a3-default-credentials-chain)
- [A4. Inject and reuse clients](#a4-inject-and-reuse-clients)

## A1. BOM and extensions

The BOM manages `quarkus-amazon-common`, `quarkus-amazon-dynamodb`, `quarkus-amazon-dynamodb-enhanced`, `quarkus-amazon-s3`, `quarkus-amazon-s3-transfer-manager` (and the `-deployment` artifacts) at `${project.version}`, and imports `software.amazon.awssdk:bom` at 2.55.6, so SDK HTTP-client artifacts are version-aligned too. Evidence: BOM POM, parent POM and release 3.23.0 (triangulated). The docs pages do not show the BOM coordinates; they come from Maven Central only ([BOM POM](https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-services-bom/3.23.0/quarkus-amazon-services-bom-3.23.0.pom), [parent POM](https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-services-parent/3.23.0/quarkus-amazon-services-parent-3.23.0.pom)).

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

## A2. HTTP client artifact

In the 3.23.0 S3 and DynamoDB extension POMs the SDK service artifact excludes `netty-nio-client`, `url-connection-client`, `apache-client` and `apache5-client`, and each transport is re-declared `optional`. The docs say to "add a URL connection client dependency" for the default sync client and "the Netty HTTP client dependency" for the default async client ([S3 page](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-s3.html), [DynamoDB page](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-dynamodb.html), [S3 POM](https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-s3/3.23.0/quarkus-amazon-s3-3.23.0.pom), [DynamoDB POM](https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-dynamodb/3.23.0/quarkus-amazon-dynamodb-3.23.0.pom)).

| Key | Default | Values |
|---|---|---|
| `quarkus.s3.sync-client.type` | `url` | `url`, `apache`, `apache5`, `aws-crt` |
| `quarkus.s3.async-client.type` | `netty` | `netty`, `aws-crt` |
| `quarkus.dynamodb.sync-client.type` | `url` | `url`, `apache`, `apache5`, `aws-crt` |
| `quarkus.dynamodb.async-client.type` | `netty` | `netty`, `aws-crt` |

Artifact per type (groupId `software.amazon.awssdk`, version from the imported SDK BOM): `url` needs `url-connection-client`; `apache` needs `apache-client`; `aws-crt` needs `aws-crt-client`; `netty` needs `netty-nio-client`. The pairing `apache5` with `apache5-client` is inferred from the POM's optional `apache5-client` and the value name (medium confidence). What fails when the artifact is missing is not stated on these pages (unverified). Which type to choose is Ask First: [C1](./ask-first-decisions.md#c1-http-client-type).

```xml
<!-- default sync client type 'url' (3.23.x) -->
<dependency>
  <groupId>software.amazon.awssdk</groupId>
  <artifactId>url-connection-client</artifactId>
</dependency>
```

## A3. Default credentials chain

`quarkus.s3.aws.credentials.type` and `quarkus.dynamodb.aws.credentials.type` default to `default` ("the provider will attempt to identify the credentials automatically"). The SDK default chain checks `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` and `AWS_SESSION_TOKEN`; Lambda sets them to "The access keys obtained from the function's execution role". The SDK Lambda guide adds: "If you intend to use Lambda SnapStart for Java at some point, you should rely on the default credentials provider chain", because on SnapStart activation the access-key environment variables "are not available to the Java SDK" ([S3 page](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-s3.html), [Lambda env vars](https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html), [credentials chain](https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/credentials-chain.html), [Lambda start time](https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/lambda-optimize-starttime.html)).

The Quarkiverse page lists system properties, environment variables, profile file, ECS container and EC2 instance profile for its `default` chain; the SDK page also lists web identity. Both include the environment-variable step Lambda uses.

```properties
# Quarkiverse 3.23.x: explicit for readability; 'default' is already the default value
quarkus.dynamodb.aws.credentials.type=default
quarkus.s3.aws.credentials.type=default
```

## A4. Inject and reuse clients

The extensions produce `DynamoDbClient`, `DynamoDbAsyncClient`, `DynamoDbEnhancedClient`, `DynamoDbEnhancedAsyncClient`, `S3Client`, `S3AsyncClient` (and `@S3Crt S3AsyncClient`, `S3TransferManager`) as injectable beans. AWS: "Each service client maintains its own HTTP connection pool… We recommend sharing a single instance of the client… All service clients are thread safe", and "We recommend initializing an SDK client outside of the Lambda handler method" ([DynamoDB page](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-dynamodb.html), [S3 page](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-s3.html), [best practices](https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/best-practices.html), [Lambda start time](https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/lambda-optimize-starttime.html)). The CDI scope Quarkiverse uses for these producers is not stated on the pages (unverified).

```java
// Quarkiverse 3.23.x injection points (types as documented)
@Inject DynamoDbClient dynamo;                 // sync
@Inject DynamoDbAsyncClient dynamoAsync;       // async
@Inject DynamoDbEnhancedClient enhanced;       // enhanced sync
@Inject S3Client s3;                           // sync
@Inject S3AsyncClient s3Async;                 // async
@Inject @S3Crt S3AsyncClient s3Crt;            // io.quarkiverse.amazon.s3.runtime.S3Crt, needs aws-crt-client
```

Per-request tenant-scoped clients built from these singletons are not documented by Quarkiverse 3.23.x (unverified); see [tenant isolation](./tenant-isolation.md#per-request-tenant-clients).

AWS also names a SDK warm-up helper (`SdkWarmUp`) for SnapStart; whether Quarkiverse integrates it is not stated (unverified).
