---
source: cloud-architecture-researcher
provider: AWS
domain: Cognito
edition: AWS Cognito 2025 (current stable)
generated: 2026-07-31
research_framework: version-absolutism
source_hierarchy: official-docs-only
---

# AWS Cognito Architecture Research

> **Version Absolutism note.** This document targets **Amazon Cognito as the current stable
> service in 2025–2026**, including the **feature-plan model (Lite / Essentials / Plus)**,
> **Managed login** (successor to the classic hosted UI), **passkey / WebAuthn sign-in**, and the
> **two-tier provisioned-quota model** — all of which are recent (2024–2025) additions. Older
> Cognito guidance that references "Advanced Security Features (ASF) pricing", the classic hosted UI
> as the primary UI, or a single flat quota model is treated as **outdated** and must not be mixed in.
>
> **Source dating.** Amazon Cognito is a continuously-updated managed service; its Developer Guide
> pages under `docs.aws.amazon.com/cognito/latest/developerguide/` do not carry per-page publish
> dates. Every claim below is anchored to a specific official page and was **verified on 2026-07-31**
> (the access date). These pages document the **current stable** service, so they satisfy the
> source-hierarchy rule (official docs are the top tier; "latest" = current stable).
>
> Anything not confirmable against an official AWS page is explicitly marked **[unverified]**.

---

## 1. Core Concepts & Service Overview

Amazon Cognito is AWS's managed **customer identity and access management (CIAM)** service. It has
**two independent-but-composable halves**:

| Half | What it is | Primary output | Standards role |
|---|---|---|---|
| **User pools** | A user directory + authentication service | **JWTs** (ID, access, refresh) | Acts as an **OIDC identity provider (IdP)** to your app |
| **Identity pools** (federated identities) | A broker that exchanges tokens/assertions for AWS creds | **Temporary AWS credentials** via STS | Acts as an **AWS IdP** / STS front-end |

- A **user pool** is "a user directory for web and mobile app authentication and authorization…
  From the perspective of your app, an Amazon Cognito user pool is an OpenID Connect (OIDC) identity
  provider (IdP)." (Source: [Amazon Cognito user pools](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-identity-pools.html), verified 2026-07-31)
- An **identity pool** is "a directory of federated identities that you can exchange for AWS
  credentials. Identity pools generate temporary AWS credentials for the users of your app, whether
  they've signed in or you haven't identified them yet." (Source: [Amazon Cognito identity pools](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-identity.html), verified 2026-07-31)

**Key mental model:** User pools answer *"who is this user and are they authenticated?"* (AuthN +
OIDC tokens). Identity pools answer *"what AWS resources may this identity touch?"* (AuthZ →
short-term IAM credentials). They are frequently chained: **user pool → identity pool → STS creds →
AWS service**, but each can be used alone. Identity pools can also consume SAML/OIDC/social tokens
directly without a user pool. (Source: [Amazon Cognito identity pools](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-identity.html), verified 2026-07-31)

### User pool feature plans (2024–2025 model)

New user pools default to the **Essentials** plan. Plan is set via the `UserPoolTier` parameter on
`CreateUserPool`/`UpdateUserPool` (`--user-pool-tier` in the CLI). (Source: [User pool feature plans](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-sign-in-feature-plans.html), verified 2026-07-31)

| Plan | Positioning | Notable inclusions | Notable exclusions |
|---|---|---|---|
| **Lite** | Low-cost, basic auth | Sign-up/sign-in, groups, social/SAML/OIDC, OAuth2/OIDC server, **classic hosted UI**, SRP/password/custom/refresh auth, SMS+authenticator MFA, ID-token claim customization, user import, M2M client-credentials | **No** Managed login, **no** access-token customization, **no** passkeys, **no** email MFA, **no** choice-based/passwordless sign-in, **no** threat protection |
| **Essentials** *(default)* | All latest auth features | Everything in Lite **+ Managed login**, **passkey (FIDO2/WebAuthn) sign-in**, **passwordless one-time-code sign-in**, **email MFA**, **choice-based sign-in**, **access-token customization**, visual branding editor | **No** advanced threat protection (compromised-credential / adaptive) |
| **Plus** | Essentials + advanced security | Everything in Essentials **+ threat protection** (unsafe-password detection, malicious sign-in detection / adaptive auth), **user-activity + risk logging and export** | — |

> **Important (2024 change):** Features formerly sold under the *"Advanced Security Features"*
> pricing SKU are now split across **Essentials** and **Plus**. Setting `AdvancedSecurityMode` to
> `AUDIT` or `ENFORCED` forces the tier to **PLUS**. (Source: [User pool feature plans](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-sign-in-feature-plans.html), verified 2026-07-31)

---

## 2. User Pools — Authentication Patterns

### Sign-up models

Three co-existable models (Source: [Amazon Cognito user pools › Sign-up](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-identity-pools.html), verified 2026-07-31):
1. **Self-service / native** — users register directly via API (`SignUp`) or Managed login.
2. **Federated** — redirect to a third-party IdP; Cognito ingests OIDC id tokens, OAuth2 `userInfo`,
   or SAML 2.0 assertions into a user profile via attribute-mapping rules.
3. **Administrative / imported** — `AdminCreateUser`, CSV import, or just-in-time Lambda migration.

> ⚠️ **Security-critical default:** If self-service sign-up is enabled, *anyone on the internet can
> create an account.* Disable it with `AdminCreateUserConfig.AllowAdminCreateUserOnly = true` unless
> public sign-up is intended. (Source: [Amazon Cognito user pools › Sign-up](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-identity-pools.html), verified 2026-07-31)

### Sign-in / authentication flows

Users can sign in with **usernames + passwords, passkeys, and email/SMS one-time passwords**, plus
MFA and custom flows. (Source: [Amazon Cognito user pools › Sign-in](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-identity-pools.html), verified 2026-07-31)

| Flow | Use it for | Notes |
|---|---|---|
| **SRP** (Secure Remote Password) | Password auth without sending the password | AWS-recommended when passwords are required. (Source: [User pool security best practices](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-security-best-practices.html), verified 2026-07-31) |
| **Passkey / WebAuthn (FIDO2)** | Passwordless, phishing-resistant first factor | **Essentials/Plus only**; AWS-recommended default over passwords. Max **20 authenticators per user**. (Sources: [Feature plans](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-sign-in-feature-plans.html); [Quotas](https://docs.aws.amazon.com/cognito/latest/developerguide/quotas.html), verified 2026-07-31) |
| **Passwordless one-time code** (email/SMS) | Frictionless first-factor | Essentials/Plus only. |
| **Custom auth (Lambda challenge)** | Bespoke challenge/response | Define/Create/Verify-auth-challenge triggers. |
| **Client-credentials (M2M)** | Service-to-service, no human | Requires an app client with a client secret; issues **access tokens only** with OAuth2 scopes. (Source: [Amazon Cognito user pools › M2M](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-identity-pools.html), verified 2026-07-31) |

### Managed login vs. classic hosted UI

**Managed login** is "a set of web pages for sign-up, sign-in, MFA, and password reset" that
replaces the older **classic hosted UI** (described as "a slimmer, less-customizable predecessor").
Managed login requires **Essentials or Plus**; the classic hosted UI is available on **all plans**.
(Sources: [Managed login](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-identity-pools.html); [Feature plans](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-sign-in-feature-plans.html), verified 2026-07-31)

### App clients: public vs confidential

- **Confidential clients** hold a **client secret**; every request carries a `SECRET_HASH` derived
  from username + client ID + secret. Store the secret in **AWS Secrets Manager / encrypted storage**
  — never embed it in a public/SPA/mobile client. (Source: [User pool security best practices › client secrets](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-security-best-practices.html), verified 2026-07-31)
- **Public clients** (SPA, mobile) must use the **authorization-code grant with PKCE** — never embed
  secrets, and generate a fresh random PKCE code verifier per request. (Source: [User pool security best practices › PKCE](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-security-best-practices.html), verified 2026-07-31)

### Lambda triggers (customization)

Triggers customize sign-up/sign-in/token generation, e.g. **Pre token generation** (add/modify/
suppress claims and scopes), custom-auth challenge triggers, migration triggers, custom SMS/email
sender triggers. Access-token customization ("v2 events") is **Essentials/Plus** and incurs extra
cost. (Sources: [User pools › Custom UX](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-identity-pools.html); [Understanding JWTs](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-with-identity-providers.html), verified 2026-07-31)

---

## 3. Identity Pools — Authorization & Federation

Identity pools exchange an authenticated token/assertion for **temporary AWS credentials** via
`sts:AssumeRoleWithWebIdentity`. Features (Source: [Amazon Cognito identity pools](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-identity.html), verified 2026-07-31):

- **Sign AWS requests** (S3, DynamoDB, etc.) with SigV4 temporary creds.
- **Guest (unauthenticated) access** — narrow-scope creds for un-signed-in users.
- **Role selection** — one role for all authenticated users, or per-claim role choice.
- **Resource-based filtering** — transform user claims into **IAM session tags** for ABAC.
- **Developer-authenticated identities** — your server vouches for users with your AWS creds.

### Supported identity providers

Cognito user pools, **Login with Amazon / Facebook / Google / Apple / Twitter** (public/social),
generic **OIDC**, generic **SAML 2.0**, and **developer-authenticated identities**. (Source: [Amazon Cognito identity pools](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-identity.html), verified 2026-07-31)

### Authentication flows: enhanced vs. basic (classic)

| Flow | Role selection | STS request | Security |
|---|---|---|---|
| **Enhanced** (`GetCredentialsForIdentity`) | Centralized in the identity pool | Hidden behind Cognito automation | **AWS-recommended default**; applies a **scope-down policy** capping unauthenticated permissions |
| **Basic / classic** (`GetOpenIdToken` → app calls `AssumeRoleWithWebIdentity`) | App chooses the role client-side | App assembles the STS call | Exposes role-selection logic; use only when you need custom role logic, and apply IAM best practices |

(Source: [Identity pools security best practices › enhanced flow](https://docs.aws.amazon.com/cognito/latest/developerguide/identity-pools-security-best-practices.html), verified 2026-07-31)

### RBAC vs ABAC

- **Role-based access control (RBAC):** map IdP claims/groups → IAM roles via **role-mapping rules**
  (max **25 RBAC rules** per pool; role mappings for up to **10 IdPs**). (Source: [Quotas › identity pools](https://docs.aws.amazon.com/cognito/latest/developerguide/quotas.html), verified 2026-07-31)
- **Attribute-based access control (ABAC):** transform claims into **IAM session tags** and write
  policies with `aws:PrincipalTag` conditions. (Sources: [Identity pools](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-identity.html); [Identity pools security best practices](https://docs.aws.amazon.com/cognito/latest/developerguide/identity-pools-security-best-practices.html), verified 2026-07-31)

---

## 4. Token Lifecycle & Security

### The three JWTs (Source: [Understanding user pool JWTs](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-with-identity-providers.html), verified 2026-07-31)

| Token | Purpose | Format | Key claims |
|---|---|---|---|
| **ID token** | Proof of authentication / identity claims | Signed JWT, base64url-decodable | username, name, email, `cognito:groups` |
| **Access token** | Authorize API/resource access | Signed JWT, base64url-decodable | `scope`, `cognito:groups`, `aws.cognito.signin.user.admin` |
| **Refresh token** | Obtain new ID/access tokens; revoke sessions | **Encrypted, opaque** (readable only by the pool) | — |

- Tokens are signed and verifiable **client-side** against the pool's **JWKS** (`.../.well-known/
  jwks.json`) — do not call the API to validate. (Source: [Quotas › validate JWTs client side](https://docs.aws.amazon.com/cognito/latest/developerguide/quotas.html), verified 2026-07-31)
- Enabling **token revocation** adds `origin_jti` + `jti` claims (increasing token size — size your
  storage accordingly). (Source: [Understanding user pool JWTs › storing tokens](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-with-identity-providers.html), verified 2026-07-31)

### Token validity limits (authoritative)

(Source: [Quotas › session validity parameters](https://docs.aws.amazon.com/cognito/latest/developerguide/quotas.html), verified 2026-07-31)

| Artifact | Configurable range |
|---|---|
| **ID token** | 5 minutes – 1 day |
| **Access token** | 5 minutes – 1 day |
| **Refresh token** | 1 hour – 3,650 days (≈10 years) |
| **Managed login / hosted UI session cookie** | **1 hour (fixed, non-configurable)** |
| **Authentication session token** (between challenges) | 3 – 15 minutes |

Code-validity companions: sign-up confirmation & attribute-verification codes = **24 h**; MFA code =
**3–15 min**; forgot-password code = **1 h**. (Source: [Quotas › code security](https://docs.aws.amazon.com/cognito/latest/developerguide/quotas.html), verified 2026-07-31)

### Token handling best practices

- **Do not** store ID/access tokens in browser local storage (they carry PII / security-model info).
  Client apps → **in-memory cache**; server apps → **encrypted cache**. (Sources: [Security best practices › tokens](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-security-best-practices.html); [Caching tokens](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-caching-tokens.html), verified 2026-07-31)
- **Refresh at ~75% of token lifetime**, not on expiry, to protect availability. (Source: [Caching tokens](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-caching-tokens.html), verified 2026-07-31)
- **Revoke refresh tokens** on sign-out or suspected compromise (`RevokeToken` / global sign-out).
  (Source: [Security best practices › tokens](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-security-best-practices.html), verified 2026-07-31)
- **Minimize scopes:** request only what's needed. `aws.cognito.signin.user.admin` grants
  self-service profile access; `openid`/`profile`/`email`/`phone` control `userInfo` output; omitting
  `openid` yields access-token-only responses. (Source: [Security best practices › scopes](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-security-best-practices.html), verified 2026-07-31)

---

## 5. Integration Patterns (API Gateway, Lambda, AppSync, ALB)

### API Gateway — REST API (`COGNITO_USER_POOLS` authorizer)

Create a `COGNITO_USER_POOLS` authorizer, attach it to methods; client sends a token in the
`Authorization` header. **ID token** → authorize on identity claims; **access token** → authorize on
**custom scopes** (via resource servers). Cross-account authorizers and CloudFormation setup are
supported. (Source: [Control access to REST APIs using Cognito user pools](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-integrate-with-cognito.html), verified 2026-07-31)

> Alternative for AWS-credential-based access: use **identity pools** and set the method
> authorization type to `AWS_IAM`. (Source: same page, verified 2026-07-31)

### API Gateway — HTTP API (JWT authorizer)

HTTP APIs support a native **JWT authorizer** validating the OIDC issuer/audience and (optionally)
scopes; typically uses the **access token**. **[unverified in this research pass]** — not fetched
from the API Gateway HTTP-API JWT-authorizer page; confirm issuer/audience/scope specifics against
`docs.aws.amazon.com/apigateway/latest/developerguide/http-api-jwt-authorizer.html` before authoring.

### M2M token caching via API Gateway (scale pattern)

For high-volume **client-credentials** (M2M) traffic that can exceed OAuth-endpoint quotas, put
**API Gateway as a caching proxy** in front of `/oauth2/token`. Cache key = `scope` query param +
`Authorization` header; **cache TTL must be shorter than the access-token lifetime**. ElastiCache
(Redis OSS) or DynamoDB are alternative caches. (Source: [Caching M2M access tokens with API Gateway](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-caching-tokens.html), verified 2026-07-31)

### Lambda

Two distinct roles: (a) **user-pool Lambda triggers** customize auth (pre-token-gen, custom
challenge, migration, custom sender); (b) **Lambda authorizers** in API Gateway as an alternative to
the Cognito authorizer for bespoke logic. (Sources: [User pools › custom UX](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-identity-pools.html); [API Gateway Cognito authorizer](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-integrate-with-cognito.html), verified 2026-07-31)

### AppSync & ALB

- **AWS AppSync** supports Amazon Cognito user pools as a GraphQL authorization mode.
  **[unverified in this research pass]** — confirm against the AppSync security/authorization docs
  before authoring.
- **Application Load Balancer (ALB)** can offload OIDC authentication to a Cognito user pool at the
  listener. **[unverified in this research pass]** — confirm against the ELB "Authenticate users
  using an ALB" doc before authoring.

---

## 6. Architecture Blueprints by Workload

### 6a. Multi-tenant SaaS

Cognito **quotas are per AWS account per Region and shared across all tenants** — model tenant count
against quotas early and buy capacity or split across accounts/Regions as you grow. (Source: [Multi-tenant application best practices](https://docs.aws.amazon.com/cognito/latest/developerguide/multi-tenant-application-best-practices.html), verified 2026-07-31)

| Isolation model | Isolation strength | When to use | Watch-outs |
|---|---|---|---|
| **User pool per tenant** | Highest (separate directory, security config, admin IAM) | Strict tenant separation; per-tenant admin delegation; regulatory isolation | Bounded by **1,000 user pools/Region** (adjustable → 10,000); more operational overhead |
| **App client per tenant** | Medium | Shared directory, per-tenant app config | Bounded by **1,000 app clients/pool** (→10,000); IAM cannot scope to a single app client |
| **User group per tenant** | Lower | Lightweight tenant tagging, shared everything | Bounded by **10,000 groups/pool**, **100 groups/user** |
| **Custom attribute per tenant** | Lower | Tenant stamped on the profile/token | 50 custom attributes/pool |
| **Custom scope per tenant** | Medium (authz) | Per-tenant API scopes | Scope limits per resource server/app client |

> **Managed login cross-tenant caveat:** a **local user's** session cookie authenticates them for
> **all app clients in the same user pool** (cookie fixed at **1 hour**). To prevent cross-tenant SSO
> leakage, either use **one user pool per tenant** or replace hosted-UI sign-in with **API-based
> sign-in**. (Source: [Multi-tenant application best practices](https://docs.aws.amazon.com/cognito/latest/developerguide/multi-tenant-application-best-practices.html), verified 2026-07-31)
>
> **IAM caveat:** Cognito IAM granularity is only **user pool** and **identity pool** — you *cannot*
> scope admin permissions to an individual app client. If your security model requires per-tenant
> admin separation, use **one tenant per user pool**. (Source: [User pool security best practices › least privilege](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-security-best-practices.html), verified 2026-07-31)

Dedicated sub-guides exist for each model (user-pool-based, app-client-based, group-based,
custom-attribute-based, scope-based, plus multi-tenancy security recommendations). (Source: [Multi-tenant application best practices › Topics](https://docs.aws.amazon.com/cognito/latest/developerguide/multi-tenant-application-best-practices.html), verified 2026-07-31)

### 6b. Serverless (SPA/API + Lambda)

Blueprint: **SPA (public client, auth-code + PKCE)** → **user pool** issues JWTs → **API Gateway
Cognito/JWT authorizer** validates → **Lambda** business logic → (optional) **identity pool** for
direct AWS-service access (S3/DynamoDB) with least-privilege roles. Add **API Gateway token caching**
for M2M microservice traffic. (Sources: [API Gateway Cognito authorizer](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-integrate-with-cognito.html); [Caching tokens](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-caching-tokens.html), verified 2026-07-31)

### 6c. Mobile / guest-first

Blueprint: **identity pool with guest (unauthenticated) access** for pre-login asset retrieval →
user signs in through a user pool or social IdP → **switch unauthenticated identity to
authenticated** to elevate access. Use the **enhanced flow** so unauthenticated creds are capped by
the scope-down policy. (Sources: [Identity pools](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-identity.html); [Identity pools security best practices](https://docs.aws.amazon.com/cognito/latest/developerguide/identity-pools-security-best-practices.html), verified 2026-07-31)

### 6d. Enterprise B2B federation

Blueprint: **SAML/OIDC IdP → user pool** (attribute mapping) → app. SAML/OIDC providers can create
users and set attributes, so treat them as trusted; keep social IdPs (public) separate from
enterprise IdPs. Federated users linked to local users count as **`EnterpriseMAU`** for billing.
(Sources: [User pool security best practices › trusted IdPs](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-security-best-practices.html); [Quotas › MAU](https://docs.aws.amazon.com/cognito/latest/developerguide/quotas.html), verified 2026-07-31)

---

## 7. Security Hardening & Well-Architected Alignment

Cognito security is **customer responsibility ("security *in* the cloud")** under the AWS Shared
Responsibility Model; MFA/threat-protection apply to **local users only** (federated users' posture
is owned by their IdP). (Source: [Using user pool security features](https://docs.aws.amazon.com/cognito/latest/developerguide/managing-security.html), verified 2026-07-31)

### ✅ Always-Do

1. **Least-privilege identity-pool IAM roles** with **trust-policy conditions**
   `cognito-identity.amazonaws.com:aud` (must match pool ID) and `:amr` (`authenticated` /
   `unauthenticated`), scoped to `sts:AssumeRoleWithWebIdentity`. (Source: [Identity pools security best practices › trust conditions](https://docs.aws.amazon.com/cognito/latest/developerguide/identity-pools-security-best-practices.html), verified 2026-07-31)
2. **Use the enhanced identity-pool flow by default** (scope-down cap on unauthenticated creds).
   (Source: same page, verified 2026-07-31)
3. **Prefer passkeys/WebAuthn; else SRP + MFA.** Never store passwords/hashes client-side. (Source: [User pool security best practices › secrets](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-security-best-practices.html), verified 2026-07-31)
4. **Auth-code grant + PKCE** for public clients; fresh verifier per request. (Source: same page, verified 2026-07-31)
5. **Store client secrets only in confidential/server-side clients** (Secrets Manager); never in
   SPA/mobile. (Source: same page, verified 2026-07-31)
6. **Attach an AWS WAF web ACL** to user-pool endpoints/managed login for network + app-layer
   filtering (CAPTCHA/drop). (Sources: [Managing security](https://docs.aws.amazon.com/cognito/latest/developerguide/managing-security.html); [User pool security best practices › network](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-security-best-practices.html), verified 2026-07-31)
7. **Enable threat protection (Plus)** for compromised-credential + adaptive-auth detection on
   public/CIAM pools. (Source: [Feature plans](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-sign-in-feature-plans.html), verified 2026-07-31)
8. **Enable `PreventUserExistenceErrors`** (return generic errors) and **case sensitivity** guards.
   (Source: [Managing security](https://docs.aws.amazon.com/cognito/latest/developerguide/managing-security.html), verified 2026-07-31)
9. **Enable deletion protection** on production user pools. (Source: same page, verified 2026-07-31)
10. **Validate JWTs client-side against JWKS**; minimize token validity and scopes; revoke on
    sign-out. (Sources: [Quotas](https://docs.aws.amazon.com/cognito/latest/developerguide/quotas.html); [Security best practices › tokens](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-security-best-practices.html), verified 2026-07-31)

### ⚠️ Ask-First (context-dependent)

| Decision | Trade-off |
|---|---|
| **Enable self-service sign-up?** | Opens the pool to the public internet — only for CIAM/public apps. (Source: [User pools › Sign-up](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-identity-pools.html)) |
| **Enable identity-pool guest access?** | Anyone knowing the (non-secret) pool ID gets unauthenticated creds — only enable if you'd grant those perms to the whole internet. (Source: [Identity pools security best practices › guest](https://docs.aws.amazon.com/cognito/latest/developerguide/identity-pools-security-best-practices.html)) |
| **Activate social IdPs?** | Public accounts, less control — enable only when public sign-in is intended. (Source: [User pool security best practices › trusted IdPs](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-security-best-practices.html)) |
| **Basic vs enhanced identity-pool flow** | Basic only when custom role-selection logic is required. (Source: [Identity pools security best practices](https://docs.aws.amazon.com/cognito/latest/developerguide/identity-pools-security-best-practices.html)) |
| **Refresh-token lifetime** | Up to 3,650 days is convenient but raises session-hijack blast radius — shorten + revoke. (Source: [Quotas](https://docs.aws.amazon.com/cognito/latest/developerguide/quotas.html)) |

### 🚫 Never-Do (with the correct alternative)

| 🚫 Anti-pattern | ✅ Correct alternative |
|---|---|
| Embed a **client secret** in an SPA/mobile app | Use a **public client + PKCE**; keep secrets server-side (Secrets Manager). (Source: [Security best practices › client secrets](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-security-best-practices.html)) |
| Store **ID/access tokens in local storage** | In-memory (client) or encrypted cache (server). (Source: [Security best practices › tokens](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-security-best-practices.html)) |
| Grant a **broad `*` IAM role** to identity-pool users | Least-privilege resource-scoped policy + trust conditions. (Source: [Identity pools security best practices](https://docs.aws.amazon.com/cognito/latest/developerguide/identity-pools-security-best-practices.html)) |
| **Enable guest access** "just in case" | Leave deactivated; fetch resources only post-auth. (Source: [Identity pools security best practices › guest](https://docs.aws.amazon.com/cognito/latest/developerguide/identity-pools-security-best-practices.html)) |
| Rely on a **static/predictable PKCE verifier** | Generate a fresh random verifier per authorization request. (Source: [Security best practices › PKCE](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-security-best-practices.html)) |
| **Mix internal + external trust** in one identity pool | Separate developer providers and SSO providers into distinct identity pools. (Source: [Identity pools security best practices › developer providers](https://docs.aws.amazon.com/cognito/latest/developerguide/identity-pools-security-best-practices.html)) |
| Poll **`AdminGetUser`/`getUser`** for attributes on every request | Read validated claims from the JWT; cache; use external DB for hot attributes. (Source: [Quotas › optimize](https://docs.aws.amazon.com/cognito/latest/developerguide/quotas.html)) |

**Well-Architected note:** These map to the Security pillar's identity-management best practices
(strong sign-in, least privilege, short-lived credentials, centralized identity). The specific
mapping to the AWS Well-Architected **Security pillar** / IAM whitepaper text was **not fetched in
this research pass** — mark cross-references to Well-Architected as **[unverified]** until confirmed
against `docs.aws.amazon.com/wellarchitected/latest/security-pillar/`.

---

## 8. Limits, Quotas & Operational Considerations

### Request-rate quotas (per account, per Region) — user pools

Quotas are **category-based** (pooled across all pools in a Region). (Source: [Quotas in Amazon Cognito](https://docs.aws.amazon.com/cognito/latest/developerguide/quotas.html), verified 2026-07-31)

| Category | Default RPS | Adjustable |
|---|---|---|
| `UserAuthentication` | 120 | Yes |
| `UserCreation` | 50 | Yes |
| `UserFederation` | 25 | Yes |
| `UserAccountRecovery` | 30 | No |
| `UserRead` | 120 | Yes |
| `UserUpdate` | 25 | No |
| `UserToken` | 120 | Yes |
| `UserResourceRead` | 50 | Yes |
| `UserResourceUpdate` | 25 | No |
| `UserList` | 30 | No |
| `ClientAuthentication` (M2M `client_credentials`) | 150 | No |
| `LimitManagement` | 1 | No |

- **`RespondToAuthChallenge`/`AdminRespondToAuthChallenge`** get **3× the `UserAuthentication`**
  rate (extra challenges above 3 spill back into the category quota).
- **Per-user** limits: read-profile 10 ops/user/s, write-profile 10 ops/user/s.
- **Domain-level** limits: 300 RPS/source-IP, 300 RPS/app-client, 500 RPS/domain, **50,000 RPS for
  jwks.json** per account/Region.
- **Two-tier provisioned model (2025):** raise the **account-level max** in Service Quotas, then set
  the **provisioned limit** with `UpdateProvisionedLimit` (billed for provisioned capacity above
  default, prorated). Managed-login pools **can't** use the API to adjust `UserAuthentication`/
  `UserFederation` — use a Service Quotas request instead.
(All: [Quotas](https://docs.aws.amazon.com/cognito/latest/developerguide/quotas.html), verified 2026-07-31)

### Request-rate quotas — identity pools (per-operation)

`GetId` 25 RPS · `GetOpenIdToken` 200 · `GetCredentialsForIdentity` 200 ·
`GetOpenIdTokenForDeveloperIdentity` 50 · `ListIdentities` 5 (all adjustable via account team).
(Source: [Quotas › identity pools](https://docs.aws.amazon.com/cognito/latest/developerguide/quotas.html), verified 2026-07-31)

### Resource quotas (per Region)

| Resource | Default | Adjustable → Max |
|---|---|---|
| User pools / Region | 1,000 | Yes → 10,000 |
| App clients / user pool | 1,000 | Yes → 10,000 |
| Identity providers / user pool | 300 | Yes → 1,000 |
| Resource servers / user pool | 25 | Yes → 300 |
| Users / user pool | 40,000,000 | Yes → contact team |
| Custom attributes / pool | 50 | No |
| Groups / user pool | 10,000 | No |
| Groups per user | 100 | No |
| Identities linked to a user | 5 | No |
| Passkey/WebAuthn authenticators per user | 20 | No |
| Callback / Logout URLs per app client | 100 / 100 | No |
| Scopes per resource server / app client | 100 / 50 | No |
| Custom domains / Region | 4 | No |
| Identity pools / account | 1,000 | Yes |
| Cognito user-pool providers / identity pool | 50 | Yes → 1,000 |
| Identities per identity pool | Unlimited | — |
| RBAC rules / identity pool | 25 | No |
| Password length policy | 6–99 chars min (256 max chars) | No |
| Default email sends / account / day | 50 (use SES for more) | No |
| CSV import: users/file / file size | 500,000 / 100 MB | No |

(Source: [Quotas › resource quotas](https://docs.aws.amazon.com/cognito/latest/developerguide/quotas.html), verified 2026-07-31)

### Operational guidance

- **Billing = Monthly Active Users (MAU)**, priced per tier; a user active in multiple tiers within a
  month is billed at the **highest** tier they touched. CSV import and admin password *reset* do
  **not** create MAUs. (Source: [Quotas › MAU](https://docs.aws.amazon.com/cognito/latest/developerguide/quotas.html), verified 2026-07-31)
- **Monitoring:** CloudTrail logs all API/managed-login calls; CloudWatch `CallCount`/`ThrottleCount`
  per category; Service Quotas console for utilization; Plus-tier risk logs exportable to
  S3/CloudWatch/Firehose. (Sources: [User pools › monitoring](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-identity-pools.html); [Quotas › track usage](https://docs.aws.amazon.com/cognito/latest/developerguide/quotas.html), verified 2026-07-31)
- **Scale/HA options:** raise quotas per Region (each Region is independent); **Multi-Region
  replication** for user pools; API Gateway/ElastiCache/DynamoDB token caching for M2M surges;
  exponential backoff + SDK retries; external DB for hot custom attributes. (Sources: [User pools](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-identity-pools.html); [Quotas › optimize](https://docs.aws.amazon.com/cognito/latest/developerguide/quotas.html); [Caching tokens](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-caching-tokens.html), verified 2026-07-31)
- **Dependency quotas:** raising Cognito quotas may require raising **SNS/SES** quotas (SMS/email
  delivery). (Source: [Quotas › identify requirements](https://docs.aws.amazon.com/cognito/latest/developerguide/quotas.html), verified 2026-07-31)

---

## References (dated, official URLs only)

All pages are AWS official documentation (top source tier) and were **verified 2026-07-31**; they
document the **current stable** Amazon Cognito service (2025–2026).

### Amazon Cognito Developer Guide
- [Amazon Cognito documentation home](https://docs.aws.amazon.com/cognito/) — 2026-07-31
- [Amazon Cognito user pools (overview + features)](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-identity-pools.html) — 2026-07-31
- [Amazon Cognito identity pools](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-identity.html) — 2026-07-31
- [User pool feature plans (Lite / Essentials / Plus)](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-sign-in-feature-plans.html) — 2026-07-31
- [Understanding user pool JSON web tokens (JWTs)](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-with-identity-providers.html) — 2026-07-31
- [Managing user pool token expiration and caching](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-caching-tokens.html) — 2026-07-31
- [Using Amazon Cognito user pools security features](https://docs.aws.amazon.com/cognito/latest/developerguide/managing-security.html) — 2026-07-31
- [Security best practices for Amazon Cognito user pools](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-security-best-practices.html) — 2026-07-31
- [Security best practices for Amazon Cognito identity pools](https://docs.aws.amazon.com/cognito/latest/developerguide/identity-pools-security-best-practices.html) — 2026-07-31
- [Multi-tenant application best practices](https://docs.aws.amazon.com/cognito/latest/developerguide/multi-tenant-application-best-practices.html) — 2026-07-31
- [Quotas in Amazon Cognito](https://docs.aws.amazon.com/cognito/latest/developerguide/quotas.html) — 2026-07-31

### API Gateway Developer Guide
- [Control access to REST APIs using Amazon Cognito user pools as an authorizer](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-integrate-with-cognito.html) — 2026-07-31

### Foundational references (context)
- [AWS Shared Responsibility Model](https://aws.amazon.com/compliance/shared-responsibility-model/) — 2026-07-31
- [Amazon Cognito Pricing](https://aws.amazon.com/cognito/pricing/) — 2026-07-31

### Marked [unverified] — confirm before skill authoring
- API Gateway **HTTP API JWT authorizer** specifics (issuer/audience/scope) — not fetched.
- **AppSync** Cognito user-pool authorization mode — not fetched.
- **ALB** OIDC authentication with Cognito — not fetched.
- **AWS Well-Architected Security pillar** exact identity-management mapping — not fetched.

---

## Agent Operation Notes (for downstream skill authoring)

- **High confidence (directly quoted from official docs):** two-service model, feature plans,
  token types + validity ranges, all quotas/limits, identity-pool trust conditions, enhanced-vs-basic
  flow, multi-tenancy models + caveats, API Gateway REST Cognito authorizer, security best-practice
  lists.
- **Medium confidence:** serverless/mobile/B2B blueprints (assembled from official building blocks,
  not a single reference-architecture page).
- **Low confidence / [unverified]:** HTTP-API JWT authorizer, AppSync, ALB, Well-Architected mapping
  — flagged inline; author must fetch source pages before asserting these in a SKILL.md.
- **Version-absolutism reminder:** this doc reflects the **2025 feature-plan era** (Managed login,
  passkeys, provisioned quotas). Reject pre-2024 "Advanced Security Features pricing" and
  classic-hosted-UI-primary guidance when authoring.

**Recommended next step:** run `/skill-best-practices-validator` on any SKILL.md derived from this
research, and resolve all four `[unverified]` items against their official pages first.
