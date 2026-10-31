# Always-Do Patterns

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1. Fetched 2026-10-28. Code is representative; method bodies are illustrative (medium confidence).

## Contents

- [1. Extension choice](#1-extension-choice)
- [2. One HTTP framework](#2-one-http-framework)
- [3. Raw event injection](#3-raw-event-injection)
- [4. REST binary media types](#4-rest-binary-media-types)
- [5. Enable security](#5-enable-security)
- [6. Mock event server](#6-mock-event-server)
- [7. Build output is reference](#7-build-output-is-reference)
- [8. Explicit Content-Type](#8-explicit-content-type)

## 1. Extension choice

"Quarkus has a different extension for each Gateway API." The HTTP handler is typed `RequestHandler<APIGatewayV2HTTPEvent, APIGatewayV2HTTPResponse>`, the REST handler `RequestHandler<AwsProxyRequest, AwsProxyResponse>`, so each only understands its own gateway's event ([guide](https://quarkus.io/version/3.40/guides/aws-lambda-http), [HTTP POM](https://repo1.maven.org/maven2/io/quarkus/quarkus-amazon-lambda-http/3.40.1.1/quarkus-amazon-lambda-http-3.40.1.1.pom), [REST POM](https://repo1.maven.org/maven2/io/quarkus/quarkus-amazon-lambda-rest/3.40.1.1/quarkus-amazon-lambda-rest-3.40.1.1.pom)). The choice of gateway is [Ask First C1](./ask-first-decisions.md#c1-http-api-or-rest-api). The guide shows no dependency XML; the coordinates come from Maven Central.

```xml
<!-- Quarkus 3.40.1.1 - API Gateway HTTP API (APIGatewayV2HTTPEvent) -->
<dependency>
  <groupId>io.quarkus</groupId>
  <artifactId>quarkus-amazon-lambda-http</artifactId>
</dependency>
<!-- OR API Gateway REST API (AwsProxyRequest) -->
<dependency>
  <groupId>io.quarkus</groupId>
  <artifactId>quarkus-amazon-lambda-rest</artifactId>
</dependency>
```

```bash
# Representative - adapt to your environment (Quarkus 3.40.1.1)
mvn archetype:generate -DarchetypeGroupId=io.quarkus \
       -DarchetypeArtifactId=quarkus-amazon-lambda-http-archetype -DarchetypeVersion=3.40.1.1
# REST API: quarkus-amazon-lambda-rest-archetype
```

## 2. One HTTP framework

The guide: "You should only use a single HTTP framework together with the AWS Lambda extension to avoid unexpected conflicts and errors." It calls `quarkus-rest`, `quarkus-reactive-routes` and `quarkus-undertow` in the generated project optional ("Pick which HTTP framework(s) you want to use"), so delete the ones you do not use. Which archetype frameworks are present by default is (unverified).

```xml
<!-- Quarkus 3.40.1.1: keep ONE of quarkus-rest | quarkus-reactive-routes | quarkus-undertow -->
<dependency><groupId>io.quarkus</groupId><artifactId>quarkus-rest</artifactId></dependency>
```

## 3. Raw event injection

With Quarkus REST, the HTTP extension exposes `Context`, `APIGatewayV2HTTPEvent` and `APIGatewayV2HTTPEvent.RequestContext`; the REST extension exposes `Context`, `AwsProxyRequestContext` and `AwsProxyRequest` ([guide](https://quarkus.io/version/3.40/guides/aws-lambda-http)). In both 3.40.1.1 handlers these are the objects stored per request with `setContextObject`. The mechanism of the REST producers is (unverified). Injection into Reactive Routes or Undertow is not documented (medium confidence).

```java
// Quarkus 3.40.1.1 - quarkus-amazon-lambda-http + quarkus-rest (HTTP API, payload 2.0)
import jakarta.ws.rs.GET;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.core.Context;
import com.amazonaws.services.lambda.runtime.events.APIGatewayV2HTTPEvent;

@Path("/myresource")
public class MyResource {
    @GET @Path("ctx")
    public String ctx(@Context com.amazonaws.services.lambda.runtime.Context ctx) { return ctx.getAwsRequestId(); }

    @GET @Path("event")
    public String event(@Context APIGatewayV2HTTPEvent event) { return event.getRawPath(); }

    @GET @Path("requestContext")
    public String requestContext(@Context APIGatewayV2HTTPEvent.RequestContext req) { return req.getRequestId(); }
}
```

```java
// quarkus-amazon-lambda-rest: same shape with
// @Context io.quarkus.amazon.lambda.http.model.AwsProxyRequestContext rc
// @Context io.quarkus.amazon.lambda.http.model.AwsProxyRequest req
```

## 4. REST binary media types

The REST API "assumes that HTTP response bodies are text unless you explicitly tell it" which media types are binary, and the guide says the `sam.yaml` must make the gateway assume all media types are binary. AWS: return binary through a Lambda proxy by Base64-encoding and configuring the API's binary media types; API Gateway uses the first `Accept` header, so use `*/*` when you cannot control it ([AWS](https://docs.aws.amazon.com/apigateway/latest/developerguide/lambda-proxy-binary-media.html)). The client-visible effect for text responses is (unverified), see [U12 in the register](./unverified-and-risks.md#unverified-items). The Terraform attribute lives in `provisioning-aws-api-gateway-v6`.

```yaml
# Reference value from target/sam.jvm.yaml of quarkus-amazon-lambda-rest 3.40.1.1
Globals:
  Api:
    EndpointConfiguration: REGIONAL
    BinaryMediaTypes:
      - "*/*"
```

## 5. Enable security

The guide says security is opt-in: "To enable this security feature, add … quarkus.lambda-http.enable-security=true" ([guide](https://quarkus.io/version/3.40/guides/aws-lambda-http)). The config reference gives the default as `false` (medium confidence: partly read page) ([all-config](https://quarkus.io/version/3.40/guides/all-config)), and the 3.40.1.1 deployment processor registers `LambdaHttpAuthenticationMechanism` and `DefaultLambdaIdentityProvider` only when it is true (medium confidence, source summarised, L4). Depth, and the access-token caveat for the Cognito Principal path (`cognito:username` is an ID-token claim, access tokens carry `username`; identify users by `sub`; Quarkus behaviour with an access token is (unverified)): `securing-quarkus-lambda-cognito-v3-40`.

```properties
# src/main/resources/application.properties (Quarkus 3.40.1.1)
quarkus.lambda-http.enable-security=true
```

## 6. Mock event server

"In dev and test mode, Quarkus will start a mock AWS Lambda event server" that converts HTTP requests into API Gateway events, also for `@QuarkusIntegrationTest`. Keys and defaults: [build output and artifact contract](./build-output-and-artifact-contract.md#configuration-keys). Testing in depth: `testing-quarkus-amazon-lambda-v3-40`.

```bash
# Representative - adapt to your environment (Quarkus 3.40.1.1)
./mvnw quarkus:dev
curl -s http://localhost:8080/hello        # converted into an API Gateway event
# complex case: POST an API Gateway event JSON (HTTP API: APIGatewayV2HTTPEvent) to http://localhost:8080/_lambda_
```

## 7. Build output is reference

The build writes `function.zip`, `sam.jvm.yaml` and `sam.native.yaml` to `target/` or `build/`. The templates carry the values the extension expects; hand those to `provisioning-aws-lambda-v6` and `provisioning-aws-api-gateway-v6`. Table: [artifact contract](./build-output-and-artifact-contract.md#artifact-contract). Packaging and runtime choice: [U1 skill](../../developing-quarkus-amazon-lambda-v3-40/SKILL.md).

## 8. Explicit Content-Type

This is an Ask First practice ([C10](./ask-first-decisions.md#c10-handler-behaviour-read-from-source)), not an Always Do: the behaviour below was read from source (medium confidence). The 3.40.1.1 HTTP handler Base64-encodes any response whose `Content-Type` is not text (`text*`, or containing `json`, `yaml` or `xml` except `openxmlformats`); a missing `Content-Type` counts as binary (medium confidence: source read through a summarising tool, L4) ([source file at tag](https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-http/runtime/src/main/java/io/quarkus/amazon/lambda/http/LambdaHttpHandler.java)). Deployed, binary responses are Base64-encoded; `quarkus:dev` returns raw bytes ([guide](https://quarkus.io/version/3.40/guides/aws-lambda-http)).

```java
// Quarkus 3.40.1.1 - illustrative body (medium confidence)
@GET @Produces(MediaType.APPLICATION_JSON)
public Map<String, String> hello(@Context APIGatewayV2HTTPEvent.RequestContext rc,
                                 @Context com.amazonaws.services.lambda.runtime.Context lambda) {
    return Map.of("apiRequestId", rc.getRequestId(), "lambdaRequestId", lambda.getAwsRequestId());
}
```
