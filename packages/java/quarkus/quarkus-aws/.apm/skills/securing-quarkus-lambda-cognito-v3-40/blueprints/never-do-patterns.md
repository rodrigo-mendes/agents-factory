# Never-Do Patterns

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1. Fetched 2026-10-28. Severity wording: low, moderate, high.

## Contents

- [N1. Tenant from the path, header or body alone (high)](#n1-tenant-from-the-path-header-or-body-alone-high)
- [N2. Authorization on a writable custom attribute (high)](#n2-authorization-on-a-writable-custom-attribute-high)
- [N3. Any Cognito JWT without token_use and client check (high)](#n3-any-cognito-jwt-without-token_use-and-client-check-high)
- [N4. Issuer verification disabled (high)](#n4-issuer-verification-disabled-high)
- [N5. Identity from caller-controlled data (high)](#n5-identity-from-caller-controlled-data-high)
- [N6. Forced user name outside sam local (high)](#n6-forced-user-name-outside-sam-local-high)
- [N7. custom: attributes expected in the access token (high)](#n7-custom-attributes-expected-in-the-access-token-high)

## N1. Tenant from the path, header or body alone (high)

A path or header value is chosen by the caller. Only claims of a signature-checked token can be trusted. Impact: cross-tenant data access by changing a URL (family rule 6).

```java
// ❌ WRONG: caller-chosen tenant
@GET @Path("/tenants/{tenantId}/orders") @Authenticated
public List<Order> list(@PathParam("tenantId") String tenantId) {
    return repo.findByTenant(tenantId);
}
```

```java
// ✅ CORRECT: verified claim, compared with the path
String tokenTenant = claims.get("custom:tenantId");
if (!pathTenant.equals(tokenTenant)) return Response.status(403).build();
return Response.ok(repo.findByTenant(tokenTenant)).build();
```

Source: [Cognito access token](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-the-access-token.html).

## N2. Authorization on a writable custom attribute (high)

By default an app client "has write access to all standard and custom attributes", and "Users can change the value of these attributes for themselves with `UpdateUserAttributes`". "A value that a user writes through one app client appears in the tokens that all app clients issue." Impact: a user moves themself into another tenant or role and the signed token carries the forged value.

```text
❌ WRONG   App client "web": WriteAttributes not specified   -> custom:tenantId writable by the user
✅ CORRECT Every app client: WriteAttributes excludes custom:tenantId (set by AdminCreateUser or an admin process)
```

Source: [Cognito attributes](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-attributes.html).

## N3. Any Cognito JWT without token_use and client check (high)

Cognito says to check `token_use` and to match `client_id` (access) or `aud` (ID) to the app client. Impact: an ID token, or a token for another app client of the same pool, is accepted as an API access token.

```properties
# ❌ WRONG: nothing but the issuer
quarkus.oidc.auth-server-url=https://cognito-idp.us-east-1.amazonaws.com/us-east-1_EXAMPLE
```

```text
✅ CORRECT (High fact, layer chosen by Ask First K1):
  edge:     JWT authorizer Issuer = pool issuer, Audience = app client ID, route authorizationScopes set
  function: token_use and client_id / aud checked; keys in option-b-in-function-oidc.md#reference-keys
```

Sources: [Cognito verifying a JWT](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html), [OIDC configuration reference](https://quarkus.io/version/3.40/guides/security-oidc-configuration-properties-reference).

## N4. Issuer verification disabled (high)

Quarkus says to set `any` only when a fixed `iss` cannot be configured at the provider, as a last resort. Cognito issuers are fixed per pool. Impact: tokens from any issuer whose keys resolve are accepted.

```properties
# ❌ WRONG
quarkus.oidc.token.issuer=any
```

```text
✅ CORRECT (High fact, layer chosen by Ask First K1): the issuer is the exact pool issuer
  edge:     JWT authorizer Issuer = exact pool issuer (Option A)
  function: in-function issuer config only through Option B (option-b-in-function-oidc.md#reference-keys), never as a default
```

Sources: [OIDC bearer guide](https://quarkus.io/version/3.40/guides/security-oidc-bearer-token-authentication), [Cognito verifying a JWT](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html).

## N5. Identity from caller-controlled data (high)

The guide's `CustomSecurityProvider` example reads an `x-user` header to show the API. It is an example, not a trust model. Cognito: "JSON web tokens (JWTs) can be decoded, read, and modified easily", and the signature "is the key component of token validation". Impact: anyone who can reach the function URL or a route without an authorizer can impersonate any user.

```java
// ❌ WRONG: caller-controlled header
public SecurityIdentity authenticate(APIGatewayV2HTTPEvent event) {
    Principal p = new QuarkusPrincipal(event.getHeaders().get("x-user"));
    return QuarkusSecurityIdentity.builder().setPrincipal(p).build();
}
```

```properties
# ✅ CORRECT: authorizer-validated event, the route has a JWT or COGNITO_USER_POOLS authorizer
quarkus.lambda-http.enable-security=true
```

Signature-verified in-function validation is the other path and belongs to Ask First K1. Source: [aws-lambda-http guide](https://quarkus.io/version/3.40/guides/aws-lambda-http).

## N6. Forced user name outside sam local (high)

The guide documents `QUARKUS_AWS_LAMBDA_FORCE_USER_NAME` only for `sam local` testing: "If you are testing your application with `sam local` you can hardcode a principal name". Impact: every request runs as the forced user.

```text
❌ WRONG   deployed function environment: QUARKUS_AWS_LAMBDA_FORCE_USER_NAME=admin
✅ CORRECT variable set only in the local sam test environment; absent from every deployed function configuration
```

Source: [aws-lambda-http guide](https://quarkus.io/version/3.40/guides/aws-lambda-http).

## N7. custom: attributes expected in the access token (high)

The default token type of `custom:` attributes is "ID". Access-token customization needs event version V2_0/V3_0 (Essentials or Plus feature plan). Impact: the tenant claim is `null`; code that falls back to the path tenant breaks N1.

```java
// ❌ WRONG: access token, no V2_0 trigger, fallback to caller input
String tenant = jwt.getClaim("custom:tenantId");
if (tenant == null) tenant = pathTenant;
```

```text
✅ CORRECT (High fact): read the tenant from the ID token, or from an access token whose V2_0/V3_0 trigger adds it, and answer 403 when the claim is absent
  Option A code reads it from the event claims (always-do pattern 4); in-function code is Option B (option-b-in-function-oidc.md), chosen by Ask First K1
```

Sources: [pre token generation](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-pre-token-generation.html), [Cognito ID token](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-the-id-token.html).
