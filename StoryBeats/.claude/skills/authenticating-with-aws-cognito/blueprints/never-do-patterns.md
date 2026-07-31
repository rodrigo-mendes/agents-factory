# Never Do Patterns — Amazon Cognito (2025 feature-plan model)

Source: [research_aws-cognito_v1.md](../../../../StoryBeat/docs/research_aws-cognito_v1.md) — verified 2026-07-31

Each entry shows the prohibited code and the correct alternative side by side.

---

## Anti-Pattern 1: Embedding Client Secret in SPA / Mobile App

```javascript
// 🚫 WRONG: Secret in frontend code — extracted trivially from JS bundle
const userPool = new CognitoUserPool({
  UserPoolId: 'us-east-1_XXXXX',
  ClientId: 'xxxxxxxxxxxxxxxx',
  ClientSecret: 'abc123secretvalue'  // ❌ Visible to anyone with browser DevTools
});

// ✅ CORRECT: Public client — no secret, PKCE only
const userPool = new CognitoUserPool({
  UserPoolId: 'us-east-1_XXXXX',
  ClientId: 'xxxxxxxxxxxxxxxx'   // Public app client — no ClientSecret field
  // Implement PKCE for auth-code flow (see always-do-patterns.md Pattern 4)
});
```

**Impact of getting this wrong**: Anyone who downloads your app or reads the minified JS bundle
obtains the client secret and can impersonate your application.

Source: [User pool security best practices](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-security-best-practices.html)

---

## Anti-Pattern 2: Storing ID/Access Tokens in Browser localStorage

```javascript
// 🚫 WRONG: localStorage is readable by any XSS payload on the same origin
localStorage.setItem('id_token', tokens.IdToken);
localStorage.setItem('access_token', tokens.AccessToken);
const idToken = localStorage.getItem('id_token'); // Retrieved anywhere in the app

// ✅ CORRECT: In-memory storage — cleared on page refresh (intentional for security)
let _tokens = null;

function setTokens(tokens) {
  _tokens = {
    idToken: tokens.IdToken,
    accessToken: tokens.AccessToken,
    refreshToken: tokens.RefreshToken  // Can be in a secure HttpOnly cookie
  };
}

function getAccessToken() {
  if (!_tokens) throw new Error('Not authenticated — redirect to sign-in');
  return _tokens.accessToken;
}
```

**Server-side:** store tokens in an encrypted server-side cache (e.g., encrypted Redis), not in
plaintext session variables or a database field.

Source: [User pool security best practices](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-security-best-practices.html)

---

## Anti-Pattern 3: Granting Broad `*` IAM Role to Identity-Pool Users

```json
// 🚫 WRONG: Wildcard grants full AWS account access to every authenticated user
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": "*",
    "Resource": "*"
  }]
}

// ✅ CORRECT: Least-privilege — scope to user's own resources via cognito sub
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
    "Resource": [
      "arn:aws:s3:::my-app-data/${cognito-identity.amazonaws.com:sub}",
      "arn:aws:s3:::my-app-data/${cognito-identity.amazonaws.com:sub}/*"
    ]
  }]
}
```

**For ABAC (role-mapping rules):** add IAM session tags from Cognito claims and write policies
with `aws:PrincipalTag` conditions.

Source: [Identity pool security best practices](https://docs.aws.amazon.com/cognito/latest/developerguide/identity-pools-security-best-practices.html)

---

## Anti-Pattern 4: Enabling Guest Access Without Explicit Scoped Policy

```bash
# 🚫 WRONG: Guest access enabled with no thought about who can call this
aws cognito-identity update-identity-pool \
  --identity-pool-id <POOL_ID> \
  --allow-unauthenticated-identities  # Anyone knowing the (non-secret) pool ID gets AWS creds

# ✅ CORRECT: Deactivated by default; enable only with explicit minimal role
aws cognito-identity update-identity-pool \
  --identity-pool-id <POOL_ID> \
  --no-allow-unauthenticated-identities   # Default safe state
```

**If guest access is legitimately required (e.g., mobile pre-login asset fetch):**
The unauthenticated IAM role must be restricted to the minimum necessary (e.g., `s3:GetObject` on a
single public prefix) — never `*` on any resource.

Source: [Identity pool security best practices](https://docs.aws.amazon.com/cognito/latest/developerguide/identity-pools-security-best-practices.html)

---

## Anti-Pattern 5: Static or Predictable PKCE Code Verifier

```javascript
// 🚫 WRONG: Static string — PKCE protection is nullified
const codeVerifier = 'my-constant-pkce-verifier';  // ❌ Predictable → CSRF possible

// 🚫 ALSO WRONG: Low-entropy random
const codeVerifier = Math.random().toString(36).slice(2);  // ❌ Insufficient entropy

// ✅ CORRECT: Cryptographically random, fresh per authorization request
function generateCodeVerifier() {
  const array = new Uint8Array(32);       // 256 bits
  crypto.getRandomValues(array);          // CSPRNG
  return btoa(String.fromCharCode(...array))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '');                   // URL-safe base64, ≥ 43 chars
}

// Called fresh at the START of every authorization flow
const verifier = generateCodeVerifier();  // Different every time
sessionStorage.setItem('pkce_verifier', verifier);
// Clear immediately after token exchange:
sessionStorage.removeItem('pkce_verifier');
```

Source: [User pool security best practices](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-security-best-practices.html)

---

## Anti-Pattern 6: Mixing Internal and External Trust in One Identity Pool

```bash
# 🚫 WRONG: Developer provider (internal) + social (public) in the same pool
# Internal trust level and external/social trust level share the same role-selection rules
aws cognito-identity update-identity-pool \
  --supported-login-providers '{"accounts.google.com":"<GOOGLE_CLIENT_ID>"}' \
  --developer-provider-name 'login.myapp.internal'
# Risk: cross-contamination of trust boundaries; role-mapping logic becomes complex and error-prone

# ✅ CORRECT: Separate identity pools per trust boundary
# Pool A — Enterprise / developer-authenticated identities only
aws cognito-identity create-identity-pool \
  --identity-pool-name EnterprisePool \
  --developer-provider-name 'login.myapp.internal' \
  --no-allow-unauthenticated-identities

# Pool B — Social/public providers only (if needed)
aws cognito-identity create-identity-pool \
  --identity-pool-name PublicPool \
  --supported-login-providers '{"accounts.google.com":"<GOOGLE_CLIENT_ID>"}' \
  --no-allow-unauthenticated-identities
```

Source: [Identity pool security best practices](https://docs.aws.amazon.com/cognito/latest/developerguide/identity-pools-security-best-practices.html)

---

## Anti-Pattern 7: Polling AdminGetUser/GetUser for Attributes on Every Request

```python
# 🚫 WRONG: API call per HTTP request — hits UserRead quota (120 RPS default)
@app.middleware("http")
async def enrich_request_with_user(request: Request, call_next):
    username = extract_username_from_header(request)
    user = cognito_client.admin_get_user(      # ❌ Cognito API call per request
        UserPoolId=POOL_ID,
        Username=username
    )
    request.state.user_attrs = {
        a['Name']: a['Value'] for a in user['UserAttributes']
    }
    return await call_next(request)


# ✅ CORRECT: Read validated JWT claims (no API call required)
@app.middleware("http")
async def enrich_request_from_jwt(request: Request, call_next):
    token = request.headers.get('Authorization', '').removeprefix('Bearer ')
    claims = validate_cognito_jwt(token, POOL_ID, REGION, CLIENT_ID)
    # Claims are already validated cryptographically — no API call needed
    request.state.user_attrs = claims
    return await call_next(request)

# For high-churn attributes not in the JWT:
# Use an external DB (DynamoDB) keyed on cognito:sub — do NOT call AdminGetUser per request
```

**Impact of getting this wrong:** `AdminGetUser` consumes `UserRead` quota (120 RPS default,
shared across the Region). Under load, your service throttles with `ThrottleException`.

Source: [Quotas — optimize API calls](https://docs.aws.amazon.com/cognito/latest/developerguide/quotas.html)
