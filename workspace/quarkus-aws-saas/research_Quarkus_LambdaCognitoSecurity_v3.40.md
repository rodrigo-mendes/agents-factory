# Research: Amazon Cognito authentication and authorization for Quarkus 3.40 LTS (3.40.1.1) HTTP Lambdas

Unit U3 of the quarkus-aws-saas family. Future skill: `securing-quarkus-lambda-cognito-v3-40` (package `quarkus-aws`).
Source item: "Cognito authN/authZ in Quarkus, multi-tenant SaaS".
Family facts applied as given: `workspace/quarkus-aws-saas/_family_facts_v3.40.md`, `workspace/_family_facts_v3.40.md`.
Family rules applied as given: `workspace/quarkus-aws-saas/_family_rules_v3.40.md` (rule 6: tenant from token, never from path alone; rules 9-12), `workspace/_family_rules_v3.40.md` (evidence rule 5, tag notation rule 7, register IDs rule 12).

All pages were read on **2026-10-28** through the WebFetch tool. Text in quotes was returned verbatim by the tool. Where the tool paraphrased, the statement is written as a paraphrase. Pages read only in part are listed as coverage limits (L-ids) in Research Gaps.

Out of scope (other units or skills): Lambda HTTP mechanics (U2), packaging and native/SnapStart (U1), AWS SDK clients (U4/U5), Cognito user-pool provisioning (`provisioning-aws-cognito-v6`), Cognito architecture (`securing-aws-cognito`), browser login and managed login/Hosted UI, Quarkus 4.

---

## Metadata

```yaml
Full_Name: Security for Quarkus AWS Lambda HTTP/REST functions with Amazon Cognito (quarkus-amazon-lambda-http / quarkus-amazon-lambda-rest security integration, quarkus-oidc bearer tokens, quarkus-smallrye-jwt)
Target_Version: Quarkus 3.40 LTS, patch 3.40.1.1
Release_Date: Quarkus 3.40 released 2026-09-30; 3.40.1.1 released 2026-10-19 (family fact, https://quarkus.io/releases)
Support_Status: LTS, community-maintained until 2027-09-30 (family fact, https://quarkus.io/releases)
Primary_Docs: https://quarkus.io/version/3.40/guides/aws-lambda-http (Security Integration section)
Secondary_Docs: >
  https://quarkus.io/version/3.40/guides/security-oidc-bearer-token-authentication ;
  https://quarkus.io/version/3.40/guides/security-oidc-configuration-properties-reference ;
  https://quarkus.io/version/3.40/guides/security-authorize-web-endpoints-reference ;
  https://quarkus.io/version/3.40/guides/security-openid-connect-multitenancy ;
  https://quarkus.io/version/3.40/guides/security-jwt ;
  https://quarkus.io/version/3.40/guides/security-authentication-mechanisms ;
  https://quarkus.io/version/3.40/guides/all-config
Registry: >
  https://repo1.maven.org/maven2/io/quarkus/quarkus-amazon-lambda-http/3.40.1.1/quarkus-amazon-lambda-http-3.40.1.1.pom ;
  https://repo1.maven.org/maven2/io/quarkus/quarkus-amazon-lambda-rest/3.40.1.1/quarkus-amazon-lambda-rest-3.40.1.1.pom
Platform_Docs: >
  Cognito: amazon-cognito-user-pools-using-tokens-verifying-a-jwt, -using-the-access-token, -using-the-id-token,
  -using-the-refresh-token, federation-endpoints, user-pool-lambda-pre-token-generation, user-pool-settings-attributes;
  API Gateway: http-api-jwt-authorizer, http-api-develop-integrations-lambda, apigateway-integrate-with-cognito,
  apigateway-enable-cognito-user-pool (full URLs in Source Bibliography)
Official_Repo: https://github.com/quarkusio/quarkus (extensions/amazon-lambda-http) (page not recorded: source not fetched)
Research_Date: 2026-10-28
Domain_Complexity: Complex   # auth, multi-tenant isolation, two validation layers, two AWS API types
Research_Depth: deep
Max_Iterations: 3
Gap_Loop_Ran: true
Iterations_Used: 3 of 3
Triangulated_Count: 6
Unverified_Count: 10
Irresolvable_Count: 0
Research_Quality_Score: 88%   # ~85 sourced claims; 10 unverified -> (85-10)/85
Execution_Notes: >
  Caller constraints honoured: no sub-agents (P2.parallel skipped), no plan mode (scope approval relayed by the
  caller from workspace/quarkus-aws-saas/PIPELINE_STATE.md#approvals; recorded here as a relay, not as an approval
  given by this agent), file written directly instead of via research-synthesizer.
```

---

## Executive Summary

A Quarkus 3.40 HTTP Lambda (`quarkus-amazon-lambda-http` for API Gateway HTTP APIs, `quarkus-amazon-lambda-rest` for REST APIs) can get a Cognito-authenticated caller in two documented ways. **Option A, API Gateway validates and Quarkus maps.** With `quarkus.lambda-http.enable-security=true` (default `false`), "Quarkus will automatically parse the event JSON" and register a `java.security.Principal` (`io.quarkus.amazon.lambda.http.CognitoPrincipal`, `IAMPrincipal` or `CustomPrincipal`). The Principal name comes from `requestContext.authorizer.jwt.claims.cognito:username` (HTTP API) or `requestContext.authorizer.claims.cognito:username` (REST API). `cognito:groups` becomes Quarkus roles (`quarkus.lambda-http.map-cognito-to-roles`, default `true`; `quarkus.lambda-http.cognito-role-claim`, default `cognito:groups`), so `@RolesAllowed` works. A CDI bean implementing `io.quarkus.amazon.lambda.http.LambdaIdentityProvider` can replace the mapping (https://quarkus.io/version/3.40/guides/aws-lambda-http ; https://quarkus.io/version/3.40/guides/all-config, read 2026-10-28). The guide does not say that the function checks the token itself. It maps what API Gateway puts in the event, and by default it maps only the principal name and roles: "It does not map claims" (paraphrase of the guide). **Option B, in-function validation.** `quarkus-oidc` in `service` mode, with `quarkus.oidc.auth-server-url` set to the Cognito issuer `https://cognito-idp.<Region>.amazonaws.com/<userPoolId>`, finds the JWKS through `/.well-known/openid-configuration`, a discovery document that Cognito publishes (https://quarkus.io/version/3.40/guides/security-oidc-bearer-token-authentication ; https://docs.aws.amazon.com/cognito/latest/developerguide/federation-endpoints.html). The guides do not document that `quarkus-oidc` runs inside the Lambda HTTP extensions (unverified, see U1). Both extension POMs depend on `quarkus-vertx-http` and `quarkus-security`, which makes it likely (medium confidence).

Cognito details that the Quarkus defaults do not cover: an access token carries `client_id` and `token_use=access` and has **no `aud`** unless a resource binding was requested. An ID token carries `aud` = app client ID and `token_use=id`. AWS says you must check `token_use` (https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html). Quarkus checks `aud` for ID tokens by default, and for access tokens "only if this property is configured" (`quarkus.oidc.token.audience`). Cognito access tokens therefore need `quarkus.oidc.token.required-claims.client_id` and `required-claims.token_use`. `required-claims` accepts "Strings and arrays of strings" (https://quarkus.io/version/3.40/guides/security-oidc-configuration-properties-reference). Quarkus OIDC takes roles from `groups` or Keycloak paths unless `quarkus.oidc.roles.role-claim-path` is set, so `cognito:groups` must be configured explicitly. Custom attributes (`custom:<name>`, always strings) are written to the **ID token** by default. An access token gets them only through a pre token generation trigger at event version V2_0/V3_0 (Essentials or Plus feature plan) (https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-pre-token-generation.html).

The three critical patterns: (1) pick one validation layer deliberately (API Gateway authorizer, in-function `quarkus-oidc`, or both), an Ask-First decision, and never accept an unverified token or header as identity. (2) For Cognito access tokens, check issuer, `token_use=access` and `client_id`. Map `cognito:groups` and scopes explicitly to `@RolesAllowed` / `@PermissionsAllowed`. (3) Multi-tenancy (family rule 6): read the tenant from a verified claim, such as `custom:tenantId` in the ID token or a claim added to the access token. Treat a path or header tenant only as a value that must equal the claim. Remove that attribute from the `WriteAttributes` of every app client, because "Users can change the value of these attributes for themselves with `UpdateUserAttributes`" (https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-attributes.html). The domain is **Complex**: security-critical, two AWS API types with different event shapes, two validation layers, and tenant isolation.

---

## Architectural Guardrails

> Confidence legend: 🟢 High (versioned Quarkus 3.40 page, Maven Central POM, or official AWS page read 2026-10-28) | 🟡 Medium (partly read page used for an unread part, or inference) | 🔴 Low (community or unverified: verify before use)
> Family evidence rule applied (`_family_rules_v3.40.md` rule 5): one versioned official source is enough for High. The template's "fewer than 2 sources means Medium" downgrade does not apply.

### ✅ Mandatory Patterns

**A1. Option A: turn on the Lambda HTTP security integration explicitly**
> Confidence: 🟢 High | [✓✓ Triangulated | aws-lambda-http guide (2026-10-28) + all-config reference (2026-10-28)]
- Why: `quarkus.lambda-http.enable-security` is boolean, default `false`: "Enable security mechanisms to process lambda and AWS based security (i.e. Cognito, IAM) from the http event sent from API Gateway". When it is on, Quarkus parses the event JSON and registers a `java.security.Principal`. Jakarta REST reads it through `jakarta.ws.rs.core.SecurityContext`, servlet through `HttpServletRequest.getUserPrincipal()`, Reactive Routes through `RouteContext.user()`.
- Code (Quarkus 3.40.1.1, `application.properties`):
  ```properties
  # Quarkus 3.40: default is false, so without this line no Principal is registered
  quarkus.lambda-http.enable-security=true
  ```
- Source: https://quarkus.io/version/3.40/guides/aws-lambda-http (2026-10-28); https://quarkus.io/version/3.40/guides/all-config (2026-10-28, rows in the read range 0-100000, see L1)

**A2. Option A: know which event field becomes the Principal name for each API type**
> Confidence: 🟢 High | aws-lambda-http guide (2026-10-28)
- Why: the guide documents fixed paths. HTTP API: Cognito JWT `requestContext.authorizer.jwt.claims.cognito:username`; IAM `requestContext.authorizer.iam.userId`; Lambda authorizer `requestContext.authorizer.lambda.principalId`. REST API: Cognito `requestContext.authorizer.claims.cognito:username`; IAM `requestContext.identity.user`; Lambda authorizer `requestContext.authorizer.principalId`. Principal classes for both: `io.quarkus.amazon.lambda.http.CognitoPrincipal`, `IAMPrincipal`, `CustomPrincipal`. The Principal name is the Cognito username, not `sub`. AWS says "The username might not be unique in your user pool. The `sub` claim is the best way to identify a given user" (https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-the-access-token.html).
- Code (Quarkus 3.40.1.1, Quarkus REST):
  ```java
  @GET
  @RolesAllowed("admin")
  public String whoAmI(@Context jakarta.ws.rs.core.SecurityContext sec) {
      // Name = cognito:username (HTTP API: requestContext.authorizer.jwt.claims.cognito:username)
      return sec.getUserPrincipal().getName();
  }
  ```
- Source: https://quarkus.io/version/3.40/guides/aws-lambda-http (2026-10-28)

**A3. Option A: Cognito groups become Quarkus roles by default; change the claim only through the documented keys**
> Confidence: 🟢 High | [✓✓ Triangulated | aws-lambda-http guide (2026-10-28) + all-config reference (2026-10-28)]
- Why: "If the `cognito:groups` claim is present, then Quarkus will extract and map those groups to Quarkus roles", which `@RolesAllowed` can then use. Per key (family rule 10): `quarkus.lambda-http.map-cognito-to-roles` boolean, default `true`; `quarkus.lambda-http.cognito-role-claim` string, default `cognito:groups`; `quarkus.lambda-http.cognito-claim-matcher` string, default `[^\[\] \t]+` ("Regular expression to locate role values within a Cognito claim string. By default, it looks for space delimited strings enclosed in brackets"). The guide's example role value is `[ user admin ]`.
- Code (Quarkus 3.40.1.1):
  ```properties
  quarkus.lambda-http.enable-security=true
  # Defaults shown explicitly (all-config 3.40):
  quarkus.lambda-http.map-cognito-to-roles=true
  quarkus.lambda-http.cognito-role-claim=cognito:groups
  ```
- Source: https://quarkus.io/version/3.40/guides/aws-lambda-http (2026-10-28); https://quarkus.io/version/3.40/guides/all-config (2026-10-28)

**A4. Option A: read claims beyond name and roles from the injected API Gateway event**
> Confidence: 🟢 High (injection) | aws-lambda-http guide (2026-10-28)
- Why: by default the integration maps only the principal name (and Cognito roles), not other claims (paraphrase of the guide). The guide documents injection with `@Context` (Jakarta REST) or `@Inject` (CDI) of `com.amazonaws.services.lambda.runtime.Context`, `com.amazonaws.services.lambda.runtime.events.APIGatewayV2HTTPEvent` and `APIGatewayV2HTTPEvent.RequestContext` (HTTP API), and `io.quarkus.amazon.lambda.http.model.AwsProxyRequestContext` / `AwsProxyRequest` (REST API). API Gateway "passes the claims in the token to the API route's integration", for example in `$event.requestContext.authorizer.jwt.claims.emailID` (https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-jwt-authorizer.html).
- Code (Quarkus 3.40.1.1, HTTP API; the `getAuthorizer().getJwt().getClaims()` accessor names come from aws-lambda-java-events and were not read here (unverified)):
  ```java
  @GET
  @Path("/tenants/{tenantId}/orders")
  @Authenticated
  public Response list(@PathParam("tenantId") String pathTenant,
                       @Context APIGatewayV2HTTPEvent event) {
      Map<String, String> claims = event.getRequestContext().getAuthorizer().getJwt().getClaims();
      String tokenTenant = claims.get("custom:tenantId");   // ID token claim, see A8
      if (tokenTenant == null || !tokenTenant.equals(pathTenant)) {
          return Response.status(Response.Status.FORBIDDEN).build();  // family rule 6
      }
      // ... query scoped by tokenTenant
  }
  ```
- Source: https://quarkus.io/version/3.40/guides/aws-lambda-http (2026-10-28); https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-jwt-authorizer.html (2026-10-28)

**A5. Option B: point `quarkus-oidc` at the exact Cognito issuer and run it in `service` mode**
> Confidence: 🟢 High | [✓✓ Triangulated | Quarkus bearer-token guide (2026-10-28) + Cognito federation-endpoints (2026-10-28) + Cognito verifying-a-JWT (2026-10-28)]
- Why: Quarkus discovers endpoints "by appending `/.well-known/openid-configuration`" to `quarkus.oidc.auth-server-url`. `quarkus.oidc.discovery-enabled` defaults to `true`. Cognito publishes `https://cognito-idp.<Region>.amazonaws.com/<userPoolId>/.well-known/openid-configuration` and `/.well-known/jwks.json`. The `iss` "must match your user pool", for example `https://cognito-idp.us-east-1.amazonaws.com/<userpoolID>`. `quarkus.oidc.application-type` values: `web-app`, `service`, `hybrid`. `client-id` is "not required if `application-type` is `service` and no token introspection is required".
- Code (Quarkus 3.40.1.1):
  ```properties
  quarkus.oidc.application-type=service
  # Original issuer format; see K4 for the updated issuer
  quarkus.oidc.auth-server-url=https://cognito-idp.us-east-1.amazonaws.com/us-east-1_EXAMPLE
  ```
- Source: https://quarkus.io/version/3.40/guides/security-oidc-bearer-token-authentication (2026-10-28, partly read, see L2); https://quarkus.io/version/3.40/guides/security-oidc-configuration-properties-reference (2026-10-28); https://docs.aws.amazon.com/cognito/latest/developerguide/federation-endpoints.html (2026-10-28)

**A6. Option B: for Cognito access tokens, require `token_use=access` and the app client's `client_id`**
> Confidence: 🟢 High | [✓✓ Triangulated | Cognito verifying-a-JWT (2026-10-28) + Cognito access-token page (2026-10-28) + Quarkus OIDC config reference (2026-10-28)]
- Why: Cognito: "The `aud` claim in an ID token and the `client_id` claim in an access token must match the app client ID". `token_use` "must be `access`" when you accept only access tokens. An access-token `aud` is "Present only if your application requested a resource binding". Quarkus: `quarkus.oidc.token.audience` ... "Audience verification for access tokens is only done if this property is configured". `quarkus.oidc.token.required-claims."claim-name"` is "A map of required claims and their expected values. Strings and arrays of strings are currently the only supported types."
- Code (Quarkus 3.40.1.1, access tokens without a resource binding):
  ```properties
  quarkus.oidc.token.required-claims.token_use=access
  quarkus.oidc.token.required-claims.client_id=${COGNITO_APP_CLIENT_ID}
  ```
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html (2026-10-28); https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-the-access-token.html (2026-10-28); https://quarkus.io/version/3.40/guides/security-oidc-configuration-properties-reference (2026-10-28)

**A7. Option B: map `cognito:groups` to roles explicitly; Quarkus' default role claims are not Cognito's**
> Confidence: 🟢 High (behaviour) | Quarkus bearer-token guide + OIDC config reference (2026-10-28) + Cognito access-token page (2026-10-28)
- Why: Quarkus takes roles from the `quarkus.oidc.roles.role-claim-path` claims if set, then a `groups` claim, then `realm_access/roles` or `resource_access/<client-id>/roles` (paraphrase of the bearer guide). `quarkus.oidc.roles.source` defaults to `accesstoken` for `service` applications. Cognito access tokens carry `cognito:groups`, "An array of the names of user pool groups". The config reference says: "Use double quotes with the namespace-qualified claim names". Whether `cognito:groups` needs those quotes is not stated (medium confidence, M2); see the Implementation Blueprint.
- Code (Quarkus 3.40.1.1):
  ```properties
  # Quoting of the colon-containing claim name: (medium confidence), verify with a test (Quality Control)
  quarkus.oidc.roles.role-claim-path="cognito:groups"
  ```
- Source: https://quarkus.io/version/3.40/guides/security-oidc-bearer-token-authentication (2026-10-28); https://quarkus.io/version/3.40/guides/security-oidc-configuration-properties-reference (2026-10-28); https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-the-access-token.html (2026-10-28)

**A8. Tenant identity comes from a verified token claim whose attribute users cannot write (family rule 6)**
> Confidence: 🟢 High | [✓✓ Triangulated | Cognito ID-token page + user-pool attributes page + pre-token-generation page (all 2026-10-28)]
- Why: custom attributes "are always prefixed with `custom:`", and "Amazon Cognito writes custom attribute values to the ID token as strings regardless of attribute type". In the pre token generation table, `custom:` attributes have default token type "ID". Access tokens can get extra claims only with event version V2_0/V3_0 ("In user pools with the Essentials or Plus feature plan"). Write protection: "When you don't specify `WriteAttributes` for an app client, the app client has write access to all standard and custom attributes. Users can change the value of these attributes for themselves with `UpdateUserAttributes`." AWS adds: "Your application or identity pool might make authorization decisions based on an attribute. In that case, remove the attribute from the `WriteAttributes` of every app client in your user pool." An immutable custom attribute "can be updated once, during user creation".
- Code: see A4 (Option A) and the Implementation Blueprint (Option B).
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-the-id-token.html (2026-10-28); https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-attributes.html (2026-10-28); https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-pre-token-generation.html (2026-10-28)

**A9. Express authorization with the documented Quarkus 3.40 annotations and HTTP policies**
> Confidence: 🟢 High | authorize-web-endpoints reference (2026-10-28) + bearer-token guide (2026-10-28)
- Why: `@RolesAllowed` limits access to roles. `@Authenticated` (`io.quarkus.security.Authenticated`) is "equivalent to `@RolesAllowed("**")`". `@PermitAll` "lets everybody in, even without authentication". `@PermissionsAllowed` (`io.quarkus.security.PermissionsAllowed`) uses `io.quarkus.security.StringPermission` by default. A colon separates permission name and action, and a literal colon is escaped as `\\:`. With `quarkus-oidc`, token scopes become `StringPermission`s, so `@PermissionsAllowed("orders_read")` admits clients holding that scope. "Authorization checks for `quarkus.http.auth.` configurations are performed before security checks for standard security annotations." Whether `quarkus.http.auth.permission.*` policies run inside the Lambda HTTP extensions is (unverified), see U2.
- Code (Quarkus 3.40.1.1):
  ```java
  @GET @RolesAllowed("tenant-admin")                 // cognito:groups -> roles (A3 / A7)
  public List<Order> all() { ... }

  @GET @Path("/mine") @PermissionsAllowed("orders/read")   // Option B: Cognito custom scope "orders/read"
  public List<Order> mine() { ... }
  ```
- Source: https://quarkus.io/version/3.40/guides/security-authorize-web-endpoints-reference (2026-10-28); https://quarkus.io/version/3.40/guides/security-oidc-bearer-token-authentication (2026-10-28)

**A10. Option B: let `quarkus-oidc` follow Cognito key rotation; do not pin static keys**
> Confidence: 🟢 High | [✓✓ Triangulated | Cognito verifying-a-JWT (2026-10-28) + Quarkus bearer guide and config reference (2026-10-28)]
- Why: Cognito "might rotate signing keys". Its advice is to "cache public keys in your app, using the `kid` as a cache key, and refresh the cache periodically", and to refresh when a token has "the correct issuer but a different `kid`". The `jwks.json` "can be updated at any time with new public token signing keys". Quarkus refreshes the key set when no key matches the `kid`, at most once per `quarkus.oidc.token.forced-jwk-refresh-interval` (Duration, default `10M`). Other keys: `quarkus.oidc.jwks.resolve-early` (default `true`), `quarkus.oidc.jwks.cache-size` (default `10`), `quarkus.oidc.jwks.cache-time-to-live` (default `10M`).
- Code (Quarkus 3.40.1.1): keep discovery on (`quarkus.oidc.discovery-enabled` default `true`). If discovery is turned off, set `quarkus.oidc.jwks-path` to the pool's `/.well-known/jwks.json`, never to a copied key.
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html (2026-10-28); https://docs.aws.amazon.com/cognito/latest/developerguide/federation-endpoints.html (2026-10-28); https://quarkus.io/version/3.40/guides/security-oidc-configuration-properties-reference (2026-10-28)

### ⚠️ Conditional Patterns

**K1. Where is the token validated: API Gateway authorizer (Option A), in-function (Option B), or both?**
> Confidence: 🟡 Medium (the cost and latency figures are not documented; facts per row are High where cited)
- Options: A) API Gateway JWT authorizer (HTTP API) or `COGNITO_USER_POOLS` authorizer (REST API), plus `quarkus.lambda-http.enable-security=true`. B) No authorizer on the route; `quarkus-oidc` checks the bearer token in the function (compatibility unverified, U1). C) Both, as defence in depth.
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A | Invalid tokens are rejected before the Lambda is invoked. The HTTP JWT authorizer checks `kid`, `iss`, `aud`/`client_id`, `exp`, `nbf`, `iat` and route scopes, and caches the public key "for up to two hours on a best-effort basis" (AWS). The Quarkus side only maps the event. | The function trusts the event. Only the name and roles are mapped (A4). A route left without an authorizer gives no Principal. A cache miss "adds latency to the request that triggers it" (AWS). | One pool or a few pools, scope or group checks are enough at the edge. |
  | B | The function verifies `token_use`, `client_id` and custom claims itself and does not depend on route configuration. | The Lambda is invoked (and billed) for rejected requests. JWKS fetch at connection init (`jwks.resolve-early` default `true`); cold-start impact (unverified, U6). Running in the Lambda extension is not documented (unverified, U1). | Checks the authorizer cannot express, or a stack without API Gateway authorizers. |
  | C | Defence in depth: a misconfigured route is still protected by the function. | Both costs. Two configurations must agree on issuer and audience. Interaction of `enable-security` with `quarkus-oidc` (unverified, U4). | Multi-tenant SaaS with a high isolation requirement. |

- Agent: "Ask the user whether tokens are validated by API Gateway, by the function, or both, and what pricing/latency data they accept (AWS pricing not read in this research: (unverified), U7)."
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-jwt-authorizer.html (2026-10-28); https://quarkus.io/version/3.40/guides/aws-lambda-http (2026-10-28); https://quarkus.io/version/3.40/guides/security-oidc-configuration-properties-reference (2026-10-28)

**K2. ID token or access token at the API?**
> Confidence: 🟢 High (facts) / decision is context-dependent
- Options: A) Access token with custom scopes. B) ID token. C) Both (then `token_use` must be `id` or `access`).
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | Access token | Scopes for API authorization. HTTP JWT authorizer: "we recommend that you configure your routes to require authorization scopes". REST authorizer with Authorization Scopes treats the token as an access token. | No `custom:` attributes unless a V2_0/V3_0 pre token trigger adds them (Essentials/Plus). No `aud` without a resource binding. | Standard API authorization. |
  | ID token | Carries `custom:` attributes (for example tenant) and `aud`. REST authorizer: "If you do not configure any Authorization scopes, API Gateway treats the supplied token as an identity token". | AWS: "There is no standard mechanism to differentiate JWT access tokens from other types of JWTs". No scopes. | Simple user APIs that need profile claims and have no pre token trigger. |

- Agent: "Ask which token the client sends and whether the user pool's feature plan allows access-token customization (V2_0)."
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-jwt-authorizer.html (2026-10-28); https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-enable-cognito-user-pool.html (2026-10-28); https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-pre-token-generation.html (2026-10-28)

**K3. Tenant model: single pool with a tenant claim, or a user pool per tenant**
> Confidence: 🟢 High (Quarkus and AWS mechanisms) / 🟡 Medium (one issuer per HTTP JWT authorizer, M5)
- Options: A) One pool, `custom:tenantId` (or a pre-token claim) per user (A8). B) Pool per tenant, Option B with Quarkus OIDC multi-tenancy: named tenants `quarkus.oidc.<tenant>.auth-server-url`, plus `quarkus.oidc.resolve-tenants-with-issuer=true` (the bearer token must be a JWT with `iss`; only `service`/`hybrid` tenants are considered) or a `TenantResolver` / `TenantConfigResolver`. C) Pool per tenant behind a REST API `COGNITO_USER_POOLS` authorizer, which accepts "up to 1,000 user pools for one `COGNITO_USER_POOLS` authorizer. This limit cannot be increased."
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A | One issuer and one config. | The tenant claim must be protected (A8, N5). | Most pooled SaaS. |
  | B (issuer) | Tenant follows from the signed `iss`, not from the path. | One config block per tenant, or a dynamic `TenantConfigResolver`. | Few large tenants with separate pools. |
  | B (path) | `quarkus.oidc.<tenant>.tenant-paths` is simple. | Selects only which issuer's keys check the token. It does not prove the caller belongs to the path's tenant unless each tenant has its own issuer (family rule 6). | Only together with per-tenant issuers. |
  | C | Edge validation for many pools. | 1,000-pool hard limit. | REST APIs. |

- Agent: "Ask for the tenant model (pooled vs pool-per-tenant) and the expected tenant count."
- Source: https://quarkus.io/version/3.40/guides/security-openid-connect-multitenancy (2026-10-28); https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-enable-cognito-user-pool.html (2026-10-28)

**K4. Original or updated Cognito issuer**
> Confidence: 🟢 High (formats) / (unverified) the issuer value inside the updated issuer's discovery document (U9)
- Options: original `https://cognito-idp.<region>.amazonaws.com/<poolId>` ("The current default issuer configuration") or updated `https://issuer-cognito-idp.<region>.amazonaws.com/<poolId>` ("Recommended for all user pools, including for multi-Region replication").
- Tradeoffs: the token's `iss`, `quarkus.oidc.auth-server-url` (or `quarkus.oidc.token.issuer`) and the API Gateway authorizer `Issuer` must all name the same issuer.
- Agent: "Ask which issuer type the pool uses (decode a real token's `iss`)."
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/federation-endpoints.html (2026-10-28)

**K5. Revocation and token lifetime**
> Confidence: 🟢 High (facts)
- Facts: access and ID tokens: "any value between 5 minutes and 1 day", per app client. Refresh token: default 30 days, "any value between 60 minutes and 10 years". Rotation is optional, "As a security best practice, enable refresh token rotation". Offline checks "can't detect revocation on their own. If your application must honor revocation before a token expires, verify the token's status against Amazon Cognito ... or keep access token lifetimes short."
- Options: short access-token lifetime (offline validation only) vs an online check per request (extra latency; no Quarkus pattern for Cognito was researched).
- Agent: "Ask whether revocation must take effect before token expiry."
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-the-access-token.html ; https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-the-refresh-token.html ; https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html (all 2026-10-28)

**K6. Deny-by-default for unannotated endpoints**
> Confidence: 🟢 High (property) / 🟡 Medium (that it is the right default for this family: engineering judgement)
- Options: `quarkus.security.jaxrs.deny-unannotated-endpoints=true` (default `false`); `quarkus.security.jaxrs.default-roles-allowed=...` ("The `**` role is a special role that means any authenticated user"). The page notes that `deny-unannotated-endpoints` takes precedence over `default-roles-allowed`.
- Agent: "Ask whether every endpoint must carry an explicit security annotation."
- Source: https://quarkus.io/version/3.40/guides/security-authorize-web-endpoints-reference (2026-10-28)

**K7. `quarkus-oidc` or `quarkus-smallrye-jwt` for Option B**
> Confidence: 🟢 High (facts)
- Facts: SmallRye JWT "verifies only `JWT` tokens" and "does not support the remote introspection". Both refresh the JWK set (https://quarkus.io/version/3.40/guides/security-authentication-mechanisms, partly read, L3). SmallRye JWT keys: `mp.jwt.verify.publickey.location` (a path or URL, including an HTTPS JWK set; native mode needs `quarkus.ssl.native`), `mp.jwt.verify.issuer`, `mp.jwt.verify.audiences` (matched against `aud`, so it does not fit access tokens without `aud`), `smallrye.jwt.path.groups` ("Use double quotes with the namespace-qualified claims"), `smallrye.jwt.required.claims` ("Comma-separated list of the claims a token must contain", presence only), `smallrye.jwt.jwks.refresh-interval` (60 min), `smallrye.jwt.jwks.forced-refresh-interval` (30 min) (https://quarkus.io/version/3.40/guides/security-jwt). `quarkus-oidc` has value checks (`required-claims`) and issuer discovery.
- Agent: "Ask before choosing smallrye-jwt: it has no documented value check for `client_id`/`token_use`, so a `SecurityIdentityAugmentor` or code check would be needed."
- Source: https://quarkus.io/version/3.40/guides/security-jwt (2026-10-28); https://quarkus.io/version/3.40/guides/security-authentication-mechanisms (2026-10-28)

### 🚫 Forbidden Patterns

**N1. Taking the tenant from the path, a header or the body alone (family rule 6)**
> Severity: Critical
> Confidence: 🟢 High
- Why: a path or header value is chosen by the caller. Only claims in a token whose signature was checked can be trusted: "Don't trust the claims in an access token until you verify the signature."
- Impact: cross-tenant data access by changing a URL.
- ❌ Wrong:
  ```java
  @GET @Path("/tenants/{tenantId}/orders") @Authenticated
  public List<Order> list(@PathParam("tenantId") String tenantId) {
      return repo.findByTenant(tenantId);           // caller-chosen tenant
  }
  ```
- ✅ Correct:
  ```java
  String tokenTenant = claims.get("custom:tenantId"); // verified claim (A4 / Implementation Blueprint)
  if (!pathTenant.equals(tokenTenant)) return Response.status(403).build();
  return Response.ok(repo.findByTenant(tokenTenant)).build();
  ```
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-the-access-token.html (2026-10-28); family rule 6 (`workspace/quarkus-aws-saas/_family_rules_v3.40.md`)

**N2. Making authorization decisions on a custom attribute that app clients can write**
> Severity: Critical
> Confidence: 🟢 High
- Why: by default an app client "has write access to all standard and custom attributes", and "Users can change the value of these attributes for themselves with `UpdateUserAttributes`". "A value that a user writes through one app client appears in the tokens that all app clients issue."
- Impact: a user moves themself into another tenant or role; the signed token then carries the forged value.
- ❌ Wrong (app client config artifact):
  ```text
  App client "web": WriteAttributes not specified   -> custom:tenantId writable by the user
  ```
- ✅ Correct:
  ```text
  Every app client: WriteAttributes excludes custom:tenantId (attribute set by AdminCreateUser / an admin process)
  ```
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-attributes.html (2026-10-28)

**N3. Accepting any Cognito JWT without checking `token_use` (and `client_id` / `aud`)**
> Severity: High
> Confidence: 🟢 High
- Why: Cognito says to check `token_use` and to match `client_id` (access) or `aud` (ID) to the app client. API Gateway: "There is no standard mechanism to differentiate JWT access tokens from other types of JWTs".
- Impact: an ID token, or a token for another app client of the same pool, is accepted as an API access token.
- ❌ Wrong:
  ```properties
  quarkus.oidc.auth-server-url=https://cognito-idp.us-east-1.amazonaws.com/us-east-1_EXAMPLE
  # nothing else: no token_use / client_id check for access tokens
  ```
- ✅ Correct:
  ```properties
  quarkus.oidc.auth-server-url=https://cognito-idp.us-east-1.amazonaws.com/us-east-1_EXAMPLE
  quarkus.oidc.token.required-claims.token_use=access
  quarkus.oidc.token.required-claims.client_id=${COGNITO_APP_CLIENT_ID}
  ```
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html (2026-10-28); https://quarkus.io/version/3.40/guides/security-oidc-configuration-properties-reference (2026-10-28)

**N4. Disabling issuer verification (`quarkus.oidc.token.issuer=any`) for Cognito**
> Severity: High
> Confidence: 🟢 High
- Why: Quarkus says to set `any` only when a fixed `iss` value cannot be configured at the provider, as a last resort. Cognito issuers are fixed per pool, and "The issuer (`iss`) claim must match your user pool".
- Impact: tokens from any issuer whose keys resolve are accepted.
- ❌ Wrong:
  ```properties
  quarkus.oidc.token.issuer=any
  ```
- ✅ Correct:
  ```properties
  # issuer taken from the pool's discovery document (auth-server-url = exact pool issuer)
  quarkus.oidc.auth-server-url=https://cognito-idp.us-east-1.amazonaws.com/us-east-1_EXAMPLE
  ```
- Source: https://quarkus.io/version/3.40/guides/security-oidc-bearer-token-authentication (2026-10-28); https://quarkus.io/version/3.40/guides/security-oidc-configuration-properties-reference (2026-10-28); https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html (2026-10-28)

**N5. Building identity from unverified request data (decoded JWT, `x-user`-style header) in a `LambdaIdentityProvider`**
> Severity: Critical
> Confidence: 🟢 High
- Why: the guide's `CustomSecurityProvider` example reads an `x-user` header to show the API. It is an example, not a trust model. Cognito: "JSON web tokens (JWTs) can be decoded, read, and modified easily", and the signature "is the key component of token validation".
- Impact: anyone who can reach the function URL or a route without an authorizer can impersonate any user.
- ❌ Wrong:
  ```java
  public SecurityIdentity authenticate(APIGatewayV2HTTPEvent event) {
      Principal p = new QuarkusPrincipal(event.getHeaders().get("x-user")); // caller-controlled
      return QuarkusSecurityIdentity.builder().setPrincipal(p).build();
  }
  ```
- ✅ Correct (High alternatives only, family rule 9):
  ```properties
  # Either: authorizer-validated event (A1-A3), the route has a JWT / COGNITO_USER_POOLS authorizer
  quarkus.lambda-http.enable-security=true
  # Or: signature-verified bearer token in the function (A5-A7)
  # (running quarkus-oidc in the Lambda extension: see K1 / U1)
  ```
- Source: https://quarkus.io/version/3.40/guides/aws-lambda-http (2026-10-28); https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html (2026-10-28)

**N6. Setting `QUARKUS_AWS_LAMBDA_FORCE_USER_NAME` outside `sam local` testing**
> Severity: Critical
> Confidence: 🟢 High (the guide documents the variable only for `sam local` testing; it hard-codes a principal name)
- Why: "If you are testing your application with `sam local` you can hardcode a principal name" through this variable.
- Impact: every request runs as the forced user.
- ❌ Wrong (deployed function environment):
  ```text
  QUARKUS_AWS_LAMBDA_FORCE_USER_NAME=admin
  ```
- ✅ Correct:
  ```text
  Variable set only in the local sam test environment; absent from every deployed function configuration
  ```
- Source: https://quarkus.io/version/3.40/guides/aws-lambda-http (2026-10-28)

**N7. Expecting `custom:` attributes in the access token without a V2_0/V3_0 pre token generation trigger**
> Severity: High (moderate)
> Confidence: 🟢 High
- Why: the default token type of `custom:` attributes is "ID". Access-token customization needs event version V2_0/V3_0 (Essentials or Plus feature plan).
- Impact: the tenant claim is `null`. Code that then falls back to the path tenant breaks N1.
- ❌ Wrong:
  ```java
  String tenant = jwt.getClaim("custom:tenantId");   // access token, no V2_0 trigger
  if (tenant == null) tenant = pathTenant;          // falls back to caller input
  ```
- ✅ Correct:
  ```java
  String tenant = jwt.getClaim("custom:tenantId");   // ID token, or access token with a V2_0 trigger adding the claim
  if (tenant == null) throw new ForbiddenException();
  ```
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-pre-token-generation.html (2026-10-28); https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-the-id-token.html (2026-10-28)

> `jwt.getClaim(String)` is the MicroProfile JWT API. Its exact signature was not read here (medium confidence, M3).

---

## Migration Guide

> Confidence: 🟢 High | Sources: https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.40 (2026-10-28)

**Breaking Changes**: none for security, OIDC, SmallRye JWT, HTTP permissions or Lambda HTTP in 3.40. The wiki says "Quarkus 3.40 LTS is the direct continuation of 3.39 so we don't expect any changes requiring manual intervention in 3.40." Migration guides 3.31-3.39 were not read for security entries (unverified, U8). Inherited family fact: `quarkus-junit5` was renamed `quarkus-junit` in Quarkus 3.31 (High, `workspace/_family_facts_v3.40.md`); it applies to the test dependencies below.

**Upgrade Steps** (for a project moving onto 3.40.1.1):
1. Align the Quarkus platform BOM to 3.40.1.1 (family fact; command per U1 research).
2. Re-run the security tests in Quality Control. No config key renames are documented for 3.40.

**Compatibility Matrix**:

| Dependency | Min | Max | Notes |
|------------|-----|-----|-------|
| `io.quarkus:quarkus-amazon-lambda-http` | 3.40.1.1 | 3.40.x | depends on `quarkus-vertx-http`, `quarkus-security`, `quarkus-amazon-lambda`, `aws-lambda-java-core`, `microprofile-jwt-auth-api` (POM) |
| `io.quarkus:quarkus-amazon-lambda-rest` | 3.40.1.1 | 3.40.x | same runtime dependencies (POM) |
| `io.quarkus:quarkus-oidc` | 3.40.x (platform) | 3.40.x | in Lambda HTTP: (unverified), U1 |
| `io.quarkus:quarkus-smallrye-jwt` | 3.40.x (platform) | 3.40.x | artifact name per security-jwt guide |
| Quarkus 4 | n/a | n/a | out of scope (family rule 1) |

---

## Implementation Blueprint

> Confidence: 🟢 High for keys and APIs cited; code composition is this research's, verify with the tests in Quality Control

**Option A lifecycle (API Gateway HTTP API + JWT authorizer, Quarkus 3.40.1.1)**:
```properties
# application.properties (Quarkus 3.40.1.1)
quarkus.lambda-http.enable-security=true          # default false (all-config)
# map-cognito-to-roles default true; cognito-role-claim default cognito:groups
quarkus.security.jaxrs.deny-unannotated-endpoints=true   # K6, ask first
```
```java
// Quarkus 3.40.1.1, quarkus-amazon-lambda-http + Quarkus REST
@Path("/tenants/{tenantId}/orders")
public class OrdersResource {

    @GET
    @RolesAllowed("tenant-user")                                   // from cognito:groups (A3)
    public Response list(@PathParam("tenantId") String pathTenant,
                         @Context SecurityContext sec,             // Principal = cognito:username (A2)
                         @Context APIGatewayV2HTTPEvent event) {   // documented injection (A4)
        // accessor chain from aws-lambda-java-events: (unverified)
        String tokenTenant = event.getRequestContext().getAuthorizer().getJwt()
                                  .getClaims().get("custom:tenantId");
        if (tokenTenant == null || !tokenTenant.equals(pathTenant)) {   // family rule 6
            return Response.status(Response.Status.FORBIDDEN).build();
        }
        return Response.ok(service.ordersFor(tokenTenant, sec.getUserPrincipal().getName())).build();
    }
}
```
Edge configuration (IaC belongs to `provisioning-aws-*-v6`, family rule 4): JWT authorizer `Issuer` = pool issuer, `Audience` = app client ID. For an access token "bound to a resource server", use the resource server URL as audience (https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html). Route `authorizationScopes` set (K2).

REST API variant: inject `io.quarkus.amazon.lambda.http.model.AwsProxyRequestContext`. The Principal comes from `requestContext.authorizer.claims.cognito:username`. A custom provider overrides `authenticate(AwsProxyRequest event)` (https://quarkus.io/version/3.40/guides/aws-lambda-http).

**Option A, custom identity mapping (documented hook)**: implement `io.quarkus.amazon.lambda.http.LambdaIdentityProvider` (extends `IdentityProvider<LambdaAuthenticationRequest>`) as an `@ApplicationScoped` CDI bean. It is discovered automatically. Override `authenticate(APIGatewayV2HTTPEvent)` (HTTP) or `authenticate(AwsProxyRequest)` (REST), and build `QuarkusSecurityIdentity.builder().setPrincipal(...)`. Read only authorizer-populated `requestContext` fields, never caller headers (N5). The package of `LambdaAuthenticationRequest` is not shown in the guide (unverified, U10).

**Option B lifecycle (in-function validation, Quarkus 3.40.1.1; running in Lambda HTTP: (unverified), U1)**:
```properties
quarkus.oidc.application-type=service
quarkus.oidc.auth-server-url=https://cognito-idp.${COGNITO_REGION}.amazonaws.com/${COGNITO_USER_POOL_ID}
quarkus.oidc.token.required-claims.token_use=access
quarkus.oidc.token.required-claims.client_id=${COGNITO_APP_CLIENT_ID}
quarkus.oidc.roles.role-claim-path="cognito:groups"          # quoting (medium confidence), M2
# JWT-only setup, no introspection (bearer guide):
quarkus.oidc.token.allow-jwt-introspection=false
quarkus.oidc.token.allow-opaque-token-introspection=false
```
For ID tokens instead: `required-claims.token_use=id`. `aud` is verified for ID tokens by default against the configured client (set `quarkus.oidc.client-id` to the app client ID; how the default ID-token audience check picks the expected value was not read in detail (medium confidence, M4)). Setting `quarkus.oidc.token.audience` for access tokens without a resource binding would compare against an absent `aud` claim (medium confidence, M4).

```java
// Quarkus 3.40.1.1, quarkus-oidc: tenant from the verified token (A8, N1)
@Path("/tenants/{tenantId}/orders")
public class OrdersResource {
    @Inject org.eclipse.microprofile.jwt.JsonWebToken jwt;   // OIDC represents tokens as JsonWebToken (security-jwt guide)

    @GET @PermissionsAllowed("orders/read")                   // scope -> StringPermission (bearer guide)
    public Response list(@PathParam("tenantId") String pathTenant) {
        String tokenTenant = jwt.getClaim("custom:tenantId");  // access token needs V2_0 trigger (N7); getClaim signature (medium confidence), M3
        if (tokenTenant == null || !tokenTenant.equals(pathTenant)) {
            return Response.status(Response.Status.FORBIDDEN).build();
        }
        return Response.ok(service.ordersFor(tokenTenant)).build();
    }
}
```

**Central tenant check with `SecurityIdentityAugmentor` (Quarkus 3.40)**: the interface `io.quarkus.security.identity.SecurityIdentityAugmentor` with `public Uni<SecurityIdentity> augment(SecurityIdentity identity, AuthenticationRequestContext context)` is documented. The example uses `QuarkusSecurityIdentity.builder(identity).addPermission(...)` (https://quarkus.io/version/3.40/guides/security-authorize-web-endpoints-reference). An augmentor can turn the tenant claim into a permission such as `tenant:<id>`, which `@PermissionChecker` methods (`io.quarkus.security.PermissionChecker`, returning `boolean` or `Uni<Boolean>`) then compare with the path parameter. Whether augmentors run for identities from `LambdaIdentityProvider` / `enable-security` is (unverified), U5.

**Multi-pool (pool-per-tenant) with Quarkus OIDC**:
```properties
# Quarkus 3.40.1.1, named tenants, resolved by the token issuer (multitenancy guide)
quarkus.oidc.resolve-tenants-with-issuer=true
quarkus.oidc.tenant-a.application-type=service
quarkus.oidc.tenant-a.auth-server-url=https://cognito-idp.us-east-1.amazonaws.com/us-east-1_AAAA
quarkus.oidc.tenant-b.application-type=service
quarkus.oidc.tenant-b.auth-server-url=https://cognito-idp.us-east-1.amazonaws.com/us-east-1_BBBB
```
Resolution order: `@Tenant` (`io.quarkus.oidc.Tenant`, needs `quarkus.http.auth.proactive=false`), then `TenantConfigResolver` (`Uni<OidcTenantConfig> resolve(RoutingContext, OidcRequestContext<OidcTenantConfig>)`), then static `TenantResolver` (`String resolve(RoutingContext)`), tenant paths, or the last path segment. Unresolved means the default tenant. A path-selected tenant still needs the claim check of N1 (https://quarkus.io/version/3.40/guides/security-openid-connect-multitenancy).

---

## Quality Control

**Verification Commands**:
```bash
# Representative — adapt to your environment (Quarkus 3.40.1.1 project)
# 1. Security keys present
grep -E "quarkus\.lambda-http\.enable-security|quarkus\.oidc\.(auth-server-url|token\.required-claims)" src/main/resources/application.properties
# Expected: Option A -> enable-security=true; Option B -> auth-server-url + required-claims.token_use + required-claims.client_id
# 2. Forbidden settings absent
grep -nE "token\.issuer=any|QUARKUS_AWS_LAMBDA_FORCE_USER_NAME" -r src/ deploy/ || echo "OK: none"
# Expected: OK: none (N4, N6)
# 3. Tenant never read only from the path
grep -rnE "@PathParam\(\"tenantId\"\)" src/main/java   # each hit must be compared with a token claim (N1)
# 4. Tests
./mvnw -q test
# Expected: BUILD SUCCESS, including the 401/403/cross-tenant cases below
```

**Tests that must exist** (behavioural, Quarkus 3.40):
- No token -> 401. Valid token, missing role -> 403. The bearer guide shows an invalid token giving 401 with `WWW-Authenticate: Bearer` and a missing role giving 403 (Option B).
- Valid token for tenant A calling `/tenants/B/...` -> 403 (family rule 6).
- ID token presented where an access token is required -> 401 (N3).
- Token from another app client of the same pool -> 401 (A6).
- `cognito:groups` role mapping, including the quoting of `role-claim-path` (M2).

**Mocking**:
- Option B: `@TestSecurity` with `@OidcSecurity` (artifact `quarkus-test-security-oidc`) for claim and role cases, and `OidcWiremockTestResource` (artifact `quarkus-test-oidc-server`) for signed tokens. Both are documented in https://quarkus.io/version/3.40/guides/security-oidc-bearer-token-authentication (2026-10-28).
  ```java
  // Quarkus 3.40.1.1, quarkus-test-security-oidc (claims attribute usage: see the bearer guide)
  @QuarkusTest
  class OrdersResourceTest {
      @Test
      @TestSecurity(user = "alice", roles = "tenant-user")
      @OidcSecurity(claims = { @Claim(key = "custom:tenantId", value = "A") })
      void crossTenantIsForbidden() {
          given().when().get("/tenants/B/orders").then().statusCode(403);
      }
  }
  ```
  The `@OidcSecurity(claims=...)` / `@Claim(key, value)` attribute names come from the bearer guide summary and were not quoted verbatim (medium confidence, M6).
- Option A: the guide documents only `QUARKUS_AWS_LAMBDA_FORCE_USER_NAME` for `sam local`. Whether the mock event server (dev 8080 / test 8081, family fact) passes an authorizer context, so that `enable-security` can be tested in `@QuarkusTest`, is (unverified), U3. A unit test of the tenant check can call the resource method with a constructed `APIGatewayV2HTTPEvent`.

---

## Production Readiness

- **Performance**: HTTP JWT authorizer caches the issuer key "for up to two hours on a best-effort basis". A miss fetches it over the network and adds latency to that request (AWS). In-function: `quarkus.oidc.jwks.resolve-early` (default `true`) fetches keys when the OIDC connection is initialized. Its cold-start cost, and whether it happens during the SnapStart snapshot phase, are (unverified), U6.
- **Scalability**: REST `COGNITO_USER_POOLS` authorizer up to 1,000 user pools (hard limit). `quarkus.oidc.jwks.cache-size` default `10`. Per-tenant OIDC configs grow with tenant count (K3).
- **Monitoring**: log `requestId` and `tenantId` (from the claim, never from the path) as JSON, no tokens and no PII (family rule 7). Count 401/403 per route. Bounded metric dimensions; no per-tenant dimension without an ADR (family rule 7).
- **Security checklist** (Quarkus 3.40 + Cognito):
  - [ ] One validation layer chosen deliberately (K1); every route has an authorizer (Option A) or `quarkus-oidc` (Option B).
  - [ ] Issuer exact (N4); `token_use` and `client_id`/`aud` checked (A6, N3).
  - [ ] Roles from `cognito:groups` (A3/A7); scopes as `@PermissionsAllowed` (A9).
  - [ ] Tenant from a verified claim, compared with any path tenant (N1); tenant attribute not in any `WriteAttributes` (N2).
  - [ ] `QUARKUS_AWS_LAMBDA_FORCE_USER_NAME` absent from deployed configs (N6).
  - [ ] Access-token lifetime chosen against the revocation requirement (K5); refresh token rotation enabled ("As a security best practice").
  - [ ] Cognito "might rotate signing keys": JWKS from discovery or `jwks.json`, never a pinned key (A10).

---

## Reference Implementations

- Quarkus 3.40 `CustomSecurityProvider` (`LambdaIdentityProvider`) example and principal tables: https://quarkus.io/version/3.40/guides/aws-lambda-http (2026-10-28). The example reads an `x-user` header for demonstration only (N5).
- Quarkus 3.40 OIDC bearer token examples (Keycloak/Auth0 based, no Cognito example): https://quarkus.io/version/3.40/guides/security-oidc-bearer-token-authentication (2026-10-28).
- Quarkus 3.40 multi-tenancy examples (`TenantResolver`, `TenantConfigResolver`): https://quarkus.io/version/3.40/guides/security-openid-connect-multitenancy (2026-10-28).
- AWS `aws-jwt-verify` (Node.js, `CognitoJwtVerifier` with `tokenUse` and `clientId`) as the reference for Cognito checks: https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html (2026-10-28). Not Java, cited for the check list only.
- AWS CloudFormation example of an HTTP API JWT authorizer with a Cognito issuer and app-client audience: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-jwt-authorizer.html (2026-10-28). The family uses Terraform instead (rule 4).

---

## Source Bibliography

**Primary (Quarkus 3.40, versioned, read 2026-10-28)**:
- S1 https://quarkus.io/version/3.40/guides/aws-lambda-http — "Version: 3.40 (latest)", archetype 3.40.1.1; Security Integration section read in full.
- S2 https://quarkus.io/version/3.40/guides/all-config — read characters 0-100000 of 232437 (L1); the four `quarkus.lambda-http.*` rows were quoted from that range.
- S3 https://quarkus.io/version/3.40/guides/security-oidc-bearer-token-authentication — read 0-100000 of 109477 (L2).
- S4 https://quarkus.io/version/3.40/guides/security-oidc-configuration-properties-reference — read in two passes, 0-100000 and 100000-137630 (full).
- S5 https://quarkus.io/version/3.40/guides/security-openid-connect-multitenancy — full (no truncation reported).
- S6 https://quarkus.io/version/3.40/guides/security-authorize-web-endpoints-reference — full (no truncation reported).
- S7 https://quarkus.io/version/3.40/guides/security-jwt — full (no truncation reported).
- S8 https://quarkus.io/version/3.40/guides/security-authentication-mechanisms — read 0-100000 of 110821 (L3).
- S9 https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.40 — official wiki, versioned by name.
- S10 https://repo1.maven.org/maven2/io/quarkus/quarkus-amazon-lambda-http/3.40.1.1/quarkus-amazon-lambda-http-3.40.1.1.pom
- S11 https://repo1.maven.org/maven2/io/quarkus/quarkus-amazon-lambda-rest/3.40.1.1/quarkus-amazon-lambda-rest-3.40.1.1.pom

**Primary (AWS official, current pages, read 2026-10-28; no page date shown)**:
- A1 https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html
- A2 https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-the-access-token.html
- A3 https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-the-id-token.html
- A4 https://docs.aws.amazon.com/cognito/latest/developerguide/federation-endpoints.html
- A5 https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-the-refresh-token.html
- A6 https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-pre-token-generation.html
- A7 https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-attributes.html
- A8 https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-jwt-authorizer.html
- A9 https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-integrate-with-cognito.html
- A10 https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-enable-cognito-user-pool.html
- A11 https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-develop-integrations-lambda.html

**Validation**: two WebSearch queries (2026-10-28) found no official page documenting `quarkus-oidc` inside `quarkus-amazon-lambda-http`. The results (Maven Central listings, older Quarkus guide versions) were not used as evidence.

**Family inputs**: `workspace/quarkus-aws-saas/_family_facts_v3.40.md`, `_family_rules_v3.40.md`; `workspace/_family_facts_v3.40.md`, `_family_rules_v3.40.md`. No fetched page contradicted a family fact.

---

## Research Gaps

Unverified items (U-ids):

```
U1 Gap: quarkus-oidc bearer authentication running inside quarkus-amazon-lambda-http / -rest is not documented
   (S1 never mentions quarkus-oidc, smallrye-jwt or bearer tokens). S10/S11 show both extensions depend on
   quarkus-vertx-http and quarkus-security, which makes it likely (medium confidence, M1).
Impact: Option B could fail at runtime. Workaround: integration test with a real Cognito token in sam local or a deployed stage.
Follow-up: quarkus source extensions/amazon-lambda-http at tag 3.40.1.1; Quarkus issue tracker.
§7-ref: Iteration 1 — unresolved, carried as (unverified)

U2 Gap: whether quarkus.http.auth.permission.* path policies are evaluated in the Lambda HTTP extensions (S6 does not mention Lambda).
Impact: path policies might silently not apply. Workaround: rely on annotations; test each path. Follow-up: extension source.
§7-ref: not attempted (iteration budget), carried as (unverified)

U3 Gap: whether the mock event server (dev/test) passes an authorizer context so enable-security works in @QuarkusTest.
Impact: Option A tests may not cover role mapping. Workaround: sam local + QUARKUS_AWS_LAMBDA_FORCE_USER_NAME (local only). Follow-up: S1 testing section / source.
§7-ref: not attempted, carried as (unverified)

U4 Gap: interaction when both enable-security and quarkus-oidc are active (which identity wins). Follow-up: source.
§7-ref: not attempted, carried as (unverified)

U5 Gap: whether SecurityIdentityAugmentor runs for identities built by LambdaIdentityProvider / enable-security; and whether
   QuarkusSecurityIdentity.Builder has addAttribute (only addPermission was seen). Follow-up: S6 full API / javadoc.
§7-ref: not attempted, carried as (unverified)

U6 Gap: cold-start latency of the OIDC JWKS/discovery fetch in Lambda, and whether it happens during a SnapStart snapshot.
Impact: unknown latency; possible stale state after restore. Follow-up: measurement; U1 SnapStart research.
§7-ref: not attempted, carried as (unverified)

U7 Gap: API Gateway authorizer vs Lambda invocation pricing (pricing pages not read). Follow-up: aws.amazon.com/api-gateway/pricing, /lambda/pricing.
§7-ref: not attempted, carried as (unverified)

U8 Gap: security-related entries in migration guides 3.31-3.39 (only 3.40 was read). Follow-up: wiki Migration-Guide-3.3x.
§7-ref: Iteration 2 — partially resolved (3.40 has none)

U9 Gap: the `issuer` value in the discovery document of an updated issuer (issuer-cognito-idp host), i.e. the exact
   auth-server-url to use. Follow-up: fetch a real pool's /.well-known/openid-configuration.
§7-ref: not attempted, carried as (unverified)

U10 Gap: package of LambdaAuthenticationRequest (not shown in S1); aws-lambda-java-events accessor names
   (getRequestContext().getAuthorizer().getJwt().getClaims()). Follow-up: javadoc / source at 3.40.1.1.
§7-ref: not attempted, carried as (unverified)
```

Medium-confidence items (M-ids):
- M1 `quarkus-oidc` likely works in the Lambda HTTP extensions (inference from S10/S11 dependencies).
- M2 `quarkus.oidc.roles.role-claim-path` needs double quotes for `cognito:groups` (S4 says to quote "namespace-qualified claim names" and gives only a `/` example).
- M3 `JsonWebToken.getClaim(String)` signature (MicroProfile JWT API not read).
- M4 Default ID-token audience check uses `quarkus.oidc.client-id`; setting `quarkus.oidc.token.audience` for access tokens without `aud` rejects them (inference from S4 wording and A2).
- M5 An HTTP API JWT authorizer takes a single issuer (inferred from `Issuer` singular in A8's CLI/CloudFormation examples).
- M6 `@OidcSecurity(claims = @Claim(key, value))` attribute names (from a tool summary of S3, not quoted).
- M7 Array claims such as `cognito:groups` reach the Lambda event as a bracketed string `[ a b ]` (implied by S1's default matcher description; A11 shows only string claims and does not state the serialization).
- M8 Deny-unannotated as the family default (K6, engineering judgement).

Coverage limits (L-ids):
- L1 S2 all-config: characters 0-100000 of 232437.
- L2 S3 bearer-token guide: 0-100000 of 109477 (the part after "Step Up Authentication" not read).
- L3 S8 authentication-mechanisms: 0-100000 of 110821; `quarkus.http.auth.proactive` default not confirmed.

---

## Research Iteration Changelog

| Iteration | Section | Item | Action | Source |
|-----------|---------|------|--------|--------|
| 1 | Conditional K1 / U1 | quarkus-oidc inside quarkus-amazon-lambda-http | Searched (2 WebSearch); no official page. Fetched extension POMs: dependencies on quarkus-vertx-http + quarkus-security recorded; claim kept (unverified), inference M1 added | S10, S11 (2026-10-28) |
| 1 | Mandatory A3 | Defaults of map-cognito-to-roles / cognito-role-claim / cognito-claim-matcher (S1 gave no defaults) | Resolved from all-config rows | S2 (2026-10-28) |
| 2 | Migration Guide | Security changes in 3.40 | Resolved: none ("we don't expect any changes requiring manual intervention in 3.40"); 3.31-3.39 left as U8 | S9 (2026-10-28) |
| 2 | Mandatory A10 | JWKS cache properties | Resolved from second pass of the OIDC config reference | S4 offset 100000 (2026-10-28) |
| 3 | Conditional K7 | quarkus-oidc vs smallrye-jwt for bearer tokens | Resolved (smallrye-jwt JWT-only, no introspection; both refresh JWKS) | S8 (2026-10-28) |
| 3 | Coverage L3 | `quarkus.http.auth.proactive` default | Not confirmed in read range; left as coverage limit | — |

---

## Completion Checklist

- [x] Domain complexity tier assessed and documented (Complex)
- [x] All scope areas cited (Lambda HTTP security, quarkus-oidc, smallrye-jwt, Cognito tokens, roles/scopes, annotations/policies, multi-tenancy, authorizer trade-off, lifetimes)
- [x] Pattern counts driven by domain needs (10 / 7 / 7)
- [x] Every anti-pattern has an alternative (❌/✅ pairs; ✅ alternatives are High, family rule 9)
- [x] All CLI commands marked as representative
- [x] Integration examples complete (Option A, Option B, multi-pool)
- [x] Sources dated and linked (2026-10-28)
- [x] Security documented
- [x] 1+ copy-paste working example (properties blocks; Java samples carry their unverified accessor tags)
- [x] Confidence badge applied to every pattern entry
- [x] Always-Do patterns: 6 triangulated; others High under family rule 5 (single versioned/official source)
- [x] Research Iteration Changelog present
- [x] Research_Quality_Score calculated (88%)
- [x] Every Research Gap cross-referenced in the Changelog or marked "not attempted"

---

## Agent Operation Notes

- **High Confidence (execute without asking)**: A1-A10 facts; N1-N7; Cognito claim facts (`token_use`, `client_id` vs `aud`, `cognito:groups` array, `custom:` strings in the ID token, issuer/JWKS URLs, lifetimes).
- **Medium Confidence (validate with user)**: M1-M8; K1 cost/latency weighting; K6 default.
- **Low Confidence (must ask human)**: U1-U10, above all U1 (Option B in Lambda) and U2 (HTTP path policies in Lambda).
- **Edge Cases (pause)**: Quarkus 3.40.1.1 is 9 days old (released 2026-10-19), but the 3.40 line was released 2026-09-30 (>28 days); no CVE was researched.
- **Emergency Stop**: not triggered. All evidence is official Quarkus 3.40 or AWS documentation.
