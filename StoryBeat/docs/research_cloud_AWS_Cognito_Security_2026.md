# AWS Cognito — Security Architecture (AWS Cognito 2026)

> Anti-hallucination research base. Every pattern is sourced to official AWS documentation with an
> access date. Items that could not be confirmed against an official source are tagged
> `⚠️ unverified` or `⚠️ IRRESOLVABLE`. Do not treat this file as legal or compliance advice.

## Metadata

```yaml
Full_Name: "AWS Amazon Cognito — Security Architecture"
Cloud_Provider: "AWS"
Architecture_Domain: "Security Architecture - Cognito (CIAM / identity)"
Target_Edition: "AWS Cognito 2026 (feature-tier model: Lite / Essentials / Plus)"
Architecture_Context: "B2B/B2C SaaS with multi-tenant requirements (assumed — not supplied in ARGUMENTS)"
Official_Source_URL: "https://docs.aws.amazon.com/cognito/latest/developerguide/"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-08-26"
Research_Depth: "exhaustive"
Currency_Threshold: "2027-08-26 — review after this date; Cognito ships features frequently"
```

> ⚠️ **Scope assumption.** `ARCHITECTURE_CONTEXT` was not provided in `$ARGUMENTS`. This research
> assumes a **B2B/B2C SaaS, multi-tenant** context. If the target is instead a single-tenant
> internal app, workforce SSO, or a machine-to-machine (M2M) API platform, the multi-tenancy and
> adaptive-authentication sections should be re-scoped. **Ask the architect to confirm context**
> before generating a SKILL from this base.

> ⚠️ **Compliance note (Ask-First).** SOC 2 / HIPAA / PCI-DSS / GDPR control mappings below are
> structural only, tied to the AWS Well-Architected Security pillar. They are **not** a certification
> statement. Confirm the organization's certification scope before adding compliance-specific
> constraints.

---

## Executive Summary

Amazon Cognito is AWS's managed customer identity and access management (CIAM) service. It has two
distinct primitives that are frequently conflated: **user pools** (a user directory that handles
**authentication** — sign-up, sign-in, MFA, token issuance via OIDC/OAuth 2.0) and **identity
pools**, formerly "Cognito Federated Identities" (which handle **authorization to AWS services** by
exchanging a token for temporary AWS IAM credentials via STS). A production identity architecture
often uses both: the user pool authenticates the human, the identity pool brokers scoped AWS
credentials. [✓✓ Triangulated | AWS re:Post "user pools vs identity pools" + Cognito scenarios docs]

**What changed in the 2026 edition.** The dominant architectural change is the **feature-tier
pricing/capability model** introduced **November 22, 2024** (effective December 1, 2024): **Lite**,
**Essentials**, and **Plus**. **Essentials is now the default tier for newly created user pools.**
Tier selection is now a first-class architecture decision because it gates *security capabilities*,
not just price: **Managed Login (v2)**, **passwordless authentication** (passkeys/FIDO2, email OTP,
SMS OTP), **access-token customization**, and **password-reuse prevention** require **Essentials or
Plus**; **threat protection** (adaptive/risk-based authentication, compromised-credentials
detection, IP allow/deny lists, and user-activity log export) requires **Plus**. These capabilities
were previously bundled differently (threat protection was the older "Advanced Security Features").
Feature tiers reached AWS GovCloud (US) in **March 2025**. [✓✓ Triangulated | AWS What's New 2024-11-22 + Cognito pricing page]

**Three most critical guardrails for a multi-tenant SaaS context.** (1) **Never disable JWT
validation** — backends must verify signature, `iss`, `aud`/`client_id`, `exp`, and `token_use` on
every request; a token that is merely *decoded* is not *validated*. (2) **Pick the tenant-isolation
model deliberately** — user-pool-per-tenant maxes out at the hard limit of **1,000 user pools per
account** and carries high operational cost; AWS documents four official strategies (user pool,
app-client, user-group, custom-attribute) with different isolation/effort trade-offs. (3) **Enforce
MFA and attach an AWS WAF web ACL to internet-facing user pools** — MFA is the single most effective
control against account takeover, and WAF provides rate-based / CAPTCHA guardrails in front of
Managed Login and the Cognito APIs.

---

## Cloud Architecture Glossary

```
Term: User pool
Definition: A user directory in Cognito providing sign-up/sign-in, an OIDC/OAuth 2.0 IdP, MFA,
  and JWT (ID/access/refresh) issuance. Handles AUTHENTICATION.
Provider Docs Section: Amazon Cognito user pools
Architect Usage: The identity source of truth for app users; issues tokens your app/API validates.
Common Confusion: Confused with identity pools. User pool = authentication; identity pool = AWS authz.
```
```
Term: Identity pool (Cognito Identity / Federated Identities)
Definition: Exchanges a trusted token (from a Cognito user pool, social/SAML/OIDC IdP, or a
  developer-authenticated identity) for temporary, scoped AWS credentials via STS. Handles
  AUTHORIZATION to AWS services. Supports authenticated and guest (unauthenticated) roles.
Provider Docs Section: Amazon Cognito identity pools
Architect Usage: Use when the client must call AWS services (S3, DynamoDB) directly with per-user
  IAM scoping. Not needed if the client only calls your own backend API.
Common Confusion: Assuming every Cognito app needs an identity pool. Many do not.
```
```
Term: Feature plan / tier (Lite | Essentials | Plus)
Definition: Per-user-pool capability + pricing tier. Lite = basic auth (password, social,
  SAML/OIDC), tiered MAU pricing. Essentials = adds Managed Login, passwordless, access-token
  customization, password-reuse prevention; fixed MAU price; DEFAULT for new pools. Plus = adds
  threat protection; fixed MAU price.
Provider Docs Section: Feature plans (developer guide)
Architect Usage: Choose per pool at creation; can switch tiers later. Security features are gated.
Common Confusion: Treating tiers as price-only. They gate security capabilities.
```
```
Term: Managed Login (v2)
Definition: Cognito's hosted, brandable sign-in/sign-up UI. v2 supports passwordless/passkey flows
  without hand-building WebAuthn. Requires Essentials or Plus.
Provider Docs Section: Managed login
Architect Usage: Use to avoid building auth UI + WebAuthn ceremony; supports OAuth 2.0 flows.
Common Confusion: The older "Hosted UI (classic)" is a distinct, older experience.
```
```
Term: Threat protection (formerly Advanced Security Features / ASF)
Definition: Plus-tier feature set: risk-based adaptive authentication, compromised-credentials
  detection, IP allow/deny lists, and export of user-activity/threat logs.
Provider Docs Section: Threat protection
Architect Usage: Enable for elevated-risk apps; run in audit-only first, then full-function.
Common Confusion: Older docs/console call this "Advanced Security Features".
```
```
Term: Adaptive authentication
Definition: Threat-protection component that scores each sign-in for risk (device familiarity,
  location, IP, request data) and can require MFA or block on risk.
Provider Docs Section: Working with adaptive authentication
Architect Usage: Step-up MFA on medium/high risk without forcing MFA on every login.
Common Confusion: Not the same as always-on MFA; it is conditional/risk-based.
```
```
Term: Compromised-credentials detection
Definition: Threat-protection component that flags/blocks sign-ins using credentials found in known
  breach datasets.
Provider Docs Section: Threat protection
Architect Usage: Block sign-up/sign-in/password-change with breached credentials.
Common Confusion: Not the same as password-reuse prevention (an Essentials feature).
```
```
Term: Pre token generation Lambda trigger (V2_0 / V3_0)
Definition: Lambda trigger that customizes token claims. V2_0/V3_0 add ACCESS-token customization
  (claims, scopes, roles, groups); available only in Essentials/Plus. V3_0 also covers M2M
  client-credentials grants.
Provider Docs Section: Pre token generation Lambda trigger
Architect Usage: Inject tenant_id / roles into access tokens for API authorization.
Common Confusion: The classic (V1_0) trigger customizes ID tokens only; access-token customization
  needs Essentials/Plus and V2_0/V3_0.
```
```
Term: PreventUserExistenceErrors
Definition: User-pool app-client setting that returns generic errors so attackers cannot enumerate
  which usernames exist.
Provider Docs Section: Managing error responses / security best practices
Architect Usage: Enable on every production app client.
Common Confusion: Off by default on some legacy clients; must be explicitly set to ENABLED.
```
```
Term: token_use claim
Definition: JWT claim identifying token type ("id" or "access"). Backends must check it to reject
  an ID token used where an access token is required (and vice versa).
Provider Docs Section: Verifying a JSON Web Token
Architect Usage: Part of mandatory server-side validation.
Common Confusion: Skipping token_use lets the wrong token type be accepted.
```
```
Term: App client (with/without secret)
Definition: A configured application entry point to a user pool. Public clients (SPA/mobile) have
  NO secret + PKCE; confidential clients (server) use a secret.
Provider Docs Section: App clients
Architect Usage: Also a multi-tenancy dimension (one app client per tenant).
Common Confusion: Putting a client secret in a browser/mobile app (never do this).
```

---

## Framework Pillars

AWS Well-Architected — Cognito sits primarily under the **Security** pillar, with cross-cuts into
Reliability, Operational Excellence, Cost, and Performance. Mapping below is scoped to
`AWS Cognito 2026`.

```
Pillar: Security (SEC)
Definition (WAF): "The Security pillar encompasses the ability to protect data, systems, and assets
  to take advantage of cloud technologies to improve your security."
Key Design Principles (applied to Cognito): strong identity foundation (least privilege on admin
  ops + STS roles), enable traceability (threat-protection log export, CloudTrail), apply security
  at all layers (WAF + MFA + adaptive auth), protect data in transit/at rest (TLS + token hygiene),
  keep people away from data (federated, token-based access).
Applies To multi-tenant SaaS: MFA + threat protection + per-tenant isolation + tenant-scoped IAM
  roles via identity pool role mapping.
Assessment Questions (SEC identity): "How do you manage identities for people and machines?",
  "How do you manage permissions for people and machines?", "How do you detect and investigate
  security events?"
Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html (accessed 2026-08-26)
```
```
Pillar: Reliability (REL) — cross-cut
Definition (WAF): ability of a workload to perform its intended function correctly and consistently.
Applies To Cognito: deletion protection on user pools; user-pool quotas (e.g., 1,000 pools/account)
  as hard design constraints; Cognito is a regional service — plan for regional resilience.
Source: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/welcome.html (accessed 2026-08-26)
```
```
Pillar: Operational Excellence (OPS) — cross-cut
Applies To Cognito: run threat protection in audit-only before full-function; export logs to
  CloudWatch/S3/Firehose; manage pools/clients as IaC (CloudFormation/CDK/Terraform).
Source: https://docs.aws.amazon.com/wellarchitected/latest/operational-excellence-pillar/welcome.html (accessed 2026-08-26)
```
```
Pillar: Cost Optimization (COST) — cross-cut
Applies To Cognito: tier choice (Lite/Essentials/Plus) is billed per monthly active user (MAU);
  Essentials/Plus use a fixed MAU price, Lite uses tiered MAU pricing. Over-provisioning Plus on
  low-risk pools wastes spend; under-provisioning Lite on high-risk pools loses security controls.
Source: https://aws.amazon.com/cognito/pricing/ (accessed 2026-08-26)
```

---

## Mandatory Patterns

> ✅ Always Do. Every entry cites an official AWS source with access date. `[✓✓ Triangulated]` marks
> patterns confirmed by ≥2 independent official sources (P5).

**Full server-side JWT validation on every request**
- Pillar Alignment: Security (identity foundation)
- Why: Decoding a JWT is not validating it. Backends must verify the **signature** against the pool
  JWKS, and check `iss`, `aud`/`client_id`, `exp`, and `token_use`. Skipping any of these is a
  critical gap that enables token forgery/misuse.
- AWS Services: Cognito user pool (JWKS endpoint), API Gateway Cognito authorizer or app-side
  verification (e.g., `aws-jwt-verify`).
- Architecture Decision: Prefer an API Gateway JWT/Cognito authorizer or a vetted library; never a
  hand-rolled base64 decode. Cache JWKS and honor key rotation.
- Verification: Confirm `token_use`, `iss` (matches `https://cognito-idp.<region>.amazonaws.com/<poolId>`),
  `aud`, and signature checks exist in code / authorizer config.
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html (accessed 2026-08-26)
- [✓✓ Triangulated | Verifying-a-JWT docs + user-pool security best practices docs]

**Use Authorization Code grant + PKCE for public clients (never Implicit)**
- Pillar Alignment: Security
- Why: Implicit grant returns tokens in the URL fragment where they can be intercepted/logged.
  Auth code + PKCE keeps tokens out of the URL and binds the exchange to the client.
- AWS Services: Cognito user pool app client (public, no secret), Managed Login.
- Architecture Decision: SPA/mobile = public client, no secret, PKCE. Server = confidential client
  with secret. Disable the implicit grant on the app client.
- Verification: App client OAuth settings list `code` grant only; no client secret in browser/mobile.
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-security-best-practices.html (accessed 2026-08-26)
- [✓✓ Triangulated | user-pool security best practices docs + JWT/token docs]

**Enable MFA (prefer TOTP/passkeys over SMS) and enforce it in production**
- Pillar Alignment: Security
- Why: MFA is documented as the single most effective control against account takeover; without it
  a stolen password fully compromises the account. SMS is the weakest factor (SIM-swap/interception).
- AWS Services: Cognito user pool MFA (TOTP, SMS), passwordless passkeys (FIDO2/WebAuthn) on
  Essentials/Plus.
- Architecture Decision: Set MFA to "Required" (or risk-based via adaptive auth on Plus). Prefer
  TOTP or passkeys; treat SMS as fallback only.
- Verification: User pool MFA configuration = ON/Required; app supports TOTP/passkey enrollment.
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-security-best-practices.html (accessed 2026-08-26)
- [✓✓ Triangulated | user-pool security best practices + passwordless What's New 2024-11]

**Enable PreventUserExistenceErrors on every app client**
- Pillar Alignment: Security
- Why: Prevents username/account enumeration during sign-in, reset, and confirmation flows.
- AWS Services: Cognito user pool app client setting.
- Architecture Decision: Set to `ENABLED` on all production app clients (default is not guaranteed
  on legacy clients).
- Verification: `aws cognito-idp describe-user-pool-client` → `PreventUserExistenceErrors: ENABLED`.
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-security-best-practices.html (accessed 2026-08-26)

**Attach an AWS WAF web ACL to internet-facing user pools**
- Pillar Alignment: Security (defense at all layers), Cost/Reliability (protects auth throughput)
- Why: WAF web ACLs put rate-based rules and CAPTCHA in front of Managed Login and Cognito API
  requests, dropping abusive traffic before it hits (and bills) authentication.
- AWS Services: AWS WAF + Cognito user pool association.
- Architecture Decision: Rate-based rules on sign-in/sign-up endpoints; CAPTCHA/challenge on
  suspicious patterns; combine with threat protection (Plus) for risk scoring.
- Verification: User pool shows an associated WAF web ACL; rules include rate-based limits.
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-security-best-practices.html (accessed 2026-08-26)
- [✓✓ Triangulated | user-pool security best practices docs + AWS security guidance]

**Keep token lifetimes short; secure tokens in transit and storage**
- Pillar Alignment: Security
- Why: Tokens can carry PII and security-model info; long lifetimes widen the compromise window.
- AWS Services: Cognito app client token validity settings; refresh-token rotation.
- Architecture Decision: Short access/ID token validity (commonly ≤ 1 hour), longer but bounded
  refresh tokens; store tokens securely (never in localStorage for high-risk apps); use HTTPS only.
  > ⚠️ The specific "1 hour access / 7 day refresh" figures appear in secondary guidance; the
  > official docs mandate *short* validity and secure handling but the exact numbers are
  > organization/policy-dependent — treat concrete numbers as a tunable default, not a hard rule.
- Verification: App client `AccessTokenValidity`/`IdTokenValidity`/`RefreshTokenValidity` reviewed;
  refresh-token rotation considered.
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-with-identity-providers.html (accessed 2026-08-26)

**Apply least privilege to identity-pool IAM roles and admin operations**
- Pillar Alignment: Security
- Why: Identity pools hand out real AWS credentials via STS; over-scoped roles turn one auth into
  broad AWS access. Guard admin (`AdminInitiateAuth`, user CRUD) APIs too.
- AWS Services: Cognito identity pool (authenticated/unauthenticated roles), IAM, STS, role mapping.
- Architecture Decision: Scope roles to the minimum; use role mapping / `${cognito-identity.amazonaws.com:sub}`
  policy variables for per-user resource isolation; disable guest access unless required.
- Verification: Review authenticated/guest role policies; no wildcard `*` on sensitive resources.
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/identity-pools-security-best-practices.html (accessed 2026-08-26)
- [✓✓ Triangulated | identity-pools security best practices + user-pools security best practices]

**Enable deletion protection on production user pools**
- Pillar Alignment: Reliability / Security
- Why: Prevents accidental/malicious deletion of the entire user directory (unrecoverable).
- AWS Services: Cognito user pool `DeletionProtection`.
- Architecture Decision: Set `DeletionProtection: ACTIVE` on all non-throwaway pools; manage via IaC.
- Verification: `aws cognito-idp describe-user-pool` → `DeletionProtection: ACTIVE`.
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-security-best-practices.html (accessed 2026-08-26)

**On Plus tier, enable threat protection (audit-only first, then full-function)**
- Pillar Alignment: Security (traceability + adaptive controls)
- Why: Adds compromised-credentials detection, risk-based adaptive MFA, and IP allow/deny. Running
  audit-only first lets you tune before enforcing so you don't lock out legitimate users.
- AWS Services: Cognito user pool (Plus), threat protection; log export to CloudWatch/S3/Firehose.
- Architecture Decision: Start in **audit-only** mode, review generated risk data, then switch to
  **full-function** with appropriate automatic responses; export logs for SIEM analysis.
- Verification: Threat protection = enabled; mode documented; log export destination configured.
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pool-settings-advanced-security-threat-protection.html (accessed 2026-08-26)
- [✓✓ Triangulated | threat-protection docs + Plus plan features docs]

---

## Architectural Decisions

> ⚠️ Ask First. Valid options with real trade-offs; the architect must choose based on context.

**Decision: Feature tier per user pool (Lite vs Essentials vs Plus)**
- Options:

  | Option | AWS Service/Tier | Optimizes | Sacrifices | Best When |
  |--------|------------------|-----------|------------|-----------|
  | Lite | Cognito Lite | Lowest cost; tiered MAU pricing | No Managed Login v2, no passwordless, no access-token customization, no threat protection | Value/basic apps, low risk, password+social+SAML/OIDC only |
  | Essentials (default) | Cognito Essentials | Managed Login, passwordless/passkeys, access-token customization, password-reuse prevention | No threat protection; fixed MAU price | Most production CIAM apps |
  | Plus | Cognito Plus | All Essentials + adaptive auth, compromised-credentials detection, IP allow/deny, log export | Highest per-MAU cost | Elevated-security / regulated / high-abuse apps |

- Cost Profile: Lite tiered MAU; Essentials/Plus fixed MAU price, Plus > Essentials. Free tier
  exists for Lite and Essentials.
- Lock-in Assessment: All tiers are Cognito-native; tier is switchable per pool without migration.
- Architect Instruction: "Ask what security features (passwordless, threat protection) and
  compliance posture the app requires **before** accepting the Essentials default — and whether any
  pool truly needs Plus."
- Source: https://aws.amazon.com/cognito/pricing/ ; https://aws.amazon.com/about-aws/whats-new/2024/11/new-feature-tiers-essentials-plus-amazon-cognito (accessed 2026-08-26)

**Decision: Multi-tenant isolation model**
- Options:

  | Option | AWS approach | Optimizes | Sacrifices | Best When |
  |--------|--------------|-----------|------------|-----------|
  | User pool per tenant (silo) | 1 pool / tenant | Max isolation; per-tenant config/IdP | High ops effort; **1,000 pools/account hard limit** | Few, high-value tenants needing full isolation |
  | App client per tenant | 1 app client / tenant, shared pool | Per-tenant IdP + single user profile; moderate effort | Shared pool-level config (one MFA/threat-protection standard) | Many tenants, per-tenant federation |
  | User group per tenant | Cognito groups, shared pool | Simple; group in token; IAM role mapping | Weaker isolation; group sprawl | Simpler apps, moderate tenant count |
  | Custom attribute per tenant | `custom:tenantId`, shared pool | Simplest; single standard for all | Weakest isolation; app must enforce | Uniform tenants, app-enforced separation |

- Cost Profile: Shared-pool models concentrate MAU billing; silo multiplies operational cost.
- Scaling Characteristics: Silo hits the 1,000-pool ceiling — for massive scale AWS guidance points
  to cell-based architecture rather than one-pool-per-tenant.
- Lock-in Assessment: All are Cognito-native; tenant claim design affects portability of your authz.
- Architect Instruction: "Ask how many tenants, whether tenants need distinct IdPs/branding, and
  the required isolation strength before choosing. Default to shared pool + app-client or custom
  attribute unless strong isolation is mandated."
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/multi-tenant-application-best-practices.html ;
  https://docs.aws.amazon.com/cognito/latest/developerguide/bp_user-pool-based-multi-tenancy.html ;
  https://docs.aws.amazon.com/cognito/latest/developerguide/application-client-based-multi-tenancy.html (accessed 2026-08-26)
- [✓✓ Triangulated | multi-tenant best-practices docs + user-pool multi-tenancy docs]

**Decision: User pool only vs user pool + identity pool**
- Options:

  | Option | AWS approach | Optimizes | Sacrifices | Best When |
  |--------|--------------|-----------|------------|-----------|
  | User pool only | Auth + JWT to your API | Simplicity | Client cannot call AWS services directly | Client talks only to your backend |
  | User pool + identity pool | Auth + temp AWS creds via STS | Direct, per-user-scoped AWS access from client | Extra IAM/role-mapping complexity | Client must call S3/DynamoDB/etc. directly |

- Lock-in Assessment: Identity-pool STS role mapping is AWS-specific; increases coupling to IAM.
- Architect Instruction: "Ask whether any client needs to call AWS services directly. If not, do
  not add an identity pool."
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-scenarios.html ;
  https://repost.aws/knowledge-center/cognito-user-pools-identity-pools (accessed 2026-08-26)

**Decision: Access-token authorization design (groups/roles/scopes via pre-token-gen)**
- Options: Static scopes/resource servers vs dynamic claims via Pre Token Generation Lambda
  (V2_0 for user auth, V3_0 also for M2M client-credentials). Access-token customization requires
  Essentials/Plus.
- Architect Instruction: "Ask whether the API needs tenant_id/roles inside the access token. If so,
  confirm the pool is Essentials/Plus and use V2_0/V3_0; keep claims minimal to bound token size."
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-pre-token-generation.html (accessed 2026-08-26)

**Decision: Passwordless / passkey adoption (Essentials/Plus)**
- Options: Passkeys (FIDO2/WebAuthn, phishing-resistant), email OTP, SMS OTP, or password+MFA.
  Managed Login v2 implements passkey ceremonies; up to 20 passkeys per account.
- Architect Instruction: "Ask target-user device capability and phishing-resistance requirements.
  Prefer passkeys where devices support them; treat SMS OTP as the weakest option."
- Source: https://aws.amazon.com/about-aws/whats-new/2024/11/amazon-cognito-passwordless-authentication-low-friction-secure-logins (accessed 2026-08-26)

---

## Anti-Patterns

> 🚫 Never Do. Each has a concrete ❌ wrong / ✅ correct pair using exact service names.

**Decoding JWTs without full validation**
- Risk Level: CRITICAL
- Why: Security pillar — accepting unverified tokens enables forgery, privilege escalation, and
  cross-token-type misuse.
- Blast Radius: Every API/endpoint trusting the token; full data-plane compromise.
- ❌ Wrong: API Gateway/Lambda base64-decodes the Cognito JWT and reads claims without checking
  signature, `iss`, `aud`, `exp`, or `token_use`.
- ✅ Correct: API Gateway Cognito authorizer (or `aws-jwt-verify`) validating signature against the
  user pool JWKS plus `iss`, `aud`/`client_id`, `exp`, and `token_use`.
- Detection: Code/authorizer review; test with a token from a different pool/client and an ID token
  where an access token is required — both must be rejected.
- Impact: Data breach / unauthorized access.
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html (accessed 2026-08-26)

**Using the Implicit grant / putting a client secret in a public client**
- Risk Level: HIGH
- Why: Security — implicit grant leaks tokens via URL fragments; secrets in browser/mobile are
  extractable.
- Blast Radius: All users of that app client.
- ❌ Wrong: SPA configured as a Cognito app client with the implicit grant enabled and a client
  secret embedded in JS.
- ✅ Correct: Public Cognito app client, **no secret**, **Authorization Code grant + PKCE**;
  implicit grant disabled.
- Detection: `describe-user-pool-client` — verify no secret on public clients and only `code` grant.
- Impact: Token theft / account takeover.
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-security-best-practices.html (accessed 2026-08-26)

**Production sign-in without MFA (or SMS-only as sole factor)**
- Risk Level: HIGH
- Why: Security — a stolen password alone should never grant access.
- Blast Radius: Any account whose password leaks.
- ❌ Wrong: User pool MFA set to OFF (or SMS as the only factor for high-value accounts).
- ✅ Correct: MFA Required with TOTP or passkeys (Managed Login v2); on Plus, risk-based adaptive
  MFA; SMS only as fallback.
- Detection: `describe-user-pool` → `MfaConfiguration` = ON; enabled MFA types include TOTP/passkey.
- Impact: Account takeover.
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-security-best-practices.html (accessed 2026-08-26)

**Internet-facing user pool with no WAF and no threat protection**
- Risk Level: HIGH
- Why: Security/Cost — unthrottled auth endpoints invite credential stuffing, enumeration, and
  cost-inflating abuse.
- Blast Radius: Whole pool; billing and availability.
- ❌ Wrong: Public Managed Login with no WAF web ACL and Lite tier (no threat protection).
- ✅ Correct: AWS WAF web ACL with rate-based rules + CAPTCHA on the pool; Plus tier threat
  protection (compromised-credentials + adaptive auth) enabled.
- Detection: Confirm associated WAF web ACL; confirm threat protection status on Plus pools.
- Impact: Credential stuffing / DoS / cost overrun.
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pool-settings-advanced-security-threat-protection.html (accessed 2026-08-26)

**Username enumeration left enabled**
- Risk Level: MEDIUM
- Why: Security — distinct error messages reveal which accounts exist, aiding targeted attacks.
- Blast Radius: Reconnaissance surface across the whole pool.
- ❌ Wrong: App client with `PreventUserExistenceErrors` = LEGACY/disabled.
- ✅ Correct: `PreventUserExistenceErrors` = ENABLED on every app client.
- Detection: `describe-user-pool-client` → `PreventUserExistenceErrors: ENABLED`.
- Impact: Facilitates account-takeover campaigns.
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-security-best-practices.html (accessed 2026-08-26)

**Over-permissive identity-pool roles / guest access enabled by default**
- Risk Level: HIGH
- Why: Security — identity pools mint real AWS credentials; wide roles turn auth into broad AWS access.
- Blast Radius: Any AWS resource the role can reach; unauthenticated users if guest is on.
- ❌ Wrong: Identity pool authenticated role with `Action: "*"`/`Resource: "*"`, guest access enabled
  unnecessarily.
- ✅ Correct: Least-privilege role scoped to needed actions/resources, per-user isolation via
  `${cognito-identity.amazonaws.com:sub}` policy variables; guest access disabled unless required.
- Detection: Review identity-pool role policies for wildcards; check `AllowUnauthenticatedIdentities`.
- Impact: Privilege escalation / data breach.
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/identity-pools-security-best-practices.html (accessed 2026-08-26)

**One-user-pool-per-tenant as the default scaling strategy**
- Risk Level: MEDIUM
- Why: Reliability/Operational — the **1,000 user pools per account** hard limit makes silo-per-tenant
  a scaling dead-end, with high automation/maintenance cost.
- Blast Radius: Onboarding halts at the pool ceiling; config drift across pools.
- ❌ Wrong: Automatically provisioning a new user pool for every tenant with no ceiling plan.
- ✅ Correct: Shared pool with app-client / group / custom-attribute tenancy; adopt cell-based
  architecture for massive scale; reserve silo pools for the few tenants that truly require it.
- Detection: Count pools vs tenant growth rate; review chosen tenancy strategy against AWS guidance.
- Impact: Scaling wall / operational overhead.
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/multi-tenant-application-best-practices.html (accessed 2026-08-26)

**No deletion protection on production pools**
- Risk Level: MEDIUM
- Why: Reliability — user-pool deletion is unrecoverable; losing the directory is catastrophic.
- Blast Radius: Entire user base of the pool.
- ❌ Wrong: Production user pool with `DeletionProtection: INACTIVE`.
- ✅ Correct: `DeletionProtection: ACTIVE`, managed via IaC with change control.
- Detection: `describe-user-pool` → `DeletionProtection`.
- Impact: Total identity-directory loss / outage.
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-security-best-practices.html (accessed 2026-08-26)

---

## Security Architecture (service composition)

**Identity & Authentication**
- AWS Services: Cognito user pool (Managed Login v2, MFA, passwordless/passkeys), federated IdPs
  (social, SAML 2.0, OIDC).
- Architecture: Managed Login handles OAuth 2.0 auth-code+PKCE and passkey ceremonies; user pool
  issues ID/access/refresh JWTs; federation lets enterprise tenants bring their own IdP.
- Compliance Alignment: WAF SEC "manage identities for people and machines".
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools.html (accessed 2026-08-26)

**Authorization to AWS resources**
- AWS Services: Cognito identity pool + IAM roles + STS + role mapping.
- Architecture: Exchange user-pool token for scoped temporary AWS credentials; per-user isolation
  via IAM policy variables; separate authenticated vs guest roles.
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/identity-pools-security-best-practices.html (accessed 2026-08-26)

**Threat detection & response (Plus)**
- AWS Services: Threat protection (adaptive auth, compromised-credentials, IP allow/deny), log
  export to CloudWatch Logs / S3 / Data Firehose, optional SIEM downstream.
- Architecture: Risk scoring per sign-in → automatic responses (allow, require MFA, block); export
  events for analytics; run audit-only → full-function.
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pool-settings-advanced-security-threat-protection.html ;
  https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pool-settings-adaptive-authentication.html (accessed 2026-08-26)

**Edge protection**
- AWS Services: AWS WAF web ACL on the user pool; TLS everywhere.
- Architecture: Rate-based + CAPTCHA rules in front of Managed Login and Cognito APIs.
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-security-best-practices.html (accessed 2026-08-26)

---

## Operational Patterns

**Observability & audit**
- AWS Services: CloudTrail (control-plane API audit), threat-protection log export
  (CloudWatch/S3/Firehose), CloudWatch metrics.
- Automation: Ship threat/user-activity logs to SIEM; alert on spikes in blocked sign-ins.
- Cost Profile: Low–Medium (log storage + export).
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pool-settings-advanced-security-threat-protection.html (accessed 2026-08-26)

**Change management (IaC)**
- AWS Services: CloudFormation / CDK / Terraform for pools, app clients, tiers, triggers.
- Automation: Version-control tier, MFA, WAF association, deletion protection; review via PRs.
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-security-best-practices.html (accessed 2026-08-26)

**Regional resilience**
- Note: Cognito is a **regional** service. Cross-region redundancy of the user directory requires
  explicit architecture (e.g., replication/export strategies).
- ⚠️ **unverified**: Native multi-region user-pool failover for Cognito was **not confirmed** in an
  official doc during this research. See §7 iteration log. Treat cross-region DR as a custom design
  and validate with AWS before committing an RTO/RPO.

---

## Reference Architectures

**Multi-tenant B2B/B2C SaaS on Cognito (Essentials/Plus)**
- Context: SaaS serving multiple tenants, browser + mobile clients, own backend API.
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Auth UI | Cognito Managed Login v2 | Hosted sign-in/up, passkeys, OAuth code+PKCE |
  | Directory | Cognito user pool (Essentials/Plus) | Users, MFA, tiers, tenancy via app-client/group/attribute |
  | Federation | SAML/OIDC IdPs | Enterprise tenant SSO |
  | Token authz | Pre Token Generation Lambda V2_0/V3_0 | Inject tenant_id/roles into access token |
  | API | API Gateway + Cognito authorizer | Validate JWT (sig/iss/aud/exp/token_use) |
  | AWS authz (optional) | Cognito identity pool + IAM/STS | Per-user scoped AWS creds if client calls AWS directly |
  | Edge | AWS WAF web ACL | Rate-limit/CAPTCHA on auth endpoints |
  | Threat | Threat protection (Plus) | Adaptive auth, compromised-credentials, log export |
  | Observability | CloudTrail + CloudWatch/S3/Firehose | Audit + threat log analytics |

- Key Decisions: tier per pool; tenancy model; passkey vs password+MFA; identity pool yes/no.
- Scaling Path: shared pool + app-client/attribute tenancy → cell-based architecture near the
  1,000-pool limit.
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/multi-tenant-application-best-practices.html (accessed 2026-08-26)

---

## Service Equivalence Map

> Cross-provider CIAM equivalence. Equivalence ≠ feature parity — validate against each provider's
> current docs before decisions.

| Category | AWS | Google Cloud | Azure | Oracle Cloud (OCI) |
|----------|-----|--------------|-------|--------------------|
| CIAM / user directory | Amazon Cognito user pools | Identity Platform / Firebase Authentication | Microsoft Entra External ID (Azure AD B2C successor) | OCI IAM with Identity Domains |
| Authz → cloud creds | Cognito identity pools (STS) | Workload/Workforce Identity Federation | Entra ID + Managed Identities / RBAC | OCI IAM policies / dynamic groups |
| Hosted login UI | Managed Login v2 | Identity Platform hosted UI / FirebaseUI | Entra External ID user flows | Identity Domains hosted sign-in |
| Adaptive / risk-based auth | Threat protection (Plus) | Identity Platform MFA + reCAPTCHA Enterprise | Entra ID Protection (risk-based CA) | Adaptive Security / IAM |
| Passwordless / passkeys | Passwordless (FIDO2/passkeys, email/SMS OTP) | Firebase/Identity Platform passkeys | Entra passkeys / passwordless | Identity Domains passwordless |
| Edge protection (WAF) | AWS WAF | Cloud Armor | Azure WAF | OCI WAF |
| MFA | Cognito MFA (TOTP/SMS/passkey) | Identity Platform MFA | Entra MFA | IAM MFA |
| Secrets/keys for app | Secrets Manager / KMS | Secret Manager / Cloud KMS | Key Vault | OCI Vault |

---

## Provider Differentiators (Cognito, 2026)

```
Differentiator: Feature-tier model (Lite / Essentials / Plus)
Category: Security / Cost
Unique Value: Security capabilities (passwordless, token customization, threat protection) are
  packaged into switchable per-pool tiers with per-MAU pricing; Essentials is the default.
Architecture Impact: Tier is now an explicit security AND cost decision per user pool.
When to Leverage: Any Cognito adoption after Dec 2024.
Caveat: Choosing Lite silently forfeits Managed Login v2, passwordless, and threat protection.
Source: https://aws.amazon.com/cognito/pricing/ (accessed 2026-08-26)
```
```
Differentiator: Native identity-pool → STS credential brokering
Category: Security
Unique Value: Direct exchange of a federated token for scoped temporary AWS IAM credentials with
  per-user policy variables — tighter than most CIAM competitors for direct-to-cloud client access.
Architecture Impact: Enables client-side, per-user-scoped access to S3/DynamoDB without a backend.
When to Leverage: Mobile/SPA needing direct AWS access.
Caveat: Increases IAM coupling and blast radius if roles are over-scoped.
Source: https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-scenarios.html (accessed 2026-08-26)
```

---

## Scenario Coverage

**Standard Case** — Multi-tenant SaaS, browser+mobile, own API:
- Approach: Essentials (or Plus) user pool + Managed Login v2 (auth code + PKCE) + MFA/passkeys +
  app-client/attribute tenancy + Pre-Token-Gen V2_0 for tenant claims + API Gateway Cognito
  authorizer with full JWT validation + WAF.
- Key Decisions: tier, tenancy model, passwordless adoption, identity pool yes/no.

**Edge Case** — Massive tenant count / regulated / M2M:
- Approach: Move off silo pools toward cell-based architecture before the 1,000-pool ceiling; use
  Plus threat protection + log export to SIEM for regulated workloads; use Pre-Token-Gen V3_0 for
  M2M client-credentials access-token customization. Validate cross-region DR as custom design.

**Anti-Pattern Case** — Request to "just decode the token" / skip MFA / silo-per-tenant by default:
- Clarification: Refuse and flag. Ask for the required JWT validation path (authorizer/library),
  the MFA policy, and the tenant-count/isolation requirement before proceeding.

---

## 7. Research Iteration Changelog (P5.gap-loop)

| # | Item | Status | Resolution / Source |
|---|------|--------|---------------------|
| 1 | Feature tiers & default tier | Resolved | AWS What's New 2024-11-22 + pricing page confirm Lite/Essentials/Plus, Essentials default |
| 2 | Passwordless/passkeys availability & tier | Resolved | What's New 2024-11 (GA), 2025-03 (GovCloud); features page; 20 passkeys/account |
| 3 | Threat protection scope & modes | Resolved | Threat-protection + adaptive-auth docs; audit-only vs full-function |
| 4 | Access-token customization tier + trigger versions | Resolved | Pre-token-generation docs: V2_0 (user), V3_0 (M2M), Essentials/Plus |
| 5 | Multi-tenancy strategies + 1,000-pool limit | Resolved | multi-tenant + user-pool/app-client multi-tenancy best-practice docs |
| 6 | Token validity exact numbers (1h/7d) | Downgraded | Official docs mandate "short" + secure handling; concrete numbers are secondary guidance — tagged as tunable default |
| 7 | Native multi-region user-pool failover / DR | ⚠️ IRRESOLVABLE — human verification required | Not confirmed in official docs within MAX_ITERATIONS; Cognito is regional. Validate DR design with AWS before committing RTO/RPO |

---

## Source Bibliography

Official AWS sources (accessed 2026-08-26):

1. Amazon Cognito Developer Guide (root) — https://docs.aws.amazon.com/cognito/latest/developerguide/
2. Security best practices for user pools — https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-security-best-practices.html
3. Security best practices for identity pools — https://docs.aws.amazon.com/cognito/latest/developerguide/identity-pools-security-best-practices.html
4. Verifying a JSON Web Token — https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html
5. Understanding user pool JWTs — https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-with-identity-providers.html
6. Threat protection — https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pool-settings-advanced-security-threat-protection.html
7. Working with adaptive authentication — https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pool-settings-adaptive-authentication.html
8. Pre token generation Lambda trigger — https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-pre-token-generation.html
9. Multi-tenant application best practices — https://docs.aws.amazon.com/cognito/latest/developerguide/multi-tenant-application-best-practices.html
10. User-pool multi-tenancy best practices — https://docs.aws.amazon.com/cognito/latest/developerguide/bp_user-pool-based-multi-tenancy.html
11. App-client multi-tenancy best practices — https://docs.aws.amazon.com/cognito/latest/developerguide/application-client-based-multi-tenancy.html
12. Common Amazon Cognito scenarios — https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-scenarios.html
13. Amazon Cognito user pools (overview) — https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools.html
14. Amazon Cognito pricing — https://aws.amazon.com/cognito/pricing/
15. Amazon Cognito features — https://aws.amazon.com/cognito/features/
16. What's New — New feature tiers Essentials & Plus (2024-11-22) — https://aws.amazon.com/about-aws/whats-new/2024/11/new-feature-tiers-essentials-plus-amazon-cognito
17. What's New — Passwordless authentication (2024-11) — https://aws.amazon.com/about-aws/whats-new/2024/11/amazon-cognito-passwordless-authentication-low-friction-secure-logins
18. What's New — Feature tiers in GovCloud (2025-03) — https://aws.amazon.com/about-aws/whats-new/2025/03/new-feature-tiers-essentials-plus-amazon-cognito-aws-govcloud-us-regions/
19. What's New — Passwordless in GovCloud (2025-03) — https://aws.amazon.com/about-aws/whats-new/2025/03/amazon-cognito-passwordless-authentication-low-friction-secure-logins-aws-govcloud-us-regions/
20. AWS re:Post — User pools vs identity pools — https://repost.aws/knowledge-center/cognito-user-pools-identity-pools
21. AWS Well-Architected Security Pillar — https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html

> Secondary/community sources were used only to locate official pages and were not cited as
> authority. All normative claims above trace to sources 1–21.
```
