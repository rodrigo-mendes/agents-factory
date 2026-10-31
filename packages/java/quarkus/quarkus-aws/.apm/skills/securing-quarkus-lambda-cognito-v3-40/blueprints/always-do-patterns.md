# Always-Do Patterns

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1. Fetched 2026-10-28.

## Contents

- [1. Enable the integration](#1-enable-the-integration)
- [2. Principal name](#2-principal-name)
- [3. Groups to roles](#3-groups-to-roles)
- [4. Claims from the event](#4-claims-from-the-event)
- [5. Tenant from the token](#5-tenant-from-the-token)
- [6. Protect the tenant attribute](#6-protect-the-tenant-attribute)
- [7. token_use and client binding](#7-token_use-and-client-binding)
- [8. Authorization annotations](#8-authorization-annotations)
- [9. Key rotation](#9-key-rotation)

## 1. Enable the integration

The guide says security is opt-in: "To enable this security feature, add … quarkus.lambda-http.enable-security=true". `quarkus.lambda-http.enable-security` is a boolean with default `false` (medium confidence). The key description: "Enable security mechanisms to process lambda and AWS based security (i.e. Cognito, IAM) from the http event sent from API Gateway". When it is on, Quarkus parses the event JSON and registers a `java.security.Principal`. Jakarta REST reads it through `jakarta.ws.rs.core.SecurityContext`, servlet through `HttpServletRequest.getUserPrincipal()`, Reactive Routes through `RouteContext.user()` ([aws-lambda-http guide](https://quarkus.io/version/3.40/guides/aws-lambda-http)).

```properties
# Quarkus 3.40: opt-in feature (guide); add this line to get a Principal
quarkus.lambda-http.enable-security=true
```

The route needs an authorizer for the event to carry an identity: a JWT authorizer (HTTP API) or a `COGNITO_USER_POOLS` authorizer (REST API). A route without one gives no Principal. Authorizer provisioning belongs to `provisioning-aws-api-gateway-v6`.

## 2. Principal name

| API type | Cognito | IAM | Lambda authorizer |
|---|---|---|---|
| HTTP API (`quarkus-amazon-lambda-http`) | `requestContext.authorizer.jwt.claims.cognito:username` | `requestContext.authorizer.iam.userId` | `requestContext.authorizer.lambda.principalId` |
| REST API (`quarkus-amazon-lambda-rest`) | `requestContext.authorizer.claims.cognito:username` | `requestContext.identity.user` | `requestContext.authorizer.principalId` |

Principal classes for both: `io.quarkus.amazon.lambda.http.CognitoPrincipal`, `IAMPrincipal`, `CustomPrincipal`. The name is the Cognito username.

**Token-type caveat.** `cognito:username` is an ID-token claim. Cognito ACCESS tokens carry `username` instead, and machine-to-machine (client-credentials) access tokens have no `username` and no `cognito:groups` (`sub` is the client ID) ([Cognito access token](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-the-access-token.html)). With an access token the guide's path `...claims.cognito:username` does not match; what Quarkus then returns as Principal name is (unverified). AWS says "The username might not be unique in your user pool. The `sub` claim is the best way to identify a given user" (same page). Identify users and tenants by `sub` (or a custom attribute), read from the event claims (pattern 4), not from the Principal name; M2M tokens get no roles from `cognito:groups`.

```java
// Quarkus 3.40.1.1, Quarkus REST
@GET
@RolesAllowed("admin")
public String whoAmI(@Context jakarta.ws.rs.core.SecurityContext sec) {
    return sec.getUserPrincipal().getName(); // cognito:username with an ID token; access token: unverified
}
```

## 3. Groups to roles

"If the `cognito:groups` claim is present, then Quarkus will extract and map those groups to Quarkus roles", which `@RolesAllowed` uses; the guide says the mapping applies unless `quarkus.lambda-http.map-cognito-to-roles=false` ([aws-lambda-http guide](https://quarkus.io/version/3.40/guides/aws-lambda-http)). M2M access tokens carry no `cognito:groups`, so they get no roles from it. Defaults per key come from a partly read page (L1), so each is (medium confidence) ([all-config](https://quarkus.io/version/3.40/guides/all-config)):

| Key | Type | Default |
|---|---|---|
| `quarkus.lambda-http.map-cognito-to-roles` | boolean | `true` (medium confidence) |
| `quarkus.lambda-http.cognito-role-claim` | string | `cognito:groups` (medium confidence) |
| `quarkus.lambda-http.cognito-claim-matcher` | string | `[^\[\] \t]+` (medium confidence) ("Regular expression to locate role values within a Cognito claim string. By default, it looks for space delimited strings enclosed in brackets") |

The guide's example role value is `[ user admin ]`. That array claims reach the event as a bracketed string is implied by the matcher description and not stated (medium confidence). Test the mapping with a real group token.

```properties
quarkus.lambda-http.enable-security=true
quarkus.lambda-http.map-cognito-to-roles=true
quarkus.lambda-http.cognito-role-claim=cognito:groups
```

## 4. Claims from the event

By default the integration maps only the principal name and Cognito roles, not other claims. The guide documents injecting `com.amazonaws.services.lambda.runtime.Context`, `APIGatewayV2HTTPEvent` and `APIGatewayV2HTTPEvent.RequestContext` (HTTP API) or `io.quarkus.amazon.lambda.http.model.AwsProxyRequestContext` and `AwsProxyRequest` (REST API) with `@Context` (Jakarta REST) or `@Inject` (CDI). API Gateway "passes the claims in the token to the API route's integration" ([HTTP API JWT authorizer](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-jwt-authorizer.html)).

```java
// Quarkus 3.40.1.1, HTTP API. The accessor chain getAuthorizer().getJwt().getClaims()
// comes from aws-lambda-java-events and was not read (unverified)
@GET
@Authenticated
public Response me(@Context APIGatewayV2HTTPEvent event) {
    Map<String, String> claims = event.getRequestContext().getAuthorizer().getJwt().getClaims();
    String sub = claims.get("sub");
    return Response.ok(sub).build();
}
```

## 5. Tenant from the token

Only claims of a token whose signature was checked can be trusted: "Don't trust the claims in an access token until you verify the signature." Take the tenant from a claim, and compare a path tenant with it. Full treatment: [multi-tenant isolation](./multi-tenant-isolation.md).

```java
String tokenTenant = claims.get("custom:tenantId");     // ID token claim
if (tokenTenant == null || !tokenTenant.equals(pathTenant)) {
    return Response.status(Response.Status.FORBIDDEN).build();   // family rule 6
}
return Response.ok(service.ordersFor(tokenTenant)).build();       // always scope by the claim
```

## 6. Protect the tenant attribute

Custom attributes "are always prefixed with `custom:`", and Cognito writes them to the ID token as strings. "When you don't specify `WriteAttributes` for an app client, the app client has write access to all standard and custom attributes. Users can change the value of these attributes for themselves with `UpdateUserAttributes`." AWS adds: "In that case, remove the attribute from the `WriteAttributes` of every app client in your user pool." An immutable custom attribute "can be updated once, during user creation" ([Cognito attributes](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-attributes.html)).

```text
Every app client: WriteAttributes excludes custom:tenantId (set by AdminCreateUser or an admin process)
```

The pool configuration is IaC: `provisioning-aws-cognito-v6`. Architecture: `securing-aws-cognito`.

## 7. token_use and client binding

Cognito: "The `aud` claim in an ID token and the `client_id` claim in an access token must match the app client ID". `token_use` "must be `access`" when only access tokens are accepted. An access-token `aud` is "Present only if your application requested a resource binding" ([Cognito verifying a JWT](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html)). API Gateway: "There is no standard mechanism to differentiate JWT access tokens from other types of JWTs", so the HTTP JWT authorizer `Audience` and route scopes carry the check at the edge. The in-function keys are in [option B](./option-b-in-function-oidc.md#reference-keys).

## 8. Authorization annotations

`@RolesAllowed` limits access to roles. `@Authenticated` (`io.quarkus.security.Authenticated`) is "equivalent to `@RolesAllowed("**")`". `@PermitAll` "lets everybody in, even without authentication". `@PermissionsAllowed` (`io.quarkus.security.PermissionsAllowed`) uses `io.quarkus.security.StringPermission` by default; a colon separates name and action and a literal colon is escaped as `\\:`. "Authorization checks for `quarkus.http.auth.` configurations are performed before security checks for standard security annotations" ([authorize web endpoints reference](https://quarkus.io/version/3.40/guides/security-authorize-web-endpoints-reference)). Whether `quarkus.http.auth.permission.*` path policies run inside the Lambda HTTP extensions is (unverified): rely on annotations and test each path.

```java
@GET @RolesAllowed("tenant-admin")            // cognito:groups -> roles (pattern 3)
public List<Order> all() { ... }
```

## 9. Key rotation

Cognito "might rotate signing keys". Its advice: "cache public keys in your app, using the `kid` as a cache key, and refresh the cache periodically", and refresh when a token has "the correct issuer but a different `kid`". The `jwks.json` "can be updated at any time with new public token signing keys". Cognito publishes `https://cognito-idp.<Region>.amazonaws.com/<userPoolId>/.well-known/openid-configuration` and `/.well-known/jwks.json` ([Cognito federation endpoints](https://docs.aws.amazon.com/cognito/latest/developerguide/federation-endpoints.html)). Never copy a public key into configuration. The API Gateway HTTP JWT authorizer caches the key "for up to two hours on a best-effort basis" and a cache miss adds latency to that request.
