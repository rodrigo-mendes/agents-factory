# Option B: In-Function quarkus-oidc Validation

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1. Fetched 2026-10-28.

> Never a default. No Quarkus 3.40 page documents `quarkus-oidc` bearer authentication inside `quarkus-amazon-lambda-http` or `-rest` (unverified). The extension POMs depend on `quarkus-vertx-http` and `quarkus-security`, so it is likely to work (medium confidence). A test with a real Cognito token, in `sam local` or a deployed stage, must confirm it. Decide through [Ask First K1](./ask-first-decisions.md#k1-where-the-token-is-validated). The keys below are High as Quarkus 3.40 OIDC facts; their combination with the Lambda extensions is not.

## Contents

- [Configuration](#configuration)
- [Reference keys](#reference-keys)
- [Roles from cognito:groups](#roles-from-cognitogroups)
- [Audience and ID tokens](#audience-and-id-tokens)
- [Key rotation settings](#key-rotation-settings)
- [Tenant from the verified token](#tenant-from-the-verified-token)
- [Open points](#open-points)

## Configuration

Quarkus discovers endpoints "by appending `/.well-known/openid-configuration`" to `quarkus.oidc.auth-server-url`. Cognito publishes that document and `/.well-known/jwks.json`; the `iss` "must match your user pool".

```properties
# Quarkus 3.40.1.1, access tokens without a resource binding
quarkus.oidc.application-type=service
quarkus.oidc.auth-server-url=https://cognito-idp.${COGNITO_REGION}.amazonaws.com/${COGNITO_USER_POOL_ID}
quarkus.oidc.token.required-claims.token_use=access
quarkus.oidc.token.required-claims.client_id=${COGNITO_APP_CLIENT_ID}
# JWT-only setup, no introspection (bearer guide):
quarkus.oidc.token.allow-jwt-introspection=false
quarkus.oidc.token.allow-opaque-token-introspection=false
```

`quarkus.oidc.application-type` values: `web-app`, `service`, `hybrid`. `client-id` is "not required if `application-type` is `service` and no token introspection is required". The issuer format (original or updated host) is [Ask First K4](./ask-first-decisions.md#k4-original-or-updated-issuer). Bearer guide read to 100,000 of 109,477 characters (L2).

## Reference keys

| Key | Type | Default | Note |
|---|---|---|---|
| `quarkus.oidc.discovery-enabled` | boolean | `true` | If turned off, set `quarkus.oidc.jwks-path` to the pool's `/.well-known/jwks.json`, never to a copied key |
| `quarkus.oidc.token.required-claims."claim-name"` | map | page not recorded | "Strings and arrays of strings are currently the only supported types" |
| `quarkus.oidc.token.audience` | string | page not recorded | "Audience verification for access tokens is only done if this property is configured" |
| `quarkus.oidc.token.forced-jwk-refresh-interval` | Duration | `10M` (medium confidence, M11) | Refresh when no key matches the `kid`, at most once per interval |
| `quarkus.oidc.jwks.resolve-early` | boolean | `true` (medium confidence, M11) | Fetches keys when the OIDC connection is initialized |
| `quarkus.oidc.jwks.cache-size` | int | `10` (medium confidence, M11) | |
| `quarkus.oidc.jwks.cache-time-to-live` | Duration | `10M` (medium confidence, M11) | |
| `quarkus.oidc.roles.role-claim-path` | string | page not recorded | See next section |
| `quarkus.oidc.roles.source` | enum | `accesstoken` for `service` applications (medium confidence, M11) | |

Source: [OIDC configuration reference](https://quarkus.io/version/3.40/guides/security-oidc-configuration-properties-reference), read in two passes through a summarising tool; the defaults marked M11 have no recorded verbatim quote. Cold-start latency of the discovery and JWKS fetch in Lambda, and whether it happens during a SnapStart snapshot, is (unverified).

## Roles from cognito:groups

Quarkus takes roles from `quarkus.oidc.roles.role-claim-path` if set, then a `groups` claim, then `realm_access/roles` or `resource_access/<client-id>/roles` (paraphrase of the bearer guide). Cognito access tokens carry `cognito:groups`, "An array of the names of user pool groups". The reference says "Use double quotes with the namespace-qualified claim names"; whether `cognito:groups` needs the quotes is not stated (medium confidence).

```properties
quarkus.oidc.roles.role-claim-path="cognito:groups"
```

Test the role mapping with a real token that carries a group.

## Audience and ID tokens

Quarkus checks `aud` for ID tokens by default and for access tokens only when `quarkus.oidc.token.audience` is configured. For ID tokens use `required-claims.token_use=id` and set `quarkus.oidc.client-id` to the app client ID. How the default ID-token audience check picks the expected value was not read in detail, and setting `quarkus.oidc.token.audience` for access tokens without `aud` would compare against an absent claim (medium confidence). A Cognito access token has no `aud` unless a resource binding was requested, which is why `required-claims.client_id` is used.

## Key rotation settings

Keep discovery on and let Quarkus refresh the key set; see [always-do pattern 9](./always-do-patterns.md#9-key-rotation) and the reference keys above.

## Tenant from the verified token

```java
// Quarkus 3.40.1.1, quarkus-oidc (running in Lambda HTTP: unverified)
@Path("/tenants/{tenantId}/orders")
public class OrdersResource {
    @Inject org.eclipse.microprofile.jwt.JsonWebToken jwt;   // OIDC represents tokens as JsonWebToken

    @GET @PermissionsAllowed("orders/read")                   // scope -> StringPermission
    public Response list(@PathParam("tenantId") String pathTenant) {
        // getClaim(String) signature: MicroProfile JWT API not read (medium confidence)
        String tokenTenant = jwt.getClaim("custom:tenantId");  // access token needs a V2_0 trigger
        if (tokenTenant == null || !tokenTenant.equals(pathTenant)) {
            return Response.status(Response.Status.FORBIDDEN).build();
        }
        return Response.ok(service.ordersFor(tokenTenant)).build();
    }
}
```

With `quarkus-oidc`, token scopes become `StringPermission`s, so `@PermissionsAllowed("orders_read")` admits clients holding that scope. The sample uses `orders/read` as a Cognito custom scope; permission name syntax is in [always-do pattern 8](./always-do-patterns.md#8-authorization-annotations).

## Open points

- Which identity wins when `enable-security=true` and `quarkus-oidc` are both active (unverified): do not combine without a real-token test.
- `quarkus.http.auth.permission.*` policies in the Lambda extensions: (unverified).
- Pool per tenant: `quarkus.oidc.resolve-tenants-with-issuer=true` with named tenants `quarkus.oidc.<tenant>.auth-server-url` and `application-type=service`; resolution order `@Tenant` (needs `quarkus.http.auth.proactive=false`, its default not confirmed, L3), `TenantConfigResolver`, static `TenantResolver`, tenant paths, last path segment; unresolved means the default tenant. A path-selected tenant still needs the claim check of [never-do N1](./never-do-patterns.md#n1-tenant-from-the-path-header-or-body-alone-high). Source: [multi-tenancy guide](https://quarkus.io/version/3.40/guides/security-openid-connect-multitenancy).
