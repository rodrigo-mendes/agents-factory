# Ask First Decisions — securing-aws-cognito

5 architectural crossroads. Present the tradeoff matrix and wait for the architect's decision before recommending a path.

---

## Decision 1: Feature tier per user pool (Lite vs Essentials vs Plus)

**Context**: Tier is a per-pool, switchable decision. Tier choice gates security capabilities — not just price.

| Tier | Default? | MAU Billing | Capabilities Gained | Capabilities Lost vs Higher Tier |
|------|----------|-------------|---------------------|----------------------------------|
| Lite | No (pre-Dec-2024 default) | Tiered MAU | Password auth, social/SAML/OIDC federation | No Managed Login v2, no passwordless, no access-token customization, no threat protection |
| Essentials | **Yes (new pools)** | Fixed MAU | + Managed Login v2, passkeys/FIDO2, Pre-Token-Gen V2_0/V3_0, password-reuse prevention | No threat protection (adaptive auth, compromised-credentials, IP rules) |
| Plus | No | Fixed MAU (higher) | + Threat protection (adaptive auth, compromised-credentials detection, IP allow/deny, log export) | Highest per-MAU cost |

**Cost profile**: Free tier exists for Lite and Essentials. Plus > Essentials > Lite at scale.

**Questions to ask**:
1. Does this app require passwordless/passkeys or Managed Login v2? → Requires Essentials or Plus
2. Does this app require risk-based adaptive auth or compromised-credentials detection? → Requires Plus
3. Is this app regulated (healthcare, finance)? → Strong signal for Plus
4. What is the risk profile of users authenticating? → Low-risk internal tools may be fine on Essentials

**Lock-in**: Tier is switchable per pool without user migration.

**Source**: https://aws.amazon.com/cognito/pricing/ ; https://aws.amazon.com/about-aws/whats-new/2024/11/new-feature-tiers-essentials-plus-amazon-cognito (accessed 2026-08-26)

---

## Decision 2: Multi-tenant isolation model

**Context**: Four AWS-documented strategies with different isolation strength, operational cost, and scaling ceiling.

| Model | How | Isolation | Max Tenants | Ops Cost | Best When |
|-------|-----|-----------|-------------|----------|-----------|
| User pool per tenant (silo) | 1 pool per tenant | Maximum (pool-level config, per-tenant MFA/IdP/branding) | ~1,000 (hard account limit) | Very high (automation required) | Few (<50), high-value tenants requiring full isolation |
| App client per tenant | 1 app client per tenant, shared pool | Per-tenant IdP/branding + shared pool config | Thousands (app-client limit is much higher) | Moderate | Many tenants needing per-tenant federation |
| User group per tenant | Cognito groups, shared pool | Group claim in token; IAM role mapping | Scales with group limits | Low | Simpler apps, moderate tenant count, group-based RBAC |
| Custom attribute per tenant | `custom:tenantId` on user, shared pool | App-enforced only | Scales with user count | Lowest | Uniform tenants; strongest app-side enforcement needed |

**Hard limit warning**: 1,000 user pools per AWS account — silo strategy hits a scaling wall. For massive scale (thousands of tenants), AWS guidance is cell-based architecture (sharding across multiple accounts).

**Questions to ask**:
1. How many tenants now, and what is the growth projection?
2. Do tenants need their own IdP (SAML/OIDC federation)?
3. Do tenants need distinct branding on the hosted login UI?
4. What is the required isolation strength (compliance, contractual, or preference)?

**Source**: https://docs.aws.amazon.com/cognito/latest/developerguide/multi-tenant-application-best-practices.html (accessed 2026-08-26)

---

## Decision 3: User pool only vs user pool + identity pool

**Context**: Many architectures only need a user pool. Adding an identity pool without a clear need increases IAM complexity and blast radius.

| Approach | When to Use | Tradeoff |
|----------|-------------|----------|
| User pool only | Client calls only your own backend API (Lambda, REST, GraphQL) | Simpler; JWT validated at API layer |
| User pool + identity pool | Client must call AWS services (S3, DynamoDB, Kinesis, etc.) directly | Per-user scoped STS credentials; higher IAM complexity; increased blast radius if roles are over-scoped |

**Question to ask**: Does any client (mobile, SPA, backend) need to call AWS services directly without going through your own API?

If yes — add identity pool; enforce least-privilege roles + `${cognito-identity.amazonaws.com:sub}` policy variables.
If no — user pool only.

**Source**: https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-scenarios.html ; https://repost.aws/knowledge-center/cognito-user-pools-identity-pools (accessed 2026-08-26)

---

## Decision 4: Access-token authorization design (Pre Token Generation V2_0 / V3_0)

**Context**: APIs that need tenant_id, roles, or custom scopes inside the access token require Pre Token Generation Lambda. Requires Essentials or Plus.

| Approach | Trigger | Grants covered | Requires | Use When |
|----------|---------|----------------|----------|----------|
| Static resource server scopes | None | All | Any tier | Simple permission model; standard OAuth scopes sufficient |
| Custom access-token claims via Lambda | Pre-Token-Gen V2_0 | User auth (Authorization Code, etc.) | Essentials/Plus | API needs tenant_id/roles in access token |
| M2M client-credentials customization | Pre-Token-Gen V3_0 | Client-credentials + user auth | Essentials/Plus | Service-to-service (M2M) with custom access-token claims |

**Questions to ask**:
1. Does the API authorization model require tenant_id or custom roles inside the access token?
2. Is the pool on Essentials or Plus? (V1_0 customizes ID tokens only; V2_0/V3_0 for access tokens)
3. Are there M2M (service-to-service) clients using client-credentials grant? → V3_0 required
4. Keep injected claims minimal — token size grows with each claim

**Source**: https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-pre-token-generation.html (accessed 2026-08-26)

---

## Decision 5: Passwordless / passkey adoption (Essentials/Plus only)

**Context**: Essentials/Plus unlock Managed Login v2 which implements passkey (FIDO2/WebAuthn) ceremonies natively. The right choice depends on user device capability and phishing-resistance requirements.

| Option | Phishing resistance | User friction | Device requirement | Tier |
|--------|-------------------|---------------|-------------------|------|
| Passkeys (FIDO2/WebAuthn) | Highest (hardware-bound) | Low (biometric/PIN) | Platform authenticator or security key | Essentials/Plus |
| Email OTP | Medium (link-based) | Medium (check email) | Email access | Essentials/Plus |
| SMS OTP | Lowest (SIM-swap vulnerable) | Medium (check SMS) | Phone | Essentials/Plus |
| Password + TOTP MFA | Medium-high | Medium-high | Authenticator app | Any tier |

**Limit**: Up to 20 passkeys per Cognito user account.

**Questions to ask**:
1. Do target users have devices with platform authenticators (Touch ID, Face ID, Windows Hello)?
2. What is the phishing-resistance requirement (regulated industry, high-value accounts)?
3. Is SMS OTP acceptable as a fallback, or does compliance prohibit it?

**Source**: https://aws.amazon.com/about-aws/whats-new/2024/11/amazon-cognito-passwordless-authentication-low-friction-secure-logins (accessed 2026-08-26)
