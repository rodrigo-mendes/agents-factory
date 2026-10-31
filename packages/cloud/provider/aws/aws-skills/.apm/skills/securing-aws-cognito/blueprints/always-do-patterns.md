# Always Do Patterns — securing-aws-cognito

9 mandatory patterns for AWS Cognito 2026 security architecture.
Source: all patterns triangulated against official AWS documentation (accessed 2026-08-26).

---

## 1. Full server-side JWT validation on every request

**Why**: Decoding a JWT is not validating it. An unverified token enables token forgery, privilege escalation, and cross-token-type misuse. All six checks are mandatory — omitting any single one is a critical security gap.

**Required checks**:
1. Signature — verified against the user pool JWKS endpoint
2. `iss` — must equal `https://cognito-idp.<region>.amazonaws.com/<userPoolId>`
3. `aud` (ID token) or `client_id` (access token) — must match your app client
4. `exp` — must be in the future (not expired)
5. `token_use` — must be `"id"` or `"access"` per the endpoint's expectation

**Recommended implementations**:
- API Gateway Cognito authorizer (handles JWKS fetch, signature, and claim checks automatically)
- `aws-jwt-verify` library (Node.js, TypeScript) — vetted, handles key rotation

**Verification**:
```bash
aws apigateway get-authorizer --rest-api-id <api-id> --authorizer-id <auth-id> \
  --query '{type:type,identitySource:identitySource,providerARNs:providerARNs}'
# Expected: type=COGNITO_USER_POOLS
```

**Source**: https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html

---

## 2. Authorization Code grant + PKCE for public clients (never Implicit)

**Why**: Implicit grant returns tokens in the URL fragment — logged by servers/proxies, accessible to JS. A client secret embedded in browser/mobile JS is extractable by anyone.

**Rules**:
- SPA / mobile → public app client, **no secret**, `code` grant only, PKCE enabled
- Server-side / backend → confidential client with secret, `code` grant
- Disable `implicit` and `token` (resource-owner password credentials) grants on app clients

**Verification**:
```bash
aws cognito-idp describe-user-pool-client \
  --user-pool-id <pool-id> --client-id <client-id> \
  --query 'UserPoolClient.{Flows:AllowedOAuthFlows,Secret:ClientSecret}'
# Expected: Flows=["code"], Secret=null for public clients
```

**Source**: https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-security-best-practices.html

---

## 3. Enable MFA — prefer TOTP or passkeys; SMS is fallback only

**Why**: MFA is the single most effective control against account takeover. A stolen password alone should never grant access. SMS is vulnerable to SIM-swap and interception.

**Configuration**:
- Set `MfaConfiguration: ON` (Required) or use Plus-tier adaptive auth for risk-based enforcement
- Enable TOTP (`SOFTWARE_TOKEN_MFA`) and/or passkeys via Managed Login v2 (Essentials/Plus)
- Allow SMS only as a fallback, not as the primary or sole factor

**Verification**:
```bash
aws cognito-idp describe-user-pool --user-pool-id <pool-id> \
  --query 'UserPool.{MFA:MfaConfiguration,EnabledMFAs:EnabledMfas}'
# Expected: MFA=ON or OPTIONAL (with adaptive), EnabledMFAs includes SOFTWARE_TOKEN_MFA
```

**Source**: https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-security-best-practices.html

---

## 4. Enable PreventUserExistenceErrors on every app client

**Why**: Without this, error messages distinguish between "no such user" and "wrong password", enabling targeted enumeration attacks. Must be explicitly enabled — legacy clients may have it off.

**Verification**:
```bash
aws cognito-idp describe-user-pool-client \
  --user-pool-id <pool-id> --client-id <client-id> \
  --query 'UserPoolClient.PreventUserExistenceErrors'
# Expected: ENABLED
```

**Source**: https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-security-best-practices.html

---

## 5. Attach an AWS WAF web ACL to internet-facing user pools

**Why**: WAF sits in front of Managed Login and Cognito API endpoints, dropping credential-stuffing and abusive traffic before it hits (and bills) authentication.

**Minimum rule set**:
- Rate-based rule on sign-in/sign-up paths
- CAPTCHA or challenge action on suspicious patterns
- Combine with Plus-tier threat protection for risk scoring

**Verification**:
```bash
aws cognito-idp get-web-acl-for-resource \
  --resource-arn arn:aws:cognito-idp:<region>:<account>:userpool/<pool-id>
# Expected: WebACLArn present (non-empty)
```

**Source**: https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-security-best-practices.html

---

## 6. Keep token lifetimes short; secure tokens in transit and storage

**Why**: Longer token validity widens the compromise window. Tokens may carry PII and security-model claims.

**Guidance**:
- Set short `AccessTokenValidity` and `IdTokenValidity` — specific values are organization/policy-dependent; official docs mandate "short" without specifying a fixed number
- Bound `RefreshTokenValidity`; consider refresh-token rotation
- HTTPS only — never HTTP
- High-risk apps: avoid `localStorage`; prefer `httpOnly` cookies or in-memory storage

**Verification**:
```bash
aws cognito-idp describe-user-pool-client \
  --user-pool-id <pool-id> --client-id <client-id> \
  --query 'UserPoolClient.{AccessTV:AccessTokenValidity,IdTV:IdTokenValidity,RefreshTV:RefreshTokenValidity}'
```

**Source**: https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-with-identity-providers.html

---

## 7. Apply least privilege to identity-pool IAM roles; disable guest access unless required

**Why**: Identity pools issue real temporary AWS credentials via STS. Over-scoped roles turn an identity breach into broad AWS access. Unauthenticated (guest) access compounds the risk.

**Configuration**:
- Scope authenticated role to minimum required actions and resources
- Use IAM policy variables for per-user isolation: `${cognito-identity.amazonaws.com:sub}`
- Set `AllowUnauthenticatedIdentities: false` unless the design explicitly requires guest access

**Verification**:
```bash
aws cognito-identity describe-identity-pool --identity-pool-id <id> \
  --query '{GuestEnabled:AllowUnauthenticatedIdentities}'
# Expected: GuestEnabled=false (unless deliberate)
```

**Source**: https://docs.aws.amazon.com/cognito/latest/developerguide/identity-pools-security-best-practices.html

---

## 8. Enable deletion protection on all production user pools

**Why**: A user-pool deletion is unrecoverable — the entire user directory is gone. This is an existential risk for production.

**Verification**:
```bash
aws cognito-idp describe-user-pool --user-pool-id <pool-id> \
  --query 'UserPool.DeletionProtection'
# Expected: ACTIVE
```

**IaC**: Set `DeletionProtection: ACTIVE` in CloudFormation/CDK/Terraform; gate changes behind PR review.

**Source**: https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-security-best-practices.html

---

## 9. Plus tier: enable threat protection in audit-only mode first, then full-function

**Why**: Threat protection (adaptive auth, compromised-credentials detection, IP allow/deny) is powerful but needs tuning. Enabling in full-function immediately risks blocking legitimate users before you understand your traffic patterns.

**Sequence**:
1. Enable threat protection in **audit-only** mode
2. Review generated risk events and logs for 1–2 weeks
3. Set up log export (CloudWatch Logs / S3 / Data Firehose) for SIEM analysis
4. Tune automatic responses (allow / require MFA / block) based on observed risk distribution
5. Switch to **full-function** mode

**Verification**:
```bash
# Confirm threat protection is enabled and mode is recorded
aws cognito-idp describe-user-pool --user-pool-id <pool-id> \
  --query 'UserPool.UserPoolAddOns'
# Expected: AdvancedSecurityMode=AUDIT or ENFORCED (ENFORCED = full-function)
```

**Source**: https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pool-settings-advanced-security-threat-protection.html
