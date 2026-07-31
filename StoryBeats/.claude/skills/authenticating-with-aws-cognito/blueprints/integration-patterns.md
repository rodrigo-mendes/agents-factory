# Integration Patterns — Amazon Cognito (2025 feature-plan model)

Source: [research_aws-cognito_v1.md](../../../../StoryBeat/docs/research_aws-cognito_v1.md) — verified 2026-07-31

---

## Cognito ↔ API Gateway REST (COGNITO_USER_POOLS Authorizer)

**Use case:** Protect REST API methods with Cognito JWT validation at the API Gateway layer.

**Token to use:**
- **ID token** → authorize on identity claims (user identity, groups)
- **Access token** → authorize on custom OAuth2 scopes via resource servers

**Setup (AWS CLI):**
```bash
# 1. Create the authorizer
aws apigateway create-authorizer \
  --rest-api-id <API_ID> \
  --name CognitoAuthorizer \
  --type COGNITO_USER_POOLS \
  --provider-arns "arn:aws:cognito-idp:<REGION>:<ACCOUNT>:userpool/<POOL_ID>" \
  --identity-source "method.request.header.Authorization"

# 2. Attach to a method
aws apigateway update-method \
  --rest-api-id <API_ID> \
  --resource-id <RESOURCE_ID> \
  --http-method GET \
  --patch-operations \
    '[{"op":"replace","path":"/authorizationType","value":"COGNITO_USER_POOLS"},
      {"op":"replace","path":"/authorizerId","value":"<AUTHORIZER_ID>"}]'
```

**Client request:**
```bash
curl -H "Authorization: <ID_TOKEN_OR_ACCESS_TOKEN>" \
  https://<API_ID>.execute-api.<REGION>.amazonaws.com/<STAGE>/resource
```

**For AWS IAM-credential-based access:** set the method authorization type to `AWS_IAM` and use
identity-pool credentials (SigV4 signed requests) instead of a Cognito authorizer.

Source: [Control access to REST APIs using Cognito user pools](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-integrate-with-cognito.html)

---

## Cognito ↔ API Gateway HTTP API (JWT Authorizer)

> **[unverified in research]** — issuer/audience/scope specifics not confirmed against the
> HTTP-API JWT-authorizer page. Validate against
> `docs.aws.amazon.com/apigateway/latest/developerguide/http-api-jwt-authorizer.html` before use.

**High-confidence summary:**
- HTTP APIs have a native JWT authorizer (lower latency than REST authorizers)
- Typically validates the **access token** (with scopes)
- Configure `issuer` = `https://cognito-idp.<REGION>.amazonaws.com/<POOL_ID>`
- Configure `audience` = your app client ID

---

## Cognito ↔ Lambda Triggers (User-Pool Customization)

Lambda triggers run synchronously within the Cognito auth flow. They block sign-in if they throw.

**Key triggers and their use:**

| Trigger | When it runs | Common use |
|---|---|---|
| Pre sign-up | After `SignUp` API call | Validate custom fields, auto-confirm, auto-verify |
| Pre authentication | Before password verification | Block sign-in based on custom logic |
| Post authentication | After successful sign-in | Logging, analytics |
| Pre token generation | Before tokens are issued | Add/modify/suppress JWT claims and scopes |
| Custom auth: Define/Create/Verify | Custom challenge flow | TOTP, biometrics, custom OTP |
| User migration | When user not found locally | Migrate users from legacy system on first sign-in |
| Custom message | Before Cognito sends SMS/email | Customize message content |

**Pre-token generation (add custom claims — Essentials/Plus for access token v2 events):**
```python
def handler(event, context):
    # V1 event: modify ID token claims only
    # V2 event (Essentials/Plus): modify both ID and access token claims
    if event.get('triggerSource') == 'TokenGeneration_Authentication':
        event['response']['claimsAndScopeOverrideDetails'] = {
            'idTokenGeneration': {
                'claimsToAddOrOverride': {
                    'tenant_id': get_tenant_for_user(event['userName']),
                    'custom:role': compute_role(event['request']['userAttributes'])
                },
                'claimsToSuppress': ['address']  # Remove PII if not needed by clients
            }
        }
    return event
```

**User migration trigger (lazy migration from legacy system):**
```python
def handler(event, context):
    if event['triggerSource'] == 'UserMigration_Authentication':
        user = legacy_auth(event['userName'], event['request']['password'])
        if user:
            event['response']['userAttributes'] = {
                'email': user.email,
                'email_verified': 'true',
                'custom:legacy_id': user.id
            }
            event['response']['finalUserStatus'] = 'CONFIRMED'
            event['response']['messageAction'] = 'SUPPRESS'
    return event
```

Sources: [User pools custom UX](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-identity-pools.html); [Understanding JWTs](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-with-identity-providers.html)

---

## Cognito ↔ M2M Token Caching via API Gateway

**Use case:** High-volume service-to-service (client-credentials) traffic that risks exceeding the
`ClientAuthentication` quota (150 RPS, non-adjustable).

**Pattern:** API Gateway caching proxy in front of `/oauth2/token`.

```
Service A ──▶ API Gateway (cache) ──▶ Cognito /oauth2/token
                  │
                  └─ Cache hit: return cached token (TTL < token lifetime)
                  └─ Cache miss: call Cognito, cache the response
```

**Cache configuration rules:**
- **Cache key**: `scope` query parameter + `Authorization` header (Basic auth with client_id:client_secret)
- **Cache TTL**: must be **shorter than the access-token lifetime** (e.g., if tokens are valid 1 hour, cache for 50 minutes)
- **Never cache expired tokens**: validate `expires_in` before caching

**Alternative caches:** ElastiCache (Redis OSS) or DynamoDB for distributed token caches.

```python
import boto3
import time
import base64
import json
import urllib.request
import urllib.parse

class CognitoTokenCache:
    """Simple in-process M2M token cache — replace with Redis for distributed services."""

    def __init__(self, client_id: str, client_secret: str, token_url: str):
        self._client_id = client_id
        self._client_secret = client_secret
        self._token_url = token_url
        self._cache: dict = {}

    def get_token(self, scope: str) -> str:
        cached = self._cache.get(scope)
        # Refresh at 75% of lifetime, not at expiry
        if cached and time.time() < cached['expires_at']:
            return cached['token']
        return self._fetch_and_cache(scope)

    def _fetch_and_cache(self, scope: str) -> str:
        credentials = base64.b64encode(
            f"{self._client_id}:{self._client_secret}".encode()
        ).decode()
        data = urllib.parse.urlencode({
            'grant_type': 'client_credentials',
            'scope': scope
        }).encode()
        req = urllib.request.Request(
            self._token_url,
            data=data,
            headers={'Authorization': f'Basic {credentials}',
                     'Content-Type': 'application/x-www-form-urlencoded'}
        )
        with urllib.request.urlopen(req) as resp:
            body = json.loads(resp.read())

        # Cache at 75% of lifetime
        ttl = body['expires_in'] * 0.75
        self._cache[scope] = {
            'token': body['access_token'],
            'expires_at': time.time() + ttl
        }
        return body['access_token']
```

Source: [Caching M2M access tokens](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-caching-tokens.html)

---

## Multi-Tenant SaaS — Isolation Model Selection

Quota planning: Cognito quotas are **per AWS account per Region and shared across all tenants**.
Model tenant count against quotas before committing to an isolation model.

| Model | Isolation | Key quota | Use when |
|---|---|---|---|
| **Pool per tenant** | Highest — separate directory, security config, admin IAM | 1,000 pools/Region (→ 10,000) | Regulatory isolation, per-tenant admin delegation, strict data separation |
| **App client per tenant** | Medium — shared directory, per-tenant app config | 1,000 clients/pool (→ 10,000) | Shared directory acceptable, per-tenant config needed |
| **Group per tenant** | Lower — tenant tag on shared profile | 10,000 groups/pool, 100 groups/user | Lightweight tagging, minimal isolation required |
| **Custom attribute per tenant** | Lower — tenant stamped on profile/token | 50 custom attributes/pool (hard) | Simple tenant identification only |
| **Custom scope per tenant** | Medium (authz) | 100 scopes/resource server (hard) | Per-tenant API scope authorization |

**Critical cross-tenant caveat (Managed login):**
A local user's Managed login session cookie authenticates them across all app clients in the same
pool (cookie lifetime: fixed 1 hour). To prevent cross-tenant SSO leakage:
- Use **one pool per tenant**, OR
- Replace Managed login / hosted-UI sign-in with **API-based sign-in** (call `InitiateAuth` directly)

**IAM granularity caveat:** Cognito IAM scoping is at the user-pool and identity-pool level only.
You cannot scope admin permissions to a single app client. If per-tenant admin separation is
required → one pool per tenant is the only compliant model.

```bash
# ✅ Pool-per-tenant setup (highest isolation)
for TENANT_ID in tenant-a tenant-b tenant-c; do
  aws cognito-idp create-user-pool \
    --pool-name "AppPool-${TENANT_ID}" \
    --user-pool-tier ESSENTIALS \
    --deletion-protection ACTIVE \
    --tags "Key=TenantId,Value=${TENANT_ID}"
done
```

Source: [Multi-tenant application best practices](https://docs.aws.amazon.com/cognito/latest/developerguide/multi-tenant-application-best-practices.html)
