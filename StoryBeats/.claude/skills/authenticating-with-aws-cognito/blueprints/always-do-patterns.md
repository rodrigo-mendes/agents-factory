# Always Do Patterns — Amazon Cognito (2025 feature-plan model)

Source: [research_aws-cognito_v1.md](../../../../StoryBeat/docs/research_aws-cognito_v1.md) — verified 2026-07-31

---

## Pattern 1: Least-Privilege Identity-Pool IAM Roles with Trust Conditions

IAM roles attached to identity pools must restrict assumption via `cognito-identity.amazonaws.com:aud`
(must match the identity pool ID) and `:amr` (`authenticated` or `unauthenticated`).

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Federated": "cognito-identity.amazonaws.com" },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "cognito-identity.amazonaws.com:aud": "us-east-1:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
        },
        "ForAnyValue:StringLike": {
          "cognito-identity.amazonaws.com:amr": "authenticated"
        }
      }
    }
  ]
}
```

**Resource policy — scope to the user's own prefix using ABAC:**
```json
{
  "Statement": [{
    "Effect": "Allow",
    "Action": ["s3:GetObject", "s3:PutObject"],
    "Resource": "arn:aws:s3:::my-app-bucket/${cognito-identity.amazonaws.com:sub}/*"
  }]
}
```

Source: [Identity pool security best practices](https://docs.aws.amazon.com/cognito/latest/developerguide/identity-pools-security-best-practices.html)

---

## Pattern 2: Enhanced Identity-Pool Flow (GetCredentialsForIdentity)

Use the enhanced flow (`GetCredentialsForIdentity`) as the default. It hides STS mechanics and
applies a scope-down policy that caps unauthenticated permissions.

```python
import boto3

client = boto3.client('cognito-identity', region_name='us-east-1')

# ✅ Enhanced flow — single call, role selected centrally in the identity pool
response = client.get_credentials_for_identity(
    IdentityId=identity_id,
    Logins={
        'cognito-idp.us-east-1.amazonaws.com/<POOL_ID>': id_token
    }
)
creds = response['Credentials']
# Use: creds['AccessKeyId'], creds['SecretKey'], creds['SessionToken']
```

Source: [Identity pool security best practices](https://docs.aws.amazon.com/cognito/latest/developerguide/identity-pools-security-best-practices.html)

---

## Pattern 3: Passkeys/WebAuthn First; Else SRP + MFA (Essentials/Plus)

Passkeys are phishing-resistant; prefer them over passwords for Essentials/Plus pools.
For password flows, always use SRP (password never leaves the client).

```bash
# ✅ Create Essentials pool with passkey support enabled
aws cognito-idp create-user-pool \
  --pool-name MyPool \
  --user-pool-tier ESSENTIALS \
  --passkey-configuration '{"RelyingPartyId":"example.com","UserVerification":"required"}'
```

**SRP auth flow (Python — aws-srp library):**
```python
import boto3
from warrant.aws_srp import AWSSRP

client = boto3.client('cognito-idp', region_name='us-east-1')

srp = AWSSRP(
    username=username,
    password=password,  # Never sent to server in plaintext
    pool_id=POOL_ID,
    client_id=CLIENT_ID,
    client=client
)
tokens = srp.authenticate_user()  # Returns ChallengeParameters for SRP exchange
```

Source: [User pool security best practices](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-security-best-practices.html)

---

## Pattern 4: Auth-Code + PKCE for Public Clients (SPA, Mobile)

Generate a fresh cryptographically random code verifier (≥ 43 chars, URL-safe base64) per
authorization request. Never reuse verifiers.

```javascript
// ✅ Fresh PKCE verifier + challenge per authorization request
function generateCodeVerifier() {
  const array = new Uint8Array(32); // 256 bits of entropy
  crypto.getRandomValues(array);
  return btoa(String.fromCharCode(...array))
    .replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
}

async function generateCodeChallenge(verifier) {
  const data = new TextEncoder().encode(verifier);
  const digest = await crypto.subtle.digest('SHA-256', data);
  return btoa(String.fromCharCode(...new Uint8Array(digest)))
    .replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
}

// On each auth initiation — never cache the verifier across requests
const verifier = generateCodeVerifier();
const challenge = await generateCodeChallenge(verifier);
sessionStorage.setItem('pkce_verifier', verifier); // Cleared after token exchange
```

Source: [User pool security best practices](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-security-best-practices.html)

---

## Pattern 5: Client Secrets in AWS Secrets Manager (Server-Side Only)

Confidential (server-side) clients hold secrets. Store in Secrets Manager; never hardcode.

```python
import boto3
import json
import hmac
import hashlib
import base64

def get_cognito_secret(secret_name: str) -> str:
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])['cognito_client_secret']

def compute_secret_hash(username: str, client_id: str, client_secret: str) -> str:
    """Required for confidential clients — compute per-request."""
    message = username + client_id
    dig = hmac.new(client_secret.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).digest()
    return base64.b64encode(dig).decode()

# Usage
client_secret = get_cognito_secret('prod/cognito/client-secret')
secret_hash = compute_secret_hash(username, CLIENT_ID, client_secret)
```

Source: [User pool security best practices](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-security-best-practices.html)

---

## Pattern 6: Attach AWS WAF Web ACL to User-Pool Endpoints

Attach a WAF ACL to provide CAPTCHA, rate-limiting, and drop rules against credential stuffing.

```bash
# ✅ Associate WAF web ACL (WAFv2, regional scope required for Cognito)
aws cognito-idp associate-web-acl \
  --user-pool-arn "arn:aws:cognito-idp:<REGION>:<ACCOUNT>:userpool/<POOL_ID>" \
  --web-acl-arn "arn:aws:wafv2:<REGION>:<ACCOUNT>:regional/webacl/<NAME>/<UUID>"

# Verify
aws cognito-idp get-web-acl-for-resource \
  --resource-arn "arn:aws:cognito-idp:<REGION>:<ACCOUNT>:userpool/<POOL_ID>"
# Expected: WebACLArn field populated
```

Sources: [Using security features](https://docs.aws.amazon.com/cognito/latest/developerguide/managing-security.html); [User pool security best practices](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-security-best-practices.html)

---

## Pattern 7: Enable Threat Protection (Plus Tier)

Threat protection (compromised-credential detection + adaptive authentication) requires Plus tier.
Setting `AdvancedSecurityMode` to `ENFORCED` automatically upgrades the pool to Plus.

```bash
# ✅ Upgrade to Plus and enforce threat protection
aws cognito-idp update-user-pool \
  --user-pool-id <POOL_ID> \
  --user-pool-tier PLUS \
  --user-pool-add-ons '{"AdvancedSecurityMode":"ENFORCED"}'
```

Source: [Feature plans](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-sign-in-feature-plans.html)

---

## Pattern 8: Enable PreventUserExistenceErrors and Case Sensitivity

Prevents user enumeration (generic errors on failed sign-in); enforce consistent case policies.

```bash
# ✅ Enable on the app client
aws cognito-idp update-user-pool-client \
  --user-pool-id <POOL_ID> \
  --client-id <CLIENT_ID> \
  --prevent-user-existence-errors ENABLED

# ✅ Set case-sensitivity at pool creation (cannot change after creation)
aws cognito-idp create-user-pool \
  --pool-name MyPool \
  --username-configuration '{"CaseSensitive":false}'
```

Source: [Using security features](https://docs.aws.amazon.com/cognito/latest/developerguide/managing-security.html)

---

## Pattern 9: Enable Deletion Protection on Production Pools

```bash
# ✅ Enable deletion protection
aws cognito-idp update-user-pool \
  --user-pool-id <POOL_ID> \
  --deletion-protection ACTIVE

# Verify
aws cognito-idp describe-user-pool \
  --user-pool-id <POOL_ID> \
  --query 'UserPool.DeletionProtection'
# Expected: "ACTIVE"
```

Source: [Using security features](https://docs.aws.amazon.com/cognito/latest/developerguide/managing-security.html)

---

## Pattern 10: Validate JWTs Client-Side Against JWKS (Cached)

Never call the API to validate tokens per request. Fetch JWKS once and cache it; validate locally.

```python
from functools import lru_cache
from jose import jwk, jwt
import requests

@lru_cache(maxsize=1)
def get_jwks(pool_id: str, region: str) -> dict:
    """Cache JWKS — do NOT fetch per request (jwks.json limit: 50,000 RPS)."""
    url = f"https://cognito-idp.{region}.amazonaws.com/{pool_id}/.well-known/jwks.json"
    return requests.get(url, timeout=5).json()

def validate_cognito_jwt(
    token: str,
    pool_id: str,
    region: str,
    client_id: str,
    token_use: str = "access"  # "id" or "access"
) -> dict:
    jwks = get_jwks(pool_id, region)
    header = jwt.get_unverified_header(token)
    key = next(k for k in jwks['keys'] if k['kid'] == header['kid'])

    claims = jwt.decode(
        token,
        jwk.construct(key),
        algorithms=['RS256'],
        audience=client_id,
        issuer=f"https://cognito-idp.{region}.amazonaws.com/{pool_id}"
    )

    assert claims.get('token_use') == token_use, f"Expected token_use={token_use}"
    return claims

# Token caching — refresh at ~75% of lifetime, not at expiry
# Revoke on sign-out: boto3.client('cognito-idp').revoke_token(Token=refresh_token, ClientId=CLIENT_ID)
```

**Minimize scopes**: request only what's needed; omitting `openid` yields access-token-only responses.

Sources: [User pool JWTs](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-with-identity-providers.html); [Token caching](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-caching-tokens.html); [Quotas](https://docs.aws.amazon.com/cognito/latest/developerguide/quotas.html)
