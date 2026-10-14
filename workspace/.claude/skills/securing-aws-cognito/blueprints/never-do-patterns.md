# Never Do Patterns — securing-aws-cognito

8 anti-patterns for AWS Cognito 2026 security architecture.
Each entry includes a wrong example, the correct alternative, and a detection command.

---

## 1. Decode JWT without full validation (CRITICAL)

**Why prohibited**: Decoding without signature verification and claim checks enables token forgery, privilege escalation, and cross-token-type misuse. An accepted forged token is a full data-plane compromise.

**Blast radius**: Every API endpoint trusting the token.

```python
# 🚫 WRONG — base64 decode only, no signature check, no claim validation
import base64, json
payload = json.loads(base64.b64decode(token.split('.')[1] + '=='))
user_id = payload['sub']  # NEVER DO THIS
```

```python
# ✅ CORRECT — use API Gateway Cognito authorizer or aws-jwt-verify
# API Gateway Cognito authorizer handles:
#   - JWKS fetch and key rotation
#   - Signature verification
#   - iss, aud/client_id, exp, token_use claim checks
#
# Or in Lambda (Node.js):
from aws_jwt_verify import CognitoJwtVerifier
verifier = CognitoJwtVerifier.create(
    user_pool_id="<pool-id>",
    client_id="<client-id>",
    token_use="access"  # or "id" per endpoint
)
payload = verifier.verify(token)  # raises if invalid
```

**Detection**:
```bash
# Test: send a token from a different pool — must be rejected
# Test: send an ID token where access token is expected — must be rejected (token_use check)
```

**Source**: https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html

---

## 2. Enable Implicit grant on any app client (HIGH)

**Why prohibited**: Implicit grant returns tokens in the URL fragment. URL fragments are included in browser history, server access logs, and Referer headers — anywhere the token travels, it can be intercepted.

**Blast radius**: All users of that app client.

```
# 🚫 WRONG — app client config
AllowedOAuthFlows: ["implicit", "code"]
```

```
# ✅ CORRECT — disable implicit; code only
AllowedOAuthFlows: ["code"]
# + PKCE enabled on the client side
# + No client secret on browser/mobile (public client)
```

**Detection**:
```bash
aws cognito-idp describe-user-pool-client \
  --user-pool-id <pool-id> --client-id <client-id> \
  --query 'UserPoolClient.AllowedOAuthFlows'
# Must NOT contain "implicit" or "token"
```

**Source**: https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-security-best-practices.html

---

## 3. Embed a client secret in a browser or mobile app (HIGH)

**Why prohibited**: A client secret in JavaScript source or a mobile binary is extractable by anyone who inspects the app. It provides no security for public clients.

**Blast radius**: All users of that client — secret allows impersonation of the app.

```javascript
// 🚫 WRONG — secret hardcoded in React/SPA
const CLIENT_SECRET = "abc123xyz...";  // NEVER DO THIS
```

```javascript
// ✅ CORRECT — public app client, no secret, PKCE
// No CLIENT_SECRET field in app client configuration
// PKCE provides the code_verifier/code_challenge binding instead
```

**Detection**:
```bash
aws cognito-idp describe-user-pool-client \
  --user-pool-id <pool-id> --client-id <client-id> \
  --query 'UserPoolClient.ClientSecret'
# Must be null for any SPA/mobile client
```

**Source**: https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-security-best-practices.html

---

## 4. Production user pool with MFA off (or SMS as sole factor) (HIGH)

**Why prohibited**: Without MFA, a stolen or guessed password grants full access. SMS is vulnerable to SIM-swap attacks and carrier-level interception.

**Blast radius**: Any account whose password is compromised.

```
# 🚫 WRONG
MfaConfiguration: OFF
# OR
EnabledMfas: ["SMS_MFA"]  # SMS as sole factor for high-value accounts
```

```
# ✅ CORRECT
MfaConfiguration: ON
EnabledMfas: ["SOFTWARE_TOKEN_MFA"]  # TOTP; or passkeys via Managed Login v2
# SMS allowed only as fallback, not sole factor
```

**Detection**:
```bash
aws cognito-idp describe-user-pool --user-pool-id <pool-id> \
  --query 'UserPool.{MFA:MfaConfiguration,Enabled:EnabledMfas}'
# MFA must not be OFF; EnabledMfas must include SOFTWARE_TOKEN_MFA or passkey enrollment
```

**Source**: https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-security-best-practices.html

---

## 5. Internet-facing pool with no WAF and Lite tier (no threat protection) (HIGH)

**Why prohibited**: Unprotected public auth endpoints invite credential-stuffing attacks, username enumeration, and cost-inflating API abuse — all of which hit before any application-level defense.

**Blast radius**: Whole pool; billing and availability impact.

```
# 🚫 WRONG
WebACL: none
FeaturePlan: Lite  # no threat protection
ManagedLogin: public, no WAF
```

```
# ✅ CORRECT
WebACL: attached (rate-based rule + CAPTCHA on sign-in/sign-up)
FeaturePlan: Plus  # threat protection for elevated-risk apps
ThreatProtection: AUDIT -> ENFORCED after tuning
```

**Detection**:
```bash
aws cognito-idp get-web-acl-for-resource \
  --resource-arn arn:aws:cognito-idp:<region>:<account>:userpool/<pool-id>
# WebACLArn must be present
```

**Source**: https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pool-settings-advanced-security-threat-protection.html

---

## 6. Username enumeration left enabled (PreventUserExistenceErrors not set) (MEDIUM)

**Why prohibited**: Distinct error messages ("user not found" vs "wrong password") allow attackers to determine which usernames exist, enabling targeted credential-stuffing and social-engineering campaigns.

**Blast radius**: Reconnaissance surface across the whole pool.

```
# 🚫 WRONG
PreventUserExistenceErrors: LEGACY  # or omitted on legacy clients
```

```
# ✅ CORRECT
PreventUserExistenceErrors: ENABLED  # on all production app clients
```

**Detection**:
```bash
aws cognito-idp describe-user-pool-client \
  --user-pool-id <pool-id> --client-id <client-id> \
  --query 'UserPoolClient.PreventUserExistenceErrors'
# Must be ENABLED
```

**Source**: https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-security-best-practices.html

---

## 7. Over-permissive identity-pool roles or unnecessary guest access (HIGH)

**Why prohibited**: Identity pools issue real temporary AWS credentials via STS. Wildcard roles turn a single auth event into unrestricted AWS access. Guest (unauthenticated) access multiplies the blast radius by removing the authentication requirement entirely.

**Blast radius**: Any AWS resource the role can reach; unauthenticated users if guest access is on.

```json
// 🚫 WRONG — authenticated role policy
{
  "Effect": "Allow",
  "Action": "*",
  "Resource": "*"
}
// AND AllowUnauthenticatedIdentities: true  (when not required)
```

```json
// ✅ CORRECT — scoped to specific actions/resources with per-user isolation
{
  "Effect": "Allow",
  "Action": ["s3:GetObject", "s3:PutObject"],
  "Resource": "arn:aws:s3:::my-bucket/${cognito-identity.amazonaws.com:sub}/*"
}
// AND AllowUnauthenticatedIdentities: false  (unless guest is explicitly needed)
```

**Detection**:
```bash
aws cognito-identity describe-identity-pool --identity-pool-id <id> \
  --query 'AllowUnauthenticatedIdentities'
# Must be false unless guest access is a deliberate, documented requirement
```

**Source**: https://docs.aws.amazon.com/cognito/latest/developerguide/identity-pools-security-best-practices.html

---

## 8. One user pool per tenant as the default scaling strategy (MEDIUM)

**Why prohibited**: The 1,000 user pools per AWS account is a **hard limit** — not soft, not raisable by default. Automatically provisioning a new pool per tenant will hit this ceiling and halt onboarding. High operational maintenance across pools also compounds over time.

**Blast radius**: Onboarding halts at the pool ceiling; config drift across hundreds of pools.

```
# 🚫 WRONG — automated provisioning
for each new_tenant:
    create_user_pool(name=f"pool-{tenant_id}")  # will fail at 1,000
```

```
# ✅ CORRECT — shared pool with per-tenant isolation
Strategy options (in order of preference for scale):
  1. App-client per tenant (supports per-tenant federation, shared pool config)
  2. User group per tenant (simplest, group claim in token)
  3. Custom attribute per tenant (custom:tenantId, app-enforced)
  4. Silo (pool per tenant) — only for ≤ ~50 high-value tenants requiring full isolation
  5. Cell-based architecture (sharding across multiple AWS accounts) for massive scale
```

**Detection**:
```bash
aws cognito-idp list-user-pools --max-results 60 --query 'length(UserPools)'
# If approaching 1,000, implement shared-pool strategy immediately
```

**Source**: https://docs.aws.amazon.com/cognito/latest/developerguide/multi-tenant-application-best-practices.html
