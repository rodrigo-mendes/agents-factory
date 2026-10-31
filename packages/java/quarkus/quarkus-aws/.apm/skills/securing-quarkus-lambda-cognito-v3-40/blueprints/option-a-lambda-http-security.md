# Option A: Lambda HTTP Security Mapping

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1. Fetched 2026-10-28. API Gateway validates the token; Quarkus maps what the event carries. Chosen through [Ask First K1](./ask-first-decisions.md#k1-where-the-token-is-validated).

## Contents

- [What the integration does](#what-the-integration-does)
- [HTTP API lifecycle](#http-api-lifecycle)
- [REST API variant](#rest-api-variant)
- [Custom identity mapping](#custom-identity-mapping)
- [Edge configuration](#edge-configuration)
- [Limits of the mapping](#limits-of-the-mapping)

## What the integration does

With `quarkus.lambda-http.enable-security=true` (default `false`, medium confidence) "Quarkus will automatically parse the event JSON" and register a `java.security.Principal` (`CognitoPrincipal`, `IAMPrincipal` or `CustomPrincipal`). The name comes from the `cognito:username` claim in the authorizer context (an ID-token claim: access tokens carry `username`, so with an access token this path does not match and the Quarkus behaviour is (unverified); identify users and tenants by `sub`); `cognito:groups` becomes roles (M2M access tokens carry no `cognito:groups` and get no roles). The guide does not say that the function checks the token itself: it maps what API Gateway puts in the event. By default only the principal name and roles are mapped, "It does not map claims" (paraphrase of the guide). Sources: [aws-lambda-http guide](https://quarkus.io/version/3.40/guides/aws-lambda-http), [all-config](https://quarkus.io/version/3.40/guides/all-config) (read to 100,000 of 232,437 characters, L1; the four `quarkus.lambda-http.*` rows were inside that range).

## HTTP API lifecycle

API Gateway HTTP API with a JWT authorizer, Quarkus 3.40.1.1.

```properties
# application.properties
quarkus.lambda-http.enable-security=true
# map-cognito-to-roles default true; cognito-role-claim default cognito:groups (both medium confidence)
# Ask First K6: quarkus.security.jaxrs.deny-unannotated-endpoints=true
```

```java
// Quarkus 3.40.1.1, quarkus-amazon-lambda-http + Quarkus REST
@Path("/tenants/{tenantId}/orders")
public class OrdersResource {

    @GET
    @RolesAllowed("tenant-user")                                   // from cognito:groups
    public Response list(@PathParam("tenantId") String pathTenant,
                         @Context SecurityContext sec,             // Principal = cognito:username (ID token only)
                         @Context APIGatewayV2HTTPEvent event) {   // documented injection
        // accessor chain from aws-lambda-java-events (unverified)
        String tokenTenant = event.getRequestContext().getAuthorizer().getJwt()
                                  .getClaims().get("custom:tenantId");
        if (tokenTenant == null || !tokenTenant.equals(pathTenant)) {   // family rule 6
            return Response.status(Response.Status.FORBIDDEN).build();
        }
        return Response.ok(service.ordersFor(tokenTenant, sec.getUserPrincipal().getName())).build();
    }
}
```

`custom:tenantId` is an ID-token claim by default; with an access token the claim is present only when a V2_0/V3_0 pre token generation trigger adds it ([never-do N7](./never-do-patterns.md#n7-custom-attributes-expected-in-the-access-token-high)). The API Gateway HTTP API "passes the claims in the token to the API route's integration" ([HTTP API JWT authorizer](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-jwt-authorizer.html)).

## REST API variant

`quarkus-amazon-lambda-rest` with a `COGNITO_USER_POOLS` authorizer. The Principal comes from `requestContext.authorizer.claims.cognito:username` (same ID-token caveat as above). Inject `io.quarkus.amazon.lambda.http.model.AwsProxyRequestContext` (or `AwsProxyRequest`) to read other claims. A custom provider overrides `authenticate(AwsProxyRequest event)` ([aws-lambda-http guide](https://quarkus.io/version/3.40/guides/aws-lambda-http)). A REST authorizer with Authorization Scopes treats the token as an access token; without scopes as an identity token ([REST Cognito authorizer](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-enable-cognito-user-pool.html)).

## Custom identity mapping

The documented hook is `io.quarkus.amazon.lambda.http.LambdaIdentityProvider` (extends `IdentityProvider<LambdaAuthenticationRequest>`) as an `@ApplicationScoped` CDI bean, discovered automatically. Override `authenticate(APIGatewayV2HTTPEvent)` (HTTP API) or `authenticate(AwsProxyRequest)` (REST API) and build `QuarkusSecurityIdentity.builder().setPrincipal(...)`. The package of `LambdaAuthenticationRequest` is not shown in the guide (unverified). Read only authorizer-populated `requestContext` fields, never caller headers ([never-do N5](./never-do-patterns.md#n5-identity-from-caller-controlled-data-high)).

## Edge configuration

IaC belongs to `provisioning-aws-api-gateway-v6` and `provisioning-aws-cognito-v6` (family rule 4); this skill states only what the function relies on. JWT authorizer `Issuer` = pool issuer, `Audience` = app client ID. For an access token "bound to a resource server", the resource server URL is the audience ([Cognito verifying a JWT](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html)). Set route `authorizationScopes`: AWS recommends it for HTTP routes. Every route must have an authorizer; a route without one gives no Principal.

## Limits of the mapping

- Only name and roles are mapped (pattern 4 in [always-do](./always-do-patterns.md#4-claims-from-the-event) reads the rest).
- Whether `quarkus.http.auth.permission.*` path policies run in the Lambda HTTP extensions is (unverified); use annotations and test each path.
- Whether a `SecurityIdentityAugmentor` runs for identities built by `enable-security` or `LambdaIdentityProvider` is (unverified); see [multi-tenant isolation](./multi-tenant-isolation.md#central-check-with-an-augmentor).
- Whether the mock event server passes an authorizer context, so `enable-security` can be tested in `@QuarkusTest`, is (unverified); see [testing](./testing-and-verification.md).
- The extensions are preview: backward compatibility is not guaranteed.
