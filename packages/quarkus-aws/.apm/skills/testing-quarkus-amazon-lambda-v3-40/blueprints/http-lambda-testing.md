# HTTP Lambda Tests and Secured Endpoints

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1 (`quarkus-amazon-lambda-http`, `quarkus-amazon-lambda-rest`). Fetched 2026-10-28. HTTP mapping itself belongs to `developing-quarkus-amazon-lambda-http-v3-40`; the security model to `securing-quarkus-lambda-cognito-v3-40`.

## Contents

- [1. Endpoint and raw event tests](#1-endpoint-and-raw-event-tests)
- [2. Secured endpoints](#2-secured-endpoints)

## 1. Endpoint and raw event tests

With the HTTP extensions the mock event server "converts HTTP requests into API Gateway event JSON" (paraphrase), so plain RestAssured calls on the REST endpoints work, for example `given().get("/hello")`. For "more complex API Gateway events" the guide says to POST manually to `http://localhost:8080/_lambda_` (8081 in test mode). "Unit testing is the same as any other Java project and does not require running on Amazon" ([aws-lambda-http guide](https://quarkus.io/version/3.40/guides/aws-lambda-http)). The path constant is `AmazonLambdaApi.API_BASE_PATH_TEST = "/_lambda_"` (source at tag 3.40.1.1).

| Extension | Event class (`io.quarkus.amazon.lambda.http.model` for REST) |
|---|---|
| `quarkus-amazon-lambda-http` (HTTP API) | `APIGatewayV2HTTPEvent` / `APIGatewayV2HTTPResponse` |
| `quarkus-amazon-lambda-rest` (REST API) | `AwsProxyRequest` / `AwsProxyResponse` |

The lines below were returned verbatim by the fetch tool from the guide's `AmazonLambdaSimpleTestCase`. The guide does not show the `request(String)` helper that builds the event (unverified); the `java.util.HashMap` and `org.junit.jupiter.api.Test` imports are implied. A raw-event example for a REST API build is also not shown (unverified).

```java
// Quarkus 3.40.1.1 — HTTP API (v2) raw event test, from the aws-lambda-http guide
import static io.restassured.RestAssured.given;
import static org.hamcrest.CoreMatchers.equalTo;

import com.amazonaws.services.lambda.runtime.events.APIGatewayV2HTTPEvent;
import io.quarkus.test.junit.QuarkusTest;

@QuarkusTest
public class AmazonLambdaSimpleTestCase {
    @Test
    public void testJaxrsCognitoJWTSecurityContext() throws Exception {
        APIGatewayV2HTTPEvent request = request("/security/username");
        request.getRequestContext().setAuthorizer(new APIGatewayV2HTTPEvent.RequestContext.Authorizer());
        request.getRequestContext().getAuthorizer().setJwt(new APIGatewayV2HTTPEvent.RequestContext.Authorizer.JWT());
        request.getRequestContext().getAuthorizer().getJwt().setClaims(new HashMap<>());
        request.getRequestContext().getAuthorizer().getJwt().getClaims().put("cognito:username", "Bill");
        given()
                .contentType("application/json")
                .accept("application/json")
                .body(request)
                .when()
                .post("/_lambda_")
                .then()
                .statusCode(200)
                .body("body", equalTo("Bill"));
    }
}
```

The raw-event response is the API Gateway response JSON, hence `.body("body", ...)`. Whether the HTTP Lambda test also starts the vertx-http server on `quarkus.http.test-port` (8081) next to the mock event server, and how the two share the port, is (unverified).

## 2. Secured endpoints

The guide's only documented test identity mechanism for Lambda HTTP is the claim inside the event (the example above, `cognito:username` = "Bill"). `cognito:username` is an ID-token claim; Cognito access tokens carry `username` ([AWS Cognito access token claims](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-the-access-token.html)), so with access-token claims in a real deployment this path does not match (see `securing-quarkus-lambda-cognito-v3-40`; identify users by `sub`). Cognito claim paths differ, as quoted from the [aws-lambda-http guide](https://quarkus.io/version/3.40/guides/aws-lambda-http) in the Cognito research: `requestContext.authorizer.jwt.claims.cognito:username` for the HTTP API, `requestContext.authorizer.claims.cognito:username` for the REST API.

| Key | Default | Source |
|---|---|---|
| `quarkus.lambda-http.enable-security` | `false` (medium confidence) | [all-config](https://quarkus.io/version/3.40/guides/all-config) |
| `quarkus.lambda-http.map-cognito-to-roles` | `true` (medium confidence) | [all-config](https://quarkus.io/version/3.40/guides/all-config) |
| `quarkus.lambda-http.cognito-role-claim` | `cognito:groups` (medium confidence) | [all-config](https://quarkus.io/version/3.40/guides/all-config) |
| `quarkus.lambda-http.cognito-claim-matcher` | `[^\[\] \t]+` (medium confidence) | [all-config](https://quarkus.io/version/3.40/guides/all-config) |

The guide says security is opt-in: "To enable this security feature, add … quarkus.lambda-http.enable-security=true" ([aws-lambda-http guide](https://quarkus.io/version/3.40/guides/aws-lambda-http)); the defaults above come from the config reference, a partly read page (L2).

```properties
# Quarkus 3.40.1.1
quarkus.lambda-http.enable-security=true
```

`@TestSecurity(user=..., roles=...)` comes from `io.quarkus:quarkus-test-security`, "is only available for `@QuarkusTest`" ([security-testing](https://quarkus.io/version/3.40/guides/security-testing)) and is oriented to HTTP examples (medium confidence). Whether it takes effect for requests entering through the Lambda mock event server is (unverified); prefer event claims, see [decision C5](./ask-first-decisions.md#c5-secured-http-lambda-event-claims-or-testsecurity).

Under `sam local` the HTTP guide offers the environment variable `QUARKUS_AWS_LAMBDA_FORCE_USER_NAME` to fix the principal (see [decision C3](./ask-first-decisions.md#c3-optional-sam-local-emulation)). Test events carry fake claim values only.
