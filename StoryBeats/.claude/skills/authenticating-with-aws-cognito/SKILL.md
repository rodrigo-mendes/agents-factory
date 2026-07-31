---
name: authenticating-with-aws-cognito
description: "Provisions and integrates Amazon Cognito user pools and identity pools following AWS 2025 feature-plan security best practices. Use when designing CIAM authentication (passkeys, MFA, sign-up/sign-in flows), managing JWT token lifecycle, federating identities to temporary AWS credentials, or architecting multi-tenant SaaS isolation on Cognito."
---

## Function

Specialist in CIAM architecture and security hardening for Amazon Cognito (2025 feature-plan model: Lite / Essentials / Plus).

## Version Context

**Technology**: Amazon Cognito (managed service — no pinned release version)
**Target Model**: 2025 feature-plan era (Lite / Essentials / Plus)
**Support Status**: Current stable — continuously updated managed service
**Verified**: 2026-07-31 against `docs.aws.amazon.com/cognito/latest/developerguide/`

**Breaking changes (2024–2025)**:
- `Advanced Security Features (ASF)` pricing SKU replaced by **Essentials** (passkeys, Managed login, email MFA) and **Plus** (threat protection) tiers
- **Managed login** replaces classic hosted UI as the default for Essentials/Plus pools
- **Two-tier provisioned quota model**: raise account-level max in Service Quotas, then set pool-level provisioned limit via `UpdateProvisionedLimit`; Managed-login pools cannot use the API to adjust `UserAuthentication`/`UserFederation`

**Deprecations**:
- Classic hosted UI → use **Managed login** (Essentials/Plus) for new pools
- Pre-2024 `AdvancedSecurityMode: AUDIT/ENFORCED` patterns → setting either forces the pool to **Plus**

⚠️ **Version Lock**: Targets the 2025 feature-plan model. Reject any guidance that references "Advanced Security Features pricing" or treats classic hosted UI as the primary UI — those are outdated patterns.

## Quick Navigation

- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — 10 mandatory security and auth patterns with IAM/CLI/code examples
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — 5 architectural decisions requiring business context
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — 7 anti-patterns with wrong vs correct code pairs
- **[Integration Patterns](./blueprints/integration-patterns.md)** — API Gateway, Lambda, M2M caching, multi-tenant isolation
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — Canonical, edge, and misuse test cases
- **[Verification Loop](#verification-loop)** — AWS CLI health checks for pool configuration
- **[Quick Reference](#quick-reference)** — Token validity, feature-plan matrix, key hard limits

---

## Blueprints & Guardrails

### ✅ Always Do

Full patterns with IAM policy JSON and code examples: [Always Do Patterns](./blueprints/always-do-patterns.md).

**Mandatory patterns** (domain = Complex; 10 required by this security-critical, multi-layer domain):

1. **Least-privilege identity-pool IAM roles** — trust policy must include `cognito-identity.amazonaws.com:aud` (pool ID) and `:amr` (`authenticated`/`unauthenticated`) conditions scoped to `sts:AssumeRoleWithWebIdentity`. No `*` in resource or action.
2. **Enhanced identity-pool flow** (`GetCredentialsForIdentity`) — use this as default so unauthenticated credentials are capped by the scope-down policy. Basic flow only when custom role-selection logic is required.
3. **Passkeys/WebAuthn first; else SRP + MFA** — Essentials/Plus pools: prefer FIDO2 (phishing-resistant). Never store passwords or hashes client-side.
4. **Auth-code + PKCE for public clients** — SPA and mobile use `response_type=code` with PKCE. Generate a fresh random code verifier (≥ 43 chars, URL-safe base64) per authorization request.
5. **Client secrets in confidential/server-side clients only** — store in AWS Secrets Manager; never embed in SPA, mobile bundle, or any frontend code.
6. **WAF web ACL on user-pool endpoints** — attach AWS WAF ACL to Managed login and API endpoints for CAPTCHA/drop filtering against bot and credential-stuffing attacks.
7. **Enable threat protection (Plus tier)** — activate compromised-credential and adaptive-auth detection for any public-facing CIAM pool.
8. **Enable `PreventUserExistenceErrors` + case sensitivity guards** — return generic errors on sign-in failure; enforce consistent case policies to prevent user enumeration.
9. **Enable deletion protection on production user pools** — `DeletionProtection: ACTIVE` prevents accidental pool destruction.
10. **Validate JWTs client-side against JWKS** — fetch `/.well-known/jwks.json` and cache it; do not call the API per request (50,000 RPS jwks.json limit still applies). Minimize token validity and scopes; revoke refresh tokens on sign-out via `RevokeToken`/global sign-out.

### ⚠️ Ask First

Full decision matrices with trade-off tables: [Ask First Decisions](./blueprints/ask-first-decisions.md).

**Decision points** (5 required for this multi-concern domain):

1. **Self-service sign-up** — public B2C app (enable) vs internal/corporate app (disable with `AdminCreateUserConfig.AllowAdminCreateUserOnly = true`; public sign-up = anyone on the internet can register).
2. **Identity-pool guest access** — only if pre-authentication AWS resource access is explicitly required; otherwise deactivate (any caller with the non-secret pool ID gets unauthenticated AWS credentials).
3. **Social IdPs (Google, Facebook, Apple, Amazon)** — public-facing apps only; keep social (uncontrolled, public account creation) separate from enterprise (SAML/OIDC, controlled) trust boundaries.
4. **Basic vs enhanced identity-pool flow** — enhanced (default, recommended) vs basic (only when the application requires custom client-side role selection logic).
5. **Refresh-token lifetime** — up to 3,650 days is technically valid; shorter = lower session-hijack blast radius; longer = better UX. Define the policy and always pair with `RevokeToken` on sign-out.

### 🚫 Never Do

Full anti-patterns with ❌ wrong / ✅ correct code: [Never Do Patterns](./blueprints/never-do-patterns.md).

**Prohibited patterns** (7 required for this security-critical domain):

1. **Embed client secret in SPA/mobile** — use a public app client with PKCE instead; secrets in frontend code are extracted trivially from the JS bundle.
2. **Store ID/access tokens in browser `localStorage`** — use in-memory storage (browser) or encrypted server-side cache; localStorage is readable by any XSS payload.
3. **Grant broad `*` IAM role to identity-pool users** — use least-privilege, resource-scoped policies with `${cognito-identity.amazonaws.com:sub}` path conditions.
4. **Enable guest access without explicit scoped policy** — leave deactivated; fetch resources only post-authentication. Every unauthenticated caller with the pool ID gets AWS credentials.
5. **Static or predictable PKCE code verifier** — generate a fresh cryptographically random verifier per request; static verifiers nullify PKCE's CSRF protection.
6. **Mix internal developer-authenticated and external SSO providers in one identity pool** — separate by trust boundary into distinct identity pools.
7. **Poll `AdminGetUser`/`GetUser` for attributes on every request** — read validated claims from the JWT (cached after JWKS validation); use an external DB for high-churn custom attributes. API polling hits the `UserRead` quota (120 RPS default).

---

## Integration Patterns

Full examples with code and configuration: [Integration Patterns](./blueprints/integration-patterns.md).

**Supported integrations**:
- **Cognito ↔ API Gateway REST** — `COGNITO_USER_POOLS` authorizer; ID token for identity claims; access token for custom OAuth2 scopes via resource servers.
- **Cognito ↔ API Gateway HTTP API** — native JWT authorizer (issuer/audience/scopes); confirm issuer/audience/scope specifics against the HTTP-API JWT-authorizer docs **[unverified in research]**.
- **Cognito ↔ Lambda triggers** — pre-token-gen (add/modify/suppress claims), custom-auth challenge, migration trigger, custom SMS/email sender.
- **Cognito ↔ M2M token caching** — API Gateway caching proxy in front of `/oauth2/token`; cache key = `scope` + `Authorization`; cache TTL must be shorter than access-token lifetime.
- **Multi-tenant SaaS** — pool-per-tenant (highest isolation) vs app-client-per-tenant vs group-per-tenant; isolation model drives quota planning.

**Common problems**:
- **Cross-tenant SSO leakage via Managed login** — Managed login session cookie (fixed 1-hour) authenticates a user across all app clients in the same pool. Fix: one pool per tenant or use API-based sign-in (not hosted UI/Managed login).
- **M2M `ClientAuthentication` throttle (150 RPS, non-adjustable)** — cache access tokens; cache TTL < token lifetime to avoid using stale credentials.
- **`ThrottleException` on `UserAuthentication` (default 120 RPS)** — implement exponential backoff + SDK retry configuration; raise the quota via Service Quotas for high-traffic pools.

---

## Verification Loop

Run after any Cognito configuration change and before promoting to production.

### 1. Check pool deletion protection
```bash
aws cognito-idp describe-user-pool --user-pool-id <POOL_ID> \
  --query 'UserPool.DeletionProtection'
# Expected: "ACTIVE"
```

### 2. Verify feature plan (Essentials or Plus for passkeys/Managed-login)
```bash
aws cognito-idp describe-user-pool --user-pool-id <POOL_ID> \
  --query 'UserPool.UserPoolTier'
# Expected: "ESSENTIALS" or "PLUS"
```

### 3. Validate JWKS endpoint is reachable and well-formed
```bash
curl -s "https://cognito-idp.<REGION>.amazonaws.com/<POOL_ID>/.well-known/jwks.json" \
  | python3 -m json.tool | grep '"keys"'
# Expected: "keys": [...]
```

### 4. Confirm WAF attachment
```bash
aws cognito-idp get-web-acl-for-resource \
  --resource-arn arn:aws:cognito-idp:<REGION>:<ACCOUNT>:userpool/<POOL_ID>
# Expected: response contains a populated "WebACLArn" field
```

**Troubleshooting**:
- `InvalidParameterException: UserPoolTier` → pool pre-dates feature-plan model; upgrade via `update-user-pool --user-pool-tier ESSENTIALS`.
- JWT `NotAuthorizedException` during validation → verify the `iss` claim equals `https://cognito-idp.<REGION>.amazonaws.com/<POOL_ID>`.
- WAF returns empty → attach via `aws cognito-idp associate-web-acl --user-pool-arn <ARN> --web-acl-arn <WAF_ARN>`.

---

## Quick Reference

**Feature-plan matrix**:

| Feature | Lite | Essentials | Plus |
|---|---|---|---|
| Classic hosted UI | Yes | Yes | Yes |
| Managed login | No | Yes | Yes |
| Passkeys / WebAuthn (FIDO2) | No | Yes | Yes |
| Email MFA / passwordless OTP | No | Yes | Yes |
| Access-token customization | No | Yes | Yes |
| Threat protection (adaptive auth) | No | No | Yes |

**Token validity ranges** (configurable within these bounds):

| Token | Minimum | Maximum |
|---|---|---|
| ID token | 5 minutes | 1 day |
| Access token | 5 minutes | 1 day |
| Refresh token | 1 hour | 3,650 days |
| Managed login session cookie | 1 hour (fixed) | — |

**Key hard limits** (non-adjustable unless noted):

| Resource | Default | Adjustable max |
|---|---|---|
| User pools / Region | 1,000 | 10,000 |
| App clients / pool | 1,000 | 10,000 |
| Custom attributes / pool | 50 | 50 (hard) |
| Groups / pool | 10,000 | 10,000 (hard) |
| Groups per user | 100 | 100 (hard) |
| Passkey authenticators / user | 20 | 20 (hard) |
| RBAC rules / identity pool | 25 | 25 (hard) |
| `ClientAuthentication` RPS (M2M) | 150 | 150 (hard) |
| `UserAuthentication` RPS | 120 | Yes (Service Quotas) |
| Default email sends / day | 50 | Use SES for more |

---

## External Resources

### Amazon Cognito Developer Guide (all verified 2026-07-31)
- [User pools overview](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-identity-pools.html)
- [Identity pools overview](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-identity.html)
- [Feature plans (Lite / Essentials / Plus)](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-sign-in-feature-plans.html)
- [User pool JWTs](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-with-identity-providers.html)
- [Token expiration and caching](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-caching-tokens.html)
- [User pool security best practices](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-security-best-practices.html)
- [Identity pool security best practices](https://docs.aws.amazon.com/cognito/latest/developerguide/identity-pools-security-best-practices.html)
- [Multi-tenant application best practices](https://docs.aws.amazon.com/cognito/latest/developerguide/multi-tenant-application-best-practices.html)
- [Quotas in Amazon Cognito](https://docs.aws.amazon.com/cognito/latest/developerguide/quotas.html)

### API Gateway Integration (verified 2026-07-31)
- [REST API — Cognito authorizer](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-integrate-with-cognito.html)

### Research Bibliography
- [research_aws-cognito_v1.md](../../../StoryBeat/docs/research_aws-cognito_v1.md) — source research generated 2026-07-31

### Unverified items (fetch official sources before asserting in code)
- API Gateway HTTP API JWT authorizer: issuer/audience/scope specifics
- AppSync + Cognito user-pool authorization mode
- ALB OIDC authentication with Cognito
- AWS Well-Architected Security pillar exact identity-management mapping
