# Ask-First Decisions

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1. Fetched 2026-10-28. Every decision here is put to the user; none has a default.

## Contents

- [K1. Where the token is validated](#k1-where-the-token-is-validated)
- [K2. ID token or access token](#k2-id-token-or-access-token)
- [K3. Tenant model](#k3-tenant-model)
- [K4. Original or updated issuer](#k4-original-or-updated-issuer)
- [K5. Revocation and token lifetime](#k5-revocation-and-token-lifetime)
- [K6. Deny by default](#k6-deny-by-default)
- [K7. quarkus-oidc or quarkus-smallrye-jwt](#k7-quarkus-oidc-or-quarkus-smallrye-jwt)

## K1. Where the token is validated

API Gateway authorizer, in-function validation or both. Never choose for the user.

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| A. API Gateway JWT authorizer (HTTP API) or `COGNITO_USER_POOLS` authorizer (REST API), plus `quarkus.lambda-http.enable-security=true` | Invalid tokens are rejected before the Lambda is invoked. The HTTP JWT authorizer checks `kid`, `iss`, `aud` or `client_id`, `exp`, `nbf`, `iat` and route scopes, and caches the key for up to two hours on a best-effort basis (AWS). The Quarkus side only maps the event | The function trusts the event. Only name and roles are mapped. A route left without an authorizer gives no Principal. A key cache miss "adds latency to the request that triggers it" (AWS) | One pool or a few pools; scope or group checks are enough at the edge |
| B. No authorizer on the route; `quarkus-oidc` checks the bearer token in the function | The function verifies `token_use`, `client_id` and custom claims itself and does not depend on route configuration | The Lambda is invoked, and billed, for rejected requests. JWKS fetch at connection init (`quarkus.oidc.jwks.resolve-early`, default `true`); cold-start impact and SnapStart interaction are (unverified). Running `quarkus-oidc` in the Lambda HTTP extensions is not documented (unverified) | Checks the authorizer cannot express, or a stack without authorizers |
| C. Both | Defence in depth: a misconfigured route is still protected by the function | Both costs. Issuer and audience must agree in two places. Which identity wins when `enable-security` and `quarkus-oidc` are both active is (unverified) | Multi-tenant SaaS with a high isolation requirement |

- Option B is never a default. Both extension POMs depend on `quarkus-vertx-http` and `quarkus-security`, which makes it likely that `quarkus-oidc` works (medium confidence), but no 3.40 page documents it. Require a test with a real Cognito token, in `sam local` or a deployed stage, before relying on it. Details: [option B](./option-b-in-function-oidc.md).
- Two WebSearch queries found no official page documenting `quarkus-oidc` inside `quarkus-amazon-lambda-http`; the results were not used as evidence.
- Authorizer pricing against Lambda invocation pricing was not read (unverified).
- Ask: "Are tokens validated by API Gateway, by the function, or both, and what pricing and latency data do you accept? Can a real-token test run before go-live?"

Sources: [HTTP API JWT authorizer](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-jwt-authorizer.html), [aws-lambda-http guide](https://quarkus.io/version/3.40/guides/aws-lambda-http), [OIDC configuration reference](https://quarkus.io/version/3.40/guides/security-oidc-configuration-properties-reference).

## K2. ID token or access token

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| Access token | Scopes for API authorization. HTTP JWT authorizer: "we recommend that you configure your routes to require authorization scopes". A REST authorizer with Authorization Scopes treats the token as an access token | No `custom:` attributes unless a V2_0/V3_0 pre token generation trigger adds them (Essentials or Plus feature plan). No `aud` without a resource binding. Carries `username`, NOT `cognito:username`: the guide's Principal path `...claims.cognito:username` does not match, and Quarkus behaviour with an access token is (unverified); identify users by `sub` ("The `sub` claim is the best way to identify a given user"). M2M access tokens have no `username` and no `cognito:groups` (`sub` = client ID), so they get no roles from the group mapping | Standard API authorization |
| ID token | Carries `custom:` attributes (for example tenant), `aud` and `cognito:username` (the claim the guide's Principal path reads). A REST authorizer without Authorization Scopes "treats the supplied token as an identity token" | AWS: "There is no standard mechanism to differentiate JWT access tokens from other types of JWTs". No scopes | Simple user APIs needing profile claims and no pre token trigger |
| Both | Either token accepted | `token_use` must then be `id` or `access` and each path checked | Mixed clients |

Ask: "Which token does the client send, and does the user pool's feature plan allow access-token customization (V2_0)?" Sources: [Cognito access token](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-the-access-token.html), [HTTP API JWT authorizer](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-jwt-authorizer.html), [REST Cognito authorizer](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-enable-cognito-user-pool.html), [pre token generation](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-pre-token-generation.html).

## K3. Tenant model

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| A. One pool, `custom:tenantId` (or a pre-token claim) per user | One issuer, one config | The tenant claim must be protected (see [multi-tenant isolation](./multi-tenant-isolation.md)) | Most pooled SaaS |
| B1. Pool per tenant, Quarkus OIDC multi-tenancy resolved by issuer (`quarkus.oidc.resolve-tenants-with-issuer=true`) | Tenant follows from the signed `iss`, not from the path | One config block per tenant, or a dynamic `TenantConfigResolver`. Running in Lambda is (unverified) | Few large tenants with separate pools |
| B2. `quarkus.oidc.<tenant>.tenant-paths` | Simple | Selects only which issuer's keys check the token; it does not prove the caller belongs to the path's tenant unless each tenant has its own issuer | Only together with per-tenant issuers |
| C. Pool per tenant behind a REST `COGNITO_USER_POOLS` authorizer | Edge validation for many pools | "up to 1,000 user pools for one `COGNITO_USER_POOLS` authorizer. This limit cannot be increased." | REST APIs |

An HTTP API JWT authorizer takes a single issuer (medium confidence, inferred from the singular `Issuer` in the AWS examples). Ask: "Pooled or pool per tenant, and how many tenants?" Sources: [multi-tenancy guide](https://quarkus.io/version/3.40/guides/security-openid-connect-multitenancy), [REST Cognito authorizer](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-enable-cognito-user-pool.html).

## K4. Original or updated issuer

Original `https://cognito-idp.<region>.amazonaws.com/<poolId>` ("The current default issuer configuration") or updated `https://issuer-cognito-idp.<region>.amazonaws.com/<poolId>` ("Recommended for all user pools, including for multi-Region replication"). The token `iss`, `quarkus.oidc.auth-server-url` (or `quarkus.oidc.token.issuer`) and the API Gateway authorizer `Issuer` must all name the same issuer. The `issuer` value inside the updated host's discovery document was not read (unverified): fetch a real pool's `/.well-known/openid-configuration` before choosing the `auth-server-url`. Ask: "Which issuer does a decoded real token show in `iss`?" Source: [Cognito federation endpoints](https://docs.aws.amazon.com/cognito/latest/developerguide/federation-endpoints.html).

## K5. Revocation and token lifetime

Access and ID tokens: "any value between 5 minutes and 1 day", per app client. Refresh token: default 30 days, "any value between 60 minutes and 10 years"; rotation is optional, "As a security best practice, enable refresh token rotation". Offline checks "can't detect revocation on their own. If your application must honor revocation before a token expires, verify the token's status against Amazon Cognito ... or keep access token lifetimes short." No Quarkus pattern for an online Cognito status check was researched. Ask: "Must revocation take effect before token expiry?" Sources: [access token](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-the-access-token.html), [refresh token](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-the-refresh-token.html).

## K6. Deny by default

`quarkus.security.jaxrs.deny-unannotated-endpoints=true` (default `false`, medium confidence, M13) or `quarkus.security.jaxrs.default-roles-allowed=...` (the `**` role "means any authenticated user"). `deny-unannotated-endpoints` takes precedence over `default-roles-allowed`. Whether deny-by-default is the right family default is engineering judgement (medium confidence). Ask: "Must every endpoint carry an explicit security annotation?" Source: [authorize web endpoints reference](https://quarkus.io/version/3.40/guides/security-authorize-web-endpoints-reference).

## K7. quarkus-oidc or quarkus-smallrye-jwt

SmallRye JWT "verifies only `JWT` tokens" and "does not support the remote introspection"; both refresh the key set. SmallRye keys: `mp.jwt.verify.publickey.location`, `mp.jwt.verify.issuer`, `mp.jwt.verify.audiences` (matched against `aud`, so it does not fit access tokens without `aud`), `smallrye.jwt.path.groups`, `smallrye.jwt.required.claims` (presence only), `smallrye.jwt.jwks.refresh-interval` (60 min) and `smallrye.jwt.jwks.forced-refresh-interval` (30 min), both defaults (medium confidence, M12). `quarkus-oidc` has value checks (`required-claims`) and issuer discovery. With SmallRye JWT a `SecurityIdentityAugmentor` or code check would be needed for `client_id` and `token_use`. The authentication-mechanisms guide was read to 100,000 of 110,821 characters (L3). Ask before choosing SmallRye JWT. Sources: [security-jwt](https://quarkus.io/version/3.40/guides/security-jwt), [authentication mechanisms](https://quarkus.io/version/3.40/guides/security-authentication-mechanisms).
