---
name: securing-quarkus-lambda-cognito-v3-40
description: "Secures Quarkus 3.40 LTS HTTP Lambdas with Amazon Cognito: Lambda HTTP security mapping, JWT validation, roles and permissions, tenant-from-token isolation. Use when adding authN/authZ or multi-tenant checks. Not for Cognito provisioning, API Gateway setup, login UI or Quarkus 4."
---

# Securing Quarkus HTTP Lambdas with Cognito 3.40

> Version lock: every claim applies to **Quarkus 3.40 LTS, patch 3.40.1.1** (`quarkus-amazon-lambda-http`, `quarkus-amazon-lambda-rest`) with current Amazon Cognito and API Gateway documentation. Research date **2026-10-28**.
> Claims tagged (unverified) or (medium confidence) were not fully confirmed against an official page; each maps to a line of the [register](./blueprints/unverified-and-risks.md#tag-to-register-mapping).
> Scope: authentication and authorization of Quarkus HTTP Lambdas with Cognito: Lambda HTTP security mapping (Option A), in-function token validation (Option B), roles and permissions, multi-tenant tenant resolution. Neighbours: [developing-quarkus-amazon-lambda-http-v3-40](../developing-quarkus-amazon-lambda-http-v3-40/SKILL.md) (HTTP Lambda mechanics), [testing-quarkus-amazon-lambda-v3-40](../testing-quarkus-amazon-lambda-v3-40/SKILL.md) (testing in depth). By name only: `securing-aws-cognito` (Cognito architecture), `provisioning-aws-cognito-v6` and `provisioning-aws-api-gateway-v6` (Terraform), `developing-quarkus-rest-v3-40` (Quarkus REST). Quarkus 4 is out of scope.

> **Tenant rule (family rule 6).** The tenant comes from a **verified token claim**, never from the path, a header or the body alone. A path tenant is only a value that must equal the claim. The tenant attribute must not be writable by app clients. See [multi-tenant isolation](./blueprints/multi-tenant-isolation.md).

## Version Context

| Item | Value | Source (fetched 2026-10-28) |
|---|---|---|
| Quarkus | 3.40 LTS, released 2026-09-30, community-maintained until 2027-09-30; patch 3.40.1.1 released 2026-10-19 | https://quarkus.io/releases |
| Extensions | `quarkus-amazon-lambda-http` (HTTP API, payload 2.0) and `quarkus-amazon-lambda-rest` (REST API) 3.40.1.1; both POMs depend on `quarkus-vertx-http` and `quarkus-security`; the guide states "This technology is considered preview" | https://quarkus.io/version/3.40/guides/aws-lambda-http ; https://repo1.maven.org/maven2/io/quarkus/quarkus-amazon-lambda-http/3.40.1.1/quarkus-amazon-lambda-http-3.40.1.1.pom |
| Lambda HTTP security | Opt-in: `quarkus.lambda-http.enable-security=true`; default `false` (medium confidence) | https://quarkus.io/version/3.40/guides/all-config |
| In-function `quarkus-oidc` on Lambda HTTP | Not documented by any 3.40 page read (unverified); likely to work (medium confidence) | page not recorded |
| Migration 3.40 | No security, OIDC, SmallRye JWT or Lambda HTTP changes documented | https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.40 |
| Cognito and API Gateway | Current AWS pages, no page date shown | https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html |

**Version-lifetime risk** (details in [register](./blueprints/unverified-and-risks.md#version-lifetime-risk)): Quarkus 4 is out of scope; the Lambda HTTP extensions are preview, so backward compatibility is not guaranteed; AWS pages are unversioned and can change.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Ask-first decisions in depth](./blueprints/ask-first-decisions.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [Option A: Lambda HTTP security mapping](./blueprints/option-a-lambda-http-security.md)
- [Option B: in-function quarkus-oidc validation](./blueprints/option-b-in-function-oidc.md)
- [Multi-tenant isolation](./blueprints/multi-tenant-isolation.md)
- [Verification Loop](./blueprints/testing-and-verification.md#verification-loop)
- [Testing and verification](./blueprints/testing-and-verification.md)
- [Migration notes](./blueprints/migration-notes.md)
- [Unverified and risks register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **When Option A is chosen (Ask First K1), turn the Lambda HTTP security integration on explicitly with `quarkus.lambda-http.enable-security=true`.** The guide says security is opt-in: "To enable this security feature, add … quarkus.lambda-http.enable-security=true" ([aws-lambda-http guide](https://quarkus.io/version/3.40/guides/aws-lambda-http)). See [patterns](./blueprints/always-do-patterns.md#1-enable-the-integration).
- **Treat `cognito:username` as an ID-token claim; access tokens carry `username` instead.** AWS lists `username` (not `cognito:username`) among the access-token claims ([Cognito access token](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-the-access-token.html)). See [patterns](./blueprints/always-do-patterns.md#2-principal-name).
- **When Option A is chosen, let `cognito:groups` become Quarkus roles and guard endpoints with `@RolesAllowed`.** The guide says Quarkus maps the groups to roles unless `quarkus.lambda-http.map-cognito-to-roles=false` ([aws-lambda-http guide](https://quarkus.io/version/3.40/guides/aws-lambda-http)). See [patterns](./blueprints/always-do-patterns.md#3-groups-to-roles).
- **When Option A is chosen, read claims beyond name and roles from the injected API Gateway event.** The integration maps only the principal name and roles; inject `APIGatewayV2HTTPEvent` (HTTP API) or `AwsProxyRequestContext` (REST API) with `@Context` or `@Inject` ([aws-lambda-http guide](https://quarkus.io/version/3.40/guides/aws-lambda-http)). See [patterns](./blueprints/always-do-patterns.md#4-claims-from-the-event).
- **Read the tenant from a verified claim and compare any path tenant with it.** Only claims of a signature-checked token can be trusted ([Cognito access token](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-the-access-token.html)). See [patterns](./blueprints/always-do-patterns.md#5-tenant-from-the-token).
- **Remove the tenant attribute from `WriteAttributes` of every app client.** By default an app client has write access to all custom attributes and users can change them with `UpdateUserAttributes` ([Cognito attributes](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-attributes.html)). See [patterns](./blueprints/always-do-patterns.md#6-protect-the-tenant-attribute).
- **Check `token_use` and match `client_id` (access token) or `aud` (ID token) to the app client.** Cognito requires it for every accepted token ([Cognito verifying a JWT](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html)). See [patterns](./blueprints/always-do-patterns.md#7-token_use-and-client-binding).
- **Use `@RolesAllowed`, `@Authenticated`, `@PermitAll` and `@PermissionsAllowed` to express authorization.** `@Authenticated` equals `@RolesAllowed("**")` ([authorize web endpoints reference](https://quarkus.io/version/3.40/guides/security-authorize-web-endpoints-reference)). See [patterns](./blueprints/always-do-patterns.md#8-authorization-annotations).
- **Fetch Cognito signing keys from the pool's discovery document or `jwks.json`, never from a pinned key.** Cognito "might rotate signing keys" ([Cognito verifying a JWT](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html)). See [patterns](./blueprints/always-do-patterns.md#9-key-rotation).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| **Where the token is validated (K1)**: API Gateway authorizer (A), in-function `quarkus-oidc` (B) or both (C) | A rejects invalid tokens before the Lambda runs; the function maps what the event carries. B needs no authorizer but is never a default: `quarkus-oidc` inside the Lambda HTTP extensions is (unverified) and only likely (medium confidence); a real-token test must confirm it before relying on it. C is defence in depth; which identity wins with `enable-security` and `quarkus-oidc` both active is (unverified). Cost and latency data are (unverified). See [decisions](./blueprints/ask-first-decisions.md#k1-where-the-token-is-validated) | "Are tokens validated by API Gateway, by the function, or both? Is a real-token test in `sam local` or a deployed stage available?" |
| ID token or access token (K2) | Access token: scopes, no `custom:` attributes without a V2_0/V3_0 pre token trigger, no `aud` without a resource binding, `username` instead of `cognito:username` (the guide's Principal path `...claims.cognito:username` does not match an access token; what Quarkus then returns as Principal name is (unverified), U11; identify users and tenants by `sub` or a custom attribute, [AWS](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-the-access-token.html)), M2M tokens without `username` and `cognito:groups`. ID token: `custom:` attributes, `aud` and `cognito:username`, no scopes. See [decisions](./blueprints/ask-first-decisions.md#k2-id-token-or-access-token) | "Which token does the client send? Does the pool's feature plan allow access-token customization?" |
| Tenant model (K3) | One pool with a tenant claim; pool per tenant with Quarkus OIDC multi-tenancy; pool per tenant behind a REST `COGNITO_USER_POOLS` authorizer (1,000-pool limit). One issuer per HTTP JWT authorizer is (medium confidence). See [decisions](./blueprints/ask-first-decisions.md#k3-tenant-model) | "Pooled or pool per tenant? Expected tenant count?" |
| Cognito issuer format (K4) | Original `cognito-idp` host or updated `issuer-cognito-idp` host; token `iss`, OIDC config and authorizer must agree; the discovery `issuer` of the updated host is (unverified). See [decisions](./blueprints/ask-first-decisions.md#k4-original-or-updated-issuer) | "Which issuer does a decoded real token show in `iss`?" |
| Revocation and token lifetime (K5) | Short access-token lifetime with offline validation vs an online status check per request | "Must revocation take effect before token expiry?" |
| Deny by default (K6) | `quarkus.security.jaxrs.deny-unannotated-endpoints=true` as the family default is (medium confidence) | "Must every endpoint carry an explicit security annotation?" |
| `quarkus-oidc` or `quarkus-smallrye-jwt` for Option B (K7) | SmallRye JWT checks JWT only and has no documented value check for `client_id` or `token_use` | "Is introspection or value checking of claims needed?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Take the tenant from the path, a header or the body alone (N1) | Compare the path tenant with the verified claim and answer 403 on mismatch ([Cognito access token](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-the-access-token.html)) |
| Base authorization on a custom attribute that app clients can write (N2) | Exclude the attribute from `WriteAttributes` of every app client and set it from an admin process ([Cognito attributes](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-attributes.html)) |
| Accept any Cognito JWT without checking `token_use` and `client_id` or `aud` (N3) | Check `token_use` and match `client_id` or `aud` to the app client ([Cognito verifying a JWT](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html)); the in-function config is decided by Ask First K1 |
| Set `quarkus.oidc.token.issuer=any` for Cognito (N4) | Use the exact pool issuer; "The issuer (`iss`) claim must match your user pool" ([Cognito verifying a JWT](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html)) |
| Build identity from caller-controlled data (decoded JWT, `x-user` header) in a `LambdaIdentityProvider` (N5) | Map only authorizer-populated `requestContext` fields with `quarkus.lambda-http.enable-security=true` on a route that has an authorizer ([aws-lambda-http guide](https://quarkus.io/version/3.40/guides/aws-lambda-http)) |
| Set `QUARKUS_AWS_LAMBDA_FORCE_USER_NAME` outside `sam local` testing (N6) | Keep the variable in the local test environment only; absent from every deployed function ([aws-lambda-http guide](https://quarkus.io/version/3.40/guides/aws-lambda-http)) |
| Expect `custom:` attributes in the access token without a V2_0/V3_0 pre token generation trigger, or fall back to the path tenant when the claim is `null` (N7) | Read the tenant from the ID token, or from an access token whose trigger adds it, and answer 403 when it is absent ([Cognito pre token generation](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-pre-token-generation.html)) |

Full ❌/✅ code: [never-do patterns](./blueprints/never-do-patterns.md). Unconfirmed items: [register](./blueprints/unverified-and-risks.md).

## Quick Reference

| Aspect | Value | Source |
|---|---|---|
| `quarkus.lambda-http.enable-security` | boolean, default `false` (medium confidence) | https://quarkus.io/version/3.40/guides/all-config |
| `quarkus.lambda-http.map-cognito-to-roles` | boolean, default `true` (medium confidence) | https://quarkus.io/version/3.40/guides/all-config |
| `quarkus.lambda-http.cognito-role-claim` | string, default `cognito:groups` (medium confidence) | https://quarkus.io/version/3.40/guides/all-config |
| `quarkus.lambda-http.cognito-claim-matcher` | string, default `[^\[\] \t]+` (medium confidence) | https://quarkus.io/version/3.40/guides/all-config |
| Principal classes | `io.quarkus.amazon.lambda.http.CognitoPrincipal`, `IAMPrincipal`, `CustomPrincipal`; custom mapping hook `io.quarkus.amazon.lambda.http.LambdaIdentityProvider` | https://quarkus.io/version/3.40/guides/aws-lambda-http |
| Cognito token facts | access token: `client_id`, `token_use=access`, no `aud` without a resource binding; ID token: `aud` = app client ID, `token_use=id`, `custom:` attributes as strings | https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html |
| Token lifetimes | access and ID: 5 minutes to 1 day per app client; refresh: default 30 days, 60 minutes to 10 years | https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-the-refresh-token.html |
| HTTP JWT authorizer key cache | "up to two hours on a best-effort basis" | https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-jwt-authorizer.html |
| REST `COGNITO_USER_POOLS` authorizer | up to 1,000 user pools, not increasable | https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-enable-cognito-user-pool.html |
| `quarkus.security.jaxrs.deny-unannotated-endpoints` | default `false` (medium confidence, M13) | https://quarkus.io/version/3.40/guides/security-authorize-web-endpoints-reference |
| Option B keys, defaults (several are medium confidence, M11) | see [option B](./blueprints/option-b-in-function-oidc.md#reference-keys) | https://quarkus.io/version/3.40/guides/security-oidc-configuration-properties-reference |

## External Resources

All fetched 2026-10-28.

- Lambda HTTP guide, Security Integration: https://quarkus.io/version/3.40/guides/aws-lambda-http
- Configuration reference: https://quarkus.io/version/3.40/guides/all-config
- OIDC bearer token guide: https://quarkus.io/version/3.40/guides/security-oidc-bearer-token-authentication
- Authorize web endpoints reference: https://quarkus.io/version/3.40/guides/security-authorize-web-endpoints-reference
- Cognito verifying a JWT: https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html
- Full bibliography: [unverified and risks](./blueprints/unverified-and-risks.md#source-bibliography)
