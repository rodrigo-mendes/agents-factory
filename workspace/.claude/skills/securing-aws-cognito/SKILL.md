---
name: securing-aws-cognito
description: "Architects and audits AWS Cognito CIAM security for user pools and identity pools following AWS Well-Architected Security pillar. Use when designing multi-tenant SaaS identity, configuring feature tiers (Lite/Essentials/Plus), securing JWT validation, enabling MFA/passkeys, or applying threat protection with the 2026 tier model."
---

## Function

Specialist in AWS Cognito Security Architecture (CIAM) for AWS Cognito 2026 — covering the feature-tier model (Lite / Essentials / Plus), user pools, identity pools, multi-tenant isolation strategies, JWT validation, MFA/passkeys, threat protection, and WAF integration for B2B/B2C SaaS.

## Version Context

**Technology**: Amazon Cognito
**Target version**: AWS Cognito 2026 (feature-tier model)
**Tier model effective**: December 1, 2024 (announced November 22, 2024)
**GovCloud support**: Feature tiers and passwordless GA in March 2025
**Support status**: Active
**Currency threshold**: Review after 2027-08-26 — Cognito ships features frequently

**Critical changes in this version**:
- **Feature tiers replace the legacy pricing/feature model**: Lite / Essentials / Plus per user pool
- **Essentials is the default tier** for newly created user pools
- Security capabilities (Managed Login v2, passwordless/passkeys, access-token customization, threat protection) are **tier-gated** — not just price-gated
- **Threat protection** (adaptive auth, compromised-credentials detection, IP allow/deny, log export) requires **Plus**
- Pre Token Generation trigger **V2_0** (user auth) and **V3_0** (M2M client-credentials) require **Essentials/Plus**

**Deprecated / renamed**:
- "Advanced Security Features (ASF)" → now called "Threat Protection" (Plus tier)
- "Hosted UI (classic)" → replaced by "Managed Login v2" on Essentials/Plus (classic still exists but is distinct)

> CRITICAL — Agent Warning:
> This skill targets the 2026 Cognito feature-tier model (Essentials default).
> Reject patterns written for the pre-December-2024 model that treat Advanced Security Features as a separate add-on.
> Validate tier before recommending any security capability — Lite silently omits Managed Login v2, passwordless, and threat protection.

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)** — ✅ Always Do / ⚠️ Ask First / 🚫 Never Do
- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — 9 mandatory patterns with verification commands
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — 5 architectural decisions with tradeoff matrices
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — 8 anti-patterns with wrong/correct pairs
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 6 test cases
- **[Verification Loop](#verification-loop)** — CLI checks for Cognito configuration
- **[Quick Reference](#quick-reference)** — Critical limits, tier capabilities, and key CLI commands
- **[External Resources](#external-resources)** — Official AWS documentation (accessed 2026-08-26)

---

## Blueprints & Guardrails

### ✅ Always Do

For full verification commands and implementation notes, see [Always Do Patterns](./blueprints/always-do-patterns.md).

- **Full server-side JWT validation on every request** — Verify signature against user pool JWKS + `iss`, `aud`/`client_id`, `exp`, and `token_use`. Decoding without signature verification is not validation; it enables token forgery and cross-token-type misuse. Use API Gateway Cognito authorizer or `aws-jwt-verify`; never hand-rolled base64 decode.
- **Authorization Code grant + PKCE for public clients** — SPA/mobile must use public app client (no secret) + `code` grant + PKCE. Disable the implicit grant on every app client. Confidential (server) clients use a secret.
- **Enable MFA and prefer TOTP or passkeys over SMS** — Set MFA to Required (or risk-based via adaptive auth on Plus). SMS is the weakest factor; treat it as fallback only. Passkeys (FIDO2/WebAuthn) require Essentials/Plus + Managed Login v2.
- **Enable PreventUserExistenceErrors on every app client** — Prevents username enumeration via sign-in/reset error messages. Set `PreventUserExistenceErrors: ENABLED` explicitly; legacy clients may have it off.
- **Attach an AWS WAF web ACL to internet-facing user pools** — Rate-based rules + CAPTCHA on Managed Login and Cognito API endpoints. Protects auth throughput and billing from credential stuffing and abuse.
- **Keep token lifetimes short and secure tokens in transit/storage** — Short access/ID token validity (organization-policy-dependent; official docs mandate "short" without mandating a fixed number). HTTPS only; avoid localStorage for high-risk apps.
- **Apply least privilege to identity-pool IAM roles; disable guest access unless required** — Identity pools issue real AWS STS credentials. Scope roles to minimum; use `${cognito-identity.amazonaws.com:sub}` policy variables for per-user resource isolation.
- **Enable deletion protection on all production user pools** — User-pool deletion is unrecoverable. Set `DeletionProtection: ACTIVE`; manage via IaC with change control.
- **On Plus tier, enable threat protection in audit-only mode first, then full-function** — Audit-only lets you tune automatic responses before enforcement to avoid locking out legitimate users. Export logs to CloudWatch/S3/Firehose for SIEM.

### ⚠️ Ask First

For full decision matrices with options and tradeoffs, see [Ask First Decisions](./blueprints/ask-first-decisions.md).

- **Feature tier per user pool (Lite vs Essentials vs Plus)** — Ask what security capabilities (passwordless, threat protection) and compliance posture the app requires before accepting the Essentials default. Over-provisioning Plus on low-risk pools wastes spend; under-provisioning Lite on high-risk pools loses security controls.
- **Multi-tenant isolation model** — Ask how many tenants, whether tenants need distinct IdPs/branding, and the required isolation strength. Options: user-pool-per-tenant (silo, max 1,000 pools/account hard limit), app-client-per-tenant, user-group-per-tenant, custom-attribute-per-tenant. Default to shared pool + app-client or custom attribute unless strong isolation is mandated.
- **User pool only vs user pool + identity pool** — Ask whether any client needs to call AWS services directly. If the client only calls your own backend API, do not add an identity pool; adding one without need increases IAM complexity and blast radius.
- **Access-token authorization design (groups/roles/scopes via Pre Token Generation V2_0/V3_0)** — Ask whether the API needs tenant_id/roles inside the access token. If yes, confirm the pool is Essentials/Plus; use V2_0 for user auth and V3_0 for M2M client-credentials. Keep injected claims minimal to bound token size.
- **Passwordless / passkey adoption (Essentials/Plus)** — Ask about target-user device capability and phishing-resistance requirements. Prefer passkeys (FIDO2/WebAuthn) where devices support them; email OTP is a middle ground; treat SMS OTP as the weakest passwordless option. Max 20 passkeys per account.

### 🚫 Never Do

For full wrong/correct code pairs and detection commands, see [Never Do Patterns](./blueprints/never-do-patterns.md).

| Anti-Pattern | Risk | Correct Alternative |
|---|---|---|
| Decode JWT without full validation (`iss`/`aud`/`exp`/`token_use`/signature) | CRITICAL — token forgery, privilege escalation | API Gateway Cognito authorizer or `aws-jwt-verify` with all claim checks |
| Enable the Implicit grant on any app client | HIGH — tokens leaked via URL fragments | Disable Implicit; use Authorization Code + PKCE |
| Embed a client secret in a browser/mobile app | HIGH — secret is extractable | Public app client with no secret + PKCE |
| Production user pool with MFA off (or SMS as sole factor) | HIGH — stolen password = full access | MFA Required with TOTP or passkeys; SMS as fallback |
| Internet-facing pool with no WAF and Lite tier (no threat protection) | HIGH — credential stuffing, cost abuse | WAF web ACL with rate-based rules + Plus tier threat protection |
| `PreventUserExistenceErrors` disabled on app client | MEDIUM — username enumeration | Set `ENABLED` on all production app clients |
| Over-permissive identity-pool roles (`Action: "*"` / `Resource: "*"`) or unnecessary guest access | HIGH — STS credentials = broad AWS access | Least-privilege roles + `${cognito-identity.amazonaws.com:sub}` policy variables |
| One user pool per tenant as the default (silo) scaling strategy | MEDIUM — 1,000 pools/account hard limit | Shared pool + app-client/group/attribute tenancy; cell-based architecture for massive scale |
| Production pool with `DeletionProtection: INACTIVE` | MEDIUM — unrecoverable user-directory loss | `DeletionProtection: ACTIVE`, managed via IaC |

---

## Integration Patterns

For full architecture composition details, see [Ask First Decisions](./blueprints/ask-first-decisions.md).

**Key service integrations for multi-tenant SaaS on Cognito (Essentials/Plus):**

| Layer | AWS Service | Integration Role |
|---|---|---|
| Auth UI | Cognito Managed Login v2 (Essentials/Plus) | Hosted OAuth code+PKCE, passkey ceremony |
| Federation | SAML 2.0 / OIDC external IdPs | Enterprise tenant SSO |
| Token enrichment | Pre Token Generation Lambda V2_0/V3_0 | Inject `tenant_id`/roles into access token |
| API auth | API Gateway Cognito authorizer | Full JWT validation (sig/iss/aud/exp/token_use) |
| AWS authz (optional) | Cognito identity pool + IAM/STS | Per-user scoped AWS credentials for direct-to-cloud access |
| Edge protection | AWS WAF web ACL | Rate-based rules + CAPTCHA on auth endpoints |
| Threat detection | Threat protection + CloudTrail | Adaptive auth, compromised-credentials, log export |
| Observability | CloudWatch / S3 / Data Firehose | Threat logs and control-plane audit |

**Common integration problems:**
- **ID token used where access token is required** → Use `token_use` check in authorizer; reject mismatched token type
- **JWKS key rotation breaks validation** → Cache JWKS but honor rotation; libraries like `aws-jwt-verify` handle this automatically
- **Pre-Token-Gen trigger using V1_0 for access-token claims** → V1_0 customizes ID tokens only; upgrade to V2_0/V3_0 (requires Essentials/Plus)
- **Tenant isolation silently broken after pool limit reached** → Monitor pool count vs 1,000/account ceiling; plan shard strategy early

---

## Verification Loop

The agent MUST execute these checks after each Cognito configuration or code generation:

### 1. JWT Validation Check
```bash
# Confirm authorizer or library performs full validation
aws apigateway get-authorizer --rest-api-id <api-id> --authorizer-id <auth-id> \
  --query '{type:type,identitySource:identitySource}'
# Expected: type=COGNITO_USER_POOLS, identitySource=$request.header.Authorization
```

### 2. App Client Security Settings
```bash
# Verify no implicit grant, client secret on public clients, and user-existence errors blocked
aws cognito-idp describe-user-pool-client \
  --user-pool-id <pool-id> --client-id <client-id> \
  --query 'UserPoolClient.{AllowedOAuthFlows:AllowedOAuthFlows,ClientSecret:ClientSecret,PreventUserExistenceErrors:PreventUserExistenceErrors}'
# Expected: AllowedOAuthFlows=["code"], ClientSecret=null (public clients), PreventUserExistenceErrors=ENABLED
```

### 3. MFA and Deletion Protection
```bash
aws cognito-idp describe-user-pool --user-pool-id <pool-id> \
  --query 'UserPool.{MfaConfiguration:MfaConfiguration,DeletionProtection:DeletionProtection}'
# Expected: MfaConfiguration=ON or OPTIONAL (with adaptive), DeletionProtection=ACTIVE
```

### 4. WAF Association
```bash
aws cognito-idp get-web-acl-for-resource \
  --resource-arn arn:aws:cognito-idp:<region>:<account>:userpool/<pool-id>
# Expected: WebACL ARN present
```

### 5. Identity Pool Role Scope
```bash
aws cognito-identity describe-identity-pool --identity-pool-id <id> \
  --query '{AllowUnauthenticated:AllowUnauthenticatedIdentities}'
# Expected: AllowUnauthenticatedIdentities=false (unless guest is required and deliberate)
```

**Troubleshooting:**
- `InvalidParameterException` on V2_0/V3_0 trigger → Pool must be Essentials or Plus
- JWKS fetch fails → Confirm `iss` URL format: `https://cognito-idp.<region>.amazonaws.com/<poolId>`
- Token from one pool accepted by another pool's authorizer → Confirm `iss` and `aud` checks are enforced, not just signature

---

## Quick Reference

**Critical hard limits:**

| Resource | Limit | Scope |
|---|---|---|
| User pools per account | **1,000** | Per AWS account/region — hard limit, not soft |
| Passkeys per account | 20 | Per Cognito user account (Essentials/Plus) |
| Feature tier switching | Switchable | Per pool, no user migration required |

**Tier capability gate:**

| Capability | Lite | Essentials | Plus |
|---|---|---|---|
| Password + social + SAML/OIDC | Yes | Yes | Yes |
| Managed Login v2 + passkeys/FIDO2 | No | Yes | Yes |
| Access-token customization (Pre-Token-Gen V2_0/V3_0) | No | Yes | Yes |
| Password-reuse prevention | No | Yes | Yes |
| Threat protection (adaptive auth, compromised-credentials, IP rules) | No | No | Yes |

**Default tier for new pools**: Essentials

**Key token claims to validate (mandatory):**
- `iss` — must match `https://cognito-idp.<region>.amazonaws.com/<poolId>`
- `aud` (ID token) or `client_id` (access token)
- `exp` — must be in the future
- `token_use` — must be `"id"` or `"access"` per endpoint expectation
- Signature — verified against pool JWKS endpoint

---

## Blueprints Directory Structure

```
StoryBeat/.claude/skills/securing-aws-cognito/
├── SKILL.md                              <- This file (summaries + guardrails)
└── blueprints/
    ├── always-do-patterns.md             <- 9 mandatory patterns with CLI verification
    ├── ask-first-decisions.md            <- 5 decision matrices with tradeoff tables
    ├── never-do-patterns.md              <- 8 anti-patterns with wrong/correct pairs
    └── evaluation-scenarios.md          <- 6 evaluation test cases
```

---

## External Resources

### Official AWS Documentation (accessed 2026-08-26)

- [Amazon Cognito Developer Guide](https://docs.aws.amazon.com/cognito/latest/developerguide/) — root reference
- [Security best practices — user pools](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-security-best-practices.html) — primary security reference
- [Security best practices — identity pools](https://docs.aws.amazon.com/cognito/latest/developerguide/identity-pools-security-best-practices.html)
- [Verifying a JSON Web Token](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html) — mandatory JWT validation steps
- [Threat protection](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pool-settings-advanced-security-threat-protection.html) — Plus tier, adaptive auth, log export
- [Multi-tenant application best practices](https://docs.aws.amazon.com/cognito/latest/developerguide/multi-tenant-application-best-practices.html) — four isolation strategies
- [Pre token generation Lambda trigger](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-pre-token-generation.html) — V2_0/V3_0 access-token customization
- [Amazon Cognito pricing](https://aws.amazon.com/cognito/pricing/) — Lite/Essentials/Plus MAU billing
- [What's New — Feature tiers (2024-11-22)](https://aws.amazon.com/about-aws/whats-new/2024/11/new-feature-tiers-essentials-plus-amazon-cognito) — tier model introduction
- [What's New — Passwordless auth (2024-11)](https://aws.amazon.com/about-aws/whats-new/2024/11/amazon-cognito-passwordless-authentication-low-friction-secure-logins) — passkeys/FIDO2 GA
- [AWS Well-Architected Security Pillar](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html) — framework alignment

### Unresolved Items (require human verification)
- **Native multi-region user-pool failover**: Not confirmed in official docs. Cognito is a regional service. Cross-region DR requires a custom design — validate RTO/RPO requirements with AWS before committing.
