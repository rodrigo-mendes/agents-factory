# Ask-First Decisions: HTTP client, JVM vs native, region

Back to [SKILL.md](../SKILL.md). Quarkiverse 3.23.0. Fetched 2026-10-28. Every decision here is put to the user; none has a default. Tenant, presigner, schema, large-object and Dev Services decisions: [ask-first data decisions](./ask-first-data-decisions.md).

## Contents

- [C1. HTTP client type](#c1-http-client-type)
- [C2. JVM, SnapStart or native: consequences](#c2-jvm-snapstart-or-native-consequences)
- [C3. Region](#c3-region)

## C1. HTTP client type

Two official sources point in different directions (research contradiction 3, not a factual contradiction):

- AWS SDK Lambda guide: https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/lambda-optimize-starttime.html recommends the CRT clients ("For working with AWS Lambda, we recommend the AwsCrtHttpClient… AwsCrtAsyncHttpClient"; the HTTP-configuration page adds "we recommend that you use the AWS CRT-based HTTP clients if possible", https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/http-configuration.html).
- Quarkiverse common features: https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/common-features.html defaults to `url` and warns: "Since AWS CRT version 0.31.0, native library must be embedded in the docker image. This is not done by default."

The Quarkiverse 3.23.x pages say nothing about cold start for any client type (common-features, S3 and DynamoDB pages read). Each statement in the table is quoted from its source; no page ranks the options by Lambda speed, so do not rank them.

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| A. `url` + `url-connection-client` | Quarkiverse default; SDK: "minimize the number of jars and third-party libraries" | SDK: no HTTP PATCH, no configurable idle connection timeout | Sync DynamoDB and S3 calls, minimal dependencies |
| B. `aws-crt` + `aws-crt-client` | SDK recommendation for Lambda | Quarkiverse: native library not embedded by default; SDK: `javax.net.ssl.keyStore` and `trustStore` system properties not supported; embedding CRT in a Lambda native `function.zip` is (unverified) | JVM (+ SnapStart) Lambdas; native only with the CRT library handled |
| C. `apache5` or `apache` | SDK: low latency over high throughput; Apache5 is the SDK default sync client since 2.46.0 | SDK: "Slower startup time compared to other HTTP clients"; `ApacheHttpClient` (4.x) is deprecated by the SDK; the `apache5` artifact pairing is (medium confidence) | Long-lived JVM services that are not cold-start sensitive |
| D. async `netty` + `netty-nio-client` | Default async client in both SDK and Quarkiverse | SDK: "Slower startup time compared to other HTTP clients" | Async clients without CRT |

Ask: "JVM + SnapStart or native (family rule 3)? Sync or async clients? If native, accept the CRT native-library packaging work or stay on `url`?"

## C2. JVM, SnapStart or native: consequences

JVM + SnapStart and native are mutually exclusive; the choice itself is made in [developing-quarkus-amazon-lambda-v3-40](../../developing-quarkus-amazon-lambda-v3-40/SKILL.md). Consequences for this skill ([Lambda start time](https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/lambda-optimize-starttime.html), [common features](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/common-features.html)):

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| A. JVM + SnapStart | The SDK guidance for the CRT client applies directly; `SdkWarmUp` can warm clients before the snapshot (Quarkiverse integration: (unverified)) | Must keep the default credentials chain: the SDK `EnvironmentVariableCredentialsProvider` loses its access-key variables on SnapStart activation ([SDK Lambda guide](https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/lambda-optimize-starttime.html)); that the Quarkiverse value `env-variable` maps to that provider is (medium confidence, M3) | Teams on managed Java runtimes |
| B. Native | No JVM startup | CRT native library "must be embedded… not done by default"; `@RegisterForReflection` is needed only for non-enhanced classes per the Quarkiverse note | Lowest cold start without SnapStart |

Ask: "Which ADR did the project choose? Settle it before picking the HTTP client (C1) or credentials provider."

## C3. Region

Both region keys have no default. The S3 page says "If not set, region is retrieved via the default providers chain in the following order: `aws.region` system property, `region` property from the profile file, Instance profile file"; it does not list `AWS_REGION`. The SDK chain checks `AWS_REGION` ("The Lambda container sets this environment variable"). Whether Quarkiverse 3.23.0 delegates to the SDK chain, and so picks `AWS_REGION` in Lambda, is not stated on a page and could not be resolved within the research (medium confidence; one tag for the whole statement). Setting the key to a Quarkus property expression of `AWS_REGION` is a Quarkus-config technique these pages do not cover (unverified). Whether `S3Presigner.builder()` without a region uses the default region chain is stated for service clients only (unverified). Sources: [S3 page](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-s3.html), [region selection](https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/region-selection.html), [Lambda start time](https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/lambda-optimize-starttime.html).

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| A. Leave `quarkus.<svc>.aws.region` unset | Region-independent code | Depends on undocumented delegation (medium confidence) | Verified once in a deployed function |
| B. Set it explicitly per environment | Deterministic; SDK: an explicit region "shortcuts the SDK's default Region lookup" | Per-environment configuration | Multi-region or strict environments |

Ask: "Is the function single-region, and does a deploy-time smoke test confirm region resolution?"
