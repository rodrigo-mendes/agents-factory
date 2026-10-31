# Never-Do Patterns

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1. Fetched 2026-10-28. Severity wording: low, moderate, high.

## Contents

- [F1. More than one HTTP framework (severity high)](#f1-more-than-one-http-framework-severity-high)
- [F2. Injecting the other gateway event type (severity high)](#f2-injecting-the-other-gateway-event-type-severity-high)
- [F3. REST API without binary media types (severity high)](#f3-rest-api-without-binary-media-types-severity-high)
- [F4. Copying the REST native runtime provided (severity high)](#f4-copying-the-rest-native-runtime-provided-severity-high)
- [F5. Hand-parsing multi-value headers and query strings (severity moderate)](#f5-hand-parsing-multi-value-headers-and-query-strings-severity-moderate)
- [F6. Expecting an authorizer Principal without enabling security (severity high)](#f6-expecting-an-authorizer-principal-without-enabling-security-severity-high)

## F1. More than one HTTP framework (severity high)

"You should only use a single HTTP framework together with the AWS Lambda extension to avoid unexpected conflicts and errors" ([guide](https://quarkus.io/version/3.40/guides/aws-lambda-http)). Impact: unexpected conflicts and errors (guide wording; failure mode not specified).

```xml
<!-- ❌ WRONG -->
<dependency><groupId>io.quarkus</groupId><artifactId>quarkus-rest</artifactId></dependency>
<dependency><groupId>io.quarkus</groupId><artifactId>quarkus-undertow</artifactId></dependency>
<dependency><groupId>io.quarkus</groupId><artifactId>quarkus-reactive-routes</artifactId></dependency>

<!-- ✅ CORRECT: one framework only -->
<dependency><groupId>io.quarkus</groupId><artifactId>quarkus-rest</artifactId></dependency>
```

## F2. Injecting the other gateway event type (severity high)

The HTTP extension stores only `Context`, `APIGatewayV2HTTPEvent` and its `RequestContext`; the REST extension stores only `Context`, `AwsProxyRequestContext` and `AwsProxyRequest`. The 3.40.1.1 HTTP producers return `null` when the class key is absent (medium confidence: source read through a summarising tool, L4) ([guide](https://quarkus.io/version/3.40/guides/aws-lambda-http), [producers at tag](https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-http/runtime/src/main/java/io/quarkus/amazon/lambda/http/AwsHttpContextProducers.java)). Impact: a null event at runtime.

```java
// ❌ WRONG - quarkus-amazon-lambda-rest project
public String event(@Context APIGatewayV2HTTPEvent event) { return event.getRawPath(); }

// ✅ CORRECT - quarkus-amazon-lambda-rest project
public String req(@Context io.quarkus.amazon.lambda.http.model.AwsProxyRequest req) { return req.getPath(); }
```

## F3. REST API without binary media types (severity high)

The guide says the API must "assume all media types are binary"; AWS says a REST API treats bodies as text unless configured ([guide](https://quarkus.io/version/3.40/guides/aws-lambda-http), [AWS](https://docs.aws.amazon.com/apigateway/latest/developerguide/lambda-proxy-binary-media.html)). Impact: Base64-encoded bodies can reach clients undecoded (the guide's reasoning; the exact client symptom was not tested, see [U12](./unverified-and-risks.md#unverified-items) and U3).

```yaml
# ❌ WRONG - REST API for a quarkus-amazon-lambda-rest function, no binary media types
Globals:
  Api:
    EndpointConfiguration: REGIONAL

# ✅ CORRECT
Globals:
  Api:
    EndpointConfiguration: REGIONAL
    BinaryMediaTypes:
      - "*/*"
# Terraform: set the API's binary media types through provisioning-aws-api-gateway-v6
```

## F4. Copying the REST native runtime provided (severity high)

`quarkus-amazon-lambda-rest` 3.40.1.1 generates `sam.native.yaml` with `Runtime: provided`. AWS lists `provided` as deprecated 2024-01-08, function creation blocked 2024-02-08 and updates blocked 2027-08-31; the HTTP extension's own template writes `provided.al2023` ([REST template](https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-rest/deployment/src/main/resources/http/sam.native.yaml), [HTTP template](https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-http/deployment/src/main/resources/http/sam.native.yaml), [AWS runtimes](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html)). Impact: new functions cannot be created on `provided`; existing ones lose updates. The general pairing native with `provided.al2023` stays (medium confidence); see [M1](./unverified-and-risks.md#medium-confidence-items).

```yaml
# ❌ WRONG - copied from target/sam.native.yaml of quarkus-amazon-lambda-rest 3.40.1.1
Runtime: provided
```

✅ Instead: take the runtime from the Ask-First choice in the [U1 skill](../../developing-quarkus-amazon-lambda-v3-40/blueprints/ask-first-decisions.md#c1-jvm-snapstart-or-native) and carry that value into `provisioning-aws-lambda-v6`. Do not write the runtime from the REST template.

## F5. Hand-parsing multi-value headers and query strings (severity moderate)

AWS: "Format `2.0` doesn't have `multiValueHeaders` or `multiValueQueryStringParameters` fields. Duplicate headers are combined with commas"; duplicate query strings likewise ([AWS](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-develop-integrations-lambda.html)). Impact: splitting `event.getHeaders()` or `getQueryStringParameters()` by hand loses value boundaries.

```java
// ❌ WRONG - "a,b" is ambiguous
String[] tags = event.getQueryStringParameters().get("tag").split(",");
```

✅ Instead: do not rely on the combined string for value boundaries. The binding option below is Ask First [C10](./ask-first-decisions.md#c10-handler-behaviour-read-from-source), because it rests on source read through summarisation (medium confidence, M10: the 3.40.1.1 HTTP handler rebuilds the request from `rawPath` plus `rawQueryString` before Quarkus REST sees it, [handler at tag](https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-http/runtime/src/main/java/io/quarkus/amazon/lambda/http/LambdaHttpHandler.java)).

```java
// Option (medium confidence): let Quarkus REST bind the values
@GET public String list(@QueryParam("tag") List<String> tags) { return String.join("|", tags); }
```

## F6. Expecting an authorizer Principal without enabling security (severity high)

The guide says security is opt-in: "To enable this security feature, add … quarkus.lambda-http.enable-security=true" ([guide](https://quarkus.io/version/3.40/guides/aws-lambda-http)). The config reference lists the default as `false` (medium confidence), and the 3.40.1.1 processor registers the authentication mechanism only when it is true (medium confidence, L4) ([all-config](https://quarkus.io/version/3.40/guides/all-config)). Impact: the authorizer identity is not turned into a `Principal` or `SecurityIdentity`.

```properties
# ❌ WRONG - enable-security omitted (opt-in feature)
quarkus.lambda-http.map-cognito-to-roles=true

# ✅ CORRECT
quarkus.lambda-http.enable-security=true
```
