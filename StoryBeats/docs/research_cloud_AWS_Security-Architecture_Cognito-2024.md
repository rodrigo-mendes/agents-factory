# AWS Cognito — Security Architecture Knowledge Base

---

## Metadata

```yaml
Full_Name: "AWS Security Architecture — Amazon Cognito"
Cloud_Provider: "AWS"
Architecture_Domain: "Security Architecture — Identity & Access Management (CIAM/WIAM)"
Target_Edition: "Amazon Cognito 2024–2025"
Architecture_Context: "Web and mobile applications requiring customer identity and access management (CIAM), workforce identity, and federated access to AWS resources"
Official_Source_URL: "https://docs.aws.amazon.com/cognito/latest/developerguide/"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-05-25"
Currency_Threshold: "2027-05-25 — review required after this date due to Cognito feature velocity"
```

---

## Executive Summary

Amazon Cognito is AWS's managed identity platform for web and mobile applications. It operates as two independent but composable services: **User Pools** (user directory + OIDC identity provider + authorization server) and **Identity Pools** (AWS credentials broker via STS). Together, they cover the full CIAM stack from sign-up through to fine-grained IAM-controlled AWS resource access. Cognito is HIPAA-BAA eligible, SOC 1–3 certified, ISO 27001 certified, and PCI DSS compliant for the infrastructure layer (though application-layer PCI DSS compliance remains the architect's responsibility).

The 2024–2025 edition introduced the **Feature Plan model** (Essentials vs Plus), which gates advanced security capabilities — notably Threat Protection (adaptive authentication, compromised credential detection, automated remediation) — behind the Plus tier. This is a pricing-model change that materially affects security architecture decisions. Managed Login received significant branding customization capability (custom CSS, logos). Token customization via Lambda triggers was extended. The prior "Advanced Security Features" (ASF) branding is now called **Threat Protection** under the Plus plan.

The three most critical architecture guardrails for Cognito deployments are: (1) **never expose User Pool App Client secrets in client-side code** — use PKCE flows for public clients; (2) **always associate an AWS WAF web ACL with User Pools exposed to the internet** — Cognito's managed login endpoints are public by design; (3) **separate User Pool App Clients by trust boundary** (server-side vs. client-side vs. M2M) — collapsing them into a single client with a secret shared to a browser is a CRITICAL security anti-pattern.

---

## Cloud Architecture Glossary

```
Term: User Pool
Definition: A managed user directory and OIDC identity provider that stores user profiles, handles authentication flows, and issues JWT tokens (ID token, access token, refresh token) to apps and APIs.
Provider Docs Section: https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools.html
Architect Usage: Use a User Pool as the authentication boundary for your application. A single User Pool can serve multiple App Clients (one per application or trust boundary).
Common Confusion: Confused with Identity Pools. User Pool = who the user IS (authentication + OIDC tokens). Identity Pool = what AWS resources the user can ACCESS (IAM credentials).

Term: Identity Pool
Definition: A directory of federated identities that exchanges external identity provider tokens (including User Pool JWTs, SAML assertions, OIDC tokens, OAuth tokens) for temporary AWS STS credentials.
Provider Docs Section: https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-identity.html
Architect Usage: Use an Identity Pool when your application needs to call AWS APIs directly (S3, DynamoDB, etc.) on behalf of a user. Not needed if your backend handles all AWS API calls.
Common Confusion: Not a user directory — it has no password management, no MFA, no sign-up. It is purely a credentials broker.

Term: App Client
Definition: A configuration record within a User Pool that represents a single application consuming the User Pool. Defines the allowed OAuth flows, scopes, callback URLs, secret presence, and token validity.
Provider Docs Section: https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-client-apps.html
Architect Usage: Create one App Client per distinct trust boundary. Server-side apps may use a client secret. SPAs and mobile apps must use public clients (no secret) with PKCE.
Common Confusion: An App Client is not a user — it is an OAuth 2.0 client registration. Multiple App Clients share the same user directory but may have different allowed scopes, flows, and token settings.

Term: Managed Login
Definition: AWS-hosted, customizable web UI pages for sign-up, sign-in, MFA, and password reset, served from a Cognito domain or custom domain. Implements the OAuth 2.0 authorization code flow.
Provider Docs Section: https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools-managed-login.html
Architect Usage: Default choice for apps that don't need a fully custom auth UI. Reduces implementation surface area. Requires a domain configuration (Cognito prefix or custom domain via ACM).
Common Confusion: Managed Login is not available for all authentication flows — it does not support the USER_PASSWORD_AUTH flow used by the Cognito user pools API directly.

Term: Federated Identity
Definition: A user identity authenticated by an external IdP (SAML 2.0, OIDC, OAuth 2.0 social, or custom developer provider) and mapped into a Cognito User Pool or Identity Pool.
Provider Docs Section: https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools-identity-federation.html
Architect Usage: Use federation when users should authenticate via an enterprise IdP (Okta, ADFS, Azure AD) or social provider (Google, Apple). Cognito acts as SP and normalizes claims.
Common Confusion: Federated users in a User Pool do NOT have a local password and cannot use MFA features that require local credential storage. Some User Pool features (TOTP MFA, advanced security) are unavailable to federated users.

Term: JWT (JSON Web Token)
Definition: A signed, optionally encrypted token in three parts (header.payload.signature) issued by a User Pool. Cognito issues three types: ID Token (user identity claims), Access Token (API authorization scopes), Refresh Token (obtain new ID/Access tokens).
Provider Docs Section: https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-with-identity-providers.html
Architect Usage: Validate JWTs at the API boundary using the User Pool's JWKS endpoint. Never trust a JWT without signature verification. ID Token is for authentication; Access Token is for authorization.
Common Confusion: ID Token and Access Token serve different purposes. Using an ID Token for API authorization (instead of Access Token) is a common misuse pattern. Access Token carries scopes; ID Token carries user claims.

Term: Resource Server
Definition: An OAuth 2.0 authorization server registration in a User Pool that defines custom scopes for protecting APIs. Enables machine-to-machine (M2M) authorization via client credentials grant.
Provider Docs Section: https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools-define-resource-servers.html
Architect Usage: Define Resource Servers for each protected API. Associate custom scopes (e.g., myapi/read, myapi/write) to App Clients. Use client credentials grant for service-to-service auth.
Common Confusion: Resource Servers are a User Pool concept, not an Identity Pool concept. They apply to OAuth 2.0 API authorization, not AWS IAM resource authorization.

Term: Threat Protection (Plus Feature Plan)
Definition: Advanced security capability that uses ML-based adaptive authentication to detect compromised credentials, unusual sign-in activity, and malicious actors — and automatically block, challenge with MFA, or allow with notification.
Provider Docs Section: https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pool-settings-threat-protection.html
Architect Usage: Enable for any production user pool handling sensitive data. Required for HIPAA/PCI workloads. Only available under the Plus feature plan (additional per-MAU cost).
Common Confusion: Previously called "Advanced Security Features (ASF)". The rebrand to Threat Protection in 2024 coincided with the feature plan restructuring.

Term: Feature Plan (Essentials vs Plus)
Definition: A billing and feature tier model for User Pools. Essentials includes core authentication, federation, MFA, and managed login. Plus adds Threat Protection, advanced anomaly detection, and enhanced logging to S3/CloudWatch/Firehose.
Provider Docs Section: https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-sign-in-feature-plans.html
Architect Usage: Default new user pools are on Essentials. Explicitly evaluate whether Threat Protection (Plus) is required at design time — it affects both cost and security posture.
Common Confusion: Feature Plan is a User Pool concept only. Identity Pools have separate pricing based on monthly active users performing identity operations.

Term: PKCE (Proof Key for Code Exchange)
Definition: An OAuth 2.0 extension (RFC 7636) that protects the authorization code flow for public clients (SPAs, mobile apps) by binding the authorization request to the token exchange using a cryptographic challenge.
Provider Docs Section: https://docs.aws.amazon.com/cognito/latest/developerguide/authorization-endpoint.html
Architect Usage: Mandatory for all public clients. Never use the implicit flow (deprecated). Always use authorization code + PKCE for browser and mobile apps.
Common Confusion: PKCE is not a substitute for a client secret — it is a protection for the code exchange step, not client authentication. A public client with PKCE has no client secret by design.

Term: Lambda Trigger
Definition: An AWS Lambda function invoked synchronously at specific points in the User Pool lifecycle (pre-sign-up, post-confirmation, pre-token generation, custom authentication challenge, user migration, etc.) to customize behavior.
Provider Docs Section: https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools-working-with-lambda-triggers.html
Architect Usage: Use pre-token generation trigger for custom claims in JWTs. Use custom authentication challenge for passwordless flows. Lambda triggers run synchronously and add to auth latency — keep execution fast (<5s).
Common Confusion: Lambda triggers are not available for federated users during the federation flow — only local authentication and post-federation steps.

Term: Role-Based Access Control (RBAC) — Identity Pool
Definition: An Identity Pool authorization mode where the IAM role assigned to a user is determined by their identity provider claims (group membership, attributes), with the role assumed via AssumeRoleWithWebIdentity.
Provider Docs Section: https://docs.aws.amazon.com/cognito/latest/developerguide/role-based-access-control.html
Architect Usage: Use RBAC when user access to AWS resources maps cleanly to a small number of discrete roles. Use ABAC (attribute-based) when fine-grained, per-resource access is required.
Common Confusion: Identity Pool RBAC is different from IAM Identity Center (AWS SSO) RBAC. Identity Pool RBAC is for app users accessing AWS resources, not for IAM users accessing AWS console.

Term: Attribute-Based Access Control (ABAC) — Identity Pool
Definition: An Identity Pool authorization mode where user claims are mapped to IAM session principal tags (via STS), and IAM resource policies use aws:PrincipalTag conditions to control resource access.
Provider Docs Section: https://docs.aws.amazon.com/cognito/latest/developerguide/attributes-for-access-control.html
Architect Usage: Use ABAC for multi-tenant architectures where each user should only access their own data (e.g., S3 prefix = user's sub claim). More scalable than RBAC for large user sets.
Common Confusion: Principal tags from Identity Pool ABAC are STS session tags — they are not the same as IAM user tags or resource tags.
```

---

## Architecture Guardrails

### ✅ Mandatory Patterns

**1. Public Client PKCE — No Client Secret in Browser or Mobile Apps**
- Pillar Alignment: Security
- Why: App Client secrets embedded in client-side code (JavaScript SPAs, mobile binaries) are trivially extractable. Cognito's authorization code flow with PKCE provides equivalent protection without a secret. AWS Cognito documentation explicitly states App Clients for public clients should not have a client secret.
- AWS Services: Amazon Cognito User Pool App Client (public type), Authorization Endpoint, Token Endpoint
- Architecture Decision:
  ```
  - Create App Client with "No client secret" for all browser and mobile clients
  - Enable Authorization Code Grant flow only (disable Implicit Grant — deprecated)
  - Enforce PKCE: app generates code_verifier (random 43-128 char string), computes
    code_challenge = BASE64URL(SHA256(code_verifier)), sends code_challenge in
    /oauth2/authorize, sends code_verifier in /oauth2/token exchange
  - Set short access token validity (default 60 min; reduce for sensitive apps)
  - Enable token revocation on the App Client
  ```
- Verification:
  ```bash
  # Check App Client has no secret and uses authorization code grant
  aws cognito-idp describe-user-pool-client \
    --user-pool-id <pool-id> \
    --client-id <client-id> \
    --query 'UserPoolClient.{Secret:ClientSecret,Flows:ExplicitAuthFlows,Grant:AllowedOAuthFlows}'
  # Secret should be null; AllowedOAuthFlows should contain "code" not "implicit"
  ```
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-client-apps.html

---

**2. Separate App Clients by Trust Boundary**
- Pillar Alignment: Security
- Why: Server-side (confidential) clients can use a client secret. Client-side (public) clients cannot. M2M (service accounts) use client credentials grant. Mixing them on a single App Client creates overpermissioned clients and makes rotation impossible without impact.
- AWS Services: Amazon Cognito User Pool App Client
- Architecture Decision:
  ```
  One App Client per trust boundary:
  - Public web SPA client: no secret, PKCE, authorization_code grant
  - Mobile client: no secret, PKCE, authorization_code grant
  - Server-side web app (BFF): client secret, authorization_code grant
  - M2M service account: client secret, client_credentials grant, resource server scopes
  - Admin backend: client secret or admin API with IAM auth (not user pool client)
  ```
- Verification:
  ```bash
  aws cognito-idp list-user-pool-clients --user-pool-id <pool-id> \
    --query 'UserPoolClients[*].{Name:ClientName,Id:ClientId}'
  # Then describe each to confirm separation
  ```
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-client-apps.html

---

**3. AWS WAF Web ACL on User Pool**
- Pillar Alignment: Security
- Why: Cognito managed login and the OIDC/OAuth endpoints are publicly reachable by design. Without WAF, they are exposed to credential stuffing, brute force, and bot-driven account takeover.
- AWS Services: Amazon Cognito User Pool, AWS WAF (v2), AWS WAF Managed Rules (AWSManagedRulesCommonRuleSet, AWSManagedRulesBotControlRuleSet, AWSManagedRulesATPRuleSet)
- Architecture Decision:
  ```
  - Attach a WAF Web ACL (regional) to the User Pool
  - Include at minimum:
    - AWS-AWSManagedRulesCommonRuleSet (OWASP protections)
    - AWS-AWSManagedRulesATPRuleSet (Account Takeover Prevention — monitors login endpoint)
    - Rate-based rule: max 100 requests/5min per IP to /oauth2/token and /oauth2/authorize
  - Log WAF decisions to CloudWatch Logs or S3 for audit
  ```
- Verification:
  ```bash
  aws cognito-idp get-user-pool-mfa-config --user-pool-id <pool-id>
  # Check WAF association:
  aws wafv2 get-web-acl-for-resource \
    --resource-arn arn:aws:cognito-idp:<region>:<account-id>:userpool/<pool-id>
  # Must return a WebACL, not "Resource not associated"
  ```
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-waf.html

---

**4. Enable MFA — TOTP Preferred over SMS**
- Pillar Alignment: Security
- Why: SMS-based MFA is vulnerable to SIM swapping. TOTP (RFC 6238) provides stronger second factor. Cognito supports both; TOTP (e.g., via Google Authenticator, Authy) is the recommended option. Note: MFA features apply to local users only, not federated users.
- AWS Services: Amazon Cognito User Pool MFA settings, TOTP software tokens
- Architecture Decision:
  ```
  - Set MFA configuration to OPTIONAL (user can enable) or REQUIRED (forced)
  - Enable TOTP as the preferred MFA method
  - Enable SMS MFA only as fallback if TOTP unavailable (requires SNS budget awareness)
  - Consider Adaptive Authentication (Plus plan Threat Protection) for risk-based MFA enforcement
    without forcing all users through MFA on every login
  ```
- Verification:
  ```bash
  aws cognito-idp get-user-pool-mfa-config --user-pool-id <pool-id>
  # SoftwareTokenMfaConfiguration.Enabled should be true
  # MfaConfiguration should be "ON" or "OPTIONAL" depending on risk appetite
  ```
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-mfa.html

---

**5. Validate JWTs at Every API Boundary**
- Pillar Alignment: Security
- Why: Cognito issues JWTs but does not automatically protect your APIs. Your API (via Lambda Authorizer, API Gateway Cognito Authorizer, or application middleware) must verify the JWT signature against the User Pool's JWKS endpoint on every request.
- AWS Services: Amazon Cognito User Pool (JWKS endpoint), Amazon API Gateway (Cognito Authorizer or Lambda Authorizer), AWS Lambda
- Architecture Decision:
  ```
  - JWKS endpoint: https://cognito-idp.<region>.amazonaws.com/<pool-id>/.well-known/jwks.json
  - Validate: signature (RS256), exp claim, iss claim (must match pool endpoint),
    aud/client_id claim (must match App Client ID for ID Token;
    for Access Token, aud = "https://<resource-server>")
  - Cache JWKS keys (1 hour) — Cognito rotates keys but provides overlap period
  - For API Gateway: use COGNITO_USER_POOLS authorizer (automatic JWT validation)
    or Lambda authorizer for custom claim-based authorization
  - Never trust a JWT without verifying the signature
  ```
- Verification:
  ```bash
  # Confirm API Gateway authorizer configuration:
  aws apigateway get-authorizers --rest-api-id <api-id> \
    --query 'items[?type==`COGNITO_USER_POOLS`].{Name:name,Pool:providerARNs}'
  ```
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-with-identity-providers.html

---

**6. CloudTrail Audit Logging for All Cognito API Calls**
- Pillar Alignment: Security, Operational Excellence
- Why: AWS CloudTrail logs all Amazon Cognito API management calls (CreateUserPool, AdminCreateUser, AdminSetUserPassword, etc.). These are critical for security forensics and compliance audit trails. User authentication events (InitiateAuth, etc.) are also logged.
- AWS Services: AWS CloudTrail, Amazon CloudWatch Logs, Amazon S3
- Architecture Decision:
  ```
  - Ensure CloudTrail is enabled in all regions where Cognito User Pools exist
  - Enable CloudTrail log file integrity validation
  - For compliance: enable Plus plan Threat Protection user activity logging
    (exports to S3, CloudWatch Logs, or Firehose)
  - For HIPAA/PCI: retain CloudTrail logs for minimum 1 year (7 years for PCI)
  ```
- Verification:
  ```bash
  aws cloudtrail describe-trails --include-shadow-trails false \
    --query 'trailList[?IsMultiRegionTrail==`true`].{Name:Name,S3:S3BucketName,LogEnabled:LogFileValidationEnabled}'
  # LogFileValidationEnabled should be true
  ```
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/logging-using-cloudtrail.html

---

### ⚠️ Architectural Decisions

**Decision 1: User Pool vs. External IdP (Okta, Auth0, Azure AD B2C) as Primary Identity Platform**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Cognito User Pool (native) | Amazon Cognito User Pool | AWS integration, no egress cost, single-vendor | Feature depth vs. dedicated IdP, limited enterprise workflows | Greenfield AWS-native apps, startup budget, CIAM without complex enterprise identity |
  | Cognito as SP to External IdP | Cognito User Pool + SAML/OIDC federation to Okta/Azure AD | Enterprise SSO, rich IdP features, existing enterprise investment | Architecture complexity, dual-vendor dependency, latency added by federation hop | Enterprise workforce IdP already exists, need Okta/ADFS-grade policy engine |
  | Skip Cognito, use external IdP directly | Okta / Auth0 / Azure AD B2C | Most feature-rich IdP capabilities, fine-grained MFA policies | No native AWS STS integration (need Identity Pool for AWS resource access), egress cost | Complex CIAM workflows, passwordless, step-up auth, mature enterprise policy requirements |

- Cost Profile: Native Cognito is cheapest (per-MAU pricing, free tier 50k MAU). Federating to external IdP adds IdP licensing cost. External IdP direct adds Identity Pool cost for AWS resource access.
- Lock-in Assessment: Native User Pool has high AWS lock-in (proprietary Lambda triggers, Cognito-specific token customization). Federation to external IdP reduces lock-in — Cognito can be swapped out as long as IdP supports OIDC/SAML.
- Architect Instruction: "Ask: Does the team need step-up authentication, highly customizable MFA policies, or identity orchestration workflows? If yes, evaluate dedicated IdP before committing to Cognito."
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools-identity-federation.html

---

**Decision 2: User Pool + Identity Pool (Combined) vs. User Pool Only**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | User Pool only | Cognito User Pool | Simplicity, OIDC token-based API access | No direct AWS resource access from client app | Backend-mediated architectures — all AWS API calls made by server, not client |
  | User Pool + Identity Pool | Cognito User Pool + Cognito Identity Pool + STS | Client app calls AWS APIs directly (S3, DynamoDB, IoT) | More complex auth flow, additional service, ABAC/RBAC setup required | Mobile apps directly uploading to S3, IoT devices, apps requiring per-user fine-grained AWS resource access |
  | Identity Pool only (no User Pool) | Cognito Identity Pool + external IdP (SAML/OIDC) | Reuse existing IdP investment, simpler if only AWS resource access needed | No user directory management, no Cognito MFA | Enterprise apps already using Okta/ADFS that only need AWS resource credentials |

- Cost Profile: User Pool only = per-MAU Cognito cost. Adding Identity Pool = additional per-identity-operation cost (charged separately).
- Lock-in Assessment: User Pool only is Cognito-specific. Identity Pool integration with external OIDC IdP (not User Pool) is more portable.
- Architect Instruction: "Ask: Does the client application (browser/mobile) need to call AWS APIs directly? If no, User Pool only is sufficient — avoid Identity Pool complexity."
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-scenarios.html

---

**Decision 3: Essentials vs Plus Feature Plan**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Essentials | Cognito User Pool (default) | Cost efficiency (~$0.0055/MAU after free tier) | No Threat Protection, no advanced anomaly detection, no enhanced user activity logging | Low-risk apps, internal tools, dev/test, apps with WAF as compensating control |
  | Plus | Cognito User Pool + Threat Protection | Adaptive authentication, ML-based risk detection, automated block/challenge, enhanced audit logs | Higher cost (~$0.05/MAU), requires Plus plan activation | Consumer-facing apps with credential stuffing risk, HIPAA/PCI workloads, high-value user accounts |

- Cost Profile: Plus is ~9x the cost per MAU of Essentials. At 100k MAU: Essentials ~$550/mo, Plus ~$5,000/mo. Evaluate against cost of a breach.
- Architect Instruction: "Ask: Is this user pool handling financial transactions, PII, or health data? If yes, Plus plan Threat Protection should be the default, not an optional upgrade."
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-sign-in-feature-plans.html

---

**Decision 4: Managed Login vs. Custom Authentication UI**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Managed Login | Cognito Managed Login (hosted UI) | Security (AWS manages login page, CSRF, XSS), reduced implementation, MFA handled | Limited UX customization (CSS/logo only), subdomain required, all auth in browser redirect | Standard auth flows, rapid development, apps where brand consistency is nice-but-not-critical |
  | Custom UI (Cognito User Pools API) | Cognito User Pools API + AWS SDK | Full UX control, no browser redirect, passkeys and custom flows | App is responsible for all security controls (CSRF, token storage, MFA UI), Lambda triggers not available for all flows | Native mobile apps, embedded auth experience, highly branded consumer apps |
  | BFF (Backend for Frontend) | Cognito User Pool + server-side App Client | Tokens never touch browser (session cookie pattern), highest security | Server complexity, session management, server-side infrastructure cost | High-security apps (banking, healthcare), apps requiring token binding |

- Cost Profile: All options use the same Cognito pricing. BFF adds compute cost for session management.
- Architect Instruction: "Ask: Must tokens never be accessible to JavaScript? If yes, use BFF pattern. Ask: Is auth UX highly differentiated? If no, use Managed Login."
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools-managed-login.html

---

### 🚫 Anti-Patterns

**Anti-Pattern 1: App Client Secret Embedded in Public Client**
- Risk Level: CRITICAL
- Why: Security pillar violation. A client secret embedded in a JavaScript SPA or mobile app binary is trivially extractable. An attacker can use it to forge tokens or impersonate the app client. Cognito cannot distinguish the legitimate app from the attacker using the same secret.
- Instead:
  ```
  - Create a public App Client (no client secret) for SPAs and mobile apps
  - Use Authorization Code flow + PKCE (RFC 7636)
  - For server-side apps (BFF), use a confidential App Client with a client secret
    stored in AWS Secrets Manager
  ```
- Detection:
  ```bash
  # Check if App Client has a secret and is used for a public (browser/mobile) client
  aws cognito-idp describe-user-pool-client \
    --user-pool-id <pool-id> --client-id <client-id> \
    --query 'UserPoolClient.ClientSecret'
  # If non-null and this is a browser/mobile app, this is CRITICAL
  ```
- Impact: Account takeover, token forgery, full authentication bypass
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-client-apps.html

---

**Anti-Pattern 2: Self-Registration Enabled Without Verification or WAF**
- Risk Level: HIGH
- Why: Security pillar. Open self-registration (AllowAdminCreateUserOnly = false) with no email/phone verification and no WAF exposes the user pool to mass account creation by bots — leading to abuse, spam, and credential stuffing setup.
- Instead:
  ```
  - Enable email or phone number verification on sign-up
  - Associate a WAF web ACL with the User Pool
  - Consider captcha at sign-up if using custom UI (cannot be embedded in Managed Login)
  - Use Pre Sign-Up Lambda trigger to validate against an allowlist or business domain
  - For B2B: set AllowAdminCreateUserOnly = true and provision users programmatically
  ```
- Detection:
  ```bash
  aws cognito-idp describe-user-pool --user-pool-id <pool-id> \
    --query 'UserPool.{SelfSignUp:AdminCreateUserConfig.AllowAdminCreateUserOnly,AutoVerified:AutoVerifiedAttributes}'
  # AllowAdminCreateUserOnly=false with empty AutoVerifiedAttributes is HIGH risk
  ```
- Impact: Bot-created accounts, abuse of free-tier resources, credential stuffing staging
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-email-phone-verification.html

---

**Anti-Pattern 3: Storing Tokens in localStorage**
- Risk Level: HIGH
- Why: Security pillar. localStorage is accessible to any JavaScript running on the page — including third-party scripts and XSS payloads. A Cognito refresh token in localStorage allows persistent session hijacking.
- Instead:
  ```
  - For SPAs: store tokens in memory only (JavaScript variable, not storage API)
  - Use short-lived access tokens (15–60 min); refresh on demand
  - For high-security apps: use BFF pattern — tokens stored server-side in
    HTTP-only, Secure, SameSite=Strict cookies
  - Consider Cognito's Amplify SDK which defaults to in-memory storage for tokens
  ```
- Detection: Code review and CSP audit. No AWS-side control — this is an application-layer vulnerability.
- Impact: Session hijacking via XSS, persistent account takeover via stolen refresh token
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-with-identity-providers.html

---

**Anti-Pattern 4: Wildcard `*` IAM Role Policies Attached to Identity Pool Roles**
- Risk Level: CRITICAL
- Why: Security pillar. Identity Pool issues temporary AWS credentials. If the authenticated or unauthenticated IAM role has `"Resource": "*"` and `"Action": "*"` (or similarly broad permissions), a compromised user session grants full AWS account access.
- Instead:
  ```
  - Apply least-privilege IAM policies to all Identity Pool IAM roles
  - Use ABAC (attribute-based access control) with principal tags to scope resource access
    to the authenticated user's data (e.g., S3 prefix = user's sub claim)
  - Separate roles for authenticated vs. unauthenticated users (unauthenticated should
    be read-only on public resources only)
  - Use IAM Access Analyzer to validate role policies
  ```
- Detection:
  ```bash
  # Get Identity Pool roles
  aws cognito-identity get-identity-pool-roles --identity-pool-id <pool-id>
  # Inspect each role's policy for wildcards:
  aws iam get-role-policy --role-name <role-name> --policy-name <policy-name>
  # Flag any "Resource": "*" with "Action": "*" or "Action": ["s3:*", "dynamodb:*"]
  ```
- Impact: Full AWS account compromise, data exfiltration, cryptomining, ransomware
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/role-based-access-control.html

---

**Anti-Pattern 5: No Token Revocation on App Client**
- Risk Level: HIGH
- Why: Without token revocation enabled, a stolen refresh token remains valid until natural expiry (default 30 days). There is no way to invalidate it for a specific user session.
- Instead:
  ```
  - Enable token revocation on all App Clients (console: Authentication → App clients →
    Enable token revocation)
  - Implement sign-out by calling /oauth2/revoke endpoint with the refresh token
  - For compromised accounts: use AdminUserGlobalSignOut API to revoke all active sessions
  ```
- Detection:
  ```bash
  aws cognito-idp describe-user-pool-client \
    --user-pool-id <pool-id> --client-id <client-id> \
    --query 'UserPoolClient.EnableTokenRevocation'
  # Should be true
  ```
- Impact: Persistent session access after password change, logout, or account compromise
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/token-revocation.html

---

**Anti-Pattern 6: Unauthenticated Identity Pool Access with Broad Permissions**
- Risk Level: HIGH
- Why: Unauthenticated (guest) access is a valid Identity Pool feature, but the IAM role for unauthenticated users is frequently over-permissioned. Any internet user can obtain credentials for this role — it should only allow access to genuinely public resources.
- Instead:
  ```
  - Disable unauthenticated access unless explicitly required
  - If required, scope the unauthenticated IAM role to:
    - Read-only access to specific public S3 prefixes
    - Specific DynamoDB table + partition key scope matching a "public" attribute
    - No write access, no management API access, no cross-account access
  - Enable enhanced (classic) authentication flow to prevent unauthenticated users
    from elevating to authenticated without re-authentication
  ```
- Detection:
  ```bash
  aws cognito-identity get-identity-pool-roles --identity-pool-id <pool-id> \
    --query 'Roles.unauthenticated'
  # If non-null, inspect the role's policies for over-permission
  ```
- Impact: Unauthorized data access, cost abuse, S3 data exposure
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/identity-pools-security-best-practices.html

---

## Cloud-Native Design Patterns

**Pattern: Cognito + API Gateway + Lambda (Serverless CIAM)**
- Category: Communication / Security
- Problem: Secure a serverless API where users are authenticated via Cognito and authorization is claim-based.
- Solution on AWS:
  ```
  1. User authenticates via Cognito User Pool (Managed Login or SDK)
  2. App receives JWT (ID Token + Access Token)
  3. App sends Access Token in Authorization: Bearer <token> header to API Gateway
  4. API Gateway Cognito Authorizer validates JWT signature, expiry, issuer, audience
  5. Gateway injects user claims ($context.authorizer.*) into request context
  6. Lambda handler reads claims for fine-grained authorization logic
  ```
- Services Used:
  - Amazon Cognito User Pool (authentication + JWT issuance)
  - Amazon API Gateway REST or HTTP API (Cognito Authorizer)
  - AWS Lambda (business logic + claim-based authorization)
- When to Apply: Standard REST API backends, mobile backends, BaaS patterns
- When NOT to Apply: GraphQL APIs needing field-level auth (use AppSync + Cognito), gRPC, WebSocket-heavy apps
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Security | JWT validation at the gateway — Lambda never sees unauthenticated requests | Gateway-level auth only validates token, not business logic authorization |
  | Latency | Cognito JWKS cached by API Gateway — minimal latency overhead | Cold start + Lambda execution adds P99 latency vs. ECS/EC2 |
  | Ops | Fully managed — no auth infrastructure to maintain | Less control vs. custom Lambda Authorizer |

- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-integrate-with-cognito.html

---

**Pattern: Cognito + S3 Per-User ABAC (Attribute-Based S3 Access)**
- Category: Data / Security
- Problem: Mobile/web app users need direct S3 upload/download scoped to their own data, without a backend proxy, without giving all users access to all data.
- Solution on AWS:
  ```
  1. User Pool issues JWT with sub claim (unique user identifier)
  2. Identity Pool maps sub claim to IAM session tag: PrincipalTag: {"sub": "<user-sub>"}
  3. Authenticated IAM role policy uses condition:
     "StringLike": {"s3:prefix": ["users/${cognito-identity.amazonaws.com:sub}/*"]}
  4. User can only read/write objects under their own prefix in S3
  ```
- Services Used:
  - Amazon Cognito User Pool (authentication, JWT with sub claim)
  - Amazon Cognito Identity Pool (STS credential broker, ABAC principal tags)
  - AWS STS (AssumeRoleWithWebIdentity + session tags)
  - Amazon S3 (bucket policy or IAM role policy with PrincipalTag condition)
- When to Apply: User-generated content apps, profile picture uploads, per-user file storage, IoT device data isolation
- When NOT to Apply: Shared data requiring complex group-based access (use DynamoDB + Lambda for access control), compliance-regulated data requiring audit trail per access (use S3 server-side access logging + Macie)
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Scalability | No backend bottleneck — client uploads directly to S3 | Client holds temporary AWS credentials — requires secure storage |
  | Security | IAM-enforced isolation — even a bug in app code cannot cross user boundaries | ABAC policy complexity — easy to misconfigure and create gaps |
  | Cost | No data transfer through backend | STS credential refresh every 1 hour adds API call cost at scale |

- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/attributes-for-access-control.html

---

**Pattern: Custom Authentication Flow (Passwordless OTP)**
- Category: Communication / Resilience
- Problem: Provide passwordless login via email or SMS OTP using Cognito's challenge-based authentication.
- Solution on AWS:
  ```
  1. User enters email — app calls InitiateAuth with CUSTOM_AUTH flow
  2. Define Auth Challenge Lambda: generates OTP, sends via SES/SNS, stores hash in DynamoDB
  3. Create Auth Challenge Lambda: sends challenge prompt to client
  4. Verify Auth Challenge Lambda: validates OTP hash, returns success/failure
  5. Pre Token Generation Lambda: adds custom claims to token on success
  ```
- Services Used:
  - Amazon Cognito User Pool (CUSTOM_AUTH flow)
  - AWS Lambda (Define/Create/Verify Auth Challenge triggers)
  - Amazon SES (email OTP delivery)
  - Amazon SNS (SMS OTP delivery)
  - Amazon DynamoDB (OTP storage with TTL)
- When to Apply: Consumer apps prioritizing conversion over security friction, apps where password reset UX is a business problem, compliance environments requiring phishing-resistant auth
- When NOT to Apply: High-security enterprise apps (use TOTP or hardware keys), federated user pools (Lambda triggers not available for federation flows)
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | UX | No password to forget or reset | OTP delivery latency (SMS: seconds, email: variable) |
  | Security | Phishing-resistant (no static credential to steal) | OTP interception via SIM swap (SMS), email compromise |
  | Ops | Cognito + Lambda fully managed | Lambda trigger adds auth latency; must handle retry/OTP expiry edge cases |

- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-challenge.html

---

**Pattern: User Migration Trigger (Zero-Downtime Identity Migration)**
- Category: Migration
- Problem: Migrate users from a legacy auth system to Cognito without forcing password resets for all users.
- Solution on AWS:
  ```
  1. Enable User Migration Lambda Trigger on Cognito User Pool
  2. Migration Lambda: when a user signs in and Cognito can't find them locally,
     Lambda queries the legacy auth system with the provided credentials
  3. If legacy auth succeeds: Lambda returns user attributes — Cognito creates the
     local profile and completes sign-in transparently
  4. User profile now exists in Cognito for all future logins
  5. After migration period: disable the trigger; retire legacy system
  ```
- Services Used:
  - Amazon Cognito User Pool (User Migration trigger)
  - AWS Lambda (migration trigger function)
  - Legacy auth system (via VPC Lambda or public endpoint + Secrets Manager credentials)
  - AWS Secrets Manager (legacy system credentials for Lambda)
- When to Apply: Moving from custom auth DB, Auth0, Firebase Auth, or Cognito User Pool migration
- When NOT to Apply: Federated users (no password to migrate), when user consent for re-auth is acceptable, very large user bases with known security issues in legacy passwords (force reset instead)
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | UX | Zero friction — users don't know migration happened | Legacy system stays live during migration period |
  | Security | Passwords never stored in Cognito until user successfully migrates | Migration Lambda must securely call legacy auth — potential attack surface |
  | Ops | Self-service migration driven by user activity | Long tail of inactive users never migrate — need bulk migration strategy for remainder |

- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-migrate-user.html

---

## Security Architecture

**Security Domain: Identity**

**Cognito User Pool — Workforce Identity (WIAM) with SAML Federation**
- AWS Services:
  - Amazon Cognito User Pool (SAML 2.0 SP)
  - Corporate IdP: Okta / ADFS / Azure AD (SAML 2.0 IdP)
  - AWS IAM Identity Center (for AWS Console access — separate from app auth)
  - AWS Certificate Manager (custom domain TLS)
- Architecture:
  ```
  1. Configure enterprise IdP as SAML provider in Cognito User Pool
  2. Map SAML attributes to Cognito user attributes (email, groups, department)
  3. Cognito issues OIDC tokens to the application (SAML details abstracted)
  4. Application uses groups claim for RBAC, department claim for ABAC
  5. Identity Pool exchanges Cognito JWT for AWS credentials if AWS resource access needed
  ```
- Configuration Essentials:
  ```
  - SAML assertion must include NameID (mapped to Cognito username or email)
  - Map IdP groups to Cognito user pool groups for role-claim propagation
  - Enable SAML IdP-initiated sign-on only if explicitly required (prefer SP-initiated)
  - Set appropriate assertion validity window (typically 5 min for SAML assertions)
  ```
- Verification:
  ```bash
  aws cognito-idp list-identity-providers --user-pool-id <pool-id> \
    --query 'Providers[?ProviderType==`SAML`]'
  ```
- Compliance Alignment: Supports SOC 2 CC6.1 (logical access), ISO 27001 A.9.4 (system and application access control)
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools-saml-idp.html

---

**Security Domain: Network**

**Cognito Endpoint Protection with WAF + CloudFront**
- AWS Services:
  - Amazon Cognito User Pool (OAuth2/OIDC endpoints)
  - AWS WAF v2 (web ACL attached to User Pool)
  - Amazon CloudFront (optional — for custom domain + geo-restriction)
  - AWS Certificate Manager (TLS certificate for custom domain)
- Architecture:
  ```
  Option A (WAF direct on Cognito):
  - Attach WAF Web ACL directly to User Pool (regional)
  - Managed rules: CommonRuleSet + ATPRuleSet + BotControlRuleSet
  - Rate-based rules per IP for token and authorize endpoints

  Option B (CloudFront in front of Cognito custom domain):
  - Route custom auth domain through CloudFront distribution
  - WAF attached to CloudFront (global)
  - Enables geo-restriction, edge-level rate limiting, shield advanced
  - Note: requires careful header forwarding — Cognito validates Host header
  ```
- Compliance Alignment: Supports PCI DSS Req. 6.4 (WAF), SOC 2 CC6.6 (logical access through network controls)
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-waf.html

---

**Security Domain: Detection**

**Cognito Threat Protection + CloudTrail + CloudWatch Alerts**
- AWS Services:
  - Amazon Cognito User Pool (Plus plan — Threat Protection)
  - AWS CloudTrail (API-level audit)
  - Amazon CloudWatch Logs (authentication event logs)
  - Amazon CloudWatch Alarms (anomaly detection alerts)
  - Amazon EventBridge (event routing for automated remediation)
  - AWS Lambda (automated remediation — AdminDisableUser, AdminUserGlobalSignOut)
- Architecture:
  ```
  1. Enable Threat Protection (Plus plan) — ML-based risk scoring per sign-in
  2. Configure: High risk → Block; Medium risk → MFA challenge; Low risk → Allow
  3. CloudTrail captures all Cognito management API calls
  4. Threat Protection exports user activity logs to CloudWatch Logs / S3 / Firehose
  5. CloudWatch metric filter alerts on: AdminCreateUser bursts, failed auth spikes,
     password reset volume spikes
  6. EventBridge rule triggers Lambda to AdminDisableUser on HIGH_RISK events
  ```
- Verification:
  ```bash
  # Check Threat Protection config:
  aws cognito-idp describe-user-pool --user-pool-id <pool-id> \
    --query 'UserPool.UserPoolAddOns.AdvancedSecurityMode'
  # Should be "ENFORCED" for production (not "AUDIT" — audit mode doesn't block)
  ```
- Compliance Alignment: HIPAA § 164.312(b) (audit controls), PCI DSS Req. 10.2 (implement audit trails), SOC 2 CC7.2 (anomalies and events)
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pool-settings-threat-protection.html

---

## Operational Patterns

**Operational Domain: Observability**

**Cognito Monitoring Stack**
- AWS Services:
  - Amazon CloudWatch Metrics (Cognito Service Metrics)
  - Amazon CloudWatch Logs (Threat Protection user activity logs)
  - AWS CloudTrail (API audit)
  - Amazon CloudWatch Alarms
  - AWS Service Quotas (MAU and API rate monitoring)
- Architecture:
  ```
  Key metrics to monitor:
  - TokenRefreshSuccesses / TokenRefreshFailures
  - SignUpSuccesses / SignUpThrottles
  - FederationSuccesses / FederationFailures
  - RiskDetection metrics (Plus plan)
  
  Alarms:
  - SignInFailureRate > 10% over 5 min → SNS alert (potential brute force)
  - ThrottleCount > 0 → operational alert (hitting API rate limits)
  - FederationFailures spike → IdP connectivity issue
  ```
- Cost Profile: Low — CloudWatch metrics for Cognito are included; CloudTrail data events cost extra if enabled for high-volume auth
- Automation: CloudWatch Alarms → SNS → Lambda for automated response (block IPs via WAF, suspend accounts)
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/tracking-quotas-and-usage-in-cloud-watch-and-service-quotas.html

---

**Operational Domain: Change Management**

**Cognito User Pool Configuration Management (IaC)**
- AWS Services:
  - AWS CloudFormation / AWS CDK (User Pool as code)
  - AWS Secrets Manager (App Client secrets)
  - AWS CodePipeline (deployment pipeline)
- Architecture:
  ```
  CRITICAL: Cognito User Pool replacements are destructive. CloudFormation will
  DELETE and RECREATE a User Pool if any immutable property changes (e.g., UsernameAttributes).
  This deletes all users.
  
  Safe IaC practices:
  - Set DeletionPolicy: Retain on AWS::Cognito::UserPool resources
  - Never change UsernameAttributes after pool creation (email vs. username vs. phone)
  - Use parameter-driven App Client configuration
  - Test schema changes in dev pool before production
  - Export users before any pool migration: cognito-idp list-users
  ```
- Cost Profile: No additional cost — IaC tooling cost only
- Automation: CDK Pipelines or CodePipeline for safe staged deployment; manual approval gate before production Cognito changes
- Source: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-cognito-userpool.html

---

## Reference Architectures

**Reference Architecture: B2C SaaS Application with Cognito CIAM**
- Context: Consumer-facing SaaS where end users self-register, sign in with social providers, and access per-user resources directly on the client side
- AWS Source: https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-scenarios.html
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Auth UI | Cognito Managed Login + Custom Domain | Hosted sign-up/sign-in UI with brand CSS |
  | Identity | Cognito User Pool | User directory, JWT issuance, social federation (Google/Apple) |
  | Federation | Google/Apple OAuth 2.0 → User Pool | Social sign-in normalized to Cognito JWT |
  | API Auth | API Gateway (Cognito Authorizer) | Validates JWT on all API calls |
  | Business Logic | AWS Lambda | Claim-aware authorization logic |
  | AWS Resource Access | Cognito Identity Pool + STS | Per-user S3 direct access with ABAC |
  | Storage | Amazon S3 (per-user prefix) | User-generated content, isolated by ABAC |
  | Database | Amazon DynamoDB | App data with partition key = user sub |
  | Security | AWS WAF (on User Pool + API Gateway) | Bot protection, rate limiting |
  | Audit | CloudTrail + CloudWatch | API audit trail, operational metrics |

- Key Decisions:
  - Social federation vs. local accounts: both are supported; social users cannot use TOTP MFA
  - Client-side token handling: use in-memory storage or BFF for high-security apps
  - MAU tier selection: Essentials vs Plus based on threat model
- Scaling Path:
  - Up to ~50k MAU: Free tier Cognito; Lambda @ default concurrency
  - 50k–1M MAU: Monitor Cognito API throttling limits; reserve Lambda concurrency for auth Lambdas; consider Cognito Plus for Threat Protection at this scale
  - 1M+ MAU: Evaluate Cognito regional limits; consider multi-region User Pools with Route 53 latency routing; CloudFront custom domain with geo-routing
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-scenarios.html

---

**Reference Architecture: Enterprise Internal App with SAML SSO**
- Context: Internal enterprise application where employees authenticate via corporate IdP (Okta / Azure AD / ADFS) and access AWS resources
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Corporate IdP | Okta / Azure AD (SAML 2.0) | Enterprise user directory + MFA |
  | Auth Broker | Cognito User Pool (SAML SP) | Normalizes SAML assertions to OIDC JWTs |
  | API Auth | API Gateway (Cognito Authorizer) | JWT validation for internal APIs |
  | AWS Resource Access | Cognito Identity Pool | Exchange JWT for STS credentials |
  | Access Control | IAM Roles + ABAC (department tag) | Department-based resource isolation |
  | Audit | CloudTrail | Federation event + resource access audit |

- Key Decisions:
  - MFA: delegated to corporate IdP (do not double-enforce with Cognito MFA — creates friction)
  - Token lifetime: match corporate session policy (typically 8h work day)
  - Group mapping: map IdP groups → Cognito user pool groups → IAM roles
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools-saml-idp.html

---

## Scenario Coverage

**Standard Case: Consumer mobile app with social sign-in + per-user S3 storage**
- Approach:
  - Cognito User Pool with Google/Apple federation + local signup
  - Public App Client (no secret), PKCE
  - Identity Pool for S3 credential brokering
  - ABAC: S3 prefix scoped to user `sub` via PrincipalTag
  - WAF web ACL on User Pool
- Key Decisions:
  - Feature plan: Essentials (cost-sensitive) or Plus (if handling sensitive data)
  - Token storage: in-memory for security-sensitive apps; consider BFF for highest security
  - Social vs. local: can support both in the same User Pool

**Edge Case: Multi-region high-availability Cognito for global app**
- Approach:
  - Cognito User Pools are regional and do not natively replicate
  - Pattern: active-active with Route 53 latency routing to regional User Pools
  - User creation must be replicated between pools (use post-confirmation Lambda → EventBridge → cross-region Lambda to create user in secondary pool)
  - Identity Pools are also regional — deploy in each active region
  - App Clients must be duplicated across regions — manage with CDK/CloudFormation
  - Risk: user state divergence during replication lag — architect for eventual consistency
- Approach: This is a HIGH COMPLEXITY pattern. Evaluate if CloudFront + single regional User Pool with latency optimization satisfies requirements before multi-region User Pool architecture.

**Anti-Pattern Case: Using ID Token for API authorization instead of Access Token**
- Clarification: Ask — "Is the API using the ID Token (contains user identity claims: email, name, sub) or the Access Token (contains OAuth scopes for API authorization)?" The correct pattern is Access Token for API Gateway authorization — the Access Token carries the custom scopes defined on the Resource Server. Using ID Token for API authorization is a design smell that couples identity claims to authorization logic and bypasses the Resource Server scope model. Exception: if the API only needs to know *who* the user is and doesn't use OAuth scopes, ID Token may be acceptable — but document the deviation.

---

## Service Equivalence Map (Cognito Function Context)

| Function | AWS | Google Cloud | Azure | Oracle Cloud (OCI) |
|----------|-----|-------------|-------|--------------------|
| **User Directory + OIDC IdP** | Cognito User Pool | Firebase Authentication | Azure AD B2C / Entra External ID | OCI Identity Domains (CIAM) |
| **Workforce SSO (SAML/OIDC federation)** | Cognito User Pool + IAM Identity Center | Cloud Identity + Workforce Identity Federation | Entra ID (Azure AD) | OCI Identity Domains |
| **Credentials Broker (IdP → AWS IAM)** | Cognito Identity Pool | Workload Identity Federation | Managed Identities / Federated Identity Credentials | OCI Instance Principal / Resource Principal |
| **Managed Login UI** | Cognito Managed Login | Firebase UI (open source) | Azure AD B2C User Flows | OCI Identity Domains Sign-In Page |
| **MFA** | Cognito TOTP + SMS MFA | Firebase MFA | Entra ID MFA | OCI MFA |
| **Threat Protection / Adaptive Auth** | Cognito Plus — Threat Protection | Identity Platform reCAPTCHA Enterprise | Entra ID Identity Protection (P2) | OCI Adaptive Authentication (Identity Domains Premium) |

> ⚠️ Feature parity warning: AWS Cognito lacks some enterprise CIAM capabilities present in Azure AD B2C (e.g., complex user journey orchestration, built-in CAPTCHA). For complex CIAM workflows, evaluate Cognito against dedicated CIAM platforms before committing.
